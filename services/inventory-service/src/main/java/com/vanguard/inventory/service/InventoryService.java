package com.vanguard.inventory.service;

import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.vanguard.inventory.exception.InsufficientStockException;
import com.vanguard.inventory.exception.PartNotFoundException;
import com.vanguard.inventory.model.InventoryTransaction;
import com.vanguard.inventory.model.Part;
import com.vanguard.inventory.model.TransactionType;
import com.vanguard.inventory.repository.InventoryTransactionRepository;
import com.vanguard.inventory.repository.PartRepository;




/**
 * Service layer for inventory management business logic.
 *
 * @Transactional ensures all database operations succeed or all fail (atomicity).
 */
@Service
@Transactional
public class InventoryService {

    private static final Logger logger = LoggerFactory.getLogger(InventoryService.class);
    private static final String SYSTEM_USER = "SYSTEM";

    private final PartRepository partRepository;
    private final InventoryTransactionRepository transactionRepository;

    public InventoryService(PartRepository partRepository,
            InventoryTransactionRepository transactionRepository) {
        this.partRepository = partRepository;
        this.transactionRepository = transactionRepository;
    }

    /**
     * Check if sufficient quantity of a part is available.
     *
     * @param partNumber Part to check
     * @param quantity   Quantity needed
     * @return true if available, false otherwise
     */
    @Transactional(readOnly = true)
    public boolean checkAvailability(String partNumber, int quantity) {
        return partRepository.findByPartNumber(partNumber)
                .map(part -> part.getQuantity() >= quantity)
                .orElse(false);
    }

    /**
     * Get a part by part number.
     *
     * @param partNumber Part number to find
     * @return Part entity
     * @throws PartNotFoundException if part not found
     */
    @Transactional(readOnly = true)
    public Part getPartByPartNumber(String partNumber) {
        return partRepository.findByPartNumber(partNumber)
                .orElseThrow(() -> new PartNotFoundException(partNumber));
    }

    /**
     * Remove stock from inventory.
     *
     * This is a critical operation that:
     * 1. Validates part exists
     * 2. Checks sufficient stock available
     * 3. Updates part quantity
     * 4. Creates audit transaction record
     *
     * @param partNumber Part to remove stock from
     * @param quantity   Amount to remove
     * @param reason     Why stock is being removed
     * @param eventId    Related factory event (if applicable)
     * @return Transaction record
     * @throws PartNotFoundException      if part not found
     * @throws InsufficientStockException if not enough stock
     */
    public InventoryTransaction removeStock(String partNumber, int quantity,
            String reason, String eventId) {
        logger.info("Removing {} units of {} (reason: {})", quantity, partNumber, reason);

        // find the part
        Part part = getPartByPartNumber(partNumber);

        // validate sufficient stock
        if (part.getQuantity() < quantity) {
            throw new InsufficientStockException(partNumber, quantity, part.getQuantity());
        }

        // capture before state
        int quantityBefore = part.getQuantity();

        // update inventory
        part.removeStock(quantity);
        partRepository.save(part);

        // create audit transaction
        InventoryTransaction transaction = new InventoryTransaction(
                part,
                TransactionType.REMOVE,
                -quantity, // negative for removal
                quantityBefore,
                part.getQuantity(),
                reason,
                SYSTEM_USER);
        transaction.setEventId(eventId);

        transactionRepository.save(transaction);

        logger.info("Successfully removed {} units of {}. New quantity: {}",
                quantity, partNumber, part.getQuantity());

        // check if low stock alert needed
        if (part.isLowStock()) {
            logger.warn("LOW STOCK ALERT: {} now has {} units (minimum: {})",
                    partNumber, part.getQuantity(), part.getMinimumQuantity());
        }

        return transaction;
    }

    /**
     * Add stock to inventory.
     *
     * @param partNumber Part to add stock to
     * @param quantity   Amount to add
     * @param reason     Why stock is being added
     * @return Transaction record
     * @throws PartNotFoundException if part not found
     */
    public InventoryTransaction addStock(String partNumber, int quantity, String reason) {
        logger.info("Adding {} units of {} (reason: {})", quantity, partNumber, reason);

        // find the part
        Part part = getPartByPartNumber(partNumber);

        // capture before state
        int quantityBefore = part.getQuantity();

        // update inventory
        part.addStock(quantity);
        partRepository.save(part);

        // create audit transaction
        InventoryTransaction transaction = new InventoryTransaction(
                part,
                TransactionType.ADD,
                quantity, // positive for addition
                quantityBefore,
                part.getQuantity(),
                reason,
                SYSTEM_USER);

        transactionRepository.save(transaction);

        logger.info("Successfully added {} units of {}. New quantity: {}",
                quantity, partNumber, part.getQuantity());

        return transaction;
    }

    /**
     * Get all parts with stock below minimum quantity.
     *
     * @return List of low-stock parts
     */
    @Transactional(readOnly = true)
    public List<Part> getLowStockParts() {
        return partRepository.findByQuantityLessThanMinimumQuantity();
    }
}
