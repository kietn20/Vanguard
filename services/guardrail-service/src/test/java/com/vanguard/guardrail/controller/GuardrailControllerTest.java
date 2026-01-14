package com.vanguard.guardrail.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import com.fasterxml.jackson.databind.ObjectMapper;

import com.vanguard.guardrail.controller.GuardrailController;
import com.vanguard.guardrail.dto.ActionRequest;
import com.vanguard.guardrail.dto.ValidationResult;
import com.vanguard.guardrail.service.AuditService;
import com.vanguard.guardrail.service.GuardrailValidator;

/**
 * Integration tests for GuardrailController.
 */
@WebMvcTest(GuardrailController.class)
class GuardrailControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private GuardrailValidator validator;

    @MockBean
    private AuditService auditService;

    @Test
    void validateAction_WhenApproved_Returns200() throws Exception {
        // Arrange
        ActionRequest request = new ActionRequest(
                "REMOVE",
                "BEARING_6205",
                10,
                "Used for repair",
                "event-123",
                "agent-001");

        ValidationResult result = ValidationResult.approved("Action approved");
        when(validator.validate(any())).thenReturn(result);

        // Act & Assert
        mockMvc.perform(post("/api/guardrail/validate")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.approved").value(true))
                .andExpect(jsonPath("$.decision").value("Action approved"));
    }

    @Test
    void validateAction_WhenRejected_Returns403() throws Exception {
        // Arrange
        ActionRequest request = new ActionRequest(
                "REMOVE",
                "BEARING_6205",
                100,
                "Too many",
                "event-456",
                "agent-001");

        ValidationResult result = ValidationResult.rejected(List.of("Quantity too high"));
        when(validator.validate(any())).thenReturn(result);

        // Act & Assert
        mockMvc.perform(post("/api/guardrail/validate")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.approved").value(false))
                .andExpect(jsonPath("$.violations[0]").value("Quantity too high"));
    }

    @Test
    void validateAction_WhenRequiresApproval_Returns202() throws Exception {
        // Arrange
        ActionRequest request = new ActionRequest(
                "REMOVE",
                "HYDRAULIC_PUMP_001",
                1,
                "Critical part removal",
                "event-789",
                "agent-001");

        ValidationResult result = ValidationResult.requiresApproval(
                "Critical part",
                List.of("High value component"));
        when(validator.validate(any())).thenReturn(result);

        // Act & Assert
        mockMvc.perform(post("/api/guardrail/validate")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isAccepted())
                .andExpect(jsonPath("$.requiresHumanApproval").value(true));
    }

    @Test
    void validateAction_WithInvalidRequest_Returns400() throws Exception {
        // Arrange - missing required fields
        String invalidJson = "{\"actionType\":\"REMOVE\"}";

        // Act & Assert
        mockMvc.perform(post("/api/guardrail/validate")
                .contentType(MediaType.APPLICATION_JSON)
                .content(invalidJson))
                .andExpect(status().isBadRequest());
    }

    @Test
    void health_ReturnsOk() throws Exception {
        mockMvc.perform(get("/api/guardrail/health"))
                .andExpect(status().isOk())
                .andExpect(content().string("Guardrail service is running"));
    }
}
