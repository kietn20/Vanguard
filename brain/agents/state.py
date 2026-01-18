"""
Agent state definition for LangGraph workflow.

This state flows through all nodes in the graph,
being updated at each step.
"""

import operator
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional, TypedDict


class EventType(str, Enum):
    """Factory event types."""
    SENSOR_OVERHEAT = "SENSOR_OVERHEAT"
    PART_FAILED_QC = "PART_FAILED_QC"
    MACHINE_VIBRATION = "MACHINE_VIBRATION"
    LOW_INVENTORY = "LOW_INVENTORY"
    MAINTENANCE_DUE = "MAINTENANCE_DUE"


class Severity(str, Enum):
    """Event severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

# State definitions for the agent workflow. Each node in the graph can read and update this state.
class AgentState(TypedDict):
    """
    State that flows through the LangGraph workflow.

    This is the "working memory" of the agent system.
    Each node in the graph can read from and write to this state.

    Fields with Annotated[List, operator.add] will accumulate values
    instead of being overwritten (e.g., recommended_actions).
    """

    # input: The factory event that triggered this workflow
    event_id: str
    event_type: EventType
    machine_id: str
    severity: Severity
    description: str
    timestamp: str
    metadata: Dict[str, Any]

    # workflow control
    next_agent: Optional[str]  # Which agent should process next
    should_escalate: bool  # Should this be escalated to human?

    # agent analysis
    analysis: str  # Supervisor's analysis of the event

    # lists that accumulate (using operator.add reducer)
    recommended_actions: Annotated[List[str], operator.add]
    required_parts: Annotated[List[str], operator.add]
    actions_taken: Annotated[List[Dict[str, Any]], operator.add]

    # dictionaries that get updated
    parts_available: Dict[str, bool]  # Which required parts are in stock

    # final decision
    final_decision: str  # Summary of what was decided
    human_approval_needed: bool  # Does this need human approval?
