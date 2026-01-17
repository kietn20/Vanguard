"""
MCP Client for discovering and calling tools from Java services.

This client implements the Model Context Protocol specification
to dynamically discover and execute tools exposed by microservices.
"""

import logging
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MCPToolSchema(BaseModel):
    """Schema for an MCP tool."""

    name: str
    description: str
    input_schema: Dict[str, Any] = Field(alias="inputSchema")


class MCPClient:
    """
    Client for interacting with MCP servers.

    Usage:
        client = MCPClient("http://inventory-service:8082/mcp")
        await client.initialize()
        tools = await client.list_tools()
        result = await client.call_tool("get_part_by_number", {"part_number": "ABC"})
    """

    def __init__(self, server_url: str, timeout: float = 10.0):
        """
        Initialize MCP client.

        Args:
            server_url: Base URL of the MCP server (e.g., http://localhost:8082/mcp)
            timeout: Request timeout in seconds
        """
        self.server_url = server_url
        self.timeout = timeout
        self.session_id = 0
        self._tools_cache: Optional[List[MCPToolSchema]] = None

        logger.info(f"Initialized MCP client for {server_url}")

    def _get_request_id(self) -> int:
        """Generate unique request ID."""
        self.session_id += 1
        return self.session_id

    async def _send_request(
        self, method: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Send JSON-RPC request to MCP server.

        Args:
            method: JSON-RPC method name
            params: Optional parameters

        Returns:
            Response result

        Raises:
            MCPError: If request fails
        """
        request_payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._get_request_id(),
        }

        if params:
            request_payload["params"] = params

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.server_url, json=request_payload)
                response.raise_for_status()

                data = response.json()

                if "error" in data:
                    error = data["error"]
                    raise MCPError(f"MCP Error [{error['code']}]: {error['message']}")

                return data.get("result", {})

        except httpx.HTTPError as e:
            raise MCPError(f"HTTP error communicating with MCP server: {e}")
        except Exception as e:
            raise MCPError(f"Failed to send MCP request: {e}")

    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize MCP session.

        Returns:
            Server capabilities and info
        """
        logger.info("Initializing MCP session")
        result = await self._send_request("initialize")
        logger.info(f"MCP session initialized: {result.get('serverInfo', {})}")
        return result

    async def list_tools(self, force_refresh: bool = False) -> List[MCPToolSchema]:
        """
        List all available tools from the server.

        Args:
            force_refresh: If True, bypass cache and fetch fresh tools

        Returns:
            List of available tools
        """
        if self._tools_cache and not force_refresh:
            return self._tools_cache

        logger.info("Fetching available tools from MCP server")
        result = await self._send_request("tools/list")

        tools = [MCPToolSchema(**tool_data) for tool_data in result.get("tools", [])]

        self._tools_cache = tools
        logger.info(f"Discovered {len(tools)} tools: {[t.name for t in tools]}")

        return tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as dictionary

        Returns:
            Tool execution result

        Raises:
            MCPError: If tool execution fails
        """
        logger.debug(f"Calling tool '{tool_name}' with args: {arguments}")

        params = {"name": tool_name, "arguments": arguments}

        result = await self._send_request("tools/call", params)
        logger.debug(f"Tool '{tool_name}' returned: {result}")

        return result

    async def get_tool(self, tool_name: str) -> Optional[MCPToolSchema]:
        """
        Get schema for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool schema or None if not found
        """
        tools = await self.list_tools()
        return next((t for t in tools if t.name == tool_name), None)


class MCPError(Exception):
    """Exception raised for MCP-related errors."""

    pass
