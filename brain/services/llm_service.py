"""
LLM service for AI-powered decision making.

This module provides a wrapper around Google's Gemini API for:
- Event analysis
- Decision reasoning
- Natural language explanations
"""

import logging
import os
from typing import Any, Dict, Optional

import google.generativeai as genai
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LLMAnalysis(BaseModel):
    """Structured output from LLM analysis."""

    routing_decision: str  # Which agent to use: "inventory", "maintenance", "none"
    urgency_level: str  # "low", "medium", "high", "critical"
    required_parts: list[str]  # List of part numbers that might be needed
    reasoning: str  # Natural language explanation of the decision
    key_concerns: list[str]  # Bullet points of main issues
    recommended_actions: list[str]  # Suggested next steps


class GeminiService:
    """
    Service for interacting with Google Gemini API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini service.

        Args:
            api_key: Google API key (defaults to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required. ")

        genai.configure(api_key=self.api_key)

        # choose the Gemini model (e.g., "gemini-1.5-flash")
        self.model = genai.GenerativeModel("gemini-1.5-flash")

        logger.info("✅ Gemini service initialized")

    def analyze_factory_event(self, event: Dict[str, Any]) -> LLMAnalysis:
        """
        Analyze a factory event using Gemini.

        Args:
            event: Factory event dictionary

        Returns:
            LLMAnalysis: Structured analysis with routing decision
        """
        # build the prompt
        prompt = self._build_analysis_prompt(event)

        try:
            # call Gemini API
            response = self.model.generate_content(prompt)

            # parse structured response
            analysis = self._parse_response(response.text)

            logger.info(
                f"✅ LLM Analysis complete: Route to '{analysis.routing_decision}'"
            )
            logger.debug(f"Reasoning: {analysis.reasoning}")

            return analysis

        except Exception as e:
            logger.error(f"❌ Gemini API error: {e}")
            # fallback to safe defaults
            return self._fallback_analysis(event)

    def _build_analysis_prompt(self, event: Dict[str, Any]) -> str:
        """
        Build a prompt for event analysis.
        """
        event_type = event.get("event_type", "UNKNOWN")
        machine_id = event.get("machine_id", "UNKNOWN")
        severity = event.get("severity", "UNKNOWN")
        description = event.get("description", "No description")
        metadata = event.get("metadata", {})

        prompt = f"""You are an AI supervisor for an industrial factory automation system.
                    Analyze the following factory event and provide a structured decision.

                    **FACTORY EVENT:**
                    - Type: {event_type}
                    - Machine: {machine_id}
                    - Severity: {severity}
                    - Description: {description}
                    - Metadata: {metadata}

                    **AVAILABLE AGENTS:**
                    1. "inventory" - Manages spare parts, checks stock, reserves parts
                    2. "maintenance" - Schedules repairs, manages technicians (not yet implemented)
                    3. "none" - No specialized agent needed

                    **AVAILABLE PARTS DATABASE:**
                    - HYDRAULIC_PUMP_001 (for hydraulic systems)
                    - BEARING_6205 (for rotating equipment)
                    - SERVO_MOTOR_500W (for CNC machines)
                    - PRESSURE_SENSOR_PSI (for pressure monitoring)
                    - WELDING_TIP_T15 (for welding systems)
                    - CNC_TOOL_BIT_HSS (for CNC machining)
                    - CONVEYOR_BELT_10M (for conveyor systems)
                    - PNEUMATIC_VALVE_24V (for pneumatic systems)

                    **YOUR TASK:**
                    Analyze this event and provide your decision in the following EXACT format:

                    ROUTING_DECISION: [inventory/maintenance/none]
                    URGENCY_LEVEL: [low/medium/high/critical]
                    REQUIRED_PARTS: [comma-separated list of part numbers, or "none"]
                    REASONING: [2-3 sentence explanation of your analysis]
                    KEY_CONCERNS: [bullet list of main issues]
                    RECOMMENDED_ACTIONS: [bullet list of suggested next steps]

                    **DECISION GUIDELINES:**
                    - Route to "inventory" if parts might be needed or stock should be checked
                    - Route to "maintenance" for scheduling or technician assignment
                    - Route to "none" only for informational events that need no action
                    - For CRITICAL/HIGH severity, always recommend immediate action
                    - Consider which parts would typically fail for each machine type
                    - Hydraulic systems → HYDRAULIC_PUMP_001, PRESSURE_SENSOR_PSI
                    - CNC machines → SERVO_MOTOR_500W, CNC_TOOL_BIT_HSS
                    - Welders → WELDING_TIP_T15
                    - Conveyors → CONVEYOR_BELT_10M, PNEUMATIC_VALVE_24V

                    Provide your analysis now:"""

        return prompt

    def _parse_response(self, response_text: str) -> LLMAnalysis:
        """
        Parse the LLM response into structured format.
        """
        lines = response_text.strip().split("\n")

        # Initialize with defaults
        routing_decision = "inventory"
        urgency_level = "medium"
        required_parts = []
        reasoning = ""
        key_concerns = []
        recommended_actions = []

        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("ROUTING_DECISION:"):
                routing_decision = line.split(":", 1)[1].strip().lower()
            elif line.startswith("URGENCY_LEVEL:"):
                urgency_level = line.split(":", 1)[1].strip().lower()
            elif line.startswith("REQUIRED_PARTS:"):
                parts_str = line.split(":", 1)[1].strip()
                if parts_str.lower() != "none":
                    required_parts = [p.strip() for p in parts_str.split(",")]
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()
                current_section = "reasoning"
            elif line.startswith("KEY_CONCERNS:"):
                current_section = "concerns"
            elif line.startswith("RECOMMENDED_ACTIONS:"):
                current_section = "actions"
            elif line.startswith("-") or line.startswith("•") or line.startswith("*"):
                # Bullet point
                item = line[1:].strip()
                if current_section == "concerns":
                    key_concerns.append(item)
                elif current_section == "actions":
                    recommended_actions.append(item)
            elif current_section == "reasoning" and line:
                reasoning += " " + line

        return LLMAnalysis(
            routing_decision=routing_decision,
            urgency_level=urgency_level,
            required_parts=required_parts,
            reasoning=reasoning.strip(),
            key_concerns=key_concerns,
            recommended_actions=recommended_actions,
        )

    def _fallback_analysis(self, event: Dict[str, Any]) -> LLMAnalysis:
        """
        Provide fallback analysis if LLM fails.
        """
        event_type = event.get("event_type", "UNKNOWN")
        severity = event.get("severity", "MEDIUM")

        logger.warning("⚠️ Using fallback analysis (LLM unavailable)")

        # Simple rule-based fallback
        if event_type == "LOW_INVENTORY":
            routing = "inventory"
            parts = []
        elif "OVERHEAT" in event_type or "VIBRATION" in event_type:
            routing = "inventory"
            parts = ["HYDRAULIC_PUMP_001", "BEARING_6205"]
        else:
            routing = "inventory"
            parts = []

        return LLMAnalysis(
            routing_decision=routing,
            urgency_level=severity.lower(),
            required_parts=parts,
            reasoning=f"Fallback analysis for {event_type} event (LLM unavailable)",
            key_concerns=[f"{event_type} requires attention"],
            recommended_actions=["Check system logs", "Verify part availability"],
        )
