# Inventory Service REST API Documentation

Base URL: `http://localhost:8082/api/inventory`

## Authentication
Currently no authentication required (will add in Phase 4).

---

## Part Endpoints

### Get All Parts
**GET** `/api/inventory/parts`

Lists all parts in inventory.

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "partNumber": "HYDRAULIC_PUMP_001",
    "name": "Hydraulic Pump Model A",
    "description": "High-pressure hydraulic pump for press machines",
    "category": "HYDRAULIC",
    "quantity": 15,
    "minimumQuantity": 10,
    "unitPrice": 450.00,
    "location": "WAREHOUSE-A-SHELF-12",
    "lowStock": false,
    "outOfStock": false,
    "createdAt": "2026-01-09T10:00:00Z",
    "updatedAt": "2026-01-09T10:00:00Z"
  }
]
```

---

### Get Specific Part
**GET** `/api/inventory/parts/{partNumber}`

Retrieves a specific part by its part number.

**Path Parameters:**
- `partNumber` (string, required): The part number to look up

**Response: 200 OK**
```json
{
  "id": 1,
  "partNumber": "HYDRAULIC_PUMP_001",
  "name": "Hydraulic Pump Model A",
  "quantity": 15,
  "minimumQuantity": 10,
  "lowStock": false,
  "outOfStock": false
}
```

**Response: 404 Not Found**
```json
{
  "status": 404,
  "error": "Not Found",
  "message": "Part not found: NON-EXISTENT",
  "path": "/api/inventory/parts/NON-EXISTENT",
  "timestamp": "2026-01-09T10:00:00Z"
}
```

---

### Get Low Stock Parts
**GET** `/api/inventory/parts/low-stock`

Returns all parts where quantity is below minimum quantity.

**Use Case:** AI agents can query this to trigger reordering.

**Response: 200 OK**
```json
[
  {
    "partNumber": "CONVEYOR_BELT_10M",
    "name": "10m Conveyor Belt",
    "quantity": 3,
    "minimumQuantity": 5,
    "lowStock": true
  }
]
```

---

### Check Part Availability
**GET** `/api/inventory/parts/{partNumber}/check-availability?quantity={quantity}`

Checks if sufficient quantity is available for a part.

**Path Parameters:**
- `partNumber` (string, required): The part to check

**Query Parameters:**
- `quantity` (integer, required): Quantity needed

**Response: 200 OK**
```json
true
```

**Use Case:** AI agents check availability before scheduling repairs.

---

### Add Stock
**POST** `/api/inventory/parts/{partNumber}/add`

Adds stock to a part (e.g., receiving shipment, returning unused parts).

**Path Parameters:**
- `partNumber` (string, required): The part to add stock to

**Request Body:**
```json
{
  "quantity": 10,
  "reason": "Received shipment from supplier",
  "eventId": null
}
```

**Field Validations:**
- `quantity`: Must be at least 1
- `reason`: Required, cannot be blank
- `eventId`: Optional, used to link to factory events

**Response: 201 Created**
```json
{
  "id": 5,
  "partNumber": "HYDRAULIC_PUMP_001",
  "transactionType": "ADD",
  "quantityChange": 10,
  "quantityBefore": 15,
  "quantityAfter": 25,
  "reason": "Received shipment from supplier",
  "eventId": null,
  "performedBy": "SYSTEM",
  "timestamp": "2026-01-09T10:30:00Z"
}
```

**Response: 404 Not Found** (if part doesn't exist)

**Response: 400 Bad Request** (if validation fails)

---

### Remove Stock
**POST** `/api/inventory/parts/{partNumber}/remove`

Removes stock from a part (e.g., used for repair, scrapped).

**Path Parameters:**
- `partNumber` (string, required): The part to remove stock from

**Request Body:**
```json
{
  "quantity": 5,
  "reason": "Used for machine repair",
  "eventId": "event-abc-123"
}
```

**Response: 200 OK**
```json
{
  "id": 6,
  "partNumber": "HYDRAULIC_PUMP_001",
  "transactionType": "REMOVE",
  "quantityChange": -5,
  "quantityBefore": 25,
  "quantityAfter": 20,
  "reason": "Used for machine repair",
  "eventId": "event-abc-123",
  "performedBy": "SYSTEM",
  "timestamp": "2026-01-09T10:35:00Z"
}
```

**Response: 400 Bad Request** (if insufficient stock)
```json
{
  "status": 400,
  "error": "Bad Request",
  "message": "Insufficient stock for part HYDRAULIC_PUMP_001. Requested: 100, Available: 20",
  "path": "/api/inventory/parts/HYDRAULIC_PUMP_001/remove",
  "timestamp": "2026-01-09T10:35:00Z"
}
```

---

## Transaction Endpoints

### Get All Transactions
**GET** `/api/inventory/transactions`

Returns all inventory transactions (audit trail).

**Response: 200 OK**
```json
[
  {
    "id": 6,
    "partNumber": "HYDRAULIC_PUMP_001",
    "transactionType": "REMOVE",
    "quantityChange": -5,
    "quantityBefore": 25,
    "quantityAfter": 20,
    "reason": "Used for machine repair",
    "eventId": "event-abc-123",
    "performedBy": "SYSTEM",
    "timestamp": "2026-01-09T10:35:00Z"
  }
]
```

---

### Get Transaction by ID
**GET** `/api/inventory/transactions/{id}`

Retrieves a specific transaction.

**Path Parameters:**
- `id` (long, required): Transaction ID

**Response: 200 OK**

---

### Get Part Transaction History
**GET** `/api/inventory/parts/{partNumber}/transactions`

Returns all transactions for a specific part (newest first).

**Path Parameters:**
- `partNumber` (string, required): Part to get history for

**Use Case:** AI agents can analyze usage patterns for predictive maintenance.

**Response: 200 OK**
```json
[
  {
    "id": 6,
    "partNumber": "HYDRAULIC_PUMP_001",
    "transactionType": "REMOVE",
    "quantityChange": -5,
    "reason": "Used for machine repair",
    "timestamp": "2026-01-09T10:35:00Z"
  },
  {
    "id": 5,
    "partNumber": "HYDRAULIC_PUMP_001",
    "transactionType": "ADD",
    "quantityChange": 10,
    "reason": "Received shipment",
    "timestamp": "2026-01-09T10:30:00Z"
  }
]
```

---

## Error Responses

All errors follow this standard format:
```json
{
  "status": 404,
  "error": "Not Found",
  "message": "Detailed error message here",
  "path": "/api/inventory/parts/NON-EXISTENT",
  "timestamp": "2026-01-09T10:00:00Z"
}
```

### Common HTTP Status Codes

- **200 OK**: Request succeeded
- **201 Created**: Resource created successfully
- **400 Bad Request**: Validation error or business rule violation
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Unexpected server error

---

## Usage Examples for AI Agents

### Example 1: Check if Parts Available Before Repair
```bash
# 1. Check if hydraulic pump is available
GET /api/inventory/parts/HYDRAULIC_PUMP_001/check-availability?quantity=1

# 2. If true, remove stock
POST /api/inventory/parts/HYDRAULIC_PUMP_001/remove
{
  "quantity": 1,
  "reason": "Used for PRESS-001 repair",
  "eventId": "sensor-overheat-event-123"
}
```

### Example 2: Identify Low Stock and Reorder
```bash
# 1. Get all low stock parts
GET /api/inventory/parts/low-stock

# 2. For each low stock part, calculate reorder quantity
GET /api/inventory/parts/CONVEYOR_BELT_10M

# 3. AI agent creates purchase order
```

### Example 3: Audit Trail Analysis
```bash
# Get transaction history for a part
GET /api/inventory/parts/BEARING_6205/transactions

# Analyze usage patterns:
# - Frequency of usage
# - Typical quantities consumed
# - Correlation with machine failures
```

---

## Rate Limiting


## Versioning
Current version: v1 (implicit in path structure)

Future: `/api/v2/inventory/...`
