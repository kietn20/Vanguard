"""
MCP-based guardrail client.

Uses Model Context Protocol to validate actions with the Guardrail Service.
"""

import logging
import os
from typing import Optional, List

from pydantic import BaseModel
from services.mcp_client import MCPClient, MCPError

logger = logging.getLogger(__name__)

GUARDRAIL_MCP_URL = os.getenv("GUARDRAIL_MCP_URL", "http://localhost:8083/mcp")

_guardrail_mcp_client: Optional[MCPClient] = None


async def get_guardrail_mcp_client() -> MCPClient:
    """Get or create Guardrail MCP client instance."""
    global _guardrail_mcp_client

    if _guardrail_mcp_client is None:
        _guardrail_mcp_client = MCPClient(GUARDRAIL_MCP_URL)
        await _guardrail_mcp_client.initialize()
        logger.info("✅ Guardrail MCP client initialized")

    return _guardrail_mcp_client


class GuardrailValidationResult(BaseModel):
    """Result from guardrail validation."""

    approved: bool
    decision: str
    violations: List[str]
    warnings: List[str]
    requires_human_approval: bool


async def validate_action_mcp(
    action_type: str,
    part_number: str,
    quantity: int,
    reason: str,
    event_id: Optional[str] = None,
    agent_id: str = "inventory-agent-mcp",
) -> GuardrailValidationResult:
    """
    Validate an action using MCP.

    Args:
        action_type: "ADD" or "REMOVE"
        part_number: Part to operate on
        quantity: Amount
        reason: Justification
        event_id: Optional event ID
        agent_id: Agent requesting validation

    Returns:
        Validation result

    Raises:
        MCPError: If validation fails
    """
    client = await get_guardrail_mcp_client()

    arguments = {
        "action_type": action_type,
        "part_number": part_number,
        "quantity": quantity,
        "reason": reason,
        "agent_id": agent_id,
    }

    if event_id:
        arguments["event_id"] = event_id

    try:
        result = await client.call_tool("validate_action", arguments)
        return GuardrailValidationResult(**result)
    except MCPError as e:
        logger.error(f"Guardrail MCP validation failed: {e}")
        raise
