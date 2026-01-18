"""
Routing logic for LangGraph conditional edges.

These functions determine which node to execute next
based on the current state.
"""

import logging
from typing import Literal

from agents.state import AgentState

logger = logging.getLogger(__name__)


def route_after_supervisor(state: AgentState) -> Literal["inventory", "end"]:
    """
    Route from supervisor to the appropriate specialized agent.

    Args:
        state: Current agent state

    Returns:
        Name of the next node to execute
    """
    next_agent = state.get("next_agent")

    if next_agent == "inventory":
        logger.info("🔀 [Router] Routing to Inventory Agent")
        return "inventory"
    else:
        logger.info("🔀 [Router] No agent needed, ending workflow")
        return "end"


def route_after_inventory(state: AgentState) -> Literal["escalation", "end"]:
    """
    Route from inventory agent to escalation or end.

    Args:
        state: Current agent state

    Returns:
        Name of the next node to execute
    """
    should_escalate = state.get("should_escalate", False)

    if should_escalate:
        logger.info("🔀 [Router] Escalation required, routing to escalation node")
        return "escalation"
    else:
        logger.info("🔀 [Router] No escalation needed, ending workflow")
        return "end"
