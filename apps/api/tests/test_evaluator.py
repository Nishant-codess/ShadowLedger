"""Unit tests for the evaluator and metrics calculator."""

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.enums import EventType, ReconciliationStatus
from app.domain.models import Observation
from app.engine.reconciler import MatchGroup, ReconciliationResult
from app.metrics.evaluator import compute_metrics


def test_compute_metrics_baseline():
    """Verify operational metrics calculation."""
    t0 = datetime.now(UTC)
    obs = [
        Observation(
            source_system="pos",
            source_record_id="p1",
            event_type=EventType.PAYMENT,
            amount=Decimal("100.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-1"},
        ),
        Observation(
            source_system="bank",
            source_record_id="b1",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("100.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-1"},
        ),
    ]

    mg = MatchGroup(
        group_key="ORD-1",
        status=ReconciliationStatus.MATCHED,
        reason_code="EXACT_ID_AND_AMOUNT_MATCH",
        observations=obs,
        total_volume=Decimal("200.00"),
    )

    rec_result = ReconciliationResult(
        batch_id="batch_eval_1",
        total_observations=2,
        matched_count=2,
        exception_count=0,
        match_rate=100.0,
        total_volume_inr=Decimal("200.00"),
        explained_volume_inr=Decimal("200.00"),
        unexplained_volume_inr=Decimal("0.00"),
        match_groups=[mg],
        cases=[],
        duplicate_observation_ids=[],
    )

    truth = [{"order_id": "ORD-1", "is_reconciled": True, "scenario_id": "SCN_01"}]

    metrics = compute_metrics(result=rec_result, processing_time_ms=10.0, ground_truth_list=truth)

    assert metrics.match_rate == 100.0
    assert metrics.ground_truth_precision == 100.0
    assert metrics.ground_truth_recall == 100.0
    assert metrics.unsafe_resolutions_count == 0
    assert metrics.throughput_records_per_sec == 200.0
    assert metrics.reason_code_breakdown["EXACT_ID_AND_AMOUNT_MATCH"] == 2
