"""
Tools for interacting with the Inventory Service REST API.

These tools allow AI agents to query and modify inventory data.
"""

import httpx
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


INVENTORY_API_BASE = "http://localhost:8082/api/inventory"


class InventoryToolError(Exception):
    """Raised when an inventory tool operation fails."""
    pass


# ===== Pydantic Models for Tool Responses =====

class PartInfo(BaseModel):
    """Information about a spare part"""
    part_number: str
    name: str
    quantity: int
    minimum_quantity: int
    unit_price: float
    location: str
    low_stock: bool
    out_of_stock: bool


class TransactionInfo(BaseModel):
    """Information about an inventory transaction"""
    id: int
    part_number: str
    transaction_type: str
    quantity_change: int
    quantity_before: int
    quantity_after: int
    reason: str
    event_id: Optional[str]
    performed_by: str


# ===== Tool Functions =====

def get_part_by_number(part_number: str) -> PartInfo:
    """
    Get detailed information about a specific part

    Args:
        part_number: The part number to look up (e.g., "HYDRAULIC_PUMP_001")

    Returns:
        PartInfo: Details about the part including stock levels

    Raises:
        InventoryToolError: If part not found or API error

    """
    try:
        response = httpx.get(f"{INVENTORY_API_BASE}/parts/{part_number}", timeout=5.0)
        response.raise_for_status()
        data = response.json()

        return PartInfo(
            part_number=data["partNumber"],
            name=data["name"],
            quantity=data["quantity"],
            minimum_quantity=data["minimumQuantity"],
            unit_price=data["unitPrice"],
            location=data["location"],
            low_stock=data["lowStock"],
            out_of_stock=data["outOfStock"]
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise InventoryToolError(f"Part not found: {part_number}")
        raise InventoryToolError(f"API error: {e.response.status_code}")
    except httpx.RequestError as e:
        raise InventoryToolError(f"Network error: {str(e)}")


def check_availability(part_number: str, quantity: int) -> bool:
    """
    Check if sufficient quantity of a part is available.

    Args:
        part_number: The part number to check
        quantity: The quantity needed

    Returns:
        bool: True if available, False otherwise
    """
    try:
        response = httpx.get(f"{INVENTORY_API_BASE}/parts/{part_number}/check-availability", params={"quantity": quantity}, timeout=5.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        return False


def get_low_stock_parts() -> List[PartInfo]:
    """
    Get all parts with stock below minimum quantity.

    Returns:
        List[PartInfo]: List of parts that need reordering
    """
    try:
        response = httpx.get(f"{INVENTORY_API_BASE}/parts/low-stock", timeout=5.0)
        response.raise_for_status()
        data = response.json()

        return [
            PartInfo(
                part_number=item["partNumber"],
                name=item["name"],
                quantity=item["quantity"],
                minimum_quantity=item["minimumQuantity"],
                unit_price=item["unitPrice"],
                location=item["location"],
                low_stock=item["lowStock"],
                out_of_stock=item["outOfStock"]
            )
            for item in data
        ]
    except httpx.HTTPError as e:
        raise InventoryToolError(f"Failed to get low stock parts: {str(e)}")


def remove_stock(part_number: str, quantity: int, reason: str, event_id: Optional[str] = None) -> TransactionInfo:
    """
    Remove stock from inventory

    Args:
        part_number: Part to remove stock from
        quantity: Amount to remove
        reason: Why the stock is being removed
        event_id: Optional factory event ID for traceability

    Returns:
        TransactionInfo: Record of the transaction

    Raises:
        InventoryToolError: If insufficient stock or other error
    """
    try:
        payload = {
            "quantity": quantity,
            "reason": reason,
            "eventId": event_id
        }

        response = httpx.post(f"{INVENTORY_API_BASE}/parts/{part_number}/remove", json=payload, timeout=5.0)
        response.raise_for_status()
        data = response.json()

        return TransactionInfo(
            id=data["id"],
            part_number=data["partNumber"],
            transaction_type=data["transactionType"],
            quantity_change=data["quantityChange"],
            quantity_before=data["quantityBefore"],
            quantity_after=data["quantityAfter"],
            reason=data["reason"],
            event_id=data.get("eventId"),
            performed_by=data["performedBy"]
        )
    except httpx.HTTPStatusError as e:
        error_data = e.response.json()
        raise InventoryToolError(error_data.get("message", "Unknown error"))
    except httpx.RequestError as e:
        raise InventoryToolError(f"Network error: {str(e)}")


def add_stock(  part_number: str, quantity: int, reason: str) -> TransactionInfo:
    """
    Add stock to inventory

    Args:
        part_number: Part to add stock to
        quantity: Amount to add
        reason: Why the stock is being added

    Returns:
        TransactionInfo: Record of the transaction
    """
    try:
        payload = {
            "quantity": quantity,
            "reason": reason
        }

        response = httpx.post(f"{INVENTORY_API_BASE}/parts/{part_number}/add", json=payload, timeout=5.0)
        response.raise_for_status()
        data = response.json()

        return TransactionInfo(
            id=data["id"],
            part_number=data["partNumber"],
            transaction_type=data["transactionType"],
            quantity_change=data["quantityChange"],
            quantity_before=data["quantityBefore"],
            quantity_after=data["quantityAfter"],
            reason=data["reason"],
            event_id=data.get("eventId"),
            performed_by=data["performedBy"]
        )
    except httpx.HTTPError as e:
        raise InventoryToolError(f"Failed to add stock: {str(e)}")


def get_all_parts() -> List[PartInfo]:
    """
    Get all parts in inventory

    Returns:
        List[PartInfo]: List of all parts
    """
    try:
        response = httpx.get(f"{INVENTORY_API_BASE}/parts", timeout=5.0)
        response.raise_for_status()
        data = response.json()

        return [
            PartInfo(
                part_number=item["partNumber"],
                name=item["name"],
                quantity=item["quantity"],
                minimum_quantity=item["minimumQuantity"],
                unit_price=item["unitPrice"],
                location=item["location"],
                low_stock=item["lowStock"],
                out_of_stock=item["outOfStock"]
            )
            for item in data
        ]
    except httpx.HTTPError as e:
        raise InventoryToolError(f"Failed to get parts: {str(e)}")
