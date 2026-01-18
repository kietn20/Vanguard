package com.vanguard.inventory.mcp.tools;

import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.vanguard.inventory.model.InventoryTransaction;
import com.vanguard.inventory.service.InventoryService;

/**
 * MCP Tool: Remove stock from inventory.
 */
@Component
public class RemoveStockTool implements MCPTool {

    private final InventoryService inventoryService;
    private final ObjectMapper objectMapper;

    public RemoveStockTool(InventoryService inventoryService, ObjectMapper objectMapper) {
        this.inventoryService = inventoryService;
        this.objectMapper = objectMapper;
    }

    @Override
    public String getName() {
        return "remove_stock";
    }

    @Override
    public String getDescription() {
        return "Remove stock from inventory (e.g., for repairs, consumption, or reservations)";
    }

    @Override
    public ObjectNode getInputSchema() {
        ObjectNode schema = objectMapper.createObjectNode();
        schema.put("type", "object");

        ObjectNode properties = objectMapper.createObjectNode();

        ObjectNode partNumberProp = objectMapper.createObjectNode();
        partNumberProp.put("type", "string");
        partNumberProp.put("description", "Part number to remove stock from");
        properties.set("part_number", partNumberProp);

        ObjectNode quantityProp = objectMapper.createObjectNode();
        quantityProp.put("type", "integer");
        quantityProp.put("description", "Quantity to remove");
        quantityProp.put("minimum", 1);
        properties.set("quantity", quantityProp);

        ObjectNode reasonProp = objectMapper.createObjectNode();
        reasonProp.put("type", "string");
        reasonProp.put("description", "Reason for removing stock");
        reasonProp.put("minLength", 10);
        properties.set("reason", reasonProp);

        ObjectNode eventIdProp = objectMapper.createObjectNode();
        eventIdProp.put("type", "string");
        eventIdProp.put("description", "Optional factory event ID for traceability");
        properties.set("event_id", eventIdProp);

        schema.set("properties", properties);
        schema.putArray("required").add("part_number").add("quantity").add("reason");

        return schema;
    }

    @Override
    public Object execute(JsonNode arguments) {
        String partNumber = arguments.get("part_number").asText();
        int quantity = arguments.get("quantity").asInt();
        String reason = arguments.get("reason").asText();
        String eventId = arguments.has("event_id") ? arguments.get("event_id").asText() : null;

        InventoryTransaction transaction = inventoryService.removeStock(
                partNumber, quantity, reason, eventId);

        ObjectNode response = objectMapper.createObjectNode();
        response.put("transaction_id", transaction.getId());
        response.put("part_number", transaction.getPart().getPartNumber());
        response.put("quantity_change", transaction.getQuantityChange());
        response.put("quantity_before", transaction.getQuantityBefore());
        response.put("quantity_after", transaction.getQuantityAfter());
        response.put("success", true);

        return response;
    }
}
