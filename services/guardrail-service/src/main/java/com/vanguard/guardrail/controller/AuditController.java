package com.vanguard.guardrail.controller;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.vanguard.guardrail.model.AuditLog;
import com.vanguard.guardrail.service.AuditService;

/**
 * REST API for audit logs.
 *
 * Allows querying audit trail for compliance and investigation.
 */
@RestController
@RequestMapping("/api/guardrail/audit")
public class AuditController {

    private final AuditService auditService;

    public AuditController(AuditService auditService) {
        this.auditService = auditService;
    }

    /**
     * Get recent audit logs.
     *
     * GET /api/guardrail/audit/logs?limit=50
     */
    @GetMapping("/logs")
    public ResponseEntity<List<AuditLog>> getAuditLogs(
            @RequestParam(defaultValue = "50") int limit) {
        return ResponseEntity.ok(auditService.getRecentLogs(limit));
    }

    /**
     * Get audit statistics.
     *
     * GET /api/guardrail/audit/stats
     */
    @GetMapping("/stats")
    public ResponseEntity<AuditService.AuditStats> getStats() {
        return ResponseEntity.ok(auditService.getStats());
    }
}
