package com.vanguard.guardrail.service;

import java.util.concurrent.ConcurrentLinkedQueue;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import com.vanguard.guardrail.dto.ActionRequest;
import com.vanguard.guardrail.dto.ValidationResult;
import com.vanguard.guardrail.model.AuditLog;

/**
 * Audit logging service.
 *
 * Logs every guardrail decision for:
 * - Compliance audits
 * - Investigation of incidents
 * - AI agent behavior analysis
 * - Security monitoring
 */
@Service
public class AuditService {

    private static final Logger logger = LoggerFactory.getLogger(AuditService.class);

    private final ConcurrentLinkedQueue<AuditLog> auditLogs = new ConcurrentLinkedQueue<>();

    /**
     * Log a guardrail decision.
     *
     * @param request The action that was validated
     * @param result  The validation result
     */
    public void logDecision(ActionRequest request, ValidationResult result) {
        AuditLog log = new AuditLog(
                request.agentId(),
                request.actionType(),
                request.partNumber(),
                request.quantity(),
                request.reason(),
                request.eventId(),
                result.approved(),
                result.requiresHumanApproval(),
                result.violations(),
                result.warnings());

        auditLogs.add(log);

        // log to structured logging system
        if (result.approved()) {
            logger.info("AUDIT: Agent={} Action={} Part={} Qty={} Result=APPROVED",
                    request.agentId(), request.actionType(),
                    request.partNumber(), request.quantity());
        } else if (result.requiresHumanApproval()) {
            logger.warn("AUDIT: Agent={} Action={} Part={} Qty={} Result=REQUIRES_APPROVAL Reason={}",
                    request.agentId(), request.actionType(),
                    request.partNumber(), request.quantity(),
                    result.decision());
        } else {
            logger.error("AUDIT: Agent={} Action={} Part={} Qty={} Result=REJECTED Violations={}",
                    request.agentId(), request.actionType(),
                    request.partNumber(), request.quantity(),
                    result.violations());
        }

    }

    /**
     * Get recent audit logs.
     *
     * @param limit Maximum number of logs to return
     * @return Recent audit logs
     */
    public java.util.List<AuditLog> getRecentLogs(int limit) {
        return auditLogs.stream()
                .skip(Math.max(0, auditLogs.size() - limit))
                .toList();
    }

    /**
     * Get audit statistics.
     */
    public AuditStats getStats() {
        long total = auditLogs.size();
        long approved = auditLogs.stream().filter(AuditLog::approved).count();
        long requiresApproval = auditLogs.stream().filter(AuditLog::requiresHumanApproval).count();
        long rejected = total - approved - requiresApproval;

        return new AuditStats(total, approved, rejected, requiresApproval);
    }

    public record AuditStats(
            long total,
            long approved,
            long rejected,
            long requiresApproval) {
    }
}
