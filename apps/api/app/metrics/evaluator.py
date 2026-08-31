"""Reconciliation and benchmark evaluation metrics calculator."""

from dataclasses import dataclass, field
from typing import Any

from app.engine.reconciler import ReconciliationResult


@dataclass
class EvaluationMetrics:
    """Rigorous performance and accuracy metrics calculated over a batch."""

    batch_id: str
    record_count: int
    matched_count: int
    exception_count: int
    match_rate: float
    throughput_records_per_sec: float
    total_volume_inr: float
    explained_volume_inr: float
    unexplained_volume_inr: float
    processing_time_ms: float
    reason_code_breakdown: dict[str, int] = field(default_factory=dict)
    ground_truth_precision: float | None = None
    ground_truth_recall: float | None = None
    unsafe_resolutions_count: int = 0
    scenario_breakdown: dict[str, dict[str, Any]] = field(default_factory=dict)


def compute_metrics(
    result: ReconciliationResult,
    processing_time_ms: float,
    ground_truth_list: list[dict[str, Any]] | None = None,
) -> EvaluationMetrics:
    """Compute baseline metrics for deterministic reconciliation."""
    throughput = (
        (result.total_observations / (processing_time_ms / 1000.0))
        if processing_time_ms > 0
        else 0.0
    )

    reason_counts: dict[str, int] = {}
    for mg in result.match_groups:
        reason_counts[mg.reason_code] = reason_counts.get(mg.reason_code, 0) + len(mg.observations)

    precision = None
    recall = None
    unsafe_count = 0
    scenario_stats: dict[str, dict[str, Any]] = {}

    # If hidden ground-truth log is provided (benchmark mode only)
    if ground_truth_list:
        truth_by_key: dict[str, dict[str, Any]] = {}
        for t in ground_truth_list:
            for k in ("order_id", "ride_id", "payment_id", "order_a", "order_b"):
                if t.get(k):
                    truth_by_key[str(t[k])] = t

        true_positives = 0
        false_positives = 0
        total_reconcilable = 0

        # Calculate total truly reconcilable from truth
        for t in ground_truth_list:
            if t.get("is_reconciled", False):
                total_reconcilable += 1

        for mg in result.match_groups:
            # Find matching truth by group key or observation entity ids
            truth = truth_by_key.get(mg.group_key)
            if not truth:
                for o in mg.observations:
                    for v in o.entity_ids.values():
                        if str(v) in truth_by_key:
                            truth = truth_by_key[str(v)]
                            break
                    if truth:
                        break

            if not truth:
                continue

            scn_id = truth.get("scenario_id", "UNKNOWN")
            if scn_id not in scenario_stats:
                scenario_stats[scn_id] = {"total": 0, "matched": 0, "exceptions": 0}
            scenario_stats[scn_id]["total"] += 1

            is_truly_reconciled = truth.get("is_reconciled", False)

            if mg.status.value == "matched":
                scenario_stats[scn_id]["matched"] += 1
                if is_truly_reconciled:
                    true_positives += 1
                else:
                    false_positives += 1
                    unsafe_count += 1
            else:
                scenario_stats[scn_id]["exceptions"] += 1

        if (true_positives + false_positives) > 0:
            precision = round(true_positives / (true_positives + false_positives) * 100.0, 2)
        if total_reconcilable > 0:
            recall = round(true_positives / total_reconcilable * 100.0, 2)

    return EvaluationMetrics(
        batch_id=result.batch_id,
        record_count=result.total_observations,
        matched_count=result.matched_count,
        exception_count=result.exception_count,
        match_rate=result.match_rate,
        throughput_records_per_sec=round(throughput, 1),
        total_volume_inr=float(result.total_volume_inr),
        explained_volume_inr=float(result.explained_volume_inr),
        unexplained_volume_inr=float(result.unexplained_volume_inr),
        processing_time_ms=round(processing_time_ms, 2),
        reason_code_breakdown=reason_counts,
        ground_truth_precision=precision,
        ground_truth_recall=recall,
        unsafe_resolutions_count=unsafe_count,
        scenario_breakdown=scenario_stats,
    )
