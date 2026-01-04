package com.vanguard.maintenance.consumer;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Service;

import com.vanguard.maintenance.model.FactoryEvent;

@Service
public class FactoryEventConsumer {
    private static final Logger logger = LoggerFactory.getLogger(FactoryEventConsumer.class);

    /**
     * Listen to factory_events topic and process incoming events.
     *
     * Spring automatically:
     * 1. Subscribes to the topic
     * 2. Deserializes JSON to FactoryEvent
     * 3. Calls this method for each message
     * 4. Handles errors and retries
     *
     * @param event     The deserialized factory event
     * @param partition Kafka partition number
     * @param offset    Message offset within partition
     */
    @KafkaListener(topics = "${spring.kafka.topic}", groupId = "${spring.kafka.consumer.group-id}")
    public void consumeEvent(
            @Payload FactoryEvent event,
            @Header(KafkaHeaders.RECEIVED_PARTITION) int partition,
            @Header(KafkaHeaders.OFFSET) long offset) {
        try {
            logger.info("========================================");
            logger.info("Received Event from Kafka:");
            logger.info("  Partition: {}, Offset: {}", partition, offset);
            logger.info("  Event ID: {}", event.eventId());
            logger.info("  Event Type: {}", event.eventType());
            logger.info("  Machine ID: {}", event.machineId());
            logger.info("  Severity: {}", event.severity());
            logger.info("  Timestamp: {}", event.timestamp());
            logger.info("  Description: {}", event.description());

            if (event.metadata() != null && !event.metadata().isEmpty()) {
                logger.info("  Metadata:");
                event.metadata().forEach((key, value) -> logger.info("    {}: {}", key, value));
            }

            if (event.isCritical()) {
                logger.warn("CRITICAL EVENT DETECTED - Requires immediate attention!");
            }

            logger.info("========================================");






        } catch (Exception e) {
            logger.error("Error processing event {}: {}", event.eventId(), e.getMessage(), e);
        }
    }

}
