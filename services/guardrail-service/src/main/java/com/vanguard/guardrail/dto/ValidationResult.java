package com.vanguard.guardrail.dto;

import java.time.Instant;
import java.util.List;


// result of guardrail validation
public record ValidationResult(
        boolean approved,
        String decision,
        List<String> violations,
        List<String> warnings,
        boolean requiresHumanApproval,
        String validatedBy,
        Instant timestamp)
{
    public static ValidationResult approved(String decision) {
        return approved(decision, List.of());
    }

    public static ValidationResult approved(String decision, List<String> warnings) {
        return new ValidationResult(
                true,
                decision,
                List.of(),
                warnings,
                false,
                "GUARDRAIL_SERVICE",
                Instant.now());
    }

    public static ValidationResult rejected(List<String> violations) {
        return new ValidationResult(
                false,
                "Action rejected due to policy violations",
                violations,
                List.of(),
                false,
                "GUARDRAIL_SERVICE",
                Instant.now());
    }

    public static ValidationResult requiresApproval(String reason, List<String> warnings) {
        return new ValidationResult(
                false,
                "Human approval required: " + reason,
                List.of(),
                warnings,
                true,
                "GUARDRAIL_SERVICE",
                Instant.now());
    }
}
