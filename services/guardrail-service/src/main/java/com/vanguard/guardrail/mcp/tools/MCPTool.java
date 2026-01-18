package com.vanguard.guardrail.mcp.tools;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

public interface MCPTool {
    String getName();

    String getDescription();

    ObjectNode getInputSchema();

    Object execute(JsonNode arguments);

    default ObjectNode toJson() {
        ObjectNode toolDef = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();
        toolDef.put("name", getName());
        toolDef.put("description", getDescription());
        toolDef.set("inputSchema", getInputSchema());
        return toolDef;
    }
}
