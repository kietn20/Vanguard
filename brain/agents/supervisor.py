"""
Supervisor Agent - Routes events to appropriate specialized agents.

The Supervisor is the "brain coordinator" that:
1. Analyzes incoming factory events
2. Determines which specialized agent(s) should handle it
3. Coordinates the overall workflow
"""

import logging
from typing import Dict, Any
from agents.state import AgentState, EventType, Severity

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Supervisor Agent coordinates the multi-agent workflow.
    """

    def __init__(self):
        """Initialize the supervisor agent."""
        self.name = "Supervisor"

    def analyze_event(self, state: AgentState) -> AgentState:
        """
        Analyze the event and determine routing.

        Args:
            state: Current agent state

        Returns:
            Updated state with routing decision
        """
        event_type = state["event_type"]
        severity = state["severity"]

        logger.info(f"[{self.name}] Analyzing event: {event_type} (Severity: {severity})")

        # determine which agent should handle this
        if event_type == EventType.LOW_INVENTORY:
            state["next_agent"] = "inventory"
            state["analysis"] = ("Low inventory detected. Routing to Inventory Agent for stock analysis.")

        elif event_type in [EventType.SENSOR_OVERHEAT, EventType.MACHINE_VIBRATION]:
            state["next_agent"] = "inventory"
            state["analysis"] = (f"{event_type} detected. Checking if spare parts are available for potential repairs.")
            state["required_parts"] = self._get_common_repair_parts(state["machine_id"])

        elif event_type == EventType.MAINTENANCE_DUE:
            state["next_agent"] = "inventory"
            state["analysis"] = ("Scheduled maintenance approaching. Verifying required parts are in stock.")
            state["required_parts"] = self._get_maintenance_parts(state["machine_id"])

        elif event_type == EventType.PART_FAILED_QC:
            state["next_agent"] = "inventory"
            state["analysis"] = ("Part failed quality control. Checking if replacement parts are available.")

        else:
            state["next_agent"] = None
            state["analysis"] = (f"Event type {event_type} does not require inventory action.")

        # escalate critical events
        if severity in [Severity.CRITICAL, Severity.HIGH]:
            state["should_escalate"] = True
            logger.warning(f"[{self.name}] Critical event - escalation recommended")
        else:
            state["should_escalate"] = False



        logger.info(f"[{self.name}] Decision: Route to '{state['next_agent']}' agent")

        return state


    def _get_common_repair_parts(self, machine_id: str) -> list[str]:
        """
        Get common parts needed for machine repairs.
        """
        # Simple mapping: machine type → common parts
        if "PRESS" in machine_id:
            return ["HYDRAULIC_PUMP_001", "PRESSURE_SENSOR_PSI"]
        elif "WELDER" in machine_id:
            return ["WELDING_TIP_T15"]
        elif "CNC" in machine_id:
            return ["SERVO_MOTOR_500W", "CNC_TOOL_BIT_HSS"]
        elif "ASSEMBLY" in machine_id or "CONVEYOR" in machine_id:
            return ["CONVEYOR_BELT_10M", "PNEUMATIC_VALVE_24V"]
        else:
            return ["BEARING_6205"]


    def _get_maintenance_parts(self, machine_id: str) -> list[str]:
        """Get parts typically needed for scheduled maintenance."""
        return ["BEARING_6205", "HYDRAULIC_PUMP_001", "WELDING_TIP_T15"]
