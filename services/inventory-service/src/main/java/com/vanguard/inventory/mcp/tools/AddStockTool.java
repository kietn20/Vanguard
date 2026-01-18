package com.vanguard.inventory.mcp.tools;

import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.vanguard.inventory.model.InventoryTransaction;
import com.vanguard.inventory.service.InventoryService;

/**
 * MCP Tool: Add stock to inventory.
 */
@Component
public class AddStockTool implements MCPTool {

    private final InventoryService inventoryService;
    private final ObjectMapper objectMapper;

    public AddStockTool(InventoryService inventoryService, ObjectMapper objectMapper) {
        this.inventoryService = inventoryService;
        this.objectMapper = objectMapper;
    }

    @Override
    public String getName() {
        return "add_stock";
    }

    @Override
    public String getDescription() {
        return "Add stock to inventory (e.g., receiving shipments, returns)";
    }

    @Override
    public ObjectNode getInputSchema() {
        ObjectNode schema = objectMapper.createObjectNode();
        schema.put("type", "object");

        ObjectNode properties = objectMapper.createObjectNode();

        ObjectNode partNumberProp = objectMapper.createObjectNode();
        partNumberProp.put("type", "string");
        partNumberProp.put("description", "Part number to add stock to");
        properties.set("part_number", partNumberProp);

        ObjectNode quantityProp = objectMapper.createObjectNode();
        quantityProp.put("type", "integer");
        quantityProp.put("description", "Quantity to add");
        quantityProp.put("minimum", 1);
        properties.set("quantity", quantityProp);

        ObjectNode reasonProp = objectMapper.createObjectNode();
        reasonProp.put("type", "string");
        reasonProp.put("description", "Reason for adding stock");
        reasonProp.put("minLength", 10);
        properties.set("reason", reasonProp);

        schema.set("properties", properties);
        schema.putArray("required").add("part_number").add("quantity").add("reason");

        return schema;
    }

    @Override
    public Object execute(JsonNode arguments) {
        String partNumber = arguments.get("part_number").asText();
        int quantity = arguments.get("quantity").asInt();
        String reason = arguments.get("reason").asText();

        InventoryTransaction transaction = inventoryService.addStock(
                partNumber, quantity, reason);

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
