"""
Client for calling the Guardrail Service.

AI agents must call this BEFORE executing inventory actions.
"""

import os
import httpx
from typing import Optional, List
from pydantic import BaseModel, Field


GUARDRAIL_API_BASE = os.getenv("GUARDRAIL_API_BASE", "http://localhost:8083/api/guardrail")


class GuardrailRequest(BaseModel):
    """Request to validate an action."""

    action_type: str = Field(serialization_alias="actionType")
    part_number: str = Field(serialization_alias="partNumber")
    quantity: int
    reason: str
    event_id: Optional[str] = Field(default=None, serialization_alias="eventId")
    agent_id: str = Field(default="inventory-agent", serialization_alias="agentId")


class GuardrailResponse(BaseModel):
    """Response from guardrail validation."""

    approved: bool
    decision: str
    violations: List[str]
    warnings: List[str]
    requires_human_approval: bool
    validated_by: str


class GuardrailError(Exception):
    """Raised when guardrail validation fails."""

    pass


def validate_action(
    action_type: str,
    part_number: str,
    quantity: int,
    reason: str,
    event_id: Optional[str] = None,
) -> GuardrailResponse:
    """
    Validate an action with the guardrail service.

    Args:
        action_type: "ADD" or "REMOVE"
        part_number: Part to operate on
        quantity: Amount to add/remove
        reason: Why this action is needed
        event_id: Optional event ID for traceability

    Returns:
        GuardrailResponse: Validation result

    Raises:
        GuardrailError: If validation fails or service unavailable
    """
    try:
        request = GuardrailRequest(
            action_type=action_type,
            part_number=part_number,
            quantity=quantity,
            reason=reason,
            event_id=event_id,
        )

        response = httpx.post(f"{GUARDRAIL_API_BASE}/validate", json=request.model_dump(by_alias=True), timeout=5.0)

        # accept both 200 (approved) and 202 (requires approval)
        if response.status_code in [200, 202]:
            data = response.json()
            return GuardrailResponse(
                approved=data["approved"],
                decision=data["decision"],
                violations=data.get("violations", []),
                warnings=data.get("warnings", []),
                requires_human_approval=data.get("requiresHumanApproval", False),
                validated_by=data.get("validatedBy", "UNKNOWN"),
            )
        elif response.status_code == 403:
            # Rejected
            data = response.json()
            raise GuardrailError(
                f"Action rejected: {', '.join(data.get('violations', ['Unknown violation']))}"
            )
        else:
            raise GuardrailError(f"Guardrail service error: {response.status_code}")

    except httpx.RequestError as e:
        raise GuardrailError(f"Cannot reach guardrail service: {str(e)}")
