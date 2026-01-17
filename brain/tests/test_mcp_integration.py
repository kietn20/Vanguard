"""
Integration tests for MCP client and inventory tools.
"""

import asyncio

import pytest
from services.mcp_client import MCPClient, MCPError
from tools.inventory_tools_mcp import (
    check_availability_mcp,
    discover_inventory_tools,
    get_low_stock_parts_mcp,
    get_part_by_number_mcp,
)


@pytest.mark.asyncio
async def test_mcp_initialize():
    """Test MCP session initialization."""
    client = MCPClient("http://localhost:8082/mcp")
    result = await client.initialize()

    assert "serverInfo" in result
    assert result["serverInfo"]["name"] == "vanguard-inventory"
    assert "capabilities" in result


@pytest.mark.asyncio
async def test_mcp_list_tools():
    """Test tool discovery."""
    client = MCPClient("http://localhost:8082/mcp")
    await client.initialize()

    tools = await client.list_tools()

    assert len(tools) >= 3
    tool_names = [t.name for t in tools]
    assert "get_part_by_number" in tool_names
    assert "check_availability" in tool_names
    assert "get_low_stock_parts" in tool_names


@pytest.mark.asyncio
async def test_mcp_call_get_part():
    """Test calling get_part_by_number tool via MCP."""
    part = await get_part_by_number_mcp("HYDRAULIC_PUMP_001")

    assert part.part_number == "HYDRAULIC_PUMP_001"
    assert part.name == "Hydraulic Pump Model A"
    assert part.quantity >= 0


@pytest.mark.asyncio
async def test_mcp_call_check_availability():
    """Test calling check_availability tool via MCP."""
    available = await check_availability_mcp("HYDRAULIC_PUMP_001", 5)
    assert isinstance(available, bool)


@pytest.mark.asyncio
async def test_mcp_tool_discovery():
    """Test dynamic tool discovery."""
    tools = await discover_inventory_tools()
    assert len(tools) >= 3
    assert "get_part_by_number" in tools


@pytest.mark.asyncio
async def test_mcp_error_handling():
    """Test error handling for non-existent part."""
    with pytest.raises(MCPError):
        await get_part_by_number_mcp("NON_EXISTENT_PART")
