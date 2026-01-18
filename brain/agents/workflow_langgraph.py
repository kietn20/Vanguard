"""
LangGraph-based agent workflow for Vanguard.

This replaces the manual routing with a declarative state graph.
"""

import logging
from typing import Any, Dict, Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agents.graph_nodes import escalation_node, inventory_node, supervisor_node
from agents.graph_routing import route_after_inventory, route_after_supervisor
from agents.state import AgentState, EventType, Severity

logger = logging.getLogger(__name__)


class LangGraphWorkflow:
    """
    LangGraph-based multi-agent workflow.

    This workflow uses a declarative graph structure to route
    events through specialized agents.
    """

    def __init__(self):
        """Initialize and compile the LangGraph workflow."""
        self.graph = self._build_graph()
        logger.info("=" * 60)
        logger.info("✅ LangGraph Workflow Initialized")
        logger.info("   Nodes: supervisor, inventory, escalation")
        logger.info("   Entry: START → supervisor")
        logger.info("=" * 60)

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state graph.

        Graph structure:

            START
              ↓
          Supervisor (analyzes event)
              ↓
           [routing]
          /        \
    Inventory    END
         ↓
      [routing]
      /        \
Escalation    END
     ↓
    END
        """
        # Create the graph with AgentState schema
        graph = StateGraph(AgentState)

        # Add nodes
        graph.add_node("supervisor", supervisor_node)
        graph.add_node("inventory", inventory_node)
        graph.add_node("escalation", escalation_node)

        # Add edges
        # START → supervisor (entry point)
        graph.add_edge(START, "supervisor")

        # Supervisor → inventory OR end (conditional)
        graph.add_conditional_edges(
            "supervisor", route_after_supervisor, {"inventory": "inventory", "end": END}
        )

        # Inventory → escalation OR end (conditional)
        graph.add_conditional_edges(
            "inventory", route_after_inventory, {"escalation": "escalation", "end": END}
        )

        # Escalation → END (terminal)
        graph.add_edge("escalation", END)

        # Compile the graph
        compiled_graph = graph.compile()

        logger.info("✅ LangGraph compiled successfully")
        return compiled_graph

    def process_event(self, event: Dict[str, Any]) -> AgentState:
        """
        Process a factory event through the LangGraph workflow.

        Args:
            event: Factory event from Kafka

        Returns:
            Final agent state after workflow completion
        """
        # Initialize state from event
        initial_state: AgentState = {
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
        logger.info(f"🚀 LANGGRAPH WORKFLOW STARTING")
        logger.info(
            f"Event: {initial_state['event_type']} on {initial_state['machine_id']}"
        )
        logger.info(f"Severity: {initial_state['severity']}")
        logger.info("=" * 60)

        # Execute the graph
        final_state = self.graph.invoke(initial_state)

        # Log results
        self._log_results(final_state)

        logger.info("=" * 60)
        logger.info(f"✅ LANGGRAPH WORKFLOW COMPLETE")
        logger.info("=" * 60)
        logger.info("")

        return final_state

    def _log_results(self, state: AgentState) -> None:
        """Log the final results of the workflow."""
        logger.info("")
        logger.info("WORKFLOW RESULTS:")
        logger.info(f"  Analysis: {state.get('analysis', 'N/A')}")
        logger.info(f"  Final Decision: {state.get('final_decision', 'N/A')}")

        if state.get("recommended_actions"):
            logger.info(f"  Recommended Actions ({len(state['recommended_actions'])}):")
            for action in state["recommended_actions"]:
                logger.info(f"    • {action}")

        if state.get("actions_taken"):
            logger.info(f"  Actions Taken ({len(state['actions_taken'])}):")
            for action in state["actions_taken"]:
                protocol = action.get("protocol", "REST")
                logger.info(
                    f"    • [{protocol}] {action.get('action', 'unknown')}: "
                    f"{action.get('result', 'N/A')}"
                )

        if state.get("should_escalate"):
            logger.warning("  ⚠️  ESCALATION REQUIRED")

        if state.get("human_approval_needed"):
            logger.warning("  👤 HUMAN APPROVAL NEEDED")


def stream_event(self, event: Dict[str, Any]):
    """
    Stream the workflow execution step-by-step.

    This is useful for monitoring, debugging, or building
    interactive UIs that show progress in real-time.

    Args:
        event: Factory event to process

    Yields:
        Tuple of (node_name, updated_state) for each step
    """
    # Initialize state
    initial_state: AgentState = {
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

    logger.info("🎬 Starting streaming workflow execution...")

    # Stream through the graph
    for output in self.graph.stream(initial_state):
        for node_name, state_update in output.items():
            logger.info(f"📡 Streamed update from node: {node_name}")
            yield (node_name, state_update)


class LangGraphWorkflowWithCheckpointing(LangGraphWorkflow):
    """
    Enhanced workflow with checkpoint support.

    This allows pausing and resuming workflows,
    useful for human-in-the-loop approval scenarios.
    """

    def __init__(self):
        """Initialize with memory-based checkpointing."""
        super().__init__()

        # Add checkpointing
        self.checkpointer = MemorySaver()

        # Rebuild graph with checkpointing
        self.graph = self._build_graph_with_checkpointing()

        logger.info("✅ LangGraph Workflow with Checkpointing initialized")

    def _build_graph_with_checkpointing(self):
        """Build graph with checkpoint support."""
        from langgraph.graph import END, START, StateGraph

        graph = StateGraph(AgentState)

        # Add nodes
        graph.add_node("supervisor", supervisor_node)
        graph.add_node("inventory", inventory_node)
        graph.add_node("escalation", escalation_node)

        # Add edges
        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges(
            "supervisor", route_after_supervisor, {"inventory": "inventory", "end": END}
        )
        graph.add_conditional_edges(
            "inventory", route_after_inventory, {"escalation": "escalation", "end": END}
        )
        graph.add_edge("escalation", END)

        # Compile with checkpointer
        return graph.compile(checkpointer=self.checkpointer)

    def process_with_checkpointing(
        self, event: Dict[str, Any], thread_id: str = "default"
    ) -> AgentState:
        """
        Process event with checkpointing.

        Args:
            event: Factory event
            thread_id: Unique ID for this workflow thread

        Returns:
            Final state
        """
        initial_state = self._create_initial_state(event)

        # Create config with thread_id for checkpointing
        config = {"configurable": {"thread_id": thread_id}}

        # Execute with checkpointing
        final_state = self.graph.invoke(initial_state, config)

        return final_state

    def get_checkpoint(self, thread_id: str) -> Optional[Dict]:
        """
        Get the checkpoint for a specific thread.

        Args:
            thread_id: Thread identifier

        Returns:
            Checkpoint state or None
        """
        config = {"configurable": {"thread_id": thread_id}}
        return self.checkpointer.get(config)

    def _create_initial_state(self, event: Dict[str, Any]) -> AgentState:
        """Helper to create initial state."""
        return {
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
