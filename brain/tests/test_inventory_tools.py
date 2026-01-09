# tests require the Inventory Service to be running on localhost:8082.

import pytest
from tools.inventory_tools import (
    get_part_by_number,
    check_availability,
    get_low_stock_parts,
    InventoryToolError
)


def test_get_part_by_number_success():
    """Test getting a part that exists."""
    # this assumes HYDRAULIC_PUMP_001 exists in the database
    part = get_part_by_number("HYDRAULIC_PUMP_001")

    assert part.part_number == "HYDRAULIC_PUMP_001"
    assert part.name == "Hydraulic Pump Model A"
    assert part.quantity >= 0
    assert part.minimum_quantity >= 0


def test_get_part_by_number_not_found():
    """Test getting a part that doesn't exist."""
    with pytest.raises(InventoryToolError) as exc_info:
        get_part_by_number("NON-EXISTENT-PART")

    assert "Part not found" in str(exc_info.value)


def test_check_availability_sufficient():
    """Test availability check with sufficient stock."""
    # assuming HYDRAULIC_PUMP_001 has at least 5 units
    available = check_availability("HYDRAULIC_PUMP_001", 5)
    assert available is True


def test_check_availability_insufficient():
    """Test availability check with insufficient stock."""
    # assuming HYDRAULIC_PUMP_001 doesnt have 10000 unit
    available = check_availability("HYDRAULIC_PUMP_001", 10000)
    assert available is False


def test_get_low_stock_parts():
    """Test getting low stock parts."""
    low_stock = get_low_stock_parts()

    # should return a list (may be empty)
    assert isinstance(low_stock, list)

    # if any parts returned, they should be low on stock
    for part in low_stock:
        assert part.low_stock is True
        assert part.quantity < part.minimum_quantity


def test_check_availability_non_existent_part():
    """Test availability check for non-existent part returns False."""
    available = check_availability("NON-EXISTENT", 1)
    assert available is False
