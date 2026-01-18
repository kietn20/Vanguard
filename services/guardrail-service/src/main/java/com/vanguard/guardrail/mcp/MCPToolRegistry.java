package com.vanguard.guardrail.mcp;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.vanguard.guardrail.mcp.tools.MCPTool;

@Component
public class MCPToolRegistry {

    private final Map<String, MCPTool> tools = new HashMap<>();
    private final ObjectMapper objectMapper;

    public MCPToolRegistry(
            ObjectMapper objectMapper,
            List<MCPTool> availableTools) {
        this.objectMapper = objectMapper;

        availableTools.forEach(tool -> {
            tools.put(tool.getName(), tool);
        });
    }

    public List<MCPTool> getAllTools() {
        return List.copyOf(tools.values());
    }

    public Object executeTool(String toolName, JsonNode arguments) {
        MCPTool tool = tools.get(toolName);
        if (tool == null) {
            throw new IllegalArgumentException("Tool not found: " + toolName);
        }
        return tool.execute(arguments);
    }

    public boolean hasTool(String toolName) {
        return tools.containsKey(toolName);
    }
}
