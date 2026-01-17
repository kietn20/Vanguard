package com.vanguard.inventory.mcp.tools;

import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.vanguard.inventory.service.InventoryService;

/**
 * MCP Tool: Check if sufficient quantity of a part is available.
 */
@Component
public class CheckAvailabilityTool implements MCPTool {

    private final InventoryService inventoryService;
    private final ObjectMapper objectMapper;

    public CheckAvailabilityTool(InventoryService inventoryService, ObjectMapper objectMapper) {
        this.inventoryService = inventoryService;
        this.objectMapper = objectMapper;
    }

    @Override
    public String getName() {
        return "check_availability";
    }

    @Override
    public String getDescription() {
        return "Check if sufficient quantity of a part is available in inventory";
    }

    @Override
    public ObjectNode getInputSchema() {
        ObjectNode schema = objectMapper.createObjectNode();
        schema.put("type", "object");

        ObjectNode properties = objectMapper.createObjectNode();

        ObjectNode partNumberProp = objectMapper.createObjectNode();
        partNumberProp.put("type", "string");
        partNumberProp.put("description", "The part number to check");
        properties.set("part_number", partNumberProp);

        ObjectNode quantityProp = objectMapper.createObjectNode();
        quantityProp.put("type", "integer");
        quantityProp.put("description", "Required quantity");
        quantityProp.put("minimum", 1);
        properties.set("quantity", quantityProp);

        schema.set("properties", properties);
        schema.putArray("required").add("part_number").add("quantity");

        return schema;
    }

    @Override
    public Object execute(JsonNode arguments) {
        String partNumber = arguments.get("part_number").asText();
        int quantity = arguments.get("quantity").asInt();

        boolean available = inventoryService.checkAvailability(partNumber, quantity);

        ObjectNode response = objectMapper.createObjectNode();
        response.put("available", available);
        response.put("part_number", partNumber);
        response.put("requested_quantity", quantity);

        return response;
    }
}
