"""Deterministic Hero Case Scenarios for Instant Demo Verification.

Defines reproducible, non-random benchmark scenarios:
- Hero A: Kirana Non-Monetary Settlement (₹100 POS -> ₹98 bank + ₹2 chocolate inventory change).
- Hero B: Mobility Ride Off-Ledger Payment Deviation (₹150 official fare -> ₹50 off-ledger deviation with digital trace vs cash invisible).
- Hero C: Fleet Pattern Collapse (100+ discrepancies collapsing into 3 core recurring structural patterns).
"""

from datetime import UTC, datetime, timedelta
from typing import Any


def get_hero_a_kirana() -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """Hero Case A: Kirana Non-Cash Inventory Settlement (The Chocolate Problem).

    Demonstrates how non-monetary retail item change (₹2 chocolate bar) safely
    closes a cash residual between POS and Bank Settlement.
    """
    batch_id = "hero_kirana_demo"
    t0 = datetime(2026, 9, 1, 10, 30, 0, tzinfo=UTC)

    records = [
        {
            "batch_id": batch_id,
            "source_system": "pos",
            "source_record_id": "pos_kirana_001",
            "event_type": "payment",
            "amount": 100.0,
            "currency": "INR",
            "timestamp": t0.isoformat(),
            "description": "Kirana Store Sale: Groceries + Chocolate Change",
            "entity_ids": {
                "order_id": "ORD-KIRANA-HERO",
                "merchant_id": "MERCH-KIRANA-01",
                "customer_id": "CUST-ANIL-99",
            },
            "raw_payload": {
                "scenario_id": "SCN_04",
                "item_description": "Dairy Milk Chocolate 10g",
                "inventory_change_qty": -1,
                "inventory_retail_value": 2.0,
                "valuation_basis": "retail",
            },
        },
        {
            "batch_id": batch_id,
            "source_system": "bank",
            "source_record_id": "bnk_kirana_001",
            "event_type": "settlement",
            "amount": 98.0,
            "currency": "INR",
            "timestamp": (t0 + timedelta(minutes=45)).isoformat(),
            "description": "Bank NEFT Net Settlement Ref: ORD-KIRANA-HERO",
            "entity_ids": {
                "order_id": "ORD-KIRANA-HERO",
                "merchant_id": "MERCH-KIRANA-01",
            },
            "raw_payload": {
                "scenario_id": "SCN_04",
            },
        },
    ]

    metadata = {
        "hero_id": "hero_a",
        "title": "Hero A: Kirana Non-Monetary Settlement",
        "description": "₹100 sale settled at ₹98 cash. Resolved via ₹2 chocolate inventory change.",
        "expected_resolution": "AUTO_RESOLVE",
        "expected_confidence": 0.95,
    }
    return batch_id, records, metadata


def get_hero_b_mobility() -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """Hero Case B: Mobility Ride Off-Ledger Payment Deviation (The Cab Problem).

    Demonstrates multi-source evidence:
    - Ride 1: Has indirect digital trace (driver personal QR payment) -> HUMAN_REVIEW with supporting indirect evidence.
    - Ride 2: Cash-only invisible deviation -> UNRESOLVED (Zero direct/indirect trace).
    Enforces that OFF_LEDGER_DEVIATION can NEVER auto-resolve.
    """
    batch_id = "hero_mobility_demo"
    t0 = datetime(2026, 9, 1, 11, 15, 0, tzinfo=UTC)

    records = [
        # Ride 1: Digital Extra Payment Trace (SCN_08)
        {
            "batch_id": batch_id,
            "source_system": "ride_platform",
            "source_record_id": "ride_plat_001",
            "event_type": "payment",
            "amount": 150.0,
            "currency": "INR",
            "timestamp": t0.isoformat(),
            "description": "Cab Ride Airport to Koramangala (Trip ID: RIDE-HERO-01)",
            "entity_ids": {
                "ride_id": "RIDE-HERO-01",
                "driver_id": "DRV-RAMESH-42",
                "customer_id": "CUST-PRIYA-10",
            },
            "raw_payload": {
                "scenario_id": "SCN_08",
                "cash_deviation": 50.0,
            },
        },
        {
            "batch_id": batch_id,
            "source_system": "external_trace",
            "source_record_id": "ext_upi_trace_001",
            "event_type": "payment",
            "amount": 50.0,
            "currency": "INR",
            "timestamp": (t0 + timedelta(minutes=3)).isoformat(),
            "description": "Driver UPI QR Credit: Toll & AC Surcharge (Ref: RIDE-HERO-01)",
            "entity_ids": {
                "ride_id": "RIDE-HERO-01",
                "driver_id": "DRV-RAMESH-42",
            },
            "raw_payload": {
                "scenario_id": "SCN_08",
                "source_type": "external_driver_qr",
            },
        },
        # Ride 2: Cash Invisible Deviation (SCN_09)
        {
            "batch_id": batch_id,
            "source_system": "ride_platform",
            "source_record_id": "ride_plat_002",
            "event_type": "payment",
            "amount": 150.0,
            "currency": "INR",
            "timestamp": (t0 + timedelta(minutes=30)).isoformat(),
            "description": "Cab Ride Indiranagar to Whitefield (Trip ID: RIDE-HERO-02)",
            "entity_ids": {
                "ride_id": "RIDE-HERO-02",
                "driver_id": "DRV-SURESH-88",
                "customer_id": "CUST-ROHAN-55",
            },
            "raw_payload": {
                "scenario_id": "SCN_09",
                "cash_deviation": 50.0,
            },
        },
    ]

    metadata = {
        "hero_id": "hero_b",
        "title": "Hero B: Mobility Off-Ledger Payment Deviations",
        "description": "Ride 1 has external QR trace (Human Review). Ride 2 is invisible cash (Unresolved). Never auto-resolves.",
        "expected_resolution": "HUMAN_REVIEW_AND_UNRESOLVED",
        "expected_confidence": 0.85,
    }
    return batch_id, records, metadata


