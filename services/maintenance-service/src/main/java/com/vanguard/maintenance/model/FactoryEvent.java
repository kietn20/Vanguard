package com.vanguard.maintenance.model;

import java.util.Map;

import com.fasterxml.jackson.annotation.JsonProperty;

public record FactoryEvent(
    @JsonProperty("event_id")
    String eventId,

    @JsonProperty("event_type")
    String eventType,

    @JsonProperty("machine_id")
    String machineId,

    @JsonProperty("timestamp")
    String timestamp,

    @JsonProperty("severity")
    String severity,

    @JsonProperty("description")
    String description,

    @JsonProperty("metadata")
    Map<String, Object> metadata
) {
    public FactoryEvent {
        if (eventId == null || eventId.isBlank()) {
            throw new IllegalArgumentException("Event ID cannot be null or blank");
        }

        if (eventType == null || eventType.isBlank()) {
            throw new IllegalArgumentException("Event type cannot be null or blank");
        }
    }

    public boolean isCritical() {
        return "CRITICAL".equals(severity) || "HIGH".equals(severity);
    }
}

