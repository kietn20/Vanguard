package com.vanguard.inventory.mcp.tools;

import java.util.List;

import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.vanguard.inventory.model.Part;
import com.vanguard.inventory.repository.PartRepository;

/**
 * MCP Tool: Get all parts in inventory.
 */
@Component
public class GetAllPartsTool implements MCPTool {

    private final PartRepository partRepository;
    private final ObjectMapper objectMapper;

    public GetAllPartsTool(PartRepository partRepository, ObjectMapper objectMapper) {
        this.partRepository = partRepository;
        this.objectMapper = objectMapper;
    }

    @Override
    public String getName() {
        return "get_all_parts";
    }

    @Override
    public String getDescription() {
        return "Get a list of all parts in the inventory system";
    }

    @Override
    public ObjectNode getInputSchema() {
        ObjectNode schema = objectMapper.createObjectNode();
        schema.put("type", "object");
        schema.set("properties", objectMapper.createObjectNode());
        return schema;
    }

    @Override
    public Object execute(JsonNode arguments) {
        List<Part> parts = partRepository.findAll();

        ArrayNode partsArray = objectMapper.createArrayNode();
        parts.forEach(part -> {
            ObjectNode partNode = objectMapper.createObjectNode();
            partNode.put("part_number", part.getPartNumber());
            partNode.put("name", part.getName());
            partNode.put("category", part.getCategory());
            partNode.put("quantity", part.getQuantity());
            partNode.put("minimum_quantity", part.getMinimumQuantity());
            partNode.put("unit_price", part.getUnitPrice().doubleValue());
            partNode.put("low_stock", part.isLowStock());
            partNode.put("out_of_stock", part.isOutOfStock());
            partsArray.add(partNode);
        });

        ObjectNode response = objectMapper.createObjectNode();
        response.set("parts", partsArray);
        response.put("total_count", parts.size());

        return response;
    }
}
