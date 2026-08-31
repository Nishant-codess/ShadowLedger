"""Economic Event Scenario Library.

Single authoritative source for synthetic data generation, ground truth,
benchmark evaluation, adversarial verification, and demo cases.
"""

import random
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any


@dataclass
class ScenarioDefinition:
    """Specification of an economic event pattern in multi-source financial logs."""

    scenario_id: str
    name: str
    category: str
    description: str
    expected_decision: str
    allowed_hypotheses: list[str]
    generator: Callable[[random.Random, int, datetime], tuple[list[dict[str, Any]], dict[str, Any]]]


def _iso(dt: datetime) -> str:
    return dt.isoformat()


# ----------------------------------------------------------------------
# Scenario 01: Clean Normal Settlement (1-to-1 Match)
# ----------------------------------------------------------------------
def gen_scn_01_normal_settlement(
    rng: random.Random, index: int, base_time: datetime
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    order_id = f"ORD-2026-{index:05d}"
    payment_id = f"PAY-{index:05d}"
    merchant_id = f"MERCH-{rng.randint(100, 999)}"
    customer_id = f"CUST-{rng.randint(1000, 9999)}"
    amount = Decimal(str(rng.randint(100, 15000))) + Decimal(f"{rng.randint(0, 99):02d}") / 100

    pos_time = base_time + timedelta(seconds=rng.randint(0, 120))
    gtw_time = pos_time + timedelta(seconds=rng.randint(2, 30))
    bank_time = gtw_time + timedelta(minutes=rng.randint(30, 360))

    observed = [
        {
            "source_system": "pos",
            "source_record_id": f"pos_{order_id}",
            "event_type": "payment",
            "amount": float(amount),
            "currency": "INR",
            "timestamp": _iso(pos_time),
            "description": f"POS Sale Order {order_id}",
            "entity_ids": {
                "order_id": order_id,
                "payment_id": payment_id,
                "merchant_id": merchant_id,
                "customer_id": customer_id,
            },
        },
        {
            "source_system": "gateway",
            "source_record_id": f"gtw_{payment_id}",
            "event_type": "payment",
            "amount": float(amount),
            "currency": "INR",
            "timestamp": _iso(gtw_time),
            "description": f"Payment Gateway Capture {payment_id}",
            "entity_ids": {
                "order_id": order_id,
                "payment_id": payment_id,
                "merchant_id": merchant_id,
                "customer_id": customer_id,
            },
        },
        {
            "source_system": "bank",
            "source_record_id": f"bnk_{payment_id}",
            "event_type": "settlement",
            "amount": float(amount),
            "currency": "INR",
            "timestamp": _iso(bank_time),
            "description": f"Bank Settlement NEFT/{payment_id}",
            "entity_ids": {
                "payment_id": payment_id,
                "merchant_id": merchant_id,
            },
        },
    ]

    truth = {
        "scenario_id": "SCN_01",
        "order_id": order_id,
        "true_economic_amount": float(amount),
        "is_reconciled": True,
        "expected_decision": "auto_resolve",
        "latent_events": [],
    }
    return observed, truth


# ----------------------------------------------------------------------
# Scenario 02: Partial Refund (Latent Event)
# ----------------------------------------------------------------------
def gen_scn_02_partial_refund(
    rng: random.Random, index: int, base_time: datetime
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    order_id = f"ORD-REF-{index:05d}"
    payment_id = f"PAY-REF-{index:05d}"
    merchant_id = f"MERCH-{rng.randint(100, 999)}"
    customer_id = f"CUST-{rng.randint(1000, 9999)}"

    total_amount = Decimal(str(rng.randint(2000, 10000)))
    refund_amount = Decimal(str(rng.randint(200, int(total_amount * Decimal("0.4")))))
    net_settled = total_amount - refund_amount

    t0 = base_time + timedelta(seconds=rng.randint(0, 100))
    t2 = t0 + timedelta(hours=2)

    observed = [
        {
            "source_system": "pos",
            "source_record_id": f"pos_{order_id}",
            "event_type": "payment",
            "amount": float(total_amount),
            "currency": "INR",
            "timestamp": _iso(t0),
            "description": f"POS Sale {order_id}",
            "entity_ids": {"order_id": order_id, "payment_id": payment_id, "merchant_id": merchant_id, "customer_id": customer_id},
        },
        {
            "source_system": "bank",
            "source_record_id": f"bnk_{payment_id}",
            "event_type": "settlement",
            "amount": float(net_settled),
            "currency": "INR",
            "timestamp": _iso(t2),
            "description": f"Bank Net Settlement for {payment_id}",
            "entity_ids": {"payment_id": payment_id, "merchant_id": merchant_id},
        },
    ]

    truth = {
        "scenario_id": "SCN_02",
        "order_id": order_id,
        "original_amount": float(total_amount),
        "settled_amount": float(net_settled),
        "true_refund_amount": float(refund_amount),
        "is_reconciled": False,  # deterministic baseline will see mismatch
        "expected_hypothesis": "refund",
        "expected_decision": "human_review",
    }
    return observed, truth


# ----------------------------------------------------------------------
# Scenario 03: Gateway Fee Adjustment
# ----------------------------------------------------------------------
def gen_scn_03_fee_adjustment(
    rng: random.Random, index: int, base_time: datetime
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    order_id = f"ORD-FEE-{index:05d}"
    payment_id = f"PAY-FEE-{index:05d}"
    merchant_id = f"MERCH-{rng.randint(100, 999)}"

    gross_amount = Decimal(str(rng.randint(500, 8000)))
    fee_rate = Decimal("0.02")  # 2% gateway MDR
    fee_amount = (gross_amount * fee_rate).quantize(Decimal("0.01"))
    net_amount = gross_amount - fee_amount

    t0 = base_time + timedelta(seconds=rng.randint(0, 100))
    t1 = t0 + timedelta(hours=4)

    observed = [
        {
            "source_system": "pos",
            "source_record_id": f"pos_{order_id}",
            "event_type": "payment",
            "amount": float(gross_amount),
            "currency": "INR",
            "timestamp": _iso(t0),
            "description": f"POS Sale {order_id}",
            "entity_ids": {"order_id": order_id, "payment_id": payment_id, "merchant_id": merchant_id},
        },
        {
            "source_system": "gateway",
            "source_record_id": f"gtw_fee_{payment_id}",
            "event_type": "fee",
            "amount": float(-fee_amount),
            "currency": "INR",
            "timestamp": _iso(t0 + timedelta(minutes=5)),
            "description": f"MDR Fee 2% on {payment_id}",
            "entity_ids": {"payment_id": payment_id, "merchant_id": merchant_id},
        },
        {
            "source_system": "bank",
            "source_record_id": f"bnk_net_{payment_id}",
            "event_type": "settlement",
            "amount": float(net_amount),
            "currency": "INR",
            "timestamp": _iso(t1),
            "description": f"Bank Net Settlement for {payment_id}",
            "entity_ids": {"payment_id": payment_id, "merchant_id": merchant_id},
        },
    ]

    truth = {
        "scenario_id": "SCN_03",
        "order_id": order_id,
        "gross_amount": float(gross_amount),
        "fee_amount": float(fee_amount),
        "net_amount": float(net_amount),
        "is_reconciled": True,  # fee-aware deterministic rule reconciles this
        "expected_decision": "auto_resolve",
    }
    return observed, truth


# ----------------------------------------------------------------------
# Scenario 04: Kirana Non-Cash Inventory Settlement (Hero A)
# ₹100 Bill -> ₹98 Goods Cash + ₹2 Chocolate as Change
# ----------------------------------------------------------------------
def gen_scn_04_kirana_inventory(
    rng: random.Random, index: int, base_time: datetime
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    order_id = f"ORD-KIRANA-{index:05d}"
    merchant_id = f"MERCH-KIRANA-{rng.randint(10, 99)}"
    customer_id = f"CUST-{rng.randint(100, 999)}"

    tendered_cash = Decimal("100.00")
    bill_amount = Decimal("98.00")
    chocolate_change_val = Decimal("2.00")
    chocolate_cost = Decimal("1.20")

    t0 = base_time + timedelta(seconds=rng.randint(0, 60))

    observed = [
        {
            "source_system": "pos",
            "source_record_id": f"pos_{order_id}",
            "event_type": "payment",
            "amount": float(bill_amount),
            "currency": "INR",
            "timestamp": _iso(t0),
            "description": f"Grocery Bill Total {bill_amount}",
            "entity_ids": {"order_id": order_id, "merchant_id": merchant_id, "customer_id": customer_id},
        },
        {
            "source_system": "bank",
            "source_record_id": f"cash_deposit_{order_id}",
            "event_type": "settlement",
            "amount": float(tendered_cash),
            "currency": "INR",
            "timestamp": _iso(t0 + timedelta(hours=6)),
            "description": f"Cash register batch deposit for sale {order_id}",
            "entity_ids": {"order_id": order_id, "merchant_id": merchant_id},
        },
        {
            "source_system": "inventory",
            "source_record_id": f"inv_move_{order_id}",
            "event_type": "inventory_move",
            "amount": float(chocolate_change_val),
            "currency": "INR",
            "timestamp": _iso(t0 + timedelta(seconds=10)),
            "description": "Cadbury Dairy Milk 1 Unit dispensed as change",
            "entity_ids": {"order_id": order_id, "merchant_id": merchant_id},
            "inventory_move": {
                "sku": "SKU-CHOC-02",
                "item_description": "Dairy Milk Mini 2 INR",
                "quantity": 1.0,
                "unit_cost": float(chocolate_cost),
                "retail_value": float(chocolate_change_val),
                "valuation_basis": "retail",
                "linked_order_id": order_id,
            },
        },
    ]

    truth = {
        "scenario_id": "SCN_04",
        "order_id": order_id,
        "bill_amount": float(bill_amount),
        "tendered_cash": float(tendered_cash),
        "inventory_change_retail": float(chocolate_change_val),
        "inventory_change_cost": float(chocolate_cost),
        "is_reconciled": True,
        "true_economic_resolution": "inventory_settlement",
        "expected_decision": "auto_resolve",
    }
    return observed, truth


# ----------------------------------------------------------------------
# Scenario 05: Store Credit Carry-Forward
# ----------------------------------------------------------------------
def gen_scn_05_store_credit(
    rng: random.Random, index: int, base_time: datetime
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    order_id = f"ORD-CRD-{index:05d}"
    merchant_id = f"MERCH-{rng.randint(100, 999)}"
    customer_id = f"CUST-{rng.randint(1000, 9999)}"

    paid_amount = Decimal("500.00")
    fulfilled_amount = Decimal("450.00")
    credit_amount = Decimal("50.00")

    t0 = base_time + timedelta(seconds=rng.randint(0, 100))

    observed = [
        {
            "source_system": "pos",
            "source_record_id": f"pos_{order_id}",
            "event_type": "payment",
            "amount": float(paid_amount),
            "currency": "INR",
            "timestamp": _iso(t0),
            "description": f"Customer Advance / Payment {order_id}",
            "entity_ids": {"order_id": order_id, "merchant_id": merchant_id, "customer_id": customer_id},
        },
        {
            "source_system": "gateway",
            "source_record_id": f"gtw_{order_id}",
            "event_type": "payment",
            "amount": float(fulfilled_amount),
            "currency": "INR",
            "timestamp": _iso(t0 + timedelta(minutes=1)),
            "description": f"Order Invoice Fulfilled {order_id}",
            "entity_ids": {"order_id": order_id, "merchant_id": merchant_id, "customer_id": customer_id},
        },
    ]

    truth = {
        "scenario_id": "SCN_05",
        "order_id": order_id,
        "paid_amount": float(paid_amount),
        "fulfilled_amount": float(fulfilled_amount),
        "store_credit_issued": float(credit_amount),
        "is_reconciled": False,
        "expected_hypothesis": "store_credit",
        "expected_decision": "human_review",
    }
    return observed, truth


# ----------------------------------------------------------------------
# Scenario 06: Timing Offset (Next-Day Settlement)
# ----------------------------------------------------------------------
def gen_scn_06_timing_offset(
    rng: random.Random, index: int, base_time: datetime
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    order_id = f"ORD-TIME-{index:05d}"
    payment_id = f"PAY-TIME-{index:05d}"
    amount = Decimal(str(rng.randint(500, 3000)))

    t0 = base_time + timedelta(hours=23, minutes=50)
    t1 = t0 + timedelta(hours=26)  # Crosses 24h window into next batch

    observed = [
        {
            "source_system": "pos",
            "source_record_id": f"pos_{order_id}",
            "event_type": "payment",
            "amount": float(amount),
            "currency": "INR",
            "timestamp": _iso(t0),
            "description": f"Late Night Sale {order_id}",
            "entity_ids": {"order_id": order_id, "payment_id": payment_id},
        },
        {
            "source_system": "bank",
            "source_record_id": f"bnk_{payment_id}",
            "event_type": "settlement",
            "amount": float(amount),
            "currency": "INR",
            "timestamp": _iso(t1),
            "description": f"Settlement Batch T+2 {payment_id}",
            "entity_ids": {"payment_id": payment_id},
        },
    ]

    truth = {
        "scenario_id": "SCN_06",
        "order_id": order_id,
        "amount": float(amount),
        "is_reconciled": True,
        "expected_hypothesis": "timing_offset",
        "expected_decision": "auto_resolve",
    }
    return observed, truth


# ----------------------------------------------------------------------
# Scenario 07: Duplicate Record
# ----------------------------------------------------------------------
def gen_scn_07_duplicate(
    rng: random.Random, index: int, base_time: datetime
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    order_id = f"ORD-DUP-{index:05d}"
    payment_id = f"PAY-DUP-{index:05d}"
    amount = Decimal(str(rng.randint(300, 2000)))
    t0 = base_time + timedelta(minutes=rng.randint(0, 60))

    observed = [
        {
            "source_system": "pos",
            "source_record_id": f"pos_{order_id}_1",
            "event_type": "payment",
            "amount": float(amount),
            "currency": "INR",
            "timestamp": _iso(t0),
            "description": f"POS Sale {order_id}",
            "entity_ids": {"order_id": order_id, "payment_id": payment_id},
        },
        {
            "source_system": "pos",
            "source_record_id": f"pos_{order_id}_2",
            "event_type": "payment",
            "amount": float(amount),
            "currency": "INR",
            "timestamp": _iso(t0 + timedelta(seconds=2)),
            "description": f"POS Sale {order_id} (duplicate broadcast)",
            "entity_ids": {"order_id": order_id, "payment_id": payment_id},
        },
        {
            "source_system": "bank",
            "source_record_id": f"bnk_{payment_id}",
            "event_type": "settlement",
            "amount": float(amount),
            "currency": "INR",
            "timestamp": _iso(t0 + timedelta(hours=1)),
            "description": f"Settlement {payment_id}",
            "entity_ids": {"payment_id": payment_id},
        },
    ]

    truth = {
        "scenario_id": "SCN_07",
        "order_id": order_id,
        "amount": float(amount),
        "is_reconciled": True,
        "is_duplicate": True,
        "expected_hypothesis": "duplicate_reversal",
        "expected_decision": "auto_resolve",
    }
    return observed, truth


# ----------------------------------------------------------------------
# Scenario 08: Ride-Hailing Fare Deviation With Digital Trace (Hero B1)
# Official fare ₹150 + Digital tip/extra payment ₹50 found in bank trace
# ----------------------------------------------------------------------
def gen_scn_08_ride_digital_trace(
    rng: random.Random, index: int, base_time: datetime
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ride_id = f"RIDE-DIG-{index:05d}"
    driver_id = f"DRV-{rng.randint(100, 999)}"
    passenger_id = f"PAX-{rng.randint(1000, 9999)}"

    official_fare = Decimal("150.00")
    extra_payment = Decimal("50.00")
    total_paid = official_fare + extra_payment

    t0 = base_time + timedelta(minutes=rng.randint(0, 30))
    t_end = t0 + timedelta(minutes=25)

    observed = [
        {
            "source_system": "ride_platform",
            "source_record_id": f"trip_{ride_id}",
            "event_type": "payment",
            "amount": float(official_fare),
            "currency": "INR",
            "timestamp": _iso(t_end),
            "description": f"Uber/Ola Trip Fare {ride_id}",
            "entity_ids": {"ride_id": ride_id, "driver_id": driver_id, "passenger_id": passenger_id},
        },
        {
            "source_system": "bank",
            "source_record_id": f"upi_extra_{ride_id}",
            "event_type": "payment",
            "amount": float(extra_payment),
            "currency": "INR",
            "timestamp": _iso(t_end + timedelta(minutes=1)),
            "description": f"Direct UPI transfer to driver {driver_id}",
            "entity_ids": {"driver_id": driver_id, "passenger_id": passenger_id},
        },
    ]

    truth = {
        "scenario_id": "SCN_08",
        "ride_id": ride_id,
        "official_fare": float(official_fare),
        "actual_economic_payment": float(total_paid),
        "off_ledger_extra": float(extra_payment),
        "is_reconciled": False,
        "digital_trace_available": True,
        "expected_hypothesis": "off_ledger_deviation",
        "expected_decision": "human_review",  # OFF_LEDGER_DEVIATION NEVER auto-resolves
    }
    return observed, truth


# ----------------------------------------------------------------------
# Scenario 09: Ride-Hailing Cash-Only Invisible Deviation (Hero B2)
# Official fare ₹150 + Passenger gave ₹200 cash, zero digital record exists
# ----------------------------------------------------------------------
def gen_scn_09_ride_cash_invisible(
    rng: random.Random, index: int, base_time: datetime
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ride_id = f"RIDE-CSH-{index:05d}"
    driver_id = f"DRV-{rng.randint(100, 999)}"
    passenger_id = f"PAX-{rng.randint(1000, 9999)}"

    official_fare = Decimal("150.00")
    cash_given = Decimal("200.00")
    unrecorded_cash_deviation = Decimal("50.00")

    t0 = base_time + timedelta(minutes=rng.randint(0, 30))
    t_end = t0 + timedelta(minutes=30)

    # In observed systems, only the official recorded fare exists
    observed = [
        {
            "source_system": "ride_platform",
            "source_record_id": f"trip_{ride_id}",
            "event_type": "payment",
            "amount": float(official_fare),
            "currency": "INR",
            "timestamp": _iso(t_end),
            "description": f"Ride Fare Cash Order {ride_id}",
            "entity_ids": {"ride_id": ride_id, "driver_id": driver_id, "passenger_id": passenger_id},
        },
    ]

    truth = {
        "scenario_id": "SCN_09",
        "ride_id": ride_id,
        "official_fare": float(official_fare),
        "actual_cash_handed": float(cash_given),
        "hidden_economic_deviation": float(unrecorded_cash_deviation),
        "is_reconciled": False,
        "digital_trace_available": False,
        "expected_hypothesis": "off_ledger_deviation",
        "expected_decision": "unresolved",  # No direct evidence -> UNRESOLVED
    }
    return observed, truth


# ----------------------------------------------------------------------
# Scenario 10: Repeated Micro-Deviation Pattern (Hero C)
# Driver / Merchant has recurring systematic small discrepancy
# ----------------------------------------------------------------------
def gen_scn_10_recurring_micro_pattern(
    rng: random.Random, index: int, base_time: datetime
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    order_id = f"ORD-MIC-{index:05d}"
    driver_id = "DRV-REPEAT-888"  # Same driver/merchant generating recurring leakage
    official_amount = Decimal("220.00")
    micro_leakage = Decimal("20.00")

    t0 = base_time + timedelta(minutes=index * 5)

    observed = [
        {
            "source_system": "ride_platform",
            "source_record_id": f"trip_{order_id}",
            "event_type": "payment",
            "amount": float(official_amount),
            "currency": "INR",
            "timestamp": _iso(t0),
            "description": f"Platform booking fare {order_id}",
            "entity_ids": {"order_id": order_id, "driver_id": driver_id},
        },
    ]

    truth = {
        "scenario_id": "SCN_10",
        "order_id": order_id,
        "driver_id": driver_id,
        "official_amount": float(official_amount),
        "true_deviation": float(micro_leakage),
        "is_reconciled": False,
        "pattern_cluster": "driver_repeat_micro_deviation",
        "expected_decision": "human_review",
    }
    return observed, truth


# ----------------------------------------------------------------------
# Scenario 11: Upstream Batch Adjustment Affecting Many Transactions
# ----------------------------------------------------------------------
def gen_scn_11_batch_upstream_adjustment(
    rng: random.Random, index: int, base_time: datetime
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    batch_ref = f"BATCH-ADJ-{index // 10:03d}"
    order_id = f"ORD-BAT-{index:05d}"
    payment_id = f"PAY-BAT-{index:05d}"
    amount = Decimal("1000.00")
    surcharge = Decimal("15.00")
    net_bank = amount + surcharge

    t0 = base_time + timedelta(minutes=index)

    observed = [
        {
            "source_system": "pos",
            "source_record_id": f"pos_{order_id}",
            "event_type": "payment",
            "amount": float(amount),
            "currency": "INR",
            "timestamp": _iso(t0),
            "description": f"POS Batch Sale {order_id}",
            "entity_ids": {"order_id": order_id, "payment_id": payment_id, "batch_ref": batch_ref},
        },
        {
            "source_system": "bank",
            "source_record_id": f"bnk_{payment_id}",
            "event_type": "settlement",
            "amount": float(net_bank),
            "currency": "INR",
            "timestamp": _iso(t0 + timedelta(hours=2)),
            "description": f"Bank Settlement with Batch Surcharge {payment_id}",
            "entity_ids": {"payment_id": payment_id, "batch_ref": batch_ref},
        },
    ]

    truth = {
        "scenario_id": "SCN_11",
        "order_id": order_id,
        "amount": float(amount),
        "surcharge": float(surcharge),
        "batch_ref": batch_ref,
        "is_reconciled": False,
        "expected_decision": "human_review",
    }
    return observed, truth


# ----------------------------------------------------------------------
# Scenario 12: Adversarial Deceptive Near-Match (Must NOT Auto-Resolve)
# ----------------------------------------------------------------------
def gen_scn_12_adversarial_near_match(
    rng: random.Random, index: int, base_time: datetime
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    # Same amount, but completely different unrelated customers and non-matching temporal window
    order_a = f"ORD-ADV-A-{index:05d}"
    order_b = f"ORD-ADV-B-{index:05d}"
    amount = Decimal("4999.00")

    t0 = base_time + timedelta(minutes=rng.randint(0, 60))
    t_unrelated = t0 + timedelta(days=5)

    observed = [
        {
            "source_system": "pos",
            "source_record_id": f"pos_{order_a}",
            "event_type": "payment",
            "amount": float(amount),
            "currency": "INR",
            "timestamp": _iso(t0),
            "description": f"POS Sale Customer A {order_a}",
            "entity_ids": {"order_id": order_a, "customer_id": "CUST-A-999"},
        },
        {
            "source_system": "bank",
            "source_record_id": f"bnk_{order_b}",
            "event_type": "settlement",
            "amount": float(amount),
            "currency": "INR",
            "timestamp": _iso(t_unrelated),
            "description": f"Bank Settlement Customer B {order_b}",
            "entity_ids": {"order_id": order_b, "customer_id": "CUST-B-111"},
        },
    ]

    truth = {
        "scenario_id": "SCN_12",
        "order_a": order_a,
        "order_b": order_b,
        "amount": float(amount),
        "is_unrelated_adversarial": True,
        "is_reconciled": False,
        "expected_decision": "unresolved",  # Safety target: MUST NOT auto-resolve
    }
    return observed, truth


# Complete Scenario Registry (SCN_01 through SCN_12)
SCENARIOS: dict[str, ScenarioDefinition] = {
    "SCN_01": ScenarioDefinition(
        scenario_id="SCN_01",
        name="Normal Settlement Match",
        category="clean_match",
        description="Exact amount, matching order/payment ID, compatible timestamp.",
        expected_decision="auto_resolve",
        allowed_hypotheses=[],
        generator=gen_scn_01_normal_settlement,
    ),
    "SCN_02": ScenarioDefinition(
        scenario_id="SCN_02",
        name="Partial Refund Latent Event",
        category="latent_event",
        description="Settlement is less than payment due to an unrecorded partial refund.",
        expected_decision="human_review",
        allowed_hypotheses=["refund"],
        generator=gen_scn_02_partial_refund,
    ),
    "SCN_03": ScenarioDefinition(
        scenario_id="SCN_03",
        name="Gateway MDR Fee Adjustment",
        category="accounting_rule",
        description="Gross payment minus standard 2% gateway processing fee settles at bank.",
        expected_decision="auto_resolve",
        allowed_hypotheses=["fee_adjustment"],
        generator=gen_scn_03_fee_adjustment,
    ),
    "SCN_04": ScenarioDefinition(
        scenario_id="SCN_04",
        name="Kirana Non-Cash Inventory Settlement",
        category="hero_a",
        description="Bill of ₹98 settled with ₹100 cash and ₹2 chocolate dispensed as change.",
        expected_decision="auto_resolve",
        allowed_hypotheses=["inventory_settlement"],
        generator=gen_scn_04_kirana_inventory,
    ),
    "SCN_05": ScenarioDefinition(
        scenario_id="SCN_05",
        name="Store Credit Carry-Forward",
        category="latent_event",
        description="Advance payment exceeds invoice with remaining amount converted to customer store credit.",
        expected_decision="human_review",
        allowed_hypotheses=["store_credit"],
        generator=gen_scn_05_store_credit,
    ),
    "SCN_06": ScenarioDefinition(
        scenario_id="SCN_06",
        name="Next-Day Settlement Timing Offset",
        category="timing_variance",
        description="Late night transaction settling in next calendar day / batch window.",
        expected_decision="auto_resolve",
        allowed_hypotheses=["timing_offset"],
        generator=gen_scn_06_timing_offset,
    ),
    "SCN_07": ScenarioDefinition(
        scenario_id="SCN_07",
        name="Duplicate Broadcast Reversal",
        category="system_anomaly",
        description="Duplicate POS/Gateway broadcast resulting in redundant payment entry.",
        expected_decision="auto_resolve",
        allowed_hypotheses=["duplicate_reversal"],
        generator=gen_scn_07_duplicate,
    ),
    "SCN_08": ScenarioDefinition(
        scenario_id="SCN_08",
        name="Ride-Hailing Deviation (Digital Trace)",
        category="hero_b",
        description="Official ₹150 fare with external synthetic digital extra payment trace.",
        expected_decision="human_review",
        allowed_hypotheses=["off_ledger_deviation"],
        generator=gen_scn_08_ride_digital_trace,
    ),
    "SCN_09": ScenarioDefinition(
        scenario_id="SCN_09",
        name="Ride-Hailing Deviation (Cash Invisible)",
        category="hero_b",
        description="Official ₹150 fare where ₹200 cash was paid; no digital transaction exists for the ₹50 extra.",
        expected_decision="unresolved",
        allowed_hypotheses=["off_ledger_deviation"],
        generator=gen_scn_09_ride_cash_invisible,
    ),
    "SCN_10": ScenarioDefinition(
        scenario_id="SCN_10",
        name="Recurring Micro-Deviation Pattern",
        category="hero_c",
        description="Systematic recurring micro-leakages across a merchant or driver cohort.",
        expected_decision="human_review",
        allowed_hypotheses=["off_ledger_deviation"],
        generator=gen_scn_10_recurring_micro_pattern,
    ),
    "SCN_11": ScenarioDefinition(
        scenario_id="SCN_11",
        name="Upstream Batch Fee Adjustment",
        category="batch_anomaly",
        description="Batch-level surcharge distributed across multiple transactions.",
        expected_decision="human_review",
        allowed_hypotheses=["fee_adjustment"],
        generator=gen_scn_11_batch_upstream_adjustment,
    ),
    "SCN_12": ScenarioDefinition(
        scenario_id="SCN_12",
        name="Adversarial Deceptive Near-Match",
        category="adversarial_safety",
        description="Same amount with different customers and distant timestamps; engine must refuse auto-resolve.",
        expected_decision="unresolved",
        allowed_hypotheses=[],
        generator=gen_scn_12_adversarial_near_match,
    ),
}
