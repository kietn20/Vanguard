package com.vanguard.inventory.consumer;

import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Service;

import com.vanguard.inventory.exception.PartNotFoundException;
import com.vanguard.inventory.model.Part;
import com.vanguard.inventory.service.InventoryService;

/**
 * Kafka consumer that processes factory events and updates inventory.
 *
 * Listens to factory_events topic and responds to inventory-related events.
 */
@Service
public class InventoryEventConsumer {

    private static final Logger logger = LoggerFactory.getLogger(InventoryEventConsumer.class);

    private final InventoryService inventoryService;

    public InventoryEventConsumer(InventoryService inventoryService) {
        this.inventoryService = inventoryService;
    }

    /**
     * Process incoming factory events
     *
     * @param event     Factory event as a Map (flexible structure)
     * @param partition Kafka partition
     * @param offset    Message offset
     */
    @KafkaListener(topics = "${spring.kafka.topic}", groupId = "inventory-service-group")
    public void consumeFactoryEvent(
            @Payload Map<String, Object> event,
            @Header(KafkaHeaders.RECEIVED_PARTITION) int partition,
            @Header(KafkaHeaders.OFFSET) long offset) {
        try {
            String eventId = (String) event.get("event_id");
            String eventType = (String) event.get("event_type");
            String machineId = (String) event.get("machine_id");
            String severity = (String) event.get("severity");

            logger.info("========================================");
            logger.info("Received Factory Event:");
            logger.info("  Event ID: {}", eventId);
            logger.info("  Event Type: {}", eventType);
            logger.info("  Machine ID: {}", machineId);
            logger.info("  Severity: {}", severity);

            // process based on event type
            switch (eventType) {
                case "LOW_INVENTORY" -> handleLowInventoryEvent(event, eventId);
                case "PART_FAILED_QC" -> handlePartFailureEvent(event, eventId);
                case "SENSOR_OVERHEAT", "MACHINE_VIBRATION" -> handleMaintenanceEvent(event, eventId);
                case "MAINTENANCE_DUE" -> handleMaintenanceDueEvent(event, eventId);
                default -> logger.info("  No inventory action needed for event type: {}", eventType);
            }

            logger.info("========================================");

        } catch (Exception e) {
            logger.error("Error processing factory event: {}", e.getMessage(), e);
        }
    }





    /**
     * Handle LOW_INVENTORY events.
     * Checks current stock and logs recommendations.
     */
    private void handleLowInventoryEvent(Map<String, Object> event, String eventId) {
        @SuppressWarnings("unchecked")
        Map<String, Object> metadata = (Map<String, Object>) event.get("metadata");

        if (metadata != null) {
            String partName = (String) metadata.get("part_name");
            Integer currentStock = (Integer) metadata.get("current_stock");
            Integer minimumStock = (Integer) metadata.get("minimum_stock");
            Integer recommendedOrder = (Integer) metadata.get("recommended_order_quantity");

            logger.warn(" LOW INVENTORY DETECTED:");
            logger.warn("  Part: {}", partName);
            logger.warn("  Current Stock: {}", currentStock);
            logger.warn("  Minimum Stock: {}", minimumStock);
            logger.warn("  Recommended Order: {} units", recommendedOrder);





            // todo: trigger AI agent to create purchase order
            // todo: send notification
        }
    }

    /**
     * Handle PART_FAILED_QC events.
     * Removes defective part from inventory.
     */
    private void handlePartFailureEvent(Map<String, Object> event, String eventId) {
        logger.info(" Quality Control Failure - Part removed from inventory");

        @SuppressWarnings("unchecked")
        Map<String, Object> metadata = (Map<String, Object>) event.get("metadata");

        if (metadata != null) {
            String defectType = (String) metadata.get("defect_type");
            String batchId = (String) metadata.get("batch_id");

            logger.warn("  Defect Type: {}", defectType);
            logger.warn("  Batch ID: {}", batchId);




            // todo: remove defective parts from batch
            // todo: notify quality control team
        }
    }

    /**
     * Handle maintenance events (SENSOR_OVERHEAT, MACHINE_VIBRATION)
     * Checks if spare parts are available for potential repairs
     */
    private void handleMaintenanceEvent(Map<String, Object> event, String eventId) {
        String machineId = (String) event.get("machine_id");

        logger.info("Maintenance Event Detected for machine: {}", machineId);

        checkSparePartAvailability("HYDRAULIC_PUMP_001", machineId);
        checkSparePartAvailability("BEARING_6205", machineId);
        checkSparePartAvailability("SERVO_MOTOR_500W", machineId);

        // todo: AI agent determines which parts are needed
        // todo: auto-reserve parts for scheduled maintenance
    }

    /**
     * Handle MAINTENANCE_DUE events
     * Verifies parts are available for scheduled maintenance
     */
    private void handleMaintenanceDueEvent(Map<String, Object> event, String eventId) {
        @SuppressWarnings("unchecked")
        Map<String, Object> metadata = (Map<String, Object>) event.get("metadata");

        if (metadata != null) {
            Integer hoursUntilDue = (Integer) metadata.get("hours_until_due");
            String maintenanceType = (String) metadata.get("maintenance_type");

            logger.info("Scheduled Maintenance Due:");
            logger.info("  Type: {}", maintenanceType);
            logger.info("  Hours Until Due: {}", hoursUntilDue);

            // check if we have low stock parts
            var lowStockParts = inventoryService.getLowStockParts();
            if (!lowStockParts.isEmpty()) {
                logger.warn(" WARNING: {} parts are low on stock", lowStockParts.size());
                lowStockParts.forEach(part -> logger.warn("    - {}: {} units (min: {})", part.getPartNumber(), part.getQuantity(), part.getMinimumQuantity()));
            }
        }
    }

    //  check if a specific spare part is available
    private void checkSparePartAvailability(String partNumber, String machineId) {
        try {
            Part part = inventoryService.getPartByPartNumber(partNumber);

            if (part.isLowStock()) {
                logger.warn("  {} is LOW STOCK: {} units (min: {})", part.getName(), part.getQuantity(), part.getMinimumQuantity());
            } else if (part.isOutOfStock()) {
                logger.error(" {} is OUT OF STOCK!", part.getName());
            } else {
                logger.info(" {} available: {} units", part.getName(), part.getQuantity());
            }

        } catch (PartNotFoundException e) {
            logger.debug("  Part {} not tracked in inventory", partNumber);
        }
    }
}
