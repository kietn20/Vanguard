"""
LLM-Powered Supervisor Agent - Routes events using AI reasoning.

The Supervisor uses Google Gemini to:
1. Analyze incoming factory events
2. Determine which specialized agent should handle it
3. Identify required parts
4. Provide natural language explanations
"""

import logging
from typing import Any, Dict

from services.llm_service import GeminiService

from agents.state import AgentState, EventType, Severity

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    LLM-Powered Supervisor Agent coordinates the multi-agent workflow.
    """

    def __init__(self):
        """Initialize the supervisor agent with Gemini."""
        self.name = "LLM Supervisor"

        try:
            self.llm = GeminiService()
            self.llm_enabled = True
            logger.info("✅ LLM-powered supervisor initialized")
        except ValueError as e:
            logger.warning(f"⚠️ LLM initialization failed: {e}")
            logger.warning("⚠️ Falling back to rule-based supervisor")
            self.llm = None
            self.llm_enabled = False

    def analyze_event(self, state: AgentState) -> AgentState:
        """
        Analyze the event using LLM or fallback to rules.

        Args:
            state: Current agent state

        Returns:
            Updated state with routing decision and analysis
        """
        event_type = state["event_type"]
        severity = state["severity"]

        logger.info(f"[{self.name}] Analyzing event: {event_type} (Severity: {severity})")

        if self.llm_enabled:
            # Use LLM for analysis
            return self._llm_analysis(state)
        else:
            # Fallback to rule-based
            return self._rule_based_analysis(state)

    def _llm_analysis(self, state: AgentState) -> AgentState:
        """
        Analyze event using Gemini LLM.
        """
        # prepare event data for LLM
        event = {
            "event_id": state["event_id"],
            "event_type": state["event_type"].value,
            "machine_id": state["machine_id"],
            "severity": state["severity"].value,
            "description": state["description"],
            "metadata": state["metadata"],
        }

        analysis = self.llm.analyze_factory_event(event)

        # update state based on LLM decision
        state["next_agent"] = analysis.routing_decision
        state["required_parts"] = analysis.required_parts

        # build rich analysis text
        state["analysis"] = (
            f"""
                🤖 **LLM Analysis:**

                **Reasoning:** {analysis.reasoning}

                **Urgency:** {analysis.urgency_level.upper()}

                **Key Concerns:**
                {self._format_list(analysis.key_concerns)}

                **Recommended Actions:**
                {self._format_list(analysis.recommended_actions)}
                """.strip()
        )

        # set escalation based on urgency
        if analysis.urgency_level in ["critical", "high"]:
            state["should_escalate"] = True
            logger.warning(f"[{self.name}] ⚠️ Event marked for escalation (urgency: {analysis.urgency_level})")
        else:
            state["should_escalate"] = False

        logger.info(f"[{self.name}] 🤖 LLM Decision: Route to '{analysis.routing_decision}' agent")

        if analysis.required_parts:
            logger.info(f"[{self.name}] 🔧 Required parts: {', '.join(analysis.required_parts)}")

        return state

    def _rule_based_analysis(self, state: AgentState) -> AgentState:
        """
        Fallback to rule-based analysis (original logic).
        """
        event_type = state["event_type"]
        severity = state["severity"]

        logger.info(f"[{self.name}] Using rule-based routing")

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

        if severity in [Severity.CRITICAL, Severity.HIGH]:
            state["should_escalate"] = True
            logger.warning(f"[{self.name}] Critical event - escalation recommended")
        else:
            state["should_escalate"] = False

        logger.info(f"[{self.name}] Decision: Route to '{state['next_agent']}' agent")

        return state

    def _get_common_repair_parts(self, machine_id: str) -> list[str]:
        """Get common parts needed for machine repairs."""
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

    def _format_list(self, items: list[str]) -> str:
        """Format a list of items as bullet points."""
        if not items:
            return "- None"
        return "\n".join(f"- {item}" for item in items)
