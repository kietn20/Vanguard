package com.vanguard.guardrail.mcp;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

/**
 * MCP Server endpoint for Guardrail Service.
 */
@RestController
@RequestMapping("/mcp")
public class MCPController {

    private final ObjectMapper objectMapper;
    private final MCPToolRegistry toolRegistry;

    public MCPController(ObjectMapper objectMapper, MCPToolRegistry toolRegistry) {
        this.objectMapper = objectMapper;
        this.toolRegistry = toolRegistry;
    }

    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
    public ObjectNode handleRequest(@RequestBody JsonNode request) {
        String method = request.get("method").asText();
        JsonNode id = request.get("id");

        return switch (method) {
            case "tools/list" -> listTools(id);
            case "tools/call" -> callTool(request, id);
            case "initialize" -> initialize(id);
            default -> createErrorResponse(id, -32601, "Method not found: " + method);
        };
    }

    private ObjectNode initialize(JsonNode id) {
        ObjectNode response = objectMapper.createObjectNode();
        response.put("jsonrpc", "2.0");
        response.set("id", id);

        ObjectNode result = objectMapper.createObjectNode();
        result.put("protocolVersion", "2024-11-05");

        ObjectNode serverInfo = objectMapper.createObjectNode();
        serverInfo.put("name", "vanguard-guardrail");
        serverInfo.put("version", "0.1.0");
        result.set("serverInfo", serverInfo);

        ObjectNode capabilities = objectMapper.createObjectNode();
        capabilities.put("tools", true);
        result.set("capabilities", capabilities);

        response.set("result", result);
        return response;
    }

    private ObjectNode listTools(JsonNode id) {
        ObjectNode response = objectMapper.createObjectNode();
        response.put("jsonrpc", "2.0");
        response.set("id", id);

        ArrayNode tools = objectMapper.createArrayNode();
        toolRegistry.getAllTools().forEach(tool -> tools.add(tool.toJson()));

        ObjectNode result = objectMapper.createObjectNode();
        result.set("tools", tools);

        response.set("result", result);
        return response;
    }

    private ObjectNode callTool(JsonNode request, JsonNode id) {
        JsonNode params = request.get("params");
        String toolName = params.get("name").asText();
        JsonNode arguments = params.get("arguments");

        try {
            Object result = toolRegistry.executeTool(toolName, arguments);
            return createSuccessResponse(id, result);
        } catch (Exception e) {
            return createErrorResponse(id, -32603, "Tool execution failed: " + e.getMessage());
        }
    }

    private ObjectNode createSuccessResponse(JsonNode id, Object result) {
        ObjectNode response = objectMapper.createObjectNode();
        response.put("jsonrpc", "2.0");
        response.set("id", id);
        response.putPOJO("result", result);
        return response;
    }

    private ObjectNode createErrorResponse(JsonNode id, int code, String message) {
        ObjectNode response = objectMapper.createObjectNode();
        response.put("jsonrpc", "2.0");
        response.set("id", id);

        ObjectNode error = objectMapper.createObjectNode();
        error.put("code", code);
        error.put("message", message);
        response.set("error", error);

        return response;
    }
}
