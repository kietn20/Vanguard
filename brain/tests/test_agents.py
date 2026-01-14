import pytest
from agents.state import AgentState, EventType, Severity
from agents.supervisor import SupervisorAgent
from agents.inventory_agent import InventoryAgent


class TestSupervisorAgent:
    """Tests for Supervisor Agent."""

    def test_supervisor_routes_low_inventory_to_inventory_agent(self):
        """Test that LOW_INVENTORY events are routed to inventory agent."""
        supervisor = SupervisorAgent()

        state: AgentState = {
            "event_id": "test-001",
            "event_type": EventType.LOW_INVENTORY,
            "machine_id": "INVENTORY-SYSTEM",
            "severity": Severity.MEDIUM,
            "description": "Test low inventory",
            "timestamp": "2026-01-09T10:00:00Z",
            "metadata": {},
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

        result = supervisor.analyze_event(state)

        assert result["next_agent"] == "inventory"
        # Accept either rule-based or LLM-based analysis strings
        assert "Low inventory" in result["analysis"] or "LLM Analysis" in result["analysis"]
        assert result["should_escalate"] is False

    def test_supervisor_escalates_critical_events(self):
        """Test that CRITICAL events are marked for escalation."""
        supervisor = SupervisorAgent()

        state: AgentState = {
            "event_id": "test-002",
            "event_type": EventType.SENSOR_OVERHEAT,
            "machine_id": "PRESS-001",
            "severity": Severity.CRITICAL,
            "description": "Critical overheat",
            "timestamp": "2026-01-09T10:00:00Z",
            "metadata": {},
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

        result = supervisor.analyze_event(state)

        assert result["should_escalate"] is True
        assert result["next_agent"] == "inventory"

    def test_supervisor_identifies_required_parts_for_press_machine(self):
        """Test that supervisor identifies correct parts for press machines."""
        supervisor = SupervisorAgent()

        state: AgentState = {
            "event_id": "test-003",
            "event_type": EventType.SENSOR_OVERHEAT,
            "machine_id": "PRESS-002",
            "severity": Severity.HIGH,
            "description": "Overheat on press",
            "timestamp": "2026-01-09T10:00:00Z",
            "metadata": {},
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

        result = supervisor.analyze_event(state)

        assert "HYDRAULIC_PUMP_001" in result["required_parts"]
        assert "PRESSURE_SENSOR_PSI" in result["required_parts"]


class TestInventoryAgent:
    """Tests for Inventory Agent."""

    def test_inventory_agent_processes_state(self):
        """Test that inventory agent processes state correctly."""
        agent = InventoryAgent()

        state: AgentState = {
            "event_id": "test-004",
            "event_type": EventType.LOW_INVENTORY,
            "machine_id": "INVENTORY-SYSTEM",
            "severity": Severity.MEDIUM,
            "description": "Test",
            "timestamp": "2026-01-09T10:00:00Z",
            "metadata": {},
            "next_agent": "inventory",
            "should_escalate": False,
            "analysis": "Test analysis",
            "recommended_actions": [],
            "required_parts": [],
            "parts_available": {},
            "actions_taken": [],
            "final_decision": "",
            "human_approval_needed": False,
        }

        result = agent.process(state)

        # Should have taken actions
        assert len(result["actions_taken"]) > 0

        # Should have a final decision
        assert result["final_decision"] != ""

    def test_inventory_agent_checks_required_parts(self):
        """Test that inventory agent checks required parts."""
        agent = InventoryAgent()

        state: AgentState = {
            "event_id": "test-005",
            "event_type": EventType.SENSOR_OVERHEAT,
            "machine_id": "PRESS-001",
            "severity": Severity.CRITICAL,
            "description": "Test",
            "timestamp": "2026-01-09T10:00:00Z",
            "metadata": {},
            "next_agent": "inventory",
            "should_escalate": True,
            "analysis": "Test",
            "recommended_actions": [],
            "required_parts": ["HYDRAULIC_PUMP_001"],
            "parts_available": {},
            "actions_taken": [],
            "final_decision": "",
            "human_approval_needed": False,
        }

        result = agent.process(state)

        # should have checked the part
        assert "HYDRAULIC_PUMP_001" in result["parts_available"]

        # should have recorded the check
        check_actions = [
            action
            for action in result["actions_taken"]
            if action.get("action") == "check_availability"
        ]
        assert len(check_actions) > 0

    def test_inventory_agent_escalates_when_parts_missing(self):
        """Test that agent escalates when required parts are missing."""
        agent = InventoryAgent()

        state: AgentState = {
            "event_id": "test-006",
            "event_type": EventType.MAINTENANCE_DUE,
            "machine_id": "CNC-M10",
            "severity": Severity.HIGH,
            "description": "Test",
            "timestamp": "2026-01-09T10:00:00Z",
            "metadata": {},
            "next_agent": "inventory",
            "should_escalate": False,
            "analysis": "Test",
            "recommended_actions": [],
            "required_parts": ["NON-EXISTENT-PART"],
            "parts_available": {},
            "actions_taken": [],
            "final_decision": "",
            "human_approval_needed": False,
        }

        result = agent.process(state)

        # part should be marked as unavailable
        assert result["parts_available"]["NON-EXISTENT-PART"] is False

        # should escalate
        assert result["should_escalate"] is True

        # should need human approval
        assert result["human_approval_needed"] is True
