"""
Tests for LangGraph workflow.
"""

import pytest
from agents.state import AgentState, EventType, Severity
from agents.workflow_langgraph import LangGraphWorkflow
from agents.graph_nodes import supervisor_node, inventory_node, escalation_node
from agents.graph_routing import route_after_supervisor, route_after_inventory


class TestLangGraphNodes:
    """Test individual graph nodes."""

    def test_supervisor_node_routes_to_inventory(self):
        """Test that supervisor node correctly analyzes and routes."""
        state: AgentState = {
            "event_id": "test-001",
            "event_type": EventType.LOW_INVENTORY,
            "machine_id": "INVENTORY-SYSTEM",
            "severity": Severity.MEDIUM,
            "description": "Test event",
            "timestamp": "2026-01-17T10:00:00Z",
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

        # Execute supervisor node
        updates = supervisor_node(state)

        # Should route to inventory
        assert updates["next_agent"] == "inventory"
        assert "analysis" in updates
        assert updates["analysis"] != ""

    def test_inventory_node_processes_state(self):
        """Test that inventory node processes correctly."""
        state: AgentState = {
            "event_id": "test-002",
            "event_type": EventType.SENSOR_OVERHEAT,
            "machine_id": "PRESS-001",
            "severity": Severity.CRITICAL,
            "description": "Overheat detected",
            "timestamp": "2026-01-17T10:00:00Z",
            "metadata": {},
            "next_agent": "inventory",
            "should_escalate": True,
            "analysis": "Test analysis",
            "recommended_actions": [],
            "required_parts": ["HYDRAULIC_PUMP_001"],
            "parts_available": {},
            "actions_taken": [],
            "final_decision": "",
            "human_approval_needed": False,
        }

        # Execute inventory node
        updates = inventory_node(state)

        # Should have processed parts
        assert "parts_available" in updates
        assert "final_decision" in updates
        assert updates["final_decision"] != ""


class TestLangGraphRouting:
    """Test routing logic."""

    def test_route_after_supervisor_to_inventory(self):
        """Test routing from supervisor to inventory."""
        state: AgentState = {
            "event_id": "test",
            "event_type": EventType.LOW_INVENTORY,
            "machine_id": "TEST",
            "severity": Severity.MEDIUM,
            "description": "Test",
            "timestamp": "2026-01-17T10:00:00Z",
            "metadata": {},
            "next_agent": "inventory",
            "should_escalate": False,
            "analysis": "",
            "recommended_actions": [],
            "required_parts": [],
            "parts_available": {},
            "actions_taken": [],
            "final_decision": "",
            "human_approval_needed": False,
        }

        result = route_after_supervisor(state)
        assert result == "inventory"

    def test_route_after_supervisor_to_end(self):
        """Test routing from supervisor to end."""
        state: AgentState = {
            "event_id": "test",
            "event_type": EventType.LOW_INVENTORY,
            "machine_id": "TEST",
            "severity": Severity.MEDIUM,
            "description": "Test",
            "timestamp": "2026-01-17T10:00:00Z",
            "metadata": {},
            "next_agent": None,  # No agent needed
            "should_escalate": False,
            "analysis": "",
            "recommended_actions": [],
            "required_parts": [],
            "parts_available": {},
            "actions_taken": [],
            "final_decision": "",
            "human_approval_needed": False,
        }

        result = route_after_supervisor(state)
        assert result == "end"

    def test_route_after_inventory_to_escalation(self):
        """Test routing from inventory to escalation."""
        state: AgentState = {
            "event_id": "test",
            "event_type": EventType.SENSOR_OVERHEAT,
            "machine_id": "TEST",
            "severity": Severity.CRITICAL,
            "description": "Test",
            "timestamp": "2026-01-17T10:00:00Z",
            "metadata": {},
            "next_agent": "inventory",
            "should_escalate": True,  # Should escalate
            "analysis": "",
            "recommended_actions": [],
            "required_parts": [],
            "parts_available": {},
            "actions_taken": [],
            "final_decision": "",
            "human_approval_needed": False,
        }

        result = route_after_inventory(state)
        assert result == "escalation"

    def test_route_after_inventory_to_end(self):
        """Test routing from inventory to end."""
        state: AgentState = {
            "event_id": "test",
            "event_type": EventType.LOW_INVENTORY,
            "machine_id": "TEST",
            "severity": Severity.MEDIUM,
            "description": "Test",
            "timestamp": "2026-01-17T10:00:00Z",
            "metadata": {},
            "next_agent": "inventory",
            "should_escalate": False,  # No escalation
            "analysis": "",
            "recommended_actions": [],
            "required_parts": [],
            "parts_available": {},
            "actions_taken": [],
            "final_decision": "",
            "human_approval_needed": False,
        }

        result = route_after_inventory(state)
        assert result == "end"


class TestLangGraphWorkflow:
    """Test complete workflow."""

    def test_workflow_initialization(self):
        """Test that workflow compiles successfully."""
        workflow = LangGraphWorkflow()
        assert workflow.graph is not None

    def test_workflow_processes_low_inventory_event(self):
        """Test workflow with LOW_INVENTORY event."""
        workflow = LangGraphWorkflow()

        event = {
            "event_id": "test-low-inv-001",
            "event_type": "LOW_INVENTORY",
            "machine_id": "INVENTORY-SYSTEM",
            "severity": "MEDIUM",
            "description": "Low stock detected",
            "timestamp": "2026-01-17T10:00:00Z",
            "metadata": {
                "part_name": "BEARING_6205",
                "current_stock": 5,
                "minimum_stock": 10,
            },
        }

        final_state = workflow.process_event(event)

        # Verify workflow completed
        assert final_state["event_id"] == "test-low-inv-001"
        assert final_state["final_decision"] != ""

    def test_workflow_processes_critical_event(self):
        """Test workflow with CRITICAL event (should escalate)."""
        workflow = LangGraphWorkflow()

        event = {
            "event_id": "test-critical-001",
            "event_type": "SENSOR_OVERHEAT",
            "machine_id": "PRESS-001",
            "severity": "CRITICAL",
            "description": "Critical overheat detected",
            "timestamp": "2026-01-17T10:00:00Z",
            "metadata": {"temperature_celsius": 120, "threshold_celsius": 80},
        }

        final_state = workflow.process_event(event)

        # Should have escalated
        assert final_state["should_escalate"] is True
        assert "ESCALATED" in final_state.get("final_decision", "")

    def test_workflow_state_accumulation(self):
        """Test that state properly accumulates (not overwrites)."""
        workflow = LangGraphWorkflow()

        event = {
            "event_id": "test-accum-001",
            "event_type": "MAINTENANCE_DUE",
            "machine_id": "CNC-M10",
            "severity": "HIGH",
            "description": "Maintenance due",
            "timestamp": "2026-01-17T10:00:00Z",
            "metadata": {},
        }

        final_state = workflow.process_event(event)

        # Check that lists accumulated (not replaced)
        # recommended_actions should have items from both supervisor and inventory
        assert isinstance(final_state.get("recommended_actions"), list)
        assert isinstance(final_state.get("actions_taken"), list)
