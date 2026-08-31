"""Adversarial QA Test Suite for ShadowLedger.

Tests safety guardrails against deceptive near-matches, contradictory records,
impossible timelines, and false-positive traps.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.domain.enums import DecisionType, EventType
from app.domain.models import Observation
from app.engine.shadow_engine import ValueFlowReconstructionEngine


def test_adversarial_deceptive_near_match_does_not_auto_resolve():
    """Verify adversarial SCN_12 near-match (₹500 vs ₹505 with conflicting merchant) refuses to auto-resolve."""
    engine = ValueFlowReconstructionEngine()
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)

    # 2 observations with incompatible merchants and deceptive ₹5 difference
    obs = [
        Observation(
            observation_id="obs_adv_1",
            source_system="pos",
            source_record_id="pos_adv_1",
            event_type=EventType.PAYMENT,
            amount=Decimal("505.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-ADV-A", "merchant_id": "MERCH-ALPHA"},
            raw_payload={"scenario_id": "SCN_12"},
        ),
        Observation(
            observation_id="obs_adv_2",
            source_system="bank",
            source_record_id="bnk_adv_1",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("500.00"),
            timestamp=t0 + timedelta(hours=1),
            entity_ids={"order_id": "ORD-ADV-A", "merchant_id": "MERCH-BETA"},  # CONFLICTING MERCHANT
            raw_payload={"scenario_id": "SCN_12"},
        ),
    ]

    result = engine.process_batch("batch_adv_1", obs)
    assert len(result.cases) == 1

    case = result.cases[0]
    assert case.decision is not None
    # Engine MUST NOT auto-resolve adversarial deceptive mismatch
    assert case.decision.decision != DecisionType.AUTO_RESOLVE
    assert case.decision.decision in (DecisionType.HUMAN_REVIEW, DecisionType.UNRESOLVED)


def test_adversarial_impossible_temporal_sequence():
    """Verify that settlement predating payment by 30 days incurs contradiction penalty."""
    engine = ValueFlowReconstructionEngine()
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)

    obs = [
        Observation(
            observation_id="obs_fut_1",
            source_system="pos",
            source_record_id="pos_fut_1",
            event_type=EventType.PAYMENT,
            amount=Decimal("1000.00"),
            timestamp=t0 + timedelta(days=30),  # Payment 30 days in future
            entity_ids={"order_id": "ORD-TIME-1"},
        ),
        Observation(
            observation_id="obs_past_1",
            source_system="bank",
            source_record_id="bnk_past_1",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("980.00"),
            timestamp=t0,  # Settlement in the past
            entity_ids={"order_id": "ORD-TIME-1"},
        ),
    ]

    result = engine.process_batch("batch_adv_time", obs)
    case = result.cases[0]
    assert case.decision is not None
    # Temporal anomaly should prevent auto-resolution
    assert case.decision.decision != DecisionType.AUTO_RESOLVE


def test_adversarial_invisible_cash_deviation_unresolved():
    """Verify SCN_09 invisible cash deviation with zero indirect trace remains UNRESOLVED."""
    engine = ValueFlowReconstructionEngine()
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)

    obs = [
        Observation(
            observation_id="obs_ride_invis",
            source_system="ride_platform",
            source_record_id="ride_invis",
            event_type=EventType.PAYMENT,
            amount=Decimal("150.00"),
            timestamp=t0,
            entity_ids={"ride_id": "RIDE-INVIS-1"},
            raw_payload={"scenario_id": "SCN_09"},
        ),
    ]

    result = engine.process_batch("batch_adv_invis", obs)
    assert len(result.cases) == 1
    case = result.cases[0]
    assert case.decision is not None
    assert case.decision.decision != DecisionType.AUTO_RESOLVE
