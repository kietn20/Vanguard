package com.vanguard.inventory.model;

import java.math.BigDecimal;
import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * JPA Entity representing a spare part in inventory.
 *
 * Annotations:
 * - @Entity: Marks this as a JPA entity (database table)
 * - @Table: Specifies table name and constraints
 * - @Id: Primary key
 * - @GeneratedValue: Auto-increment strategy
 * - @Column: Column-specific configuration
 */
@Entity
@Table(name = "parts", indexes = {
        @Index(name = "idx_part_number", columnList = "part_number"),
        @Index(name = "idx_category", columnList = "category"),
        @Index(name = "idx_low_stock", columnList = "quantity, minimum_quantity")
})
public class Part {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "part_number", unique = true, nullable = false, length = 50)
    @NotBlank(message = "Part number is required")
    @Size(max = 50, message = "Part number must not exceed 50 characters")
    private String partNumber;

    @Column(nullable = false)
    @NotBlank(message = "Part name is required")
    private String name;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(nullable = false, length = 100)
    @NotBlank(message = "Category is required")
    private String category;

    @Column(nullable = false)
    @Min(value = 0, message = "Quantity cannot be negative")
    private Integer quantity;

    @Column(name = "minimum_quantity", nullable = false)
    @Min(value = 0, message = "Minimum quantity cannot be negative")
    private Integer minimumQuantity;

    @Column(name = "unit_price", nullable = false, precision = 10, scale = 2)
    @DecimalMin(value = "0.01", message = "Unit price must be greater than zero")
    private BigDecimal unitPrice;

    @Column(length = 100)
    private String location;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    // JPA lifecycle callback: executed before entity is persisted
    @PrePersist
    protected void onCreate() {
        createdAt = Instant.now();
        updatedAt = Instant.now();
    }

    // JPA lifecycle callback: executed before entity is updated
    @PreUpdate
    protected void onUpdate() {
        updatedAt = Instant.now();
    }





    // Constructors

    public Part() {
        // JPA requires a no-arg constructor
    }

    public Part(String partNumber, String name, String category,
            Integer quantity, Integer minimumQuantity, BigDecimal unitPrice) {
        this.partNumber = partNumber;
        this.name = name;
        this.category = category;
        this.quantity = quantity;
        this.minimumQuantity = minimumQuantity;
        this.unitPrice = unitPrice;
    }




    // Business Logic Methods

    /**
     * Check if part stock is below minimum threshold.
     *
     * @return true if stock is low
     */
    public boolean isLowStock() {
        return quantity < minimumQuantity;
    }

    /**
     * Check if part is out of stock.
     *
     * @return true if quantity is zero
     */
    public boolean isOutOfStock() {
        return quantity == 0;
    }

    /**
     * Calculate recommended reorder quantity.
     *
     * @return quantity to reorder (3x minimum)
     */
    public int getReorderQuantity() {
        return minimumQuantity * 3;
    }

    /**
     * Add stock to inventory.
     *
     * @param quantityToAdd amount to add
     * @throws IllegalArgumentException if quantity is negative
     */
    public void addStock(int quantityToAdd) {
        if (quantityToAdd < 0) {
            throw new IllegalArgumentException("Cannot add negative quantity");
        }
        this.quantity += quantityToAdd;
    }

    /**
     * Remove stock from inventory.
     *
     * @param quantityToRemove amount to remove
     * @throws IllegalArgumentException if quantity is negative or insufficient
     *                                  stock
     */
    public void removeStock(int quantityToRemove) {
        if (quantityToRemove < 0) {
            throw new IllegalArgumentException("Cannot remove negative quantity");
        }
        if (quantityToRemove > this.quantity) {
            throw new IllegalArgumentException(
                    String.format("Insufficient stock. Requested: %d, Available: %d",
                            quantityToRemove, this.quantity));
        }
        this.quantity -= quantityToRemove;
    }




    
    // Getters and Setters

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getPartNumber() {
        return partNumber;
    }

    public void setPartNumber(String partNumber) {
        this.partNumber = partNumber;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getCategory() {
        return category;
    }

    public void setCategory(String category) {
        this.category = category;
    }

    public Integer getQuantity() {
        return quantity;
    }

    public void setQuantity(Integer quantity) {
        this.quantity = quantity;
    }

    public Integer getMinimumQuantity() {
        return minimumQuantity;
    }

    public void setMinimumQuantity(Integer minimumQuantity) {
        this.minimumQuantity = minimumQuantity;
    }

    public BigDecimal getUnitPrice() {
        return unitPrice;
    }

    public void setUnitPrice(BigDecimal unitPrice) {
        this.unitPrice = unitPrice;
    }

    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    @Override
    public String toString() {
        return "Part{" +
                "id=" + id +
                ", partNumber='" + partNumber + '\'' +
                ", name='" + name + '\'' +
                ", quantity=" + quantity +
                ", minimumQuantity=" + minimumQuantity +
                '}';
    }
}
