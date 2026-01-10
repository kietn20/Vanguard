"""
Integration tests for guardrail + inventory agent.

These tests verify that agents respect guardrail decisions.
"""

import pytest
from tools.guardrail_client import validate_action, GuardrailError


def test_guardrail_approves_normal_action():
    """Test that guardrail approves normal actions."""
    result = validate_action(
        action_type="REMOVE",
        part_number="BEARING_6205",
        quantity=10,
        reason="Used for machine repair on PRESS-001",
        event_id="test-integration-001",
    )

    assert result.approved is True
    assert len(result.violations) == 0


def test_guardrail_rejects_excessive_quantity():
    """Test that guardrail rejects excessive quantities."""
    with pytest.raises(GuardrailError) as exc_info:
        validate_action(
            action_type="REMOVE",
            part_number="BEARING_6205",
            quantity=100,
            reason="Attempting excessive removal",
            event_id="test-integration-002",
        )

    assert "rejected" in str(exc_info.value).lower()


def test_guardrail_requires_approval_for_critical_parts():
    """Test that critical parts require human approval."""
    result = validate_action(
        action_type="REMOVE",
        part_number="HYDRAULIC_PUMP_001",
        quantity=1,
        reason="Replacing failed hydraulic pump",
        event_id="test-integration-003",
    )

    assert result.requires_human_approval is True
    assert len(result.warnings) > 0


def test_guardrail_rejects_short_reason():
    """Test that short reasons are rejected."""
    with pytest.raises(GuardrailError) as exc_info:
        validate_action(
            action_type="REMOVE",
            part_number="BEARING_6205",
            quantity=5,
            reason="Fix",
            event_id="test-integration-004",
        )

    assert "reason" in str(exc_info.value).lower()
