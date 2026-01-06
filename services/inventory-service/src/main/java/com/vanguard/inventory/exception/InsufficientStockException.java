package com.vanguard.inventory.exception;

// Exception thrown when attempting to remove more stock than available.
public class InsufficientStockException extends RuntimeException {

    private final String partNumber;
    private final int requested;
    private final int available;

    public InsufficientStockException(String partNumber, int requested, int available) {
        super(String.format(
                "Insufficient stock for part %s. Requested: %d, Available: %d",
                partNumber, requested, available));
        this.partNumber = partNumber;
        this.requested = requested;
        this.available = available;
    }

    public String getPartNumber() {
        return partNumber;
    }

    public int getRequested() {
        return requested;
    }

    public int getAvailable() {
        return available;
    }
}
