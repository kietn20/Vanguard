package com.vanguard.guardrail.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;



// request to validate an agent action
public record ActionRequest(
        @NotBlank(message = "Action type is required") String actionType,

        @NotBlank(message = "Part number is required") String partNumber,

        @NotNull(message = "Quantity is required") @Min(value = 1, message = "Quantity must be at least 1") Integer quantity,

        @NotBlank(message = "Reason is required") String reason,

        String eventId,

        String agentId) {
}
