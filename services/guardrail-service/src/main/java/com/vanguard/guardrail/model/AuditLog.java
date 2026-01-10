package com.vanguard.guardrail.model;

import java.time.Instant;
import java.util.List;

/**
 * Audit log entry for guardrail decisions.
 *
 * Every validation is logged for compliance and review.
 */
public record AuditLog(
        String auditId,
        String agentId,
        String actionType,
        String partNumber,
        Integer quantity,
        String reason,
        String eventId,
        boolean approved,
        boolean requiresHumanApproval,
        List<String> violations,
        List<String> warnings,
        String validatedBy,
        Instant timestamp,
        String ipAddress) {
    public AuditLog(
            String agentId,
            String actionType,
            String partNumber,
            Integer quantity,
            String reason,
            String eventId,
            boolean approved,
            boolean requiresHumanApproval,
            List<String> violations,
            List<String> warnings) {
        this(
                java.util.UUID.randomUUID().toString(),
                agentId,
                actionType,
                partNumber,
                quantity,
                reason,
                eventId,
                approved,
                requiresHumanApproval,
                violations,
                warnings,
                "GUARDRAIL_SERVICE",
                Instant.now(),
                "internal");
    }
}
