"""
Inventory Agent - Handles all inventory-related decisions.

This agent:
1. Checks if required parts are available
2. Analyzes low stock situations
3. Makes recommendations for reordering
4. Validates actions through guardrail service (SAFETY)
5. Can reserve parts for repairs (with approval)
"""

import logging
from typing import Dict, Any, List
from agents.state import AgentState
from tools.inventory_tools import (
    get_part_by_number,
    check_availability,
    get_low_stock_parts,
    remove_stock,
    InventoryToolError,
)
from tools.guardrail_client import validate_action, GuardrailError

logger = logging.getLogger(__name__)


class InventoryAgent:
    """
    Inventory Agent manages spare parts and stock levels.
    """

    def __init__(self):
        """Initialize the inventory agent."""
        self.name = "Inventory Agent"

    def process(self, state: AgentState) -> AgentState:
        """
        Process the event and take inventory-related actions.

        Args:
            state: Current agent state

        Returns:
            Updated state with inventory analysis
        """
        logger.info(f"[{self.name}] Processing event: {state['event_type']}")

        # initialize tracking
        state["parts_available"] = {}
        state["recommended_actions"] = []
        state["actions_taken"] = []

        # check if specific parts are required
        if state.get("required_parts"):
            self._check_required_parts(state)

        # check overall low stock situation
        self._check_low_stock_parts(state)

        # generate final decision
        self._generate_decision(state)

        logger.info(f"[{self.name}] Processing complete")

        return state

    def _check_required_parts(self, state: AgentState) -> None:
        """
        Check availability of required parts
        """
        required_parts = state.get("required_parts", [])

        logger.info(f"[{self.name}] Checking {len(required_parts)} required parts")

        for part_number in required_parts:
            try:
                part = get_part_by_number(part_number)
                available = part.quantity > 0
                state["parts_available"][part_number] = available

                if available:
                    logger.info(f"  ✅ {part.name}: {part.quantity} units available")

                    if part.low_stock:
                        logger.warning(
                            f"  ⚠️  {part.name} is LOW STOCK ({part.quantity}/{part.minimum_quantity})"
                        )
                        state["recommended_actions"].append(
                            f"Reorder {part.name} - stock is below minimum"
                        )

                    # attempt to reserve part with guardrail validation
                    if state["severity"] in ["CRITICAL", "HIGH"]:
                        self._attempt_reserve_part(state, part_number, part.name)
                else:
                    logger.error(f"  ❌ {part.name}: OUT OF STOCK!")
                    state["recommended_actions"].append(
                        f"URGENT: Order {part.name} immediately - no stock available"
                    )
                    state["should_escalate"] = True

                # log the action
                state["actions_taken"].append(
                    {
                        "action": "check_availability",
                        "part": part_number,
                        "result": f"{part.quantity} units available",
                        "low_stock": part.low_stock,
                    }
                )

            except InventoryToolError as e:
                logger.error(f"  ❌ Error checking {part_number}: {e}")
                state["parts_available"][part_number] = False
                state["actions_taken"].append(
                    {
                        "action": "check_availability",
                        "part": part_number,
                        "error": str(e),
                    }
                )

    def _attempt_reserve_part(self, state: AgentState, part_number: str, part_name: str) -> None:
        """
        Attempt to reserve a part for critical repairs

        This validates the action through the guardrail service first
        """
        try:
            event_id = state.get("event_id", "")
            machine_id = state.get("machine_id", "")

            reason = f"Reserved for {machine_id} repair (Event: {state['event_type']})"
            logger.info(f"   Attempting to reserve {part_name} with guardrail validation...")

            # step 1: Validate with guardrail service
            validation = validate_action(
                action_type="REMOVE",
                part_number=part_number,
                quantity=1,
                reason=reason,
                event_id=event_id,
            )

            # step 2: Handle validation result
            if validation.approved:
                logger.info(f"   Guardrail APPROVED reservation of {part_name}")

                # Actually reserve the part
                transaction = remove_stock(
                    part_number=part_number,
                    quantity=1,
                    reason=reason,
                    event_id=event_id,
                )

                logger.info(
                    f"  ✅ Successfully reserved {part_name} (Transaction ID: {transaction.id})"
                )

                state["actions_taken"].append(
                    {
                        "action": "reserve_part",
                        "part": part_number,
                        "result": "Reserved 1 unit",
                        "transaction_id": transaction.id,
                        "guardrail_validated": True,
                    }
                )

            elif validation.requires_human_approval:
                logger.warning(f"  👤 Guardrail requires HUMAN APPROVAL for {part_name}")
                logger.warning(f"     Reason: {validation.decision}")

                state["human_approval_needed"] = True
                state["should_escalate"] = True

                state["recommended_actions"].append(f"Human approval required to reserve {part_name}: {validation.decision}")

                state["actions_taken"].append(
                    {
                        "action": "reserve_part",
                        "part": part_number,
                        "result": "Pending human approval",
                        "guardrail_decision": validation.decision,
                        "warnings": validation.warnings,
                    }
                )

            else:
                logger.error(f"  ❌ Unexpected validation state for {part_name}")

        except GuardrailError as e:
            logger.error(f"  ❌ Guardrail REJECTED reservation of {part_name}")
            logger.error(f"     Reason: {e}")

            state["actions_taken"].append(
                {
                    "action": "reserve_part",
                    "part": part_number,
                    "result": "Rejected by guardrails",
                    "error": str(e),
                }
            )

        except InventoryToolError as e:
            logger.error(f"  ❌ Failed to reserve {part_name}: {e}")

            state["actions_taken"].append(
                {
                    "action": "reserve_part",
                    "part": part_number,
                    "result": "Failed to execute",
                    "error": str(e),
                }
            )

    def _check_low_stock_parts(self, state: AgentState) -> None:
        """
        Check for any low stock parts in the system.
        """
        try:
            low_stock_parts = get_low_stock_parts()

            if low_stock_parts:
                logger.warning(f"[{self.name}] Found {len(low_stock_parts)} low stock parts")

                for part in low_stock_parts:
                    logger.warning(f"  ⚠️  {part.name}: {part.quantity}/{part.minimum_quantity} units")

                    # calculate reorder quantity (3x minimum)
                    reorder_qty = part.minimum_quantity * 3

                    state["recommended_actions"].append(
                        f"Reorder {part.name}: current={part.quantity}, "
                        f"minimum={part.minimum_quantity}, recommend={reorder_qty} units"
                    )

                state["actions_taken"].append(
                    {
                        "action": "check_low_stock",
                        "result": f"Found {len(low_stock_parts)} parts below minimum",
                    }
                )
            else:
                logger.info(f"[{self.name}] All parts are adequately stocked")
                state["actions_taken"].append(
                    {
                        "action": "check_low_stock",
                        "result": "All parts above minimum quantity",
                    }
                )

        except InventoryToolError as e:
            logger.error(f"[{self.name}] Error checking low stock: {e}")

    def _generate_decision(self, state: AgentState) -> None:
        """
        Generate final decision based on analysis.
        """
        parts_available = state.get("parts_available", {})
        recommended_actions = state.get("recommended_actions", [])

        # check if all required parts are available
        if parts_available:
            all_available = all(parts_available.values())

            if all_available:
                state["final_decision"] = (
                    "✅ All required parts are in stock. "
                    "Maintenance/repair can proceed as scheduled."
                )

                # check if any parts were reserved
                reserved = any(
                    action.get("action") == "reserve_part"
                    and action.get("result") == "Reserved 1 unit"
                    for action in state.get("actions_taken", [])
                )

                if reserved:
                    state["final_decision"] += " Parts have been reserved."

                state["human_approval_needed"] = state.get("human_approval_needed", False)
            else:
                missing_parts = [part for part, available in parts_available.items() if not available]
                state["final_decision"] = (f"❌ Critical parts missing: {', '.join(missing_parts)}. "f"Cannot proceed with maintenance/repair until parts arrive.")
                state["human_approval_needed"] = True
                state["should_escalate"] = True
        else:
            # No specific parts required, general inventory check
            if recommended_actions:
                state["final_decision"] = (f"!!! {len(recommended_actions)} inventory action(s) recommended. "f"Review reorder suggestions.")
                state["human_approval_needed"] = len(recommended_actions) > 3
            else:
                state["final_decision"] = ("Inventory levels are healthy. No action needed.")
                state["human_approval_needed"] = False

        logger.info(f"[{self.name}] Decision: {state['final_decision']}")
