package com.vanguard.inventory.exception;

// Exception thrown when a requested part is not found in inventory
public class PartNotFoundException extends RuntimeException {

    private final String partNumber;

    public PartNotFoundException(String partNumber) {
        super(String.format("Part not found: %s", partNumber));
        this.partNumber = partNumber;
    }

    public String getPartNumber() {
        return partNumber;
    }
}
