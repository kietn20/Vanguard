package com.vanguard.inventory.repository;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.test.context.TestPropertySource;

import com.vanguard.inventory.model.Part;
import com.vanguard.inventory.repository.PartRepository;

/**
 * Integration test for PartRepository.
 *
 * Annotations:
 * - @DataJpaTest: Sets up in-memory H2 database for testing
 * - @TestPropertySource: Disables data.sql initialization for tests
 * - @Autowired: Spring injects dependencies
 *
 * This tests the REPOSITORY LAYER (database interactions).
 */
@DataJpaTest
@TestPropertySource(properties = "spring.sql.init.mode=never")
class PartRepositoryTest {

    @Autowired
    private PartRepository partRepository;

    @Autowired
    private TestEntityManager entityManager;

    private Part hydraulicPump;
    private Part bearing;
    private Part lowStockPart;

    /**
     * Setup method runs before each test.
     * Creates test data in the in-memory database.
     */
    @BeforeEach
    void setUp() {
        // Create test parts
        hydraulicPump = new Part(
                "TEST-PUMP-001",
                "Test Hydraulic Pump",
                "HYDRAULIC",
                15,
                10,
                new BigDecimal("450.00"));
        hydraulicPump.setLocation("TEST-WAREHOUSE");

        bearing = new Part(
                "TEST-BEARING-001",
                "Test Bearing",
                "MECHANICAL",
                50,
                20,
                new BigDecimal("12.50"));

        lowStockPart = new Part(
                "TEST-LOW-001",
                "Low Stock Part",
                "ELECTRICAL",
                3, // quantity below minimum
                10,
                new BigDecimal("100.00"));

        // Persist to test database
        entityManager.persist(hydraulicPump);
        entityManager.persist(bearing);
        entityManager.persist(lowStockPart);
        entityManager.flush();
    }

    @Test
    void testFindByPartNumber_WhenExists_Returnspart() {
        // Act
        Optional<Part> found = partRepository.findByPartNumber("TEST-PUMP-001");

        // Assert
        assertThat(found).isPresent();
        assertThat(found.get().getName()).isEqualTo("Test Hydraulic Pump");
        assertThat(found.get().getQuantity()).isEqualTo(15);
    }

    @Test
    void testFindByPartNumber_WhenNotExists_ReturnsEmpty() {
        // Act
        Optional<Part> found = partRepository.findByPartNumber("NON-EXISTENT");

        // Assert
        assertThat(found).isEmpty();
    }

    @Test
    void testFindByCategory_ReturnsAllPartsInCategory() {
        // Act
        List<Part> hydraulicParts = partRepository.findByCategory("HYDRAULIC");

        // Assert
        assertThat(hydraulicParts).hasSize(1);
        assertThat(hydraulicParts.get(0).getPartNumber()).isEqualTo("TEST-PUMP-001");
    }

    @Test
    void testFindByQuantityLessThanMinimumQuantity_ReturnsLowStockParts() {
        // Act
        List<Part> lowStockParts = partRepository.findByQuantityLessThanMinimumQuantity();

        // Assert
        assertThat(lowStockParts).hasSize(1);
        assertThat(lowStockParts.get(0).getPartNumber()).isEqualTo("TEST-LOW-001");
        assertThat(lowStockParts.get(0).isLowStock()).isTrue();
    }

    @Test
    void testFindByQuantity_ReturnsPartsWithExactQuantity() {
        // Act
        List<Part> parts = partRepository.findByQuantity(15);

        // Assert
        assertThat(parts).hasSize(1);
        assertThat(parts.get(0).getPartNumber()).isEqualTo("TEST-PUMP-001");
    }

    @Test
    void testFindByNameContainingIgnoreCase_ReturnsMatchingParts() {
        // Act - search is case-insensitive
        List<Part> parts = partRepository.findByNameContainingIgnoreCase("bearing");

        // Assert
        assertThat(parts).hasSize(1);
        assertThat(parts.get(0).getName()).isEqualTo("Test Bearing");
    }

    @Test
    void testFindPartsNeedingReorder_ReturnsLowStockPartsOrdered() {
        // Act
        List<Part> needsReorder = partRepository.findPartsNeedingReorder();

        // Assert
        assertThat(needsReorder).hasSize(1);
        assertThat(needsReorder.get(0).getQuantity()).isLessThan(
                needsReorder.get(0).getMinimumQuantity());
    }

    @Test
    void testExistsByPartNumber_WhenExists_ReturnsTrue() {
        // Act
        boolean exists = partRepository.existsByPartNumber("TEST-PUMP-001");

        // Assert
        assertThat(exists).isTrue();
    }

    @Test
    void testExistsByPartNumber_WhenNotExists_ReturnsFalse() {
        // Act
        boolean exists = partRepository.existsByPartNumber("NON-EXISTENT");

        // Assert
        assertThat(exists).isFalse();
    }

    @Test
    void testSave_CreatesNewPart() {
        // Arrange
        Part newPart = new Part(
                "TEST-NEW-001",
                "New Test Part",
                "SENSORS",
                25,
                15,
                new BigDecimal("125.00"));

        // Act
        Part saved = partRepository.save(newPart);

        // Assert
        assertThat(saved.getId()).isNotNull();
        assertThat(saved.getCreatedAt()).isNotNull();
        assertThat(saved.getUpdatedAt()).isNotNull();
    }

    @Test
    void testAddStock_UpdatesQuantity() {
        // Arrange
        Part part = partRepository.findByPartNumber("TEST-PUMP-001").orElseThrow();
        int initialQuantity = part.getQuantity();

        // Act
        part.addStock(10);
        partRepository.save(part);
        entityManager.flush();
        entityManager.clear(); // Clear persistence context to force reload

        // Assert
        Part reloaded = partRepository.findByPartNumber("TEST-PUMP-001").orElseThrow();
        assertThat(reloaded.getQuantity()).isEqualTo(initialQuantity + 10);
    }

    @Test
    void testRemoveStock_UpdatesQuantity() {
        // Arrange
        Part part = partRepository.findByPartNumber("TEST-PUMP-001").orElseThrow();
        int initialQuantity = part.getQuantity();

        // Act
        part.removeStock(5);
        partRepository.save(part);
        entityManager.flush();
        entityManager.clear();

        // Assert
        Part reloaded = partRepository.findByPartNumber("TEST-PUMP-001").orElseThrow();
        assertThat(reloaded.getQuantity()).isEqualTo(initialQuantity - 5);
    }
}
