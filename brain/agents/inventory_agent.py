"""
Inventory Agent - Handles all inventory-related decisions.
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

# ===== ADD METRICS IMPORTS =====
from metrics.agent_metrics import (
    decisions_made_total,
    actions_taken_total,
    guardrail_validations_total,
    low_stock_parts,
    parts_awaiting_approval,
    track_decision_time,
)

logger = logging.getLogger(__name__)


class InventoryAgent:
    """
    Inventory Agent manages spare parts and stock levels.
    """

    def __init__(self):
        """Initialize the inventory agent."""
        self.name = "Inventory Agent"

    @track_decision_time("inventory-agent")
    def process(self, state: AgentState) -> AgentState:
        """
        Process the event and take inventory-related actions.
        """
        logger.info(f"[{self.name}] Processing event: {state['event_type']}")

        state["parts_available"] = {}
        state["recommended_actions"] = []
        state["actions_taken"] = []

        if state.get("required_parts"):
            self._check_required_parts(state)

        self._check_low_stock_parts(state)
        self._generate_decision(state)

        logger.info(f"[{self.name}] Processing complete")

        return state

    def _check_required_parts(self, state: AgentState) -> None:
        """Check availability of required parts"""
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

                    if state["severity"] in ["CRITICAL", "HIGH"]:
                        self._attempt_reserve_part(state, part_number, part.name)
                else:
                    logger.error(f"  ❌ {part.name}: OUT OF STOCK!")
                    state["recommended_actions"].append(
                        f"URGENT: Order {part.name} immediately - no stock available"
                    )
                    state["should_escalate"] = True

                state["actions_taken"].append(
                    {
                        "action": "check_availability",
                        "part": part_number,
                        "result": f"{part.quantity} units available",
                        "low_stock": part.low_stock,
                    }
                )

                # ===== TRACK ACTION METRIC =====
                actions_taken_total.labels(
                    action_type="check_availability", result="success"
                ).inc()

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

                # ===== TRACK FAILED ACTION =====
                actions_taken_total.labels(
                    action_type="check_availability", result="failed"
                ).inc()

    def _attempt_reserve_part(
        self, state: AgentState, part_number: str, part_name: str
    ) -> None:
        """Attempt to reserve a part for critical repairs"""
        try:
            event_id = state.get("event_id", "")
            machine_id = state.get("machine_id", "")
            reason = f"Reserved for {machine_id} repair (Event: {state['event_type']})"

            logger.info(
                f"   Attempting to reserve {part_name} with guardrail validation..."
            )

            validation = validate_action(
                action_type="REMOVE",
                part_number=part_number,
                quantity=1,
                reason=reason,
                event_id=event_id,
            )

            # ===== TRACK GUARDRAIL DECISION =====
            if validation.approved:
                guardrail_validations_total.labels(
                    action_type="REMOVE", result="approved"
                ).inc()

                logger.info(f"   Guardrail APPROVED reservation of {part_name}")

                transaction = remove_stock(
                    part_number=part_number,
                    quantity=1,
                    reason=reason,
                    event_id=event_id,
                )

                logger.info(f"  ✅ Successfully reserved {part_name}")

                state["actions_taken"].append(
                    {
                        "action": "reserve_part",
                        "part": part_number,
                        "result": "Reserved 1 unit",
                        "transaction_id": transaction.id,
                        "guardrail_validated": True,
                    }
                )

                # ===== TRACK SUCCESSFUL RESERVATION =====
                actions_taken_total.labels(
                    action_type="reserve_part", result="success"
                ).inc()

            elif validation.requires_human_approval:
                guardrail_validations_total.labels(
                    action_type="REMOVE", result="requires_approval"
                ).inc()

                logger.warning(
                    f"  👤 Guardrail requires HUMAN APPROVAL for {part_name}"
                )
                logger.warning(f"     Reason: {validation.decision}")

                state["human_approval_needed"] = True
                state["should_escalate"] = True

                state["recommended_actions"].append(
                    f"Human approval required to reserve {part_name}: {validation.decision}"
                )

                state["actions_taken"].append(
                    {
                        "action": "reserve_part",
                        "part": part_number,
                        "result": "Pending human approval",
                        "guardrail_decision": validation.decision,
                        "warnings": validation.warnings,
                    }
                )

                # ===== INCREMENT APPROVAL COUNTER =====
                parts_awaiting_approval.inc()

        except GuardrailError as e:
            # ===== TRACK REJECTION =====
            guardrail_validations_total.labels(
                action_type="REMOVE", result="rejected"
            ).inc()

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

            actions_taken_total.labels(
                action_type="reserve_part", result="failed"
            ).inc()

    def _check_low_stock_parts(self, state: AgentState) -> None:
        """Check for any low stock parts in the system."""
        try:
            low_stock_parts_list = get_low_stock_parts()

            # ===== UPDATE GAUGE =====
            low_stock_parts.set(len(low_stock_parts_list))

            if low_stock_parts_list:
                logger.warning(
                    f"[{self.name}] Found {len(low_stock_parts_list)} low stock parts"
                )

                for part in low_stock_parts_list:
                    logger.warning(
                        f"  ⚠️  {part.name}: {part.quantity}/{part.minimum_quantity} units"
                    )

                    reorder_qty = part.minimum_quantity * 3

                    state["recommended_actions"].append(
                        f"Reorder {part.name}: current={part.quantity}, "
                        f"minimum={part.minimum_quantity}, recommend={reorder_qty} units"
                    )

                state["actions_taken"].append(
                    {
                        "action": "check_low_stock",
                        "result": f"Found {len(low_stock_parts_list)} parts below minimum",
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
        """Generate final decision based on analysis."""
        parts_available = state.get("parts_available", {})
        recommended_actions = state.get("recommended_actions", [])

        # ===== TRACK DECISION =====
        if parts_available:
            all_available = all(parts_available.values())

            if all_available:
                decisions_made_total.labels(
                    agent="inventory-agent", decision_type="approve"
                ).inc()

                state["final_decision"] = (
                    "✅ All required parts are in stock. "
                    "Maintenance/repair can proceed as scheduled."
                )

                reserved = any(
                    action.get("action") == "reserve_part"
                    and action.get("result") == "Reserved 1 unit"
                    for action in state.get("actions_taken", [])
                )

                if reserved:
                    state["final_decision"] += " Parts have been reserved."

                state["human_approval_needed"] = state.get(
                    "human_approval_needed", False
                )
            else:
                decisions_made_total.labels(
                    agent="inventory-agent", decision_type="escalate"
                ).inc()

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
                decisions_made_total.labels(
                    agent="inventory-agent", decision_type="recommend"
                ).inc()

                state["final_decision"] = (
                    f"⚠️ {len(recommended_actions)} inventory action(s) recommended. "
                    f"Review reorder suggestions."
                )
                state["human_approval_needed"] = len(recommended_actions) > 3
            else:
                decisions_made_total.labels(
                    agent="inventory-agent", decision_type="approve"
                ).inc()

                state["final_decision"] = (
                    "✅ Inventory levels are healthy. No action needed."
                )
                state["human_approval_needed"] = False

        logger.info(f"[{self.name}] Decision: {state['final_decision']}")
