package com.vanguard.guardrail.service;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import com.vanguard.guardrail.dto.ActionRequest;
import com.vanguard.guardrail.dto.ValidationResult;
import com.vanguard.guardrail.rules.BusinessRules;
import com.vanguard.guardrail.service.GuardrailValidator;

/**
 * Tests for GuardrailValidator.
 */
class GuardrailValidatorTest {

    private GuardrailValidator validator;

    @BeforeEach
    void setUp() {
        validator = new GuardrailValidator();
    }

    // ===== SUCCESSFUL VALIDATIONS =====

    @Test
    void validate_NormalRemoval_Approves() {
        // Arrange
        ActionRequest request = new ActionRequest(
                "REMOVE",
                "BEARING_6205",
                10,
                "Used for machine repair on PRESS-001",
                "event-123",
                "inventory-agent");

        // Act
        ValidationResult result = validator.validate(request);

        // Assert
        assertThat(result.approved()).isTrue();
        assertThat(result.violations()).isEmpty();
        assertThat(result.requiresHumanApproval()).isFalse();
    }

    @Test
    void validate_NormalAddition_Approves() {
        // Arrange
        ActionRequest request = new ActionRequest(
                "ADD",
                "WELDING_TIP_T15",
                50,
                "Received shipment from supplier ABC-123",
                null,
                "inventory-agent");

        // Act
        ValidationResult result = validator.validate(request);

        // Assert
        assertThat(result.approved()).isTrue();
    }

    // ===== QUANTITY LIMIT VIOLATIONS =====

    @Test
    void validate_ExcessiveRemoval_Rejects() {
        // Arrange - trying to remove more than MAX_REMOVAL_QUANTITY
        ActionRequest request = new ActionRequest(
                "REMOVE",
                "BEARING_6205",
                100, // Exceeds limit of 50
                "Large repair operation",
                "event-456",
                "inventory-agent");

        // Act
        ValidationResult result = validator.validate(request);

        // Assert
        assertThat(result.approved()).isFalse();
        assertThat(result.violations()).isNotEmpty();
        assertThat(result.violations().get(0)).contains("exceeds maximum allowed");
    }

    @Test
    void validate_ExcessiveAddition_Rejects() {
        // Arrange - trying to add more than MAX_ADDITION_QUANTITY
        ActionRequest request = new ActionRequest(
                "ADD",
                "BEARING_6205",
                150, // Exceeds limit of 100
                "Received large shipment",
                null,
                "inventory-agent");

        // Act
        ValidationResult result = validator.validate(request);

        // Assert
        assertThat(result.approved()).isFalse();
        assertThat(result.violations()).isNotEmpty();
        assertThat(result.violations().get(0)).contains("exceeds maximum allowed");
    }

    // ===== CRITICAL PARTS =====

    @Test
    void validate_CriticalPartRemoval_RequiresApproval() {
        // Arrange - removing a critical part
        ActionRequest request = new ActionRequest(
                "REMOVE",
                "HYDRAULIC_PUMP_001",
                1,
                "Replacing failed hydraulic pump on PRESS-001",
                "event-789",
                "inventory-agent");

        // Act
        ValidationResult result = validator.validate(request);

        // Assert
        assertThat(result.approved()).isFalse();
        assertThat(result.requiresHumanApproval()).isTrue();
        assertThat(result.decision()).contains("human approval");
        assertThat(result.warnings()).isNotEmpty();
    }

    @Test
    void validate_CriticalPartAddition_ApprovesWithWarning() {
        // Arrange - adding a critical part (should approve but warn)
        ActionRequest request = new ActionRequest(
                "ADD",
                "SERVO_MOTOR_500W",
                5,
                "Received critical component from supplier",
                null,
                "inventory-agent");

        // Act
        ValidationResult result = validator.validate(request);

        // Assert
        assertThat(result.approved()).isTrue();
        assertThat(result.warnings()).isNotEmpty();
        assertThat(result.warnings().get(0)).contains("critical");
    }

    // ===== REASON VALIDATION =====

    @Test
    void validate_ShortReason_Rejects() {
        // Arrange - reason too short
        ActionRequest request = new ActionRequest(
                "REMOVE",
                "BEARING_6205",
                5,
                "Fix", // Too short (< 10 characters)
                "event-999",
                "inventory-agent");

        // Act
        ValidationResult result = validator.validate(request);

        // Assert
        assertThat(result.approved()).isFalse();
        assertThat(result.violations()).isNotEmpty();
        assertThat(result.violations().get(0)).contains("at least");
    }

    @Test
    void validate_NullReason_Rejects() {
        // Arrange - null reason
        ActionRequest request = new ActionRequest(
                "REMOVE",
                "BEARING_6205",
                5,
                null,
                "event-999",
                "inventory-agent");

        // Act
        ValidationResult result = validator.validate(request);

        // Assert
        assertThat(result.approved()).isFalse();
        assertThat(result.violations()).isNotEmpty();
    }

    // ===== SUSPICIOUS PATTERNS =====

    @Test
    void validate_TestReason_ApprovesWithWarning() {
        // Arrange - reason contains "test"
        ActionRequest request = new ActionRequest(
                "REMOVE",
                "BEARING_6205",
                5,
                "Testing removal process for documentation",
                "event-test-001",
                "inventory-agent");

        // Act
        ValidationResult result = validator.validate(request);

        // Assert
        assertThat(result.approved()).isTrue();
        assertThat(result.warnings()).isNotEmpty();
        assertThat(result.warnings().get(0).toLowerCase()).contains("test");
    }

    // ===== BOUNDARY TESTS =====

    @Test
    void validate_ExactlyAtRemovalLimit_Approves() {
        // Arrange - exactly at the limit
        ActionRequest request = new ActionRequest(
                "REMOVE",
                "BEARING_6205",
                BusinessRules.MAX_REMOVAL_QUANTITY, // Exactly 50
                "Large but legitimate repair operation",
                "event-limit",
                "inventory-agent");

        // Act
        ValidationResult result = validator.validate(request);

        // Assert
        assertThat(result.approved()).isTrue();
    }

    @Test
    void validate_OneOverRemovalLimit_Rejects() {
        // Arrange - one over the limit
        ActionRequest request = new ActionRequest(
                "REMOVE",
                "BEARING_6205",
                BusinessRules.MAX_REMOVAL_QUANTITY + 1, // 51
                "Large repair operation",
                "event-over",
                "inventory-agent");

        // Act
        ValidationResult result = validator.validate(request);

        // Assert
        assertThat(result.approved()).isFalse();
    }
}
