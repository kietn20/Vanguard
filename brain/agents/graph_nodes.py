"""
LangGraph nodes for the Vanguard agent workflow.

Each node is a function that:
1. Takes AgentState as input
2. Performs some action
3. Returns a dict with state updates
"""

import logging
from typing import Dict, Any

from agents.state import AgentState
from agents.supervisor import SupervisorAgent
from agents.inventory_agent_mcp import InventoryAgentMCP

logger = logging.getLogger(__name__)

# Initialize agents (singletons)
_supervisor = SupervisorAgent()
_inventory_agent = InventoryAgentMCP()


def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """
    Supervisor node: Analyzes event and decides routing.

    Returns state updates with:
    - analysis: LLM reasoning
    - next_agent: Which agent to route to
    - required_parts: Parts that might be needed
    - should_escalate: Whether to escalate
    """
    logger.info("🧠 [Supervisor Node] Analyzing event...")

    # Supervisor analyzes and updates state
    updated_state = _supervisor.analyze_event(state)

    # Return only the fields that changed
    return {
        "analysis": updated_state["analysis"],
        "next_agent": updated_state["next_agent"],
        "required_parts": updated_state.get("required_parts", []),
        "should_escalate": updated_state.get("should_escalate", False),
    }


def inventory_node(state: AgentState) -> Dict[str, Any]:
    """
    Inventory node: Checks parts and makes decisions.

    Returns state updates with:
    - parts_available: Availability status
    - recommended_actions: What to do
    - actions_taken: What was done
    - final_decision: Summary
    - human_approval_needed: If approval needed
    """
    logger.info("📦 [Inventory Node] Processing inventory checks...")

    # Inventory agent processes (synchronous wrapper around async)
    updated_state = _inventory_agent.process(state)

    # Return only the fields that changed
    return {
        "parts_available": updated_state.get("parts_available", {}),
        "recommended_actions": updated_state.get("recommended_actions", []),
        "actions_taken": updated_state.get("actions_taken", []),
        "final_decision": updated_state.get("final_decision", ""),
        "human_approval_needed": updated_state.get("human_approval_needed", False),
        "should_escalate": updated_state.get("should_escalate", False),
    }


def escalation_node(state: AgentState) -> Dict[str, Any]:
    """
    Escalation node: Handles critical events requiring human intervention.

    This node is called when should_escalate = True.
    """
    logger.warning("⚠️  [Escalation Node] Event requires human attention!")
    logger.warning(f"   Reason: {state.get('analysis', 'Unknown')}")
    logger.warning(f"   Decision: {state.get('final_decision', 'Pending')}")

    # In a real system, this would:
    # - Send notification (email, Slack, PagerDuty)
    # - Create ticket in ticketing system
    # - Pause workflow and wait for approval

    # For now, just log
    escalation_summary = (
        f"ESCALATED: {state['event_type']} on {state['machine_id']} "
        f"(Severity: {state['severity']})"
    )

    return {
        "final_decision": state.get("final_decision", "") + f" [{escalation_summary}]"
    }
