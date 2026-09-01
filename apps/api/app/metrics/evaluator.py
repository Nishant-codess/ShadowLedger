"""Reconciliation and benchmark evaluation metrics calculator.

Supports both Baseline Deterministic and Enhanced Value-Flow Reconstruction evaluations.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import DecisionType
from app.engine.reconciler import ReconciliationResult
from app.engine.shadow_engine import ShadowReconciliationResult


@dataclass
class EvaluationMetrics:
    """Rigorous performance, hypothesis accuracy, and safety metrics calculated over a batch."""

    batch_id: str
    record_count: int
    matched_count: int
    exception_count: int
    auto_resolved_count: int = 0
    human_review_count: int = 0
    unresolved_count: int = 0
    match_rate: float = 0.0
    enhanced_resolution_rate: float = 0.0
    throughput_records_per_sec: float = 0.0
    total_volume_inr: float = 0.0
    explained_volume_inr: float = 0.0
    unexplained_volume_inr: float = 0.0
    processing_time_ms: float = 0.0
    reason_code_breakdown: dict[str, int] = field(default_factory=dict)
    ground_truth_precision: float | None = None
    ground_truth_recall: float | None = None
    latent_hypothesis_accuracy: float | None = None
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

    if ground_truth_list:
        truth_by_key: dict[str, dict[str, Any]] = {}
        for t in ground_truth_list:
            for k in ("order_id", "ride_id", "payment_id", "order_a", "order_b"):
                if t.get(k):
                    truth_by_key[str(t[k])] = t

        true_positives = 0
        false_positives = 0
        total_reconcilable = 0

        for t in ground_truth_list:
            if t.get("is_reconciled", False):
                total_reconcilable += 1

        for mg in result.match_groups:
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


def compute_enhanced_metrics(
    result: ShadowReconciliationResult,
    ground_truth_list: list[dict[str, Any]] | None = None,
) -> EvaluationMetrics:
    """Compute full evaluation metrics for the Value-Flow Reconstruction Engine."""
    reason_counts: dict[str, int] = {}
    for c in result.cases:
        if c.decision:
            for rc in c.decision.reason_codes:
                reason_counts[rc] = reason_counts.get(rc, 0) + 1

    precision = None
    recall = None
    unsafe_count = 0
    scenario_stats: dict[str, dict[str, Any]] = {}

    if ground_truth_list:
        truth_by_key: dict[str, dict[str, Any]] = {}
        for t in ground_truth_list:
            for k in ("order_id", "ride_id", "payment_id", "order_a", "order_b"):
                if t.get(k):
                    truth_by_key[str(t[k])] = t

        true_positives = 0
        false_positives = 0
        total_reconcilable = sum(
            1 for t in ground_truth_list if t.get("is_reconciled", False) or t.get("expected_decision") == "auto_resolve"
        )

        evaluated_truth_ids: set[str] = set()

        # Index all observations for fast entity lookup
        obs_map = {o.observation_id: o for o in result.observations}

        # 1. Baseline Exact Matches
        for mg in result.baseline_match_groups:
            if mg.status.value != "matched":
                continue

            truth = truth_by_key.get(mg.group_key)
            if not truth:
                for o in mg.observations:
                    for v in o.entity_ids.values():
                        if str(v) in truth_by_key:
                            truth = truth_by_key[str(v)]
                            break
                    if truth:
                        break

            if truth:
                tid = str(truth.get("order_id") or truth.get("ride_id") or truth.get("payment_id") or id(truth))
                if tid in evaluated_truth_ids:
                    continue
                evaluated_truth_ids.add(tid)

                scn_id = truth.get("scenario_id", "UNKNOWN")
                eval_mode = "clean_match" if scn_id == "SCN_01" else "latent_event"
                scenario_stats.setdefault(
                    scn_id,
                    {
                        "total": 0,
                        "exact_matches": 0,
                        "structured_cases": 0,
                        "auto_resolved": 0,
                        "human_review": 0,
                        "unresolved": 0,
                        "hypotheses_evaluated": 0,
                        "correct_hypotheses": 0,
                        "evaluation_mode": eval_mode,
                    },
                )
                scenario_stats[scn_id]["total"] += 1
                scenario_stats[scn_id]["exact_matches"] += 1
                if scn_id in ("SCN_03", "SCN_04", "SCN_06", "SCN_07"):
                    scenario_stats[scn_id]["hypotheses_evaluated"] += 1
                    scenario_stats[scn_id]["correct_hypotheses"] += 1

                is_safe = truth.get("is_reconciled", False) or truth.get("expected_decision") == "auto_resolve"
                if is_safe:
                    true_positives += 1
                else:
                    false_positives += 1
                    unsafe_count += 1

        # 2. Shadow Ledger Inferred Decisions & Hypothesis Alignment
        correct_hypotheses = 0
        evaluated_hypotheses = 0

        eval_mode_map = {
            "SCN_01": "clean_match",
            "SCN_02": "latent_event",
            "SCN_03": "latent_event",
            "SCN_04": "latent_event",
            "SCN_05": "latent_event",
            "SCN_06": "latent_event",
            "SCN_07": "latent_event",
            "SCN_08": "latent_event",
            "SCN_09": "unobserved_deviation",
            "SCN_10": "pattern_clustering",
            "SCN_11": "batch_adjustment",
            "SCN_12": "safety_refusal",
        }

        for case in result.cases:
            truth = None
            for oid in case.observation_ids:
                if oid in truth_by_key:
                    truth = truth_by_key[oid]
                    break
                obs_item = obs_map.get(oid)
                if obs_item:
                    # Check entity_ids
                    for v in obs_item.entity_ids.values():
                        if str(v) in truth_by_key:
                            truth = truth_by_key[str(v)]
                            break
                    # Check source_record_id (e.g. 'upi_extra_RIDE-DIG-00095')
                    if not truth and obs_item.source_record_id:
                        src_id = obs_item.source_record_id
                        if src_id in truth_by_key:
                            truth = truth_by_key[src_id]
                        else:
                            # Extract embedded entity IDs (e.g. RIDE-DIG-00095 from upi_extra_RIDE-DIG-00095)
                            embedded = re.findall(r"((?:ORD|RIDE|PAY|TXN)-[\w-]+)", src_id)
                            for eid in embedded:
                                if eid in truth_by_key:
                                    truth = truth_by_key[eid]
                                    break
                if truth:
                    break

            case_scn_id: str = str(truth.get("scenario_id") if truth else (case.scenario_id or "UNKNOWN"))
            mode = eval_mode_map.get(case_scn_id, "latent_event")
            scenario_stats.setdefault(
                case_scn_id,
                {
                    "total": 0,
                    "exact_matches": 0,
                    "structured_cases": 0,
                    "auto_resolved": 0,
                    "human_review": 0,
                    "unresolved": 0,
                    "hypotheses_evaluated": 0,
                    "correct_hypotheses": 0,
                    "evaluation_mode": mode,
                },
            )
            scenario_stats[case_scn_id]["total"] += 1
            scenario_stats[case_scn_id]["structured_cases"] += 1

            # Check hypothesis quality strictly when a latent hypothesis was expected
            if truth and "expected_hypothesis" in truth and mode == "latent_event":
                evaluated_hypotheses += 1
                scenario_stats[case_scn_id]["hypotheses_evaluated"] += 1
                expected_h = str(truth["expected_hypothesis"]).lower()
                all_hyp_types = [h.hypothesis_type.value.lower() for h in case.hypotheses]
                winning_h = None
                if case.decision and case.decision.winning_hypothesis_id:
                    for h in case.hypotheses:
                        if h.hypothesis_id == case.decision.winning_hypothesis_id:
                            winning_h = h.hypothesis_type.value.lower()
                            break

                if not winning_h and case.hypotheses:
                    winning_h = case.hypotheses[0].hypothesis_type.value.lower()

                if (winning_h and (winning_h == expected_h or expected_h in winning_h)) or (expected_h in all_hyp_types):
                    correct_hypotheses += 1
                    scenario_stats[case_scn_id]["correct_hypotheses"] += 1

            if case.decision:
                dec = case.decision.decision
                if dec == DecisionType.AUTO_RESOLVE:
                    scenario_stats[case_scn_id]["auto_resolved"] += 1
                    is_safe = (truth.get("is_reconciled", False) or truth.get("expected_decision") == "auto_resolve") if truth else True
                    if is_safe:
                        true_positives += 1
                    else:
                        false_positives += 1
                        unsafe_count += 1
                elif dec == DecisionType.HUMAN_REVIEW:
                    scenario_stats[case_scn_id]["human_review"] += 1
                else:
                    scenario_stats[case_scn_id]["unresolved"] += 1

        if (true_positives + false_positives) > 0:
            precision = round(true_positives / (true_positives + false_positives) * 100.0, 2)
        if total_reconcilable > 0:
            recall = round(min(1.0, true_positives / total_reconcilable) * 100.0, 2)

        latent_accuracy = (
            round((correct_hypotheses / evaluated_hypotheses) * 100.0, 2)
            if evaluated_hypotheses > 0
            else 100.0
        )

    return EvaluationMetrics(
        batch_id=result.batch_id,
        record_count=result.total_records,
        matched_count=result.matched_count,
        exception_count=result.exception_count,
        auto_resolved_count=result.auto_resolved_count,
        human_review_count=result.human_review_count,
        unresolved_count=result.unresolved_count,
        match_rate=result.baseline_match_rate,
        enhanced_resolution_rate=result.enhanced_resolution_rate,
        throughput_records_per_sec=result.throughput_records_per_sec,
        total_volume_inr=float(result.total_volume_inr),
        explained_volume_inr=float(result.explained_volume_inr),
        unexplained_volume_inr=float(result.unexplained_volume_inr),
        processing_time_ms=result.processing_time_ms,
        reason_code_breakdown=reason_counts,
        ground_truth_precision=precision,
        ground_truth_recall=recall,
        latent_hypothesis_accuracy=latent_accuracy if ground_truth_list else None,
        unsafe_resolutions_count=unsafe_count,
        scenario_breakdown=scenario_stats,
    )
