package com.vanguard.inventory.mcp;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

/**
 * MCP Server endpoint that exposes inventory tools.
 *
 * Implements Model Context Protocol (MCP) specification for tool discovery and
 * execution.
 * MCP uses JSON-RPC 2.0 for message exchange.
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

    /**
     * Handle MCP JSON-RPC requests.
     *
     * MCP clients send requests like:
     * {
     * "jsonrpc": "2.0",
     * "method": "tools/list",
     * "id": 1
     * }
     */
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

    /**
     * Initialize MCP session.
     * Returns server capabilities.
     */
    private ObjectNode initialize(JsonNode id) {
        ObjectNode response = objectMapper.createObjectNode();
        response.put("jsonrpc", "2.0");
        response.set("id", id);

        ObjectNode result = objectMapper.createObjectNode();
        result.put("protocolVersion", "2024-11-05");
        result.put("serverInfo", createServerInfo());

        ObjectNode capabilities = objectMapper.createObjectNode();
        capabilities.put("tools", true);
        result.set("capabilities", capabilities);

        response.set("result", result);
        return response;
    }

    /**
     * List available tools.
     * Returns tool definitions with JSON schemas.
     */
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

    /**
     * Execute a tool.
     */
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

    private ObjectNode createServerInfo() {
        ObjectNode serverInfo = objectMapper.createObjectNode();
        serverInfo.put("name", "vanguard-inventory");
        serverInfo.put("version", "0.1.0");
        return serverInfo;
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
