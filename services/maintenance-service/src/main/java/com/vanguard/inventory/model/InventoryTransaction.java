package com.vanguard.inventory.model;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.validation.constraints.NotNull;

/**
 * JPA Entity representing an inventory transaction (audit log).
 *
 * Every inventory change creates a transaction record for:
 * - Audit trail (who changed what and when)
 * - Historical analysis
 * - Event correlation (linking to factory events)
 */
@Entity
@Table(name = "inventory_transactions", indexes = {
        @Index(name = "idx_part_id", columnList = "part_id"),
        @Index(name = "idx_timestamp", columnList = "timestamp"),
        @Index(name = "idx_event_id", columnList = "event_id")
})
public class InventoryTransaction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Many-to-One relationship: Many transactions can reference one part.
     *
     * @ManyToOne: Defines the relationship
     * @JoinColumn: Specifies the foreign key column name
     *              FetchType.LAZY: Don't load the Part unless explicitly requested
     *              (performance)
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "part_id", nullable = false)
    @NotNull(message = "Part reference is required")
    private Part part;

    /**
     * Transaction type enumeration.
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "transaction_type", nullable = false, length = 50)
    @NotNull(message = "Transaction type is required")
    private TransactionType transactionType;

    @Column(name = "quantity_change", nullable = false)
    @NotNull(message = "Quantity change is required")
    private Integer quantityChange;

    @Column(name = "quantity_before", nullable = false)
    @NotNull(message = "Quantity before is required")
    private Integer quantityBefore;

    @Column(name = "quantity_after", nullable = false)
    @NotNull(message = "Quantity after is required")
    private Integer quantityAfter;

    @Column(length = 255)
    private String reason;

    /**
     * Links this transaction to a factory event (if applicable).
     * Enables tracing: "Which inventory changes resulted from which events?"
     */
    @Column(name = "event_id")
    private String eventId;

    @Column(name = "performed_by", length = 100)
    private String performedBy;

    @Column(nullable = false)
    @NotNull(message = "Timestamp is required")
    private Instant timestamp;






    // Constructors

    public InventoryTransaction() {
        // JPA requires a no-arg constructor
    }

    /**
     * Create a transaction record.
     *
     * @param part            The part being modified
     * @param transactionType Type of transaction (ADD, REMOVE, ADJUST)
     * @param quantityChange  Amount changed (positive or negative)
     * @param quantityBefore  Stock before transaction
     * @param quantityAfter   Stock after transaction
     * @param reason          Why this transaction occurred
     * @param performedBy     Who/what performed the transaction
     */
    public InventoryTransaction(Part part, TransactionType transactionType,
            Integer quantityChange, Integer quantityBefore,
            Integer quantityAfter, String reason, String performedBy) {
        this.part = part;
        this.transactionType = transactionType;
        this.quantityChange = quantityChange;
        this.quantityBefore = quantityBefore;
        this.quantityAfter = quantityAfter;
        this.reason = reason;
        this.performedBy = performedBy;
        this.timestamp = Instant.now();
    }







    // Business Logic Methods

    /**
     * Check if this transaction was triggered by a factory event.
     *
     * @return true if linked to an event
     */
    public boolean isEventTriggered() {
        return eventId != null && !eventId.isBlank();
    }

    /**
     * Check if transaction resulted in stock going below minimum.
     *
     * @return true if stock became low after this transaction
     */
    public boolean causedLowStock() {
        return quantityAfter < part.getMinimumQuantity();
    }






    // Getters and Setters

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Part getPart() {
        return part;
    }

    public void setPart(Part part) {
        this.part = part;
    }

    public TransactionType getTransactionType() {
        return transactionType;
    }

    public void setTransactionType(TransactionType transactionType) {
        this.transactionType = transactionType;
    }

    public Integer getQuantityChange() {
        return quantityChange;
    }

    public void setQuantityChange(Integer quantityChange) {
        this.quantityChange = quantityChange;
    }

    public Integer getQuantityBefore() {
        return quantityBefore;
    }

    public void setQuantityBefore(Integer quantityBefore) {
        this.quantityBefore = quantityBefore;
    }

    public Integer getQuantityAfter() {
        return quantityAfter;
    }

    public void setQuantityAfter(Integer quantityAfter) {
        this.quantityAfter = quantityAfter;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }

    public String getEventId() {
        return eventId;
    }

    public void setEventId(String eventId) {
        this.eventId = eventId;
    }

    public String getPerformedBy() {
        return performedBy;
    }

    public void setPerformedBy(String performedBy) {
        this.performedBy = performedBy;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Instant timestamp) {
        this.timestamp = timestamp;
    }

    @Override
    public String toString() {
        return "InventoryTransaction{" +
                "id=" + id +
                ", transactionType=" + transactionType +
                ", quantityChange=" + quantityChange +
                ", quantityBefore=" + quantityBefore +
                ", quantityAfter=" + quantityAfter +
                ", timestamp=" + timestamp +
                '}';
    }
}
