#!/bin/bash

# Test script for Inventory Service REST API
# Usage: ./test-api.sh

BASE_URL="http://localhost:8082/api/inventory"

echo "======================================"
echo "Testing Inventory Service REST API"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4

    echo -e "${GREEN}Test: ${description}${NC}"
    echo "  ${method} ${endpoint}"

    if [ -z "$data" ]; then
        curl -s -X ${method} "${BASE_URL}${endpoint}" | jq '.' || echo -e "${RED}Failed${NC}"
    else
        curl -s -X ${method} "${BASE_URL}${endpoint}" \
            -H "Content-Type: application/json" \
            -d "${data}" | jq '.' || echo -e "${RED}Failed${NC}"
    fi

    echo ""
    echo "--------------------------------------"
    echo ""
}

# Test 1: Get all parts
test_endpoint "GET" "/parts" "" "Get all parts"

# Test 2: Get specific part
test_endpoint "GET" "/parts/HYDRAULIC_PUMP_001" "" "Get specific part"

# Test 3: Get low stock parts
test_endpoint "GET" "/parts/low-stock" "" "Get low stock parts"

# Test 4: Check availability
test_endpoint "GET" "/parts/HYDRAULIC_PUMP_001/check-availability?quantity=10" "" "Check availability (10 units)"

# Test 5: Add stock
test_endpoint "POST" "/parts/HYDRAULIC_PUMP_001/add" \
    '{"quantity": 5, "reason": "API test - adding stock"}' \
    "Add 5 units to HYDRAULIC_PUMP_001"

# Test 6: Remove stock
test_endpoint "POST" "/parts/HYDRAULIC_PUMP_001/remove" \
    '{"quantity": 2, "reason": "API test - removing stock", "eventId": "test-event-001"}' \
    "Remove 2 units from HYDRAULIC_PUMP_001"

# Test 7: Get transactions
test_endpoint "GET" "/transactions" "" "Get all transactions"

# Test 8: Get part transaction history
test_endpoint "GET" "/parts/HYDRAULIC_PUMP_001/transactions" "" "Get transaction history for HYDRAULIC_PUMP_001"

# Test 9: Error test - Part not found
test_endpoint "GET" "/parts/NON-EXISTENT" "" "Error test - Part not found (expect 404)"

# Test 10: Error test - Insufficient stock
test_endpoint "POST" "/parts/HYDRAULIC_PUMP_001/remove" \
    '{"quantity": 10000, "reason": "Test"}' \
    "Error test - Insufficient stock (expect 400)"

echo ""
echo "======================================"
echo "All tests completed!"
echo "======================================"
