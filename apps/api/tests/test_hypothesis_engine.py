"""Unit tests for the Latent Hypothesis Engine."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.domain.enums import EventType, HypothesisType, ValuationBasis
from app.domain.models import InventoryMove, Observation
from app.engine.hypothesis_engine import LatentHypothesisEngine


def test_generate_refund_and_fee_hypotheses():
    """Verify generating candidate refund and fee hypotheses for payment > settlement."""
    engine = LatentHypothesisEngine()
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)

    # 1. Partial refund scenario: ₹10,000 paid, ₹8,500 settled
    obs = [
        Observation(
            observation_id="obs_p1",
            source_system="pos",
            source_record_id="p1",
            event_type=EventType.PAYMENT,
            amount=Decimal("10000.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-REF-1"},
        ),
        Observation(
            observation_id="obs_s1",
            source_system="bank",
            source_record_id="s1",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("8500.00"),
            timestamp=t0 + timedelta(hours=2),
            entity_ids={"order_id": "ORD-REF-1"},
        ),
    ]

    candidates = engine.generate_hypotheses("case_ref_1", obs)
    candidate_types = [h.hypothesis_type for h in candidates]

    assert HypothesisType.REFUND in candidate_types
    assert HypothesisType.STORE_CREDIT in candidate_types

    refund_hyp = next(h for h in candidates if h.hypothesis_type == HypothesisType.REFUND)
    assert refund_hyp.generated_event.amount == Decimal("1500.00")
    assert refund_hyp.can_auto_resolve is False  # Latent refund requires human approval


def test_generate_inventory_settlement_hypothesis():
    """Verify generating non-monetary chocolate change settlement candidate."""
    engine = LatentHypothesisEngine()
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)

    obs = [
        Observation(
            observation_id="obs_p2",
            source_system="pos",
            source_record_id="p2",
            event_type=EventType.PAYMENT,
            amount=Decimal("100.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-KIR-1"},
        ),
        Observation(
            observation_id="obs_s2",
            source_system="bank",
            source_record_id="s2",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("98.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-KIR-1"},
        ),
    ]

    inv = [
        InventoryMove(
            move_id="inv_c1",
            observation_id="obs_p2",
            item_description="Chocolate Bar",
            retail_value=Decimal("2.00"),
            valuation_basis=ValuationBasis.RETAIL,
            linked_order_id="ORD-KIR-1",
            timestamp=t0,
        )
    ]

    candidates = engine.generate_hypotheses("case_kir_1", obs, inv)
    inv_hyp = next((h for h in candidates if h.hypothesis_type == HypothesisType.INVENTORY_SETTLEMENT), None)

    assert inv_hyp is not None
    assert inv_hyp.generated_event.amount == Decimal("2.00")
    assert inv_hyp.can_auto_resolve is True  # Linked, known retail basis, closes residual


def test_generate_off_ledger_deviation_hypothesis():
    """Verify strict off-ledger payment deviation candidate generation."""
    engine = LatentHypothesisEngine()
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)

    obs = [
        Observation(
            observation_id="obs_ride_1",
            source_system="ride_platform",
            source_record_id="ride_100",
            event_type=EventType.PAYMENT,
            amount=Decimal("150.00"),
            timestamp=t0,
            entity_ids={"ride_id": "RIDE-99", "driver_id": "DRV-1"},
            raw_payload={"scenario_id": "SCN_08", "cash_deviation": 50.0},
        ),
        Observation(
            observation_id="obs_ext_trace_1",
            source_system="external_trace",
            source_record_id="ext_upi_100",
            event_type=EventType.PAYMENT,
            amount=Decimal("50.00"),
            timestamp=t0 + timedelta(minutes=5),
            entity_ids={"driver_id": "DRV-1"},
            raw_payload={"source_type": "external_driver_qr"},
        ),
    ]

    candidates = engine.generate_hypotheses("case_ride_1", obs)
    dev_hyp = next((h for h in candidates if h.hypothesis_type == HypothesisType.OFF_LEDGER_DEVIATION), None)

    assert dev_hyp is not None
    assert dev_hyp.can_auto_resolve is False  # Invariant: can never auto-resolve
    assert len(dev_hyp.indirect_evidence_ids) >= 1
