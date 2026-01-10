from typing import TypedDict, Optional, List, Dict, Any
from enum import Enum


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


# State definitions for the agent workflow. Each node in the graph can read and update this state
class AgentState(TypedDict):
    """
    State that flows through the agent workflow.

    This is the "working memory" of the agent system.
    Each agent can read from and write to this state.
    """

    # input: the factory event that triggered this workflow
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
    recommended_actions: List[str]  # Actions the agent recommends

    # inventory checks
    required_parts: List[str]  # Parts needed for this event
    parts_available: Dict[str, bool]  # Which required parts are in stock

    # actions taken
    actions_taken: List[Dict[str, Any]]  # Log of actions performed

    # final decision
    final_decision: str  # Summary of what was decided
    human_approval_needed: bool  # Does this need human approval?
