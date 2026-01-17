package com.vanguard.inventory.mcp.tools;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

/**
 * Interface for MCP tools.
 *
 * Each tool must:
 * 1. Have a unique name
 * 2. Provide a description
 * 3. Define input schema (JSON Schema)
 * 4. Implement execution logic
 */
public interface MCPTool {

    /**
     * Unique tool identifier (e.g., "get_part_by_number").
     */
    String getName();

    /**
     * Human-readable description of what the tool does.
     */
    String getDescription();

    /**
     * JSON Schema defining the tool's input parameters.
     */
    ObjectNode getInputSchema();

    /**
     * Execute the tool with given arguments.
     *
     * @param arguments JSON object containing tool parameters
     * @return Tool execution result (will be serialized to JSON)
     */
    Object execute(JsonNode arguments);

    /**
     * Convert tool definition to MCP-compliant JSON.
     */
    default ObjectNode toJson() {
        ObjectNode toolDef = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();
        toolDef.put("name", getName());
        toolDef.put("description", getDescription());
        toolDef.set("inputSchema", getInputSchema());
        return toolDef;
    }
}
