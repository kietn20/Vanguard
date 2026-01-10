package com.vanguard.guardrail.rules;

import java.math.BigDecimal;
import java.util.Map;

/**
 * Business rules and constraints for the factory.
 *
 * These are HARD LIMITS that cannot be violated.
 * Even if an AI agent requests it, these rules enforce safety.
 */
public class BusinessRules {

    
    // ===== INVENTORY RULES =====

    /**
     * Maximum quantity that can be removed in a single operation.
     * Prevents agent from removing entire inventory by mistake.
     */
    public static final int MAX_REMOVAL_QUANTITY = 50;

    /**
     * Maximum quantity that can be added in a single operation.
     * Prevents data entry errors or hallucinations.
     */
    public static final int MAX_ADDITION_QUANTITY = 100;

    /**
     * Minimum stock level below which removal requires approval.
     * Protects against running out of critical parts.
     */
    public static final int CRITICAL_STOCK_THRESHOLD = 5;

    /**
     * Maximum cost per transaction.
     * Actions exceeding this require human approval.
     */
    public static final BigDecimal MAX_TRANSACTION_COST = new BigDecimal("5000.00");





    // ===== PART-SPECIFIC RULES =====

    /**
     * Critical parts that always require approval for removal.
     * These are high-value or safety-critical components.
     */
    public static final Map<String, String> CRITICAL_PARTS = Map.of(
            "SERVO_MOTOR_500W", "High-value component",
            "HYDRAULIC_PUMP_001", "Safety-critical component",
            "PRESSURE_SENSOR_PSI", "Safety monitoring equipment");





    // ===== RATE LIMITING =====

    /**
     * Maximum operations per minute per agent.
     * Prevents runaway AI from making too many changes.
     */
    public static final int MAX_OPERATIONS_PER_MINUTE = 10;

    /**
     * Maximum operations per hour across all agents.
     * System-wide circuit breaker.
     */
    public static final int MAX_OPERATIONS_PER_HOUR = 100;




    // ===== OPERATIONAL CONSTRAINTS =====

    /**
     * Parts that cannot be removed during production hours.
     */
    public static final String[] PRODUCTION_LOCKED_PARTS = {
            "CONVEYOR_BELT_10M",
            "PNEUMATIC_VALVE_24V"
    };

    /**
     * Minimum reason length for removal operations.
     * Ensures proper documentation.
     */
    public static final int MIN_REASON_LENGTH = 10;
}
