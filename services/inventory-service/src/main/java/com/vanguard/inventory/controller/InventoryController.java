package com.vanguard.inventory.controller;

import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.vanguard.inventory.dto.PartResponse;
import com.vanguard.inventory.dto.StockUpdateRequest;
import com.vanguard.inventory.dto.TransactionResponse;
import com.vanguard.inventory.model.InventoryTransaction;
import com.vanguard.inventory.model.Part;
import com.vanguard.inventory.repository.InventoryTransactionRepository;
import com.vanguard.inventory.repository.PartRepository;
import com.vanguard.inventory.service.InventoryService;

import jakarta.validation.Valid;



/**
 * REST API controller for inventory management.
 *
 * Base path: /api/inventory
 *
 * Annotations:
 * - @RestController: Marks this as a REST controller (returns JSON, not views)
 * - @RequestMapping: Base path for all endpoints
 * - @GetMapping/@PostMapping: HTTP method mappings
 * - @PathVariable: Extract value from URL path
 * - @RequestBody: Parse JSON request body
 * - @Valid: Trigger validation on request body
 */
@RestController
@RequestMapping("/api/inventory")
public class InventoryController {

    private static final Logger logger = LoggerFactory.getLogger(InventoryController.class);

    private final InventoryService inventoryService;
    private final PartRepository partRepository;
    private final InventoryTransactionRepository transactionRepository;



    public InventoryController(InventoryService inventoryService, PartRepository partRepository, InventoryTransactionRepository transactionRepository) {
        this.inventoryService = inventoryService;
        this.partRepository = partRepository;
        this.transactionRepository = transactionRepository;
    }



    // ===== PART ENDPOINTS =====

    /**
     * GET /api/inventory/parts
     * List all parts in inventory.
     *
     * @return List of all parts
     */
    @GetMapping("/parts")
    public ResponseEntity<List<PartResponse>> getAllParts() {
        logger.info("GET /api/inventory/parts - Fetching all parts");

        List<PartResponse> parts = partRepository.findAll()
                .stream()
                .map(PartResponse::from)
                .toList();

        logger.info("Returning {} parts", parts.size());
        return ResponseEntity.ok(parts);
    }

    /**
     * GET /api/inventory/parts/{partNumber}
     * Get specific part by part number.
     *
     * @param partNumber Part number to find
     * @return Part details
     */
    @GetMapping("/parts/{partNumber}")
    public ResponseEntity<PartResponse> getPartByPartNumber(@PathVariable String partNumber) {

        logger.info("GET /api/inventory/parts/{} - Fetching part", partNumber);

        Part part = inventoryService.getPartByPartNumber(partNumber);
        return ResponseEntity.ok(PartResponse.from(part));
    }

    /**
     * GET /api/inventory/parts/low-stock
     * Get all parts with stock below minimum quantity.
     *
     * @return List of low-stock parts
     */
    @GetMapping("/parts/low-stock")
    public ResponseEntity<List<PartResponse>> getLowStockParts() {
        logger.info("GET /api/inventory/parts/low-stock - Fetching low stock parts");

        List<PartResponse> lowStockParts = inventoryService.getLowStockParts()
                .stream()
                .map(PartResponse::from)
                .toList();

        logger.info("Returning {} low stock parts", lowStockParts.size());
        return ResponseEntity.ok(lowStockParts);
    }

    /**
     * POST /api/inventory/parts/{partNumber}/add
     * Add stock to a part.
     *
     * @param partNumber Part to add stock to
     * @param request    Stock update details
     * @return Transaction record
     */
    @PostMapping("/parts/{partNumber}/add")
    public ResponseEntity<TransactionResponse> addStock(@PathVariable String partNumber, @Valid @RequestBody StockUpdateRequest request) {

        logger.info("POST /api/inventory/parts/{}/add - Adding {} units", partNumber, request.quantity());

        InventoryTransaction transaction = inventoryService.addStock(
                partNumber,
                request.quantity(),
                request.reason());

        return ResponseEntity.status(HttpStatus.CREATED).body(TransactionResponse.from(transaction));
    }

    /**
     * POST /api/inventory/parts/{partNumber}/remove
     * Remove stock from a part.
     *
     * @param partNumber Part to remove stock from
     * @param request    Stock update details
     * @return Transaction record
     */
    @PostMapping("/parts/{partNumber}/remove")
    public ResponseEntity<TransactionResponse> removeStock(@PathVariable String partNumber, @Valid @RequestBody StockUpdateRequest request) {

        logger.info("POST /api/inventory/parts/{}/remove - Removing {} units", partNumber, request.quantity());

        InventoryTransaction transaction = inventoryService.removeStock(
                partNumber,
                request.quantity(),
                request.reason(),
                request.eventId());

        return ResponseEntity.ok(TransactionResponse.from(transaction));
    }

    /**
     * GET /api/inventory/parts/{partNumber}/check-availability
     * Check if sufficient quantity is available.
     *
     * @param partNumber Part to check
     * @param quantity   Quantity needed
     * @return Availability status
     */
    @GetMapping("/parts/{partNumber}/check-availability")
    public ResponseEntity<Boolean> checkAvailability(@PathVariable String partNumber, @RequestParam Integer quantity) {

        logger.info("GET /api/inventory/parts/{}/check-availability?quantity={}", partNumber, quantity);

        boolean available = inventoryService.checkAvailability(partNumber, quantity);
        return ResponseEntity.ok(available);
    }







    // ===== TRANSACTION ENDPOINTS =====

    /**
     * GET /api/inventory/transactions
     * Get all transactions (latest first).
     *
     * @return List of transactions
     */
    @GetMapping("/transactions")
    public ResponseEntity<List<TransactionResponse>> getAllTransactions() {
        logger.info("GET /api/inventory/transactions - Fetching all transactions");

        List<TransactionResponse> transactions = transactionRepository.findAll()
                .stream()
                .map(TransactionResponse::from)
                .toList();

        logger.info("Returning {} transactions", transactions.size());
        return ResponseEntity.ok(transactions);
    }

    /**
     * GET /api/inventory/transactions/{id}
     * Get specific transaction by ID.
     *
     * @param id Transaction ID
     * @return Transaction details
     */
    @GetMapping("/transactions/{id}")
    public ResponseEntity<TransactionResponse> getTransactionById(@PathVariable Long id) {
        logger.info("GET /api/inventory/transactions/{} - Fetching transaction", id);

        InventoryTransaction transaction = transactionRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Transaction not found: " + id));

        return ResponseEntity.ok(TransactionResponse.from(transaction));
    }

    /**
     * GET /api/inventory/parts/{partNumber}/transactions
     * Get transaction history for a specific part.
     *
     * @param partNumber Part number
     * @return List of transactions for this part
     */
    @GetMapping("/parts/{partNumber}/transactions")
    public ResponseEntity<List<TransactionResponse>> getPartTransactions(@PathVariable String partNumber) {

        logger.info("GET /api/inventory/parts/{}/transactions - Fetching transaction history", partNumber);

        Part part = inventoryService.getPartByPartNumber(partNumber);

        List<TransactionResponse> transactions = transactionRepository
                .findByPartOrderByTimestampDesc(part)
                .stream()
                .map(TransactionResponse::from)
                .toList();

        logger.info("Returning {} transactions for part {}", transactions.size(), partNumber);
        return ResponseEntity.ok(transactions);
    }
}
