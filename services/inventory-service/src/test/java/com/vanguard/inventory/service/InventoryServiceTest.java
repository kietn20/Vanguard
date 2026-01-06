package com.vanguard.inventory.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.vanguard.inventory.exception.InsufficientStockException;
import com.vanguard.inventory.exception.PartNotFoundException;
import com.vanguard.inventory.model.InventoryTransaction;
import com.vanguard.inventory.model.Part;
import com.vanguard.inventory.model.TransactionType;
import com.vanguard.inventory.repository.InventoryTransactionRepository;
import com.vanguard.inventory.repository.PartRepository;

/**
 * Unit tests for InventoryService.
 *
 * Using Mockito to mock repository dependencies.
 *
 * Annotations:
 * - @ExtendWith(MockitoExtension.class): Enables Mockito annotations
 * - @Mock: Creates a mock object
 * - @InjectMocks: Creates instance and injects mocks into it
 */
@ExtendWith(MockitoExtension.class)
class InventoryServiceTest {

    @Mock
    private PartRepository partRepository;

    @Mock
    private InventoryTransactionRepository transactionRepository;

    @InjectMocks
    private InventoryService inventoryService;

    private Part testPart;

    @BeforeEach
    void setUp() {
        // Create a test part
        testPart = new Part(
                "TEST-PART-001",
                "Test Part",
                "TEST",
                50, // quantity
                10, // minimum quantity
                new BigDecimal("100.00"));
        testPart.setId(1L);
    }

    // ===== TEST: checkAvailability() =====

    @Test
    void checkAvailability_WhenSufficientStock_ReturnsTrue() {
        // Arrange
        when(partRepository.findByPartNumber("TEST-PART-001"))
                .thenReturn(Optional.of(testPart));

        // Act
        boolean available = inventoryService.checkAvailability("TEST-PART-001", 30);

        // Assert
        assertThat(available).isTrue();
        verify(partRepository).findByPartNumber("TEST-PART-001");
    }

    @Test
    void checkAvailability_WhenInsufficientStock_ReturnsFalse() {
        // Arrange
        when(partRepository.findByPartNumber("TEST-PART-001"))
                .thenReturn(Optional.of(testPart));

        // Act
        boolean available = inventoryService.checkAvailability("TEST-PART-001", 60);

        // Assert
        assertThat(available).isFalse();
    }

    @Test
    void checkAvailability_WhenPartNotFound_ReturnsFalse() {
        // Arrange
        when(partRepository.findByPartNumber("NON-EXISTENT"))
                .thenReturn(Optional.empty());

        // Act
        boolean available = inventoryService.checkAvailability("NON-EXISTENT", 10);

        // Assert
        assertThat(available).isFalse();
    }

    // ===== TEST: getPartByPartNumber() =====

    @Test
    void getPartByPartNumber_WhenExists_ReturnsPart() {
        // Arrange
        when(partRepository.findByPartNumber("TEST-PART-001"))
                .thenReturn(Optional.of(testPart));

        // Act
        Part found = inventoryService.getPartByPartNumber("TEST-PART-001");

        // Assert
        assertThat(found).isNotNull();
        assertThat(found.getPartNumber()).isEqualTo("TEST-PART-001");
    }

