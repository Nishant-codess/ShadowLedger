"""Unit tests for the data normalizer."""

from datetime import UTC
from decimal import Decimal

from app.domain.enums import EventType, ValuationBasis
from app.engine.normalizer import (
    normalize_amount,
    normalize_record,
    parse_utc_timestamp,
)


def test_parse_utc_timestamp_variations():
    """Verify ISO string, timestamps, and formatted dates parse to UTC."""
    dt1 = parse_utc_timestamp("2026-08-31T09:30:00Z")
    assert dt1.tzinfo == UTC
    assert dt1.year == 2026

    dt2 = parse_utc_timestamp("2026-08-31 15:45:00")
    assert dt2.tzinfo == UTC
    assert dt2.hour == 15

    dt3 = parse_utc_timestamp(1788168000)  # Epoch seconds
    assert dt3.tzinfo == UTC


def test_normalize_amount_cleaning():
    """Verify currency symbols and strings parse to exact 2-decimal Decimals."""
    assert normalize_amount("₹1,250.50") == Decimal("1250.50")
    assert normalize_amount("  $98.00 INR ") == Decimal("98.00")
    assert normalize_amount(1500) == Decimal("1500.00")
    assert normalize_amount(None) == Decimal("0.00")


def test_normalize_record_with_inventory():
    """Verify raw record transforms into canonical Observation and InventoryMove."""
    raw = {
        "source_system": "inventory",
        "source_record_id": "inv_101",
        "event_type": "inventory_move",
        "amount": "2.00",
        "currency": "INR",
        "timestamp": "2026-08-31T10:00:00Z",
        "description": "Dairy Milk Chocolate",
        "entity_ids": {"order_id": "ORD-100"},
        "inventory_move": {
            "sku": "CHOC-02",
            "item_description": "Dairy Milk Mini",
            "quantity": 1.0,
            "unit_cost": "1.20",
            "retail_value": "2.00",
            "valuation_basis": "retail",
            "linked_order_id": "ORD-100",
        },
    }

    obs, inv = normalize_record(raw, batch_id="batch_test")
    assert obs.source_system == "inventory"
    assert obs.event_type == EventType.INVENTORY_MOVE
    assert obs.amount == Decimal("2.00")
    assert obs.entity_ids["order_id"] == "ORD-100"

    assert inv is not None
    assert inv.sku == "CHOC-02"
    assert inv.unit_cost == Decimal("1.20")
    assert inv.retail_value == Decimal("2.00")
    assert inv.valuation_basis == ValuationBasis.RETAIL
    assert inv.linked_order_id == "ORD-100"
