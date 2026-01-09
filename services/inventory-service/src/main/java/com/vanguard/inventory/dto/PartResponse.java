package com.vanguard.inventory.dto;

import java.math.BigDecimal;
import java.time.Instant;

import com.vanguard.inventory.model.Part;

public record PartResponse(
    Long id,
    String partNumber,
    String name,
    String description,
    String category,
    Integer quantity,
    Integer minimumQuantity,
    BigDecimal unitPrice,
    String location,
    boolean lowStock,
    boolean outOfStock,
    Instant createdAt,
    Instant updatedAt
) {
    /**
     * Convert entity to DTO.
     *
     * @param part Part entity
     * @return PartResponse DTO
     */
    public static PartResponse from(Part part) {
        return new PartResponse(
            part.getId(),
            part.getPartNumber(),
            part.getName(),
            part.getDescription(),
            part.getCategory(),
            part.getQuantity(),
            part.getMinimumQuantity(),
            part.getUnitPrice(),
            part.getLocation(),
            part.isLowStock(),
            part.isOutOfStock(),
            part.getCreatedAt(),
            part.getUpdatedAt()
        );
    }
}