def get_hero_c_patterns() -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """Hero Case C: Fleet Pattern Collapse (Cross-Case Structural Clusters).

    Generates 30 multi-party discrepancy cases across 3 distinct systemic patterns:
    1. Kirana non-cash inventory settlement across 10 merchants.
    2. Mobility off-ledger toll/AC surcharges across 10 drivers.
    3. Payment gateway MDR fee adjustments across 10 e-commerce orders.
    """
    batch_id = "hero_patterns_demo"
    t0 = datetime(2026, 9, 1, 9, 0, 0, tzinfo=UTC)
    records: list[dict[str, Any]] = []

    # Cluster 1: 10 Kirana Inventory Change Cases (SCN_04)
    for i in range(1, 11):
        order_id = f"ORD-KIR-FLEET-{i:03d}"
        merch_id = f"MERCH-KIR-{i:02d}"
        rec_time = t0 + timedelta(minutes=i * 5)
        records.extend([
            {
                "batch_id": batch_id,
                "source_system": "pos",
                "source_record_id": f"pos_kir_f_{i}",
                "event_type": "payment",
                "amount": 100.0 + (i * 10),
                "currency": "INR",
                "timestamp": rec_time.isoformat(),
                "description": f"POS Sale {order_id}",
                "entity_ids": {"order_id": order_id, "merchant_id": merch_id},
                "inventory_move": {
                    "item_description": "Dairy Milk Chocolate Change",
                    "quantity": 1,
                    "retail_value": 2.0,
                    "valuation_basis": "retail",
                    "linked_order_id": order_id,
                },
                "raw_payload": {"scenario_id": "SCN_04"},
            },
            {
                "batch_id": batch_id,
                "source_system": "bank",
                "source_record_id": f"bnk_kir_f_{i}",
                "event_type": "settlement",
                "amount": (100.0 + (i * 10)) - 2.0,
                "currency": "INR",
                "timestamp": (rec_time + timedelta(minutes=30)).isoformat(),
                "description": f"Bank Settlement {order_id}",
                "entity_ids": {"order_id": order_id, "merchant_id": merch_id},
                "raw_payload": {"scenario_id": "SCN_04"},
            },
        ])

    # Cluster 2: 10 Mobility Deviation Cases (SCN_10)
    for i in range(1, 11):
        ride_id = f"RIDE-CAB-FLEET-{i:03d}"
        driver_id = f"DRV-FLEET-{i:02d}"
        rec_time = t0 + timedelta(minutes=60 + i * 5)
        records.extend([
            {
                "batch_id": batch_id,
                "source_system": "ride_platform",
                "source_record_id": f"ride_mob_f_{i}",
                "event_type": "payment",
                "amount": 150.0,
                "currency": "INR",
                "timestamp": rec_time.isoformat(),
                "description": f"Platform Ride {ride_id}",
                "entity_ids": {"ride_id": ride_id, "driver_id": driver_id},
                "raw_payload": {"scenario_id": "SCN_10", "cash_deviation": 50.0},
            },
            {
                "batch_id": batch_id,
                "source_system": "external_trace",
                "source_record_id": f"ext_mob_f_{i}",
                "event_type": "payment",
                "amount": 50.0,
                "currency": "INR",
                "timestamp": (rec_time + timedelta(minutes=2)).isoformat(),
                "description": f"Driver UPI QR Direct Fare Addition Ref: {ride_id}",
                "entity_ids": {"ride_id": ride_id, "driver_id": driver_id},
                "raw_payload": {"scenario_id": "SCN_10", "source_type": "external_driver_qr"},
            },
        ])

    # Cluster 3: 10 Gateway MDR Fee Adjustments (2.0%) (SCN_03)
    for i in range(1, 11):
        order_id = f"ORD-ECOM-FLEET-{i:03d}"
        rec_time = t0 + timedelta(minutes=120 + i * 5)
        gross = 1000.0 * i
        fee = gross * 0.02
        net = gross - fee
        records.extend([
            {
                "batch_id": batch_id,
                "source_system": "pos",
                "source_record_id": f"pos_ecom_f_{i}",
                "event_type": "payment",
                "amount": gross,
                "currency": "INR",
                "timestamp": rec_time.isoformat(),
                "description": f"E-Commerce Sale {order_id}",
                "entity_ids": {"order_id": order_id},
                "raw_payload": {"scenario_id": "SCN_03"},
            },
            {
                "batch_id": batch_id,
                "source_system": "bank",
                "source_record_id": f"bnk_ecom_f_{i}",
                "event_type": "settlement",
                "amount": net,
                "currency": "INR",
                "timestamp": (rec_time + timedelta(minutes=45)).isoformat(),
                "description": f"Bank Settlement Net Ref: {order_id}",
                "entity_ids": {"order_id": order_id},
                "raw_payload": {"scenario_id": "SCN_03"},
            },
        ])

    metadata = {
        "hero_id": "hero_c",
        "title": "Hero C: Fleet Cross-Case Pattern Discovery (P0)",
        "description": "60 records collapse into 3 systemic structural patterns (Inventory, Off-Ledger Tolls, Gateway MDR fees).",
        "expected_resolution": "MULTI_PATTERN_DISCOVERY",
        "expected_confidence": 0.90,
    }
    return batch_id, records, metadata


HERO_SCENARIOS = {
    "hero_a": get_hero_a_kirana,
    "hero_b": get_hero_b_mobility,
    "hero_c": get_hero_c_patterns,
}