    @Test
    void getPartByPartNumber_WhenNotFound_ThrowsException() {
        // Arrange
        when(partRepository.findByPartNumber("NON-EXISTENT"))
                .thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> inventoryService.getPartByPartNumber("NON-EXISTENT"))
                .isInstanceOf(PartNotFoundException.class)
                .hasMessageContaining("NON-EXISTENT");
    }

    // ===== TEST: removeStock() =====

    @Test
    void removeStock_WhenSufficientStock_UpdatesInventoryAndCreatesTransaction() {
        // Arrange
        when(partRepository.findByPartNumber("TEST-PART-001"))
                .thenReturn(Optional.of(testPart));
        when(partRepository.save(any(Part.class)))
                .thenReturn(testPart);
        when(transactionRepository.save(any(InventoryTransaction.class)))
                .thenAnswer(invocation -> invocation.getArgument(0));

        // Act
        InventoryTransaction transaction = inventoryService.removeStock(
                "TEST-PART-001",
                20,
                "Used for repair",
                "event-123");

        // Assert
        assertThat(testPart.getQuantity()).isEqualTo(30); // 50 - 20
        assertThat(transaction).isNotNull();
        assertThat(transaction.getTransactionType()).isEqualTo(TransactionType.REMOVE);
        assertThat(transaction.getQuantityChange()).isEqualTo(-20);
        assertThat(transaction.getQuantityBefore()).isEqualTo(50);
        assertThat(transaction.getQuantityAfter()).isEqualTo(30);
        assertThat(transaction.getEventId()).isEqualTo("event-123");

        verify(partRepository).save(testPart);
        verify(transactionRepository).save(any(InventoryTransaction.class));
    }

    @Test
    void removeStock_WhenInsufficientStock_ThrowsException() {
        // Arrange
        when(partRepository.findByPartNumber("TEST-PART-001"))
                .thenReturn(Optional.of(testPart));

        // Act & Assert
        assertThatThrownBy(() -> inventoryService.removeStock("TEST-PART-001", 100, "Test", null))
                .isInstanceOf(InsufficientStockException.class)
                .hasMessageContaining("Insufficient stock")
                .hasMessageContaining("Requested: 100")
                .hasMessageContaining("Available: 50");

        // Verify no database changes were made
        verify(partRepository, never()).save(any());
        verify(transactionRepository, never()).save(any());
    }

    @Test
    void removeStock_WhenPartNotFound_ThrowsException() {
        // Arrange
        when(partRepository.findByPartNumber("NON-EXISTENT"))
                .thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> inventoryService.removeStock("NON-EXISTENT", 10, "Test", null))
                .isInstanceOf(PartNotFoundException.class);
    }

    // ===== TEST: addStock() =====

    @Test
    void addStock_UpdatesInventoryAndCreatesTransaction() {
        // Arrange
        when(partRepository.findByPartNumber("TEST-PART-001"))
                .thenReturn(Optional.of(testPart));
        when(partRepository.save(any(Part.class)))
                .thenReturn(testPart);
        when(transactionRepository.save(any(InventoryTransaction.class)))
                .thenAnswer(invocation -> invocation.getArgument(0));

        // Act
        InventoryTransaction transaction = inventoryService.addStock(
                "TEST-PART-001",
                25,
                "Received shipment");

        // Assert
        assertThat(testPart.getQuantity()).isEqualTo(75); // 50 + 25
        assertThat(transaction).isNotNull();
        assertThat(transaction.getTransactionType()).isEqualTo(TransactionType.ADD);
        assertThat(transaction.getQuantityChange()).isEqualTo(25);
        assertThat(transaction.getQuantityBefore()).isEqualTo(50);
        assertThat(transaction.getQuantityAfter()).isEqualTo(75);

        verify(partRepository).save(testPart);
        verify(transactionRepository).save(any(InventoryTransaction.class));
    }

    @Test
    void addStock_WhenPartNotFound_ThrowsException() {
        // Arrange
        when(partRepository.findByPartNumber("NON-EXISTENT"))
                .thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> inventoryService.addStock("NON-EXISTENT", 10, "Test"))
                .isInstanceOf(PartNotFoundException.class);
    }

    // ===== TEST: getLowStockParts() =====

    @Test
    void getLowStockParts_ReturnsPartsWithQuantityBelowMinimum() {
        // Arrange
        Part lowStockPart1 = new Part("LOW-001", "Low Part 1", "TEST", 5, 10, new BigDecimal("10.00"));
        Part lowStockPart2 = new Part("LOW-002", "Low Part 2", "TEST", 3, 15, new BigDecimal("15.00"));

        when(partRepository.findByQuantityLessThanMinimumQuantity())
                .thenReturn(List.of(lowStockPart1, lowStockPart2));

        // Act
        List<Part> lowStockParts = inventoryService.getLowStockParts();

        // Assert
        assertThat(lowStockParts).hasSize(2);
        assertThat(lowStockParts).extracting(Part::getPartNumber)
                .containsExactly("LOW-001", "LOW-002");
    }

    @Test
    void getLowStockParts_WhenNoLowStock_ReturnsEmptyList() {
        // Arrange
        when(partRepository.findByQuantityLessThanMinimumQuantity())
                .thenReturn(List.of());

        // Act
        List<Part> lowStockParts = inventoryService.getLowStockParts();

        // Assert
        assertThat(lowStockParts).isEmpty();
    }

    // ===== TEST: Transaction Recording =====

    @Test
    void removeStock_RecordsTransactionWithCorrectPerformedBy() {
        // Arrange
        when(partRepository.findByPartNumber("TEST-PART-001"))
                .thenReturn(Optional.of(testPart));
        when(transactionRepository.save(any(InventoryTransaction.class)))
                .thenAnswer(invocation -> invocation.getArgument(0));

        ArgumentCaptor<InventoryTransaction> transactionCaptor = ArgumentCaptor
                .forClass(InventoryTransaction.class);

        // Act
        inventoryService.removeStock("TEST-PART-001", 5, "Test removal", "evt-001");

        // Assert
        verify(transactionRepository).save(transactionCaptor.capture());
        InventoryTransaction captured = transactionCaptor.getValue();

        assertThat(captured.getPerformedBy()).isEqualTo("SYSTEM");
        assertThat(captured.getReason()).isEqualTo("Test removal");
        assertThat(captured.getEventId()).isEqualTo("evt-001");
    }
}
