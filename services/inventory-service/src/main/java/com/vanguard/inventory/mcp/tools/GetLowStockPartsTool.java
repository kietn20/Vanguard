package com.vanguard.inventory.mcp.tools;

import java.util.List;

import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.vanguard.inventory.model.Part;
import com.vanguard.inventory.service.InventoryService;

/**
 * MCP Tool: Get all parts with stock below minimum quantity.
 */
@Component
public class GetLowStockPartsTool implements MCPTool {

    private final InventoryService inventoryService;
    private final ObjectMapper objectMapper;

    public GetLowStockPartsTool(InventoryService inventoryService, ObjectMapper objectMapper) {
        this.inventoryService = inventoryService;
        this.objectMapper = objectMapper;
    }

    @Override
    public String getName() {
        return "get_low_stock_parts";
    }

    @Override
    public String getDescription() {
        return "Get all parts where current quantity is below minimum threshold";
    }

    @Override
    public ObjectNode getInputSchema() {
        ObjectNode schema = objectMapper.createObjectNode();
        schema.put("type", "object");
        schema.set("properties", objectMapper.createObjectNode()); // No parameters needed
        return schema;
    }

    @Override
    public Object execute(JsonNode arguments) {
        List<Part> lowStockParts = inventoryService.getLowStockParts();

        ArrayNode partsArray = objectMapper.createArrayNode();
        lowStockParts.forEach(part -> {
            ObjectNode partNode = objectMapper.createObjectNode();
            partNode.put("part_number", part.getPartNumber());
            partNode.put("name", part.getName());
            partNode.put("quantity", part.getQuantity());
            partNode.put("minimum_quantity", part.getMinimumQuantity());
            partNode.put("recommended_reorder", part.getReorderQuantity());
            partsArray.add(partNode);
        });

        ObjectNode response = objectMapper.createObjectNode();
        response.set("low_stock_parts", partsArray);
        response.put("count", lowStockParts.size());

        return response;
    }
}
