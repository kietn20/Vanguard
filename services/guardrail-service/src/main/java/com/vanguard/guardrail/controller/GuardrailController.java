package com.vanguard.guardrail.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import com.vanguard.guardrail.dto.ActionRequest;
import com.vanguard.guardrail.dto.ValidationResult;
import com.vanguard.guardrail.service.GuardrailValidator;

/**
 * REST API for guardrail validation.
 *
 * AI agents call this endpoint BEFORE executing actions.
 */
@RestController
@RequestMapping("/api/guardrail")
public class GuardrailController {

    private static final Logger logger = LoggerFactory.getLogger(GuardrailController.class);

    private final GuardrailValidator validator;

    public GuardrailController(GuardrailValidator validator) {
        this.validator = validator;
    }



    /**
     * Validate an action request.
     *
     * POST /api/guardrail/validate
     *
     * @param request Action to validate
     * @return Validation result
     */
    @PostMapping("/validate")
    public ResponseEntity<ValidationResult> validateAction(@Valid @RequestBody ActionRequest request) {
        logger.info("Received validation request from agent: {}", request.agentId());

        ValidationResult result = validator.validate(request);

        if (result.approved()) {
            return ResponseEntity.ok(result);
        } else if (result.requiresHumanApproval()) {
            return ResponseEntity.status(202).body(result); // 202 Accepted (pending approval)
        } else {
            return ResponseEntity.status(403).body(result); // 403 Forbidden
        }
    }



    /**
     * Health check endpoint.
     */
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("Guardrail service is running");
    }
}
