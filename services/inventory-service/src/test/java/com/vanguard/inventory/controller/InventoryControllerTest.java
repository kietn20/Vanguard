package com.vanguard.inventory.controller;

import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.hasSize;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.math.BigDecimal;
import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.vanguard.inventory.dto.StockUpdateRequest;
import com.vanguard.inventory.exception.InsufficientStockException;
import com.vanguard.inventory.exception.PartNotFoundException;
import com.vanguard.inventory.model.InventoryTransaction;
import com.vanguard.inventory.model.Part;
import com.vanguard.inventory.model.TransactionType;
import com.vanguard.inventory.repository.InventoryTransactionRepository;
import com.vanguard.inventory.repository.PartRepository;
import com.vanguard.inventory.service.InventoryService;

/**
 * Integration test for InventoryController.
 *
 * @WebMvcTest: Loads only the web layer (controllers, advice)
 *              MockMvc: Simulates HTTP requests without starting a server
 */
@WebMvcTest(InventoryController.class)
class InventoryControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private InventoryService inventoryService;

    @MockBean
    private PartRepository partRepository;

    @MockBean
    private InventoryTransactionRepository transactionRepository;

    private Part testPart;
    private InventoryTransaction testTransaction;

    @BeforeEach
    void setUp() {
        testPart = new Part(
                "TEST-PART-001",
                "Test Part",
                "TEST",
                50,
                10,
                new BigDecimal("100.00"));
        testPart.setId(1L);

        testTransaction = new InventoryTransaction(
                testPart,
                TransactionType.REMOVE,
                -5,
                50,
                45,
                "Test removal",
                "SYSTEM");
        testTransaction.setId(1L);
    }

    // ===== GET /api/inventory/parts =====

    @Test
    void getAllParts_ReturnsListOfParts() throws Exception {
        // Arrange
        when(partRepository.findAll()).thenReturn(List.of(testPart));

        // Act & Assert
        mockMvc.perform(get("/api/inventory/parts"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].partNumber").value("TEST-PART-001"))
                .andExpect(jsonPath("$[0].name").value("Test Part"))
                .andExpect(jsonPath("$[0].quantity").value(50))
                .andExpect(jsonPath("$[0].lowStock").value(false));
    }

    // ===== GET /api/inventory/parts/{partNumber} =====

    @Test
    void getPartByPartNumber_WhenExists_ReturnsPart() throws Exception {
        // Arrange
        when(inventoryService.getPartByPartNumber("TEST-PART-001")).thenReturn(testPart);

        // Act & Assert
        mockMvc.perform(get("/api/inventory/parts/TEST-PART-001"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.partNumber").value("TEST-PART-001"))
                .andExpect(jsonPath("$.quantity").value(50));
    }

    @Test
    void getPartByPartNumber_WhenNotFound_Returns404() throws Exception {
        // Arrange
        when(inventoryService.getPartByPartNumber("NON-EXISTENT"))
                .thenThrow(new PartNotFoundException("NON-EXISTENT"));

        // Act & Assert
        mockMvc.perform(get("/api/inventory/parts/NON-EXISTENT"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.error").value("Not Found"))
                .andExpect(jsonPath("$.message").value("Part not found: NON-EXISTENT"));
    }

    // ===== GET /api/inventory/parts/low-stock =====

    @Test
    void getLowStockParts_ReturnsLowStockParts() throws Exception {
        // Arrange
        Part lowStockPart = new Part("LOW-001", "Low Part", "TEST", 3, 10, new BigDecimal("50.00"));
        when(inventoryService.getLowStockParts()).thenReturn(List.of(lowStockPart));

        // Act & Assert
        mockMvc.perform(get("/api/inventory/parts/low-stock"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].partNumber").value("LOW-001"))
                .andExpect(jsonPath("$[0].lowStock").value(true));
    }

    // ===== POST /api/inventory/parts/{partNumber}/add =====

    @Test
    void addStock_WithValidRequest_ReturnsTransaction() throws Exception {
        // Arrange
        StockUpdateRequest request = new StockUpdateRequest(5, "Received shipment", null);
        when(inventoryService.addStock(anyString(), anyInt(), anyString()))
                .thenReturn(testTransaction);

        // Act & Assert
        mockMvc.perform(post("/api/inventory/parts/TEST-PART-001/add")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.partNumber").value("TEST-PART-001"))
                .andExpect(jsonPath("$.transactionType").value("REMOVE"))
                .andExpect(jsonPath("$.quantityChange").value(-5));
    }

    @Test
    void addStock_WithInvalidRequest_Returns400() throws Exception {
        // Arrange - quantity is 0 (invalid)
        StockUpdateRequest request = new StockUpdateRequest(0, "Test", null);

        // Act & Assert
        mockMvc.perform(post("/api/inventory/parts/TEST-PART-001/add")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.error").value("Validation Failed"));
    }

    // ===== POST /api/inventory/parts/{partNumber}/remove =====

    @Test
    void removeStock_WithSufficientStock_ReturnsTransaction() throws Exception {
        // Arrange
        StockUpdateRequest request = new StockUpdateRequest(5, "Used for repair", "evt-001");
        when(inventoryService.removeStock(anyString(), anyInt(), anyString(), anyString()))
                .thenReturn(testTransaction);

        // Act & Assert
        mockMvc.perform(post("/api/inventory/parts/TEST-PART-001/remove")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.partNumber").value("TEST-PART-001"));
    }

    @Test
    void removeStock_WithInsufficientStock_Returns400() throws Exception {
        // Arrange
        StockUpdateRequest request = new StockUpdateRequest(100, "Test", null);
        when(inventoryService.removeStock(anyString(), anyInt(), anyString(), any()))
                .thenThrow(new InsufficientStockException("TEST-PART-001", 100, 50));

        // Act & Assert
        mockMvc.perform(post("/api/inventory/parts/TEST-PART-001/remove")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.message").value(containsString("Insufficient stock")));
    }

    // ===== GET /api/inventory/parts/{partNumber}/check-availability =====

    @Test
    void checkAvailability_WhenSufficient_ReturnsTrue() throws Exception {
        // Arrange
        when(inventoryService.checkAvailability("TEST-PART-001", 30)).thenReturn(true);

        // Act & Assert
        mockMvc.perform(get("/api/inventory/parts/TEST-PART-001/check-availability")
                .param("quantity", "30"))
                .andExpect(status().isOk())
                .andExpect(content().string("true"));
    }

    @Test
    void checkAvailability_WhenInsufficient_ReturnsFalse() throws Exception {
        // Arrange
        when(inventoryService.checkAvailability("TEST-PART-001", 100)).thenReturn(false);

        // Act & Assert
        mockMvc.perform(get("/api/inventory/parts/TEST-PART-001/check-availability")
                .param("quantity", "100"))
                .andExpect(status().isOk())
                .andExpect(content().string("false"));
    }

    // ===== GET /api/inventory/transactions =====

    @Test
    void getAllTransactions_ReturnsListOfTransactions() throws Exception {
        // Arrange
        when(transactionRepository.findAll()).thenReturn(List.of(testTransaction));

        // Act & Assert
        mockMvc.perform(get("/api/inventory/transactions"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].partNumber").value("TEST-PART-001"));
    }

    // ===== GET /api/inventory/parts/{partNumber}/transactions =====

    @Test
    void getPartTransactions_ReturnsTransactionHistory() throws Exception {
        // Arrange
        when(inventoryService.getPartByPartNumber("TEST-PART-001")).thenReturn(testPart);
        when(transactionRepository.findByPartOrderByTimestampDesc(testPart))
                .thenReturn(List.of(testTransaction));

        // Act & Assert
        mockMvc.perform(get("/api/inventory/parts/TEST-PART-001/transactions"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].partNumber").value("TEST-PART-001"))
                .andExpect(jsonPath("$[0].transactionType").value("REMOVE"));
    }
}
