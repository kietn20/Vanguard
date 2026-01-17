package com.vanguard.inventory.mcp;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.vanguard.inventory.mcp.tools.MCPTool;

/**
 * Registry that manages all MCP tools available in the Inventory Service.
 *
 * This acts as the central hub for:
 * - Tool registration
 * - Tool discovery
 * - Tool execution
 */
@Component
public class MCPToolRegistry {

    private final Map<String, MCPTool> tools = new HashMap<>();
    private final ObjectMapper objectMapper;

    public MCPToolRegistry(
            ObjectMapper objectMapper,
            List<MCPTool> availableTools) {
        this.objectMapper = objectMapper;

        // Auto-register all MCPTool beans
        availableTools.forEach(tool -> {
            tools.put(tool.getName(), tool);
        });
    }

    /**
     * Get all registered tools.
     */
    public List<MCPTool> getAllTools() {
        return List.copyOf(tools.values());
    }

    /**
     * Execute a tool by name with given arguments.
     */
    public Object executeTool(String toolName, JsonNode arguments) {
        MCPTool tool = tools.get(toolName);
        if (tool == null) {
            throw new IllegalArgumentException("Tool not found: " + toolName);
        }
        return tool.execute(arguments);
    }

    /**
     * Check if a tool exists.
     */
    public boolean hasTool(String toolName) {
        return tools.containsKey(toolName);
    }
}
