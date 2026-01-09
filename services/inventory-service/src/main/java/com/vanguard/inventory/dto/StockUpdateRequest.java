package com.vanguard.inventory.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;



//DTO for stock update requests (add or remove)
public record StockUpdateRequest(@Min(value = 1, message = "Quantity must be at least 1") Integer quantity, @NotBlank(message = "Reason is required") String reason,

        String eventId
)

{

}
