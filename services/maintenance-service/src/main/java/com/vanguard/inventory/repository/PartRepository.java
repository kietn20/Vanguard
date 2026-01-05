package com.vanguard.inventory.repository;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import com.vanguard.inventory.model.Part;

/**
 * Spring Data JPA Repository for Part entity.
 *
 * By extending JpaRepository, Spring automatically provides:
 * - save(part)
 * - findById(id)
 * - findAll()
 * - deleteById(id)
 * - count()
 *
 * We only need to define custom query methods.
 */
@Repository
public interface PartRepository extends JpaRepository<Part, Long> {

    /**
     * Find a part by its part number.
     *
     * Spring automatically generates SQL:
     * SELECT * FROM parts WHERE part_number = ?
     *
     * Method naming convention: findBy + FieldName
     *
     * @param partNumber The part number to search for
     * @return Optional containing the part if found, empty otherwise
     */
    Optional<Part> findByPartNumber(String partNumber);

    /**
     * Find all parts in a specific category.
     *
     * Generated SQL:
     * SELECT * FROM parts WHERE category = ?
     *
     * @param category The category to filter by
     * @return List of parts in that category
     */
    List<Part> findByCategory(String category);

    /**
     * Find all parts where stock is below minimum quantity.
     *
     * Spring parses the method name:
     * - findBy: SELECT * FROM parts WHERE
     * - QuantityLessThan: quantity
     * - MinimumQuantity: minimum_quantity (compares two columns!)
     *
     * This is called a "Derived Query Method"
     *
     * @return List of parts with low stock
     */
    List<Part> findByQuantityLessThanMinimumQuantity();

    /**
     * Find all out-of-stock parts.
     *
     * Generated SQL:
     * SELECT * FROM parts WHERE quantity = 0
     *
     * @return List of parts with zero quantity
     */
    List<Part> findByQuantity(Integer quantity);

    /**
     * Find parts by name containing a search term (case-insensitive).
     *
     * Generated SQL:
     * SELECT * FROM parts WHERE LOWER(name) LIKE LOWER(?)
     *
     * IgnoreCase: case-insensitive search
     * Containing: wraps search term with %% (e.g., %pump%)
     *
     * @param name Search term
     * @return List of matching parts
     */
    List<Part> findByNameContainingIgnoreCase(String name);

    /**
     * Custom JPQL query to find parts needing reorder.
     *
     * @Query: Define custom query using JPQL (Java Persistence Query Language)
     *         JPQL uses entity names (Part) not table names (parts)
     *
     * @return List of parts below minimum with their reorder info
     */
    @Query("SELECT p FROM Part p WHERE p.quantity < p.minimumQuantity ORDER BY p.quantity ASC")
    List<Part> findPartsNeedingReorder();

    /**
     * Check if a part number already exists.
     *
     * Generated SQL:
     * SELECT COUNT(*) > 0 FROM parts WHERE part_number = ?
     *
     * @param partNumber Part number to check
     * @return true if exists, false otherwise
     */
    boolean existsByPartNumber(String partNumber);
}
