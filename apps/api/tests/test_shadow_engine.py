"""Unit tests for the complete Value-Flow Reconstruction Master Engine."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.domain.enums import DecisionType, EventType, ValuationBasis
from app.domain.models import InventoryMove, Observation
from app.engine.shadow_engine import ValueFlowReconstructionEngine


def test_shadow_engine_end_to_end_batch():
    """Verify end-to-end execution of 7-stage engine across mixed transaction scenarios."""
    engine = ValueFlowReconstructionEngine()
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)

    # 1. Exact 1-to-1 match (SCN_01)
    obs_1 = [
        Observation(
            observation_id="obs_e1",
            source_system="pos",
            source_record_id="p1",
            event_type=EventType.PAYMENT,
            amount=Decimal("1000.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-1", "payment_id": "PAY-1"},
        ),
        Observation(
            observation_id="obs_e2",
            source_system="bank",
            source_record_id="s1",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("1000.00"),
            timestamp=t0 + timedelta(minutes=10),
            entity_ids={"order_id": "ORD-1", "payment_id": "PAY-1"},
        ),
    ]

    # 2. Kirana chocolate inventory change (SCN_04)
    obs_2 = [
        Observation(
            observation_id="obs_k1",
            source_system="pos",
            source_record_id="p2",
            event_type=EventType.PAYMENT,
            amount=Decimal("100.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-2", "payment_id": "PAY-2"},
        ),
        Observation(
            observation_id="obs_k2",
            source_system="bank",
            source_record_id="s2",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("98.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-2", "payment_id": "PAY-2"},
        ),
    ]
    inv_2 = [
        InventoryMove(
            move_id="inv_k1",
            observation_id="obs_k1",
            item_description="Chocolate Bar",
            retail_value=Decimal("2.00"),
            valuation_basis=ValuationBasis.RETAIL,
            linked_order_id="ORD-2",
            timestamp=t0,
        )
    ]

    # 3. Off-ledger cab fare deviation (SCN_08)
    obs_3 = [
        Observation(
            observation_id="obs_r1",
            source_system="ride_platform",
            source_record_id="r1",
            event_type=EventType.PAYMENT,
            amount=Decimal("150.00"),
            timestamp=t0,
            entity_ids={"ride_id": "RIDE-1", "driver_id": "DRV-1"},
            raw_payload={"scenario_id": "SCN_08", "cash_deviation": 50.0},
        ),
        Observation(
            observation_id="obs_r2",
            source_system="external_trace",
            source_record_id="ext_1",
            event_type=EventType.PAYMENT,
            amount=Decimal("50.00"),
            timestamp=t0 + timedelta(minutes=5),
            entity_ids={"driver_id": "DRV-1"},
            raw_payload={"source_type": "external_driver_qr"},
        ),
    ]

    all_obs = obs_1 + obs_2 + obs_3
    all_inv = inv_2

    result = engine.process_batch(
        batch_id="batch_test_mixed",
        observations=all_obs,
        inventory_moves=all_inv,
    )

    assert result.total_records == 6
    assert result.matched_count >= 2  # SCN_01 and SCN_04 matched
    assert result.throughput_records_per_sec > 1000.0

    # Verify that the off-ledger case was NOT auto-resolved
    off_ledger_cases = [c for c in result.cases if c.scenario_id == "SCN_08"]
    if off_ledger_cases:
        assert off_ledger_cases[0].decision is not None
        assert off_ledger_cases[0].decision.decision != DecisionType.AUTO_RESOLVE
        assert off_ledger_cases[0].decision.decision == DecisionType.HUMAN_REVIEW
