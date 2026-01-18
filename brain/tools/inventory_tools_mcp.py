"""
MCP-based inventory tools.

These tools use the Model Context Protocol to dynamically discover
and call inventory service capabilities.
"""

import logging
import os
from typing import List, Optional

from pydantic import BaseModel
from services.mcp_client import MCPClient, MCPError

logger = logging.getLogger(__name__)

# MCP server URL
INVENTORY_MCP_URL = os.getenv("INVENTORY_MCP_URL", "http://localhost:8082/mcp")

# Global MCP client instance
_mcp_client: Optional[MCPClient] = None


async def get_mcp_client() -> MCPClient:
    """
    Get or create MCP client instance.

    This is a singleton pattern - we reuse the same client
    to maintain the connection and tool cache.
    """
    global _mcp_client

    if _mcp_client is None:
        _mcp_client = MCPClient(INVENTORY_MCP_URL)
        await _mcp_client.initialize()
        logger.info("✅ MCP client initialized and ready")

    return _mcp_client


class PartInfo(BaseModel):
    """Information about a spare part."""

    part_number: str
    name: str
    quantity: int
    minimum_quantity: int
    unit_price: float
    location: str
    low_stock: bool
    out_of_stock: bool


async def get_part_by_number_mcp(part_number: str) -> PartInfo:
    """
    Get detailed information about a specific part using MCP.

    Args:
        part_number: The part number to look up

    Returns:
        PartInfo: Details about the part

    Raises:
        MCPError: If tool execution fails
    """
    client = await get_mcp_client()

    result = await client.call_tool("get_part_by_number", {"part_number": part_number})

    return PartInfo(**result)


async def check_availability_mcp(part_number: str, quantity: int) -> bool:
    """
    Check if sufficient quantity of a part is available using MCP.

    Args:
        part_number: The part number to check
        quantity: Required quantity

    Returns:
        bool: True if available, False otherwise
    """
    client = await get_mcp_client()

    result = await client.call_tool(
        "check_availability", {"part_number": part_number, "quantity": quantity}
    )

    return result.get("available", False)


async def get_low_stock_parts_mcp() -> List[dict]:
    """
    Get all parts with stock below minimum quantity using MCP.

    Returns:
        List of parts that need reordering
    """
    client = await get_mcp_client()

    result = await client.call_tool("get_low_stock_parts", {})

    return result.get("low_stock_parts", [])


async def discover_inventory_tools() -> List[str]:
    """
    Discover all available inventory tools from the MCP server.

    This demonstrates dynamic tool discovery - the AI agent
    can find new capabilities without code changes.

    Returns:
        List of available tool names
    """
    client = await get_mcp_client()
    tools = await client.list_tools()

    tool_names = [tool.name for tool in tools]
    logger.info(f"📋 Discovered {len(tool_names)} inventory tools:")
    for tool in tools:
        logger.info(f"  • {tool.name}: {tool.description}")

    return tool_names


async def remove_stock_mcp(
    part_number: str, quantity: int, reason: str, event_id: Optional[str] = None
) -> dict:
    """
    Remove stock from inventory using MCP.

    Args:
        part_number: Part to remove stock from
        quantity: Amount to remove
        reason: Reason for removal
        event_id: Optional event ID for traceability

    Returns:
        Transaction details
    """
    client = await get_mcp_client()

    arguments = {"part_number": part_number, "quantity": quantity, "reason": reason}

    if event_id:
        arguments["event_id"] = event_id

    result = await client.call_tool("remove_stock", arguments)
    return result


async def add_stock_mcp(part_number: str, quantity: int, reason: str) -> dict:
    """
    Add stock to inventory using MCP.

    Args:
        part_number: Part to add stock to
        quantity: Amount to add
        reason: Reason for addition

    Returns:
        Transaction details
    """
    client = await get_mcp_client()

    result = await client.call_tool(
        "add_stock",
        {"part_number": part_number, "quantity": quantity, "reason": reason},
    )

    return result


async def get_all_parts_mcp() -> List[dict]:
    """
    Get all parts in inventory using MCP.

    Returns:
        List of all parts
    """
    client = await get_mcp_client()

    result = await client.call_tool("get_all_parts", {})
    return result.get("parts", [])
