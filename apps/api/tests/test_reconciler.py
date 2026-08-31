"""Unit tests for the deterministic reconciliation baseline engine."""

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.enums import EventType, ReconciliationStatus, ValuationBasis
from app.domain.models import InventoryMove, Observation
from app.engine.reconciler import DeterministicReconciler


def test_exact_1_to_1_match(reconciler: DeterministicReconciler):
    """Verify exact payment and settlement match."""
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)
    obs = [
        Observation(
            source_system="pos",
            source_record_id="pos_1",
            event_type=EventType.PAYMENT,
            amount=Decimal("1500.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-01", "payment_id": "PAY-01"},
        ),
        Observation(
            source_system="bank",
            source_record_id="bnk_1",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("1500.00"),
            timestamp=t0,
            entity_ids={"payment_id": "PAY-01"},
        ),
    ]

    result = reconciler.reconcile_batch(obs)
    assert result.matched_count == 2
    assert result.exception_count == 0
    assert result.match_rate == 100.0
    assert result.match_groups[0].status == ReconciliationStatus.MATCHED
    assert result.match_groups[0].reason_code == "EXACT_ID_AND_AMOUNT_MATCH"


def test_fee_balanced_match(reconciler: DeterministicReconciler):
    """Verify Gross payment minus fee equals net bank settlement."""
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)
    obs = [
        Observation(
            source_system="pos",
            source_record_id="pos_1",
            event_type=EventType.PAYMENT,
            amount=Decimal("1000.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-02", "payment_id": "PAY-02"},
        ),
        Observation(
            source_system="gateway",
            source_record_id="gtw_fee_1",
            event_type=EventType.FEE,
            amount=Decimal("-20.00"),  # 2% fee
            timestamp=t0,
            entity_ids={"payment_id": "PAY-02"},
        ),
        Observation(
            source_system="bank",
            source_record_id="bnk_1",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("980.00"),
            timestamp=t0,
            entity_ids={"payment_id": "PAY-02"},
        ),
    ]

    result = reconciler.reconcile_batch(obs)
    assert result.matched_count == 3
    assert result.match_rate == 100.0
    assert result.match_groups[0].reason_code == "EXACT_FEE_ADJUSTMENT_MATCH"


def test_kirana_inventory_settlement_match(reconciler: DeterministicReconciler):
    """Verify ₹100 cash deposit balances ₹98 POS bill + ₹2 chocolate change."""
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)
    obs = [
        Observation(
            source_system="pos",
            source_record_id="pos_kirana_1",
            event_type=EventType.PAYMENT,
            amount=Decimal("98.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-KIRANA-1"},
        ),
        Observation(
            source_system="bank",
            source_record_id="bnk_cash_dep_1",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("100.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-KIRANA-1"},
        ),
    ]
    inv = [
        InventoryMove(
            observation_id="obs_dummy",
            sku="CHOC-02",
            item_description="Dairy Milk",
            quantity=Decimal("1.0"),
            unit_cost=Decimal("1.20"),
            retail_value=Decimal("2.00"),
            valuation_basis=ValuationBasis.RETAIL,
            linked_order_id="ORD-KIRANA-1",
        )
    ]

    result = reconciler.reconcile_batch(obs, inventory_moves=inv)
    assert result.matched_count == 2
    assert result.match_rate == 100.0
    assert result.match_groups[0].reason_code == "INVENTORY_SETTLEMENT_EXACT"


def test_amount_mismatch_creates_exception_case(reconciler: DeterministicReconciler):
    """Verify unbalance creates an investigation Case with residual."""
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)
    obs = [
        Observation(
            source_system="pos",
            source_record_id="pos_1",
            event_type=EventType.PAYMENT,
            amount=Decimal("5000.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-REF-01", "payment_id": "PAY-REF-01"},
        ),
        Observation(
            source_system="bank",
            source_record_id="bnk_1",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("4500.00"),  # ₹500 shortfall
            timestamp=t0,
            entity_ids={"payment_id": "PAY-REF-01"},
        ),
    ]

    result = reconciler.reconcile_batch(obs)
    assert result.matched_count == 0
    assert result.exception_count == 2
    assert len(result.cases) == 1
    assert result.cases[0].residual_amount == Decimal("500.00")
    assert result.cases[0].decision is not None
    assert result.cases[0].decision.decision.value == "unresolved"
