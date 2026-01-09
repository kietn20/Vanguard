package com.vanguard.inventory.dto;

import java.time.Instant;

import com.vanguard.inventory.model.InventoryTransaction;
import com.vanguard.inventory.model.TransactionType;




// DTO for transaction responses
public record TransactionResponse(
        Long id,
        String partNumber,
        TransactionType transactionType,
        Integer quantityChange,
        Integer quantityBefore,
        Integer quantityAfter,
        String reason,
        String eventId,
        String performedBy,
        Instant timestamp) {
    public static TransactionResponse from(InventoryTransaction transaction) {
        return new TransactionResponse(
                transaction.getId(),
                transaction.getPart().getPartNumber(),
                transaction.getTransactionType(),
                transaction.getQuantityChange(),
                transaction.getQuantityBefore(),
                transaction.getQuantityAfter(),
                transaction.getReason(),
                transaction.getEventId(),
                transaction.getPerformedBy(),
                transaction.getTimestamp());
    }
}
