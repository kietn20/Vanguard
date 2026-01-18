"""
Agent workflow coordinator - Now with full MCP support.
"""

import logging
import os
from typing import Any, Dict

from agents.inventory_agent_mcp import InventoryAgentMCP
from agents.state import AgentState, EventType, Severity
from agents.supervisor import SupervisorAgent

logger = logging.getLogger(__name__)

# Check if MCP should be enabled (default: True)
USE_MCP = os.getenv("USE_MCP", "true").lower() == "true"


class AgentWorkflow:
    """
    Coordinates the multi-agent workflow with MCP support.
    """

    def __init__(self):
        """Initialize the workflow with all agents."""
        self.supervisor = SupervisorAgent()
        self.inventory_agent = InventoryAgentMCP()

        if USE_MCP:
            logger.info("=" * 60)
            logger.info("✅ MCP ENABLED - Using Model Context Protocol")
            logger.info("   Inventory: http://inventory-service:8082/mcp")
            logger.info("   Guardrail: http://guardrail-service:8083/mcp")
            logger.info("=" * 60)

        logger.info("Agent workflow initialized with MCP support")

    def process_event(self, event: Dict[str, Any]) -> AgentState:
        """
        Process a factory event through the agent system.
        """
        # Initialize state from event
        state: AgentState = {
            "event_id": event.get("event_id", ""),
            "event_type": EventType(event.get("event_type", "")),
            "machine_id": event.get("machine_id", ""),
            "severity": Severity(event.get("severity", "MEDIUM")),
            "description": event.get("description", ""),
            "timestamp": event.get("timestamp", ""),
            "metadata": event.get("metadata", {}),
            "next_agent": None,
            "should_escalate": False,
            "analysis": "",
            "recommended_actions": [],
            "required_parts": [],
            "parts_available": {},
            "actions_taken": [],
            "final_decision": "",
            "human_approval_needed": False,
        }

        logger.info("=" * 60)
        logger.info(f"🤖 AGENT WORKFLOW STARTING (MCP Mode)")
        logger.info(f"Event: {state['event_type']} on {state['machine_id']}")
        logger.info(f"Severity: {state['severity']}")
        logger.info("=" * 60)

        # Step 1: Supervisor analyzes and routes
        state = self.supervisor.analyze_event(state)

        # Step 2: Execute specialized agent if needed
        if state["next_agent"] == "inventory":
            state = self.inventory_agent.process(state)

        # Step 3: Log final results
        self._log_results(state)

        logger.info("=" * 60)
        logger.info(f"✅ AGENT WORKFLOW COMPLETE (MCP)")
        logger.info("=" * 60)
        logger.info("")

        return state

    def _log_results(self, state: AgentState) -> None:
        """Log the final results of the workflow."""
        logger.info("")
        logger.info("WORKFLOW RESULTS:")
        logger.info(f"  Analysis: {state['analysis']}")
        logger.info(f"  Final Decision: {state['final_decision']}")

        if state["recommended_actions"]:
            logger.info(f"  Recommended Actions ({len(state['recommended_actions'])}):")
            for action in state["recommended_actions"]:
                logger.info(f"    • {action}")

        if state["actions_taken"]:
            logger.info(f"  Actions Taken ({len(state['actions_taken'])}):")
            for action in state["actions_taken"]:
                protocol = action.get("protocol", "REST")
                logger.info(
                    f"    • [{protocol}] {action.get('action', 'unknown')}: "
                    f"{action.get('result', 'N/A')}"
                )

        if state["should_escalate"]:
            logger.warning("  ⚠️  ESCALATION REQUIRED")

        if state["human_approval_needed"]:
            logger.warning("  👤 HUMAN APPROVAL NEEDED")
