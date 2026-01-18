"""
MCP-enabled Inventory Agent.

This version uses the Model Context Protocol to dynamically
discover and call inventory service tools.
"""

import asyncio
import logging
from typing import Any, Dict, List

from metrics.agent_metrics import (
    actions_taken_total,
    guardrail_validations_total,
    low_stock_parts,
    parts_awaiting_approval,
    track_decision_time,
)
from tools.guardrail_client import GuardrailError, validate_action
from tools.guardrail_client_mcp import MCPError as GuardrailMCPError
from tools.guardrail_client_mcp import validate_action_mcp
from tools.inventory_tools_mcp import (
    MCPError,
    check_availability_mcp,
    discover_inventory_tools,
    get_low_stock_parts_mcp,
    get_part_by_number_mcp,
)

from agents.state import AgentState

logger = logging.getLogger(__name__)


class InventoryAgentMCP:
    """
    MCP-enabled Inventory Agent.

    This agent uses MCP to dynamically discover and use
    inventory service capabilities.
    """

    def __init__(self):
        """Initialize the MCP-enabled inventory agent."""
        self.name = "Inventory Agent (MCP)"
        self._tools_discovered = False

    async def ensure_tools_discovered(self):
        """Ensure we've discovered available tools (one-time setup)."""
        if not self._tools_discovered:
            try:
                await discover_inventory_tools()
                self._tools_discovered = True
            except MCPError as e:
                logger.error(f"Failed to discover MCP tools: {e}")

    def process(self, state: AgentState) -> AgentState:
        """
        Process the event synchronously (wraps async logic).

        This maintains compatibility with the existing workflow
        while using async MCP calls internally.
        """
        return asyncio.run(self._process_async(state))

    @track_decision_time("inventory-agent-mcp")
    async def _process_async(self, state: AgentState) -> AgentState:
        """
        Process the event and take inventory-related actions using MCP.
        """
        logger.info(f"[{self.name}] Processing event: {state['event_type']}")

        # Ensure MCP tools are discovered
        await self.ensure_tools_discovered()

        state["parts_available"] = {}
        state["recommended_actions"] = []
        state["actions_taken"] = []

        if state.get("required_parts"):
            await self._check_required_parts(state)

        await self._check_low_stock_parts(state)
        self._generate_decision(state)

        logger.info(f"[{self.name}] Processing complete")
        return state

    async def _check_required_parts(self, state: AgentState) -> None:
        """Check availability of required parts using MCP."""
        required_parts = state.get("required_parts", [])

        logger.info(
            f"[{self.name}] Checking {len(required_parts)} required parts via MCP"
        )

        for part_number in required_parts:
            try:
                # Use MCP tool to get part info
                part = await get_part_by_number_mcp(part_number)
                available = part.quantity > 0
                state["parts_available"][part_number] = available

                if available:
                    logger.info(
                        f"  ✅ {part.name}: {part.quantity} units available (via MCP)"
                    )

                    if part.low_stock:
                        logger.warning(
                            f"  ⚠️  {part.name} is LOW STOCK ({part.quantity}/{part.minimum_quantity})"
                        )
                        state["recommended_actions"].append(
                            f"Reorder {part.name} - stock is below minimum"
                        )
                else:
                    logger.error(f"  ❌ {part.name}: OUT OF STOCK!")
                    state["recommended_actions"].append(
                        f"URGENT: Order {part.name} immediately - no stock available"
                    )
                    state["should_escalate"] = True

                state["actions_taken"].append(
                    {
                        "action": "check_availability_mcp",
                        "part": part_number,
                        "result": f"{part.quantity} units available",
                        "low_stock": part.low_stock,
                        "protocol": "MCP",
                    }
                )

                actions_taken_total.labels(
                    action_type="check_availability_mcp", result="success"
                ).inc()

            except MCPError as e:
                logger.error(f"  ❌ MCP Error checking {part_number}: {e}")
                state["parts_available"][part_number] = False
                state["actions_taken"].append(
                    {
                        "action": "check_availability_mcp",
                        "part": part_number,
                        "error": str(e),
                        "protocol": "MCP",
                    }
                )

                actions_taken_total.labels(
                    action_type="check_availability_mcp", result="failed"
                ).inc()

    async def _check_low_stock_parts(self, state: AgentState) -> None:
        """Check for low stock parts using MCP."""
        try:
            # Use MCP tool to get low stock parts
            low_stock_parts_list = await get_low_stock_parts_mcp()

            low_stock_parts.set(len(low_stock_parts_list))

            if low_stock_parts_list:
                logger.warning(
                    f"[{self.name}] Found {len(low_stock_parts_list)} low stock parts (via MCP)"
                )

                for part_data in low_stock_parts_list:
                    part_name = part_data.get("name")
                    quantity = part_data.get("quantity")
                    min_qty = part_data.get("minimum_quantity")
                    reorder_qty = part_data.get("recommended_reorder")

                    logger.warning(f"  ⚠️  {part_name}: {quantity}/{min_qty} units")

                    state["recommended_actions"].append(
                        f"Reorder {part_name}: current={quantity}, "
                        f"minimum={min_qty}, recommend={reorder_qty} units"
                    )

                state["actions_taken"].append(
                    {
                        "action": "check_low_stock_mcp",
                        "result": f"Found {len(low_stock_parts_list)} parts below minimum",
                        "protocol": "MCP",
                    }
                )
            else:
                logger.info(
                    f"[{self.name}] All parts adequately stocked (verified via MCP)"
                )
                state["actions_taken"].append(
                    {
                        "action": "check_low_stock_mcp",
                        "result": "All parts above minimum quantity",
                        "protocol": "MCP",
                    }
                )

        except MCPError as e:
            logger.error(f"[{self.name}] MCP Error checking low stock: {e}")

    async def _attempt_reserve_part(
        self, state: AgentState, part_number: str, part_name: str
    ) -> None:
        """Attempt to reserve a part using MCP for both inventory and guardrails."""
        try:
            event_id = state.get("event_id", "")
            machine_id = state.get("machine_id", "")
            reason = f"Reserved for {machine_id} repair (Event: {state['event_type']})"

            logger.info(
                f"   Attempting to reserve {part_name} with MCP guardrail validation..."
            )

            # Validate with Guardrail Service via MCP
            validation = await validate_action_mcp(
                action_type="REMOVE",
                part_number=part_number,
                quantity=1,
                reason=reason,
                event_id=event_id,
                agent_id="inventory-agent-mcp",
            )

            if validation.approved:
                guardrail_validations_total.labels(
                    action_type="REMOVE", result="approved"
                ).inc()

                logger.info(
                    f"   ✅ Guardrail (MCP) APPROVED reservation of {part_name}"
                )

                # Remove stock via MCP
                from tools.inventory_tools_mcp import remove_stock_mcp

                transaction = await remove_stock_mcp(
                    part_number=part_number,
                    quantity=1,
                    reason=reason,
                    event_id=event_id,
                )

                logger.info(f"  ✅ Successfully reserved {part_name} via MCP")

                state["actions_taken"].append(
                    {
                        "action": "reserve_part_mcp",
                        "part": part_number,
                        "result": "Reserved 1 unit",
                        "transaction_id": transaction.get("transaction_id"),
                        "guardrail_validated": True,
                        "protocol": "MCP",
                    }
                )

                actions_taken_total.labels(
                    action_type="reserve_part_mcp", result="success"
                ).inc()

            elif validation.requires_human_approval:
                guardrail_validations_total.labels(
                    action_type="REMOVE", result="requires_approval"
                ).inc()

                logger.warning(
                    f"  👤 Guardrail (MCP) requires HUMAN APPROVAL for {part_name}"
                )
                logger.warning(f"     Reason: {validation.decision}")

                state["human_approval_needed"] = True
                state["should_escalate"] = True

                state["recommended_actions"].append(
                    f"Human approval required to reserve {part_name}: {validation.decision}"
                )

                state["actions_taken"].append(
                    {
                        "action": "reserve_part_mcp",
                        "part": part_number,
                        "result": "Pending human approval",
                        "guardrail_decision": validation.decision,
                        "warnings": validation.warnings,
                        "protocol": "MCP",
                    }
                )

                parts_awaiting_approval.inc()

        except (MCPError, GuardrailMCPError) as e:
            guardrail_validations_total.labels(
                action_type="REMOVE", result="rejected"
            ).inc()

            logger.error(f"  ❌ MCP validation/execution failed for {part_name}")
            logger.error(f"     Reason: {e}")

            state["actions_taken"].append(
                {
                    "action": "reserve_part_mcp",
                    "part": part_number,
                    "result": "Failed",
                    "error": str(e),
                    "protocol": "MCP",
                }
            )

            actions_taken_total.labels(
                action_type="reserve_part_mcp", result="failed"
            ).inc()

    def _generate_decision(self, state: AgentState) -> None:
        """Generate final decision (same logic as before)."""
        parts_available = state.get("parts_available", {})
        recommended_actions = state.get("recommended_actions", [])

        if parts_available:
            all_available = all(parts_available.values())

            if all_available:
                state["final_decision"] = (
                    "✅ All required parts are in stock (verified via MCP). "
                    "Maintenance/repair can proceed as scheduled."
                )
                state["human_approval_needed"] = state.get(
                    "human_approval_needed", False
                )
            else:
                missing_parts = [
                    part for part, available in parts_available.items() if not available
                ]
                state["final_decision"] = (
                    f"❌ Critical parts missing: {', '.join(missing_parts)}. "
                    f"Cannot proceed with maintenance/repair until parts arrive."
                )
                state["human_approval_needed"] = True
                state["should_escalate"] = True
        else:
            if recommended_actions:
                state["final_decision"] = (
                    f"⚠️ {len(recommended_actions)} inventory action(s) recommended. "
                    f"Review reorder suggestions."
                )
                state["human_approval_needed"] = len(recommended_actions) > 3
            else:
                state["final_decision"] = (
                    "✅ Inventory levels are healthy (verified via MCP). No action needed."
                )
                state["human_approval_needed"] = False

        logger.info(f"[{self.name}] Decision: {state['final_decision']}")
