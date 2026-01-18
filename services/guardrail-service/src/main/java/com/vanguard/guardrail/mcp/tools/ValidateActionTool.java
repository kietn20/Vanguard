package com.vanguard.guardrail.mcp.tools;

import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.vanguard.guardrail.dto.ActionRequest;
import com.vanguard.guardrail.dto.ValidationResult;
import com.vanguard.guardrail.service.GuardrailValidator;

/**
 * MCP Tool: Validate an action against guardrail rules.
 */
@Component
public class ValidateActionTool implements MCPTool {

    private final GuardrailValidator validator;
    private final ObjectMapper objectMapper;

    public ValidateActionTool(GuardrailValidator validator, ObjectMapper objectMapper) {
        this.validator = validator;
        this.objectMapper = objectMapper;
    }

    @Override
    public String getName() {
        return "validate_action";
    }

    @Override
    public String getDescription() {
        return "Validate an inventory action against safety guardrails before execution";
    }

    @Override
    public ObjectNode getInputSchema() {
        ObjectNode schema = objectMapper.createObjectNode();
        schema.put("type", "object");

        ObjectNode properties = objectMapper.createObjectNode();

        ObjectNode actionTypeProp = objectMapper.createObjectNode();
        actionTypeProp.put("type", "string");
        actionTypeProp.put("description", "Action type (ADD or REMOVE)");
        actionTypeProp.putArray("enum").add("ADD").add("REMOVE");
        properties.set("action_type", actionTypeProp);

        ObjectNode partNumberProp = objectMapper.createObjectNode();
        partNumberProp.put("type", "string");
        partNumberProp.put("description", "Part number");
        properties.set("part_number", partNumberProp);

        ObjectNode quantityProp = objectMapper.createObjectNode();
        quantityProp.put("type", "integer");
        quantityProp.put("description", "Quantity");
        quantityProp.put("minimum", 1);
        properties.set("quantity", quantityProp);

        ObjectNode reasonProp = objectMapper.createObjectNode();
        reasonProp.put("type", "string");
        reasonProp.put("description", "Reason for action");
        reasonProp.put("minLength", 10);
        properties.set("reason", reasonProp);

        ObjectNode eventIdProp = objectMapper.createObjectNode();
        eventIdProp.put("type", "string");
        eventIdProp.put("description", "Optional event ID");
        properties.set("event_id", eventIdProp);

        ObjectNode agentIdProp = objectMapper.createObjectNode();
        agentIdProp.put("type", "string");
        agentIdProp.put("description", "Agent requesting the action");
        properties.set("agent_id", agentIdProp);

        schema.set("properties", properties);
        schema.putArray("required")
                .add("action_type")
                .add("part_number")
                .add("quantity")
                .add("reason");

        return schema;
    }

    @Override
    public Object execute(JsonNode arguments) {
        ActionRequest request = new ActionRequest(
                arguments.get("action_type").asText(),
                arguments.get("part_number").asText(),
                arguments.get("quantity").asInt(),
                arguments.get("reason").asText(),
                arguments.has("event_id") ? arguments.get("event_id").asText() : null,
                arguments.has("agent_id") ? arguments.get("agent_id").asText() : "mcp-agent");

        ValidationResult result = validator.validate(request);

        ObjectNode response = objectMapper.createObjectNode();
        response.put("approved", result.approved());
        response.put("decision", result.decision());
        response.put("requires_human_approval", result.requiresHumanApproval());

        ArrayNode violations = objectMapper.createArrayNode();
        result.violations().forEach(violations::add);
        response.set("violations", violations);

        ArrayNode warnings = objectMapper.createArrayNode();
        result.warnings().forEach(warnings::add);
        response.set("warnings", warnings);

        return response;
    }
}
