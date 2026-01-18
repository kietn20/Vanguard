"""
Comprehensive MCP integration tests.
"""

import pytest
from services.mcp_client import MCPClient
from tools.guardrail_client_mcp import validate_action_mcp
from tools.inventory_tools_mcp import (
    add_stock_mcp,
    check_availability_mcp,
    get_all_parts_mcp,
    get_low_stock_parts_mcp,
    get_part_by_number_mcp,
    remove_stock_mcp,
)


@pytest.mark.asyncio
async def test_full_inventory_workflow_via_mcp():
    """Test complete inventory workflow using only MCP."""

    # 1. Get initial part state
    part = await get_part_by_number_mcp("BEARING_6205")
    initial_quantity = part.quantity

    # 2. Validate adding stock
    validation = await validate_action_mcp(
        action_type="ADD",
        part_number="BEARING_6205",
        quantity=10,
        reason="Test shipment received from supplier",
    )
    assert validation.approved is True

    # 3. Add stock via MCP
    add_result = await add_stock_mcp(
        part_number="BEARING_6205",
        quantity=10,
        reason="Test shipment received from supplier",
    )
    assert add_result["success"] is True
    assert add_result["quantity_after"] == initial_quantity + 10

    # 4. Verify new quantity
    part_updated = await get_part_by_number_mcp("BEARING_6205")
    assert part_updated.quantity == initial_quantity + 10

    # 5. Validate removing stock
    validation2 = await validate_action_mcp(
        action_type="REMOVE",
        part_number="BEARING_6205",
        quantity=5,
        reason="Used for machine repair on PRESS-001",
    )
    assert validation2.approved is True

    # 6. Remove stock via MCP
    remove_result = await remove_stock_mcp(
        part_number="BEARING_6205",
        quantity=5,
        reason="Used for machine repair on PRESS-001",
    )
    assert remove_result["success"] is True

    # 7. Final verification
    part_final = await get_part_by_number_mcp("BEARING_6205")
    assert part_final.quantity == initial_quantity + 5


@pytest.mark.asyncio
async def test_mcp_tool_discovery_inventory():
    """Test tool discovery on inventory service."""
    client = MCPClient("http://localhost:8082/mcp")
    await client.initialize()
    tools = await client.list_tools()
    tool_names = [t.name for t in tools]

    expected_tools = [
        "get_part_by_number",
        "check_availability",
        "get_low_stock_parts",
        "remove_stock",
        "add_stock",
        "get_all_parts",
    ]

    for expected in expected_tools:
        assert expected in tool_names, f"Missing tool: {expected}"


@pytest.mark.asyncio
async def test_mcp_tool_discovery_guardrail():
    """Test tool discovery on guardrail service."""
    client = MCPClient("http://localhost:8083/mcp")
    await client.initialize()
    tools = await client.list_tools()
    tool_names = [t.name for t in tools]

    assert "validate_action" in tool_names


@pytest.mark.asyncio
async def test_mcp_guardrail_rejection():
    """Test that guardrail rejects excessive quantities via MCP."""
    from services.mcp_client import MCPError

    # Try to remove excessive quantity (should be rejected, NOT raise error)
    # The tool should return a valid result with approved=False
    validation = await validate_action_mcp(
        action_type="REMOVE",
        part_number="BEARING_6205",
        quantity=100,  # Exceeds max of 50
        reason="Test excessive removal",
    )
    
    assert validation.approved is False
    assert len(validation.violations) > 0


@pytest.mark.asyncio
async def test_mcp_get_all_parts():
    """Test getting all parts via MCP."""
    parts = await get_all_parts_mcp()
    assert len(parts) > 0
    assert all("part_number" in p for p in parts)
    assert all("quantity" in p for p in parts)
