package com.vanguard.inventory.mcp.tools;

import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.vanguard.inventory.model.Part;
import com.vanguard.inventory.service.InventoryService;

/**
 * MCP Tool: Get part details by part number.
 */
@Component
public class GetPartByNumberTool implements MCPTool {

    private final InventoryService inventoryService;
    private final ObjectMapper objectMapper;

    public GetPartByNumberTool(InventoryService inventoryService, ObjectMapper objectMapper) {
        this.inventoryService = inventoryService;
        this.objectMapper = objectMapper;
    }

    @Override
    public String getName() {
        return "get_part_by_number";
    }

    @Override
    public String getDescription() {
        return "Retrieve detailed information about a specific spare part by its part number";
    }

    @Override
    public ObjectNode getInputSchema() {
        ObjectNode schema = objectMapper.createObjectNode();
        schema.put("type", "object");

        ObjectNode properties = objectMapper.createObjectNode();
        ObjectNode partNumberProp = objectMapper.createObjectNode();
        partNumberProp.put("type", "string");
        partNumberProp.put("description", "The unique part number (e.g., HYDRAULIC_PUMP_001)");
        properties.set("part_number", partNumberProp);

        schema.set("properties", properties);
        schema.putArray("required").add("part_number");

        return schema;
    }

    @Override
    public Object execute(JsonNode arguments) {
        String partNumber = arguments.get("part_number").asText();
        Part part = inventoryService.getPartByPartNumber(partNumber);

        // Convert to MCP response format
        ObjectNode response = objectMapper.createObjectNode();
        response.put("part_number", part.getPartNumber());
        response.put("name", part.getName());
        response.put("description", part.getDescription());
        response.put("category", part.getCategory());
        response.put("quantity", part.getQuantity());
        response.put("minimum_quantity", part.getMinimumQuantity());
        response.put("unit_price", part.getUnitPrice().doubleValue());
        response.put("location", part.getLocation());
        response.put("low_stock", part.isLowStock());
        response.put("out_of_stock", part.isOutOfStock());

        return response;
    }
}
