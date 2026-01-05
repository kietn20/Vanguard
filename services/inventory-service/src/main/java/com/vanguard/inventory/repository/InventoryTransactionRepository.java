package com.vanguard.inventory.repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import com.vanguard.inventory.model.InventoryTransaction;
import com.vanguard.inventory.model.Part;
import com.vanguard.inventory.model.TransactionType;

/**
 * Spring Data JPA Repository for InventoryTransaction entity.
 */
@Repository
public interface InventoryTransactionRepository extends JpaRepository<InventoryTransaction, Long> {

    /**
     * Find all transactions for a specific part.
     *
     * Generated SQL:
     * SELECT * FROM inventory_transactions WHERE part_id = ? ORDER BY timestamp
     * DESC
     *
     * @param part The part to get transaction history for
     * @return List of transactions ordered by newest first
     */
    List<InventoryTransaction> findByPartOrderByTimestampDesc(Part part);

    /**
     * Find transaction by event ID (for idempotency checks).
     *
     * Used to prevent processing the same factory event multiple times.
     *
     * @param eventId Factory event ID
     * @return Optional containing transaction if found
     */
    Optional<InventoryTransaction> findByEventId(String eventId);

    /**
     * Find all transactions by type within a time range.
     *
     * @param transactionType Type to filter by
     * @param startTime       Start of time range
     * @param endTime         End of time range
     * @return List of matching transactions
     */
    List<InventoryTransaction> findByTransactionTypeAndTimestampBetween(
            TransactionType transactionType,
            Instant startTime,
            Instant endTime);

    /**
     * Get recent transactions (last N transactions).
     *
     * Custom JPQL query with parameter.
     *
     * @param limit Maximum number of transactions to return
     * @return List of recent transactions
     */
    @Query("SELECT t FROM InventoryTransaction t ORDER BY t.timestamp DESC")
    List<InventoryTransaction> findRecentTransactions(@Param("limit") int limit);

    /**
     * Check if a transaction for a given event ID already exists.
     *
     * Enables idempotency: prevent duplicate processing of the same event.
     *
     * @param eventId Factory event ID
     * @return true if transaction exists, false otherwise
     */
    boolean existsByEventId(String eventId);
}
