package com.vanguard.guardrail.service;

import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import com.vanguard.guardrail.dto.ActionRequest;
import com.vanguard.guardrail.dto.ValidationResult;
import com.vanguard.guardrail.rules.BusinessRules;

/**
 * Validates agent actions against business rules.
 *
 * This is the "safety net" that prevents AI agents from:
 * - Removing too much inventory
 * - Making expensive decisions without approval
 * - Violating business constraints
 * - Acting too quickly (rate limiting)
 */
@Service
public class GuardrailValidator {

    private static final Logger logger = LoggerFactory.getLogger(GuardrailValidator.class);

    /**
     * Validate an action request from an AI agent.
     *
     * @param request The action to validate
     * @return Validation result with approval/rejection
     */
    public ValidationResult validate(ActionRequest request) {
        logger.info("Validating action: {} on {} (quantity: {})", request.actionType(), request.partNumber(), request.quantity());

        List<String> violations = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        // rule 1: Check quantity limits
        if ("REMOVE".equals(request.actionType())) {
            if (request.quantity() > BusinessRules.MAX_REMOVAL_QUANTITY) {
                violations.add(String.format(
                        "Removal quantity %d exceeds maximum allowed %d",
                        request.quantity(), BusinessRules.MAX_REMOVAL_QUANTITY));
            }
        } else if ("ADD".equals(request.actionType())) {
            if (request.quantity() > BusinessRules.MAX_ADDITION_QUANTITY) {
                violations.add(String.format(
                        "Addition quantity %d exceeds maximum allowed %d",
                        request.quantity(), BusinessRules.MAX_ADDITION_QUANTITY));
            }
        }

        // rule 2: Check if part is critical
        if (BusinessRules.CRITICAL_PARTS.containsKey(request.partNumber())) {
            String reason = BusinessRules.CRITICAL_PARTS.get(request.partNumber());
            warnings.add(String.format("Part %s is critical: %s", request.partNumber(), reason));

            // critical parts require approval for removal
            if ("REMOVE".equals(request.actionType())) {
                return ValidationResult.requiresApproval("Critical part removal requires human approval", warnings);
            }
        }

        // rule 3: Check reason documentation
        if (request.reason() == null || request.reason().length() < BusinessRules.MIN_REASON_LENGTH) {
            violations.add(String.format("Reason must be at least %d characters for audit trail", BusinessRules.MIN_REASON_LENGTH));
        }

        // rule 4: Check for suspicious patterns
        if (request.reason() != null && request.reason().toLowerCase().contains("test")) {
            warnings.add("Action reason contains 'test' - verify this is intentional");
        }

        // if there are violations, reject
        if (!violations.isEmpty()) {
            logger.warn("Action rejected: {} violation(s)", violations.size());
            violations.forEach(v -> logger.warn("  - {}", v));
            return ValidationResult.rejected(violations);
        }

        // if there are warnings but no violations, approve with warnings
        if (!warnings.isEmpty()) {
            logger.info("Action approved with {} warning(s)", warnings.size());
            warnings.forEach(w -> logger.warn("  ⚠️  {}", w));
        } else {
            logger.info("✅ Action approved - all rules passed");
        }

        return ValidationResult.approved(
                String.format("Action %s on %s approved by guardrails", request.actionType(), request.partNumber()),
                warnings);
    }
}
