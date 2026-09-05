"""Value-Flow Reconstruction & Shadow Ledger Engine.

Coordinates the end-to-end 7-stage pipeline:
Stage 1: Deterministic Baseline Reconciliation
Stage 2: Exception Mining (Residuals & Anomaly Clues)
Stage 3: Case-Local Value-Flow Graph Construction (NetworkX)
Stage 4: Latent-Event Hypothesis Generation
Stage 5: Multi-Dimensional Evidence Scoring (Separated from Risk)
Stage 6: Decision Risk Gate (4 Independent Dimensions)
Stage 7: Cross-Case Pattern Engine (P0)
"""

import time
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.domain.enums import DecisionType, ReconciliationStatus
from app.domain.models import Case, Event, InventoryMove, Observation, PatternCluster
from app.engine.decision_gate import DecisionRiskGate
from app.engine.evidence_scorer import EvidenceScorer
from app.engine.graph_builder import ValueFlowGraphBuilder
from app.engine.hypothesis_engine import LatentHypothesisEngine
from app.engine.miner import ExceptionMiner
from app.engine.pattern_engine import CrossCasePatternEngine
from app.engine.reconciler import DeterministicReconciler, MatchGroup
from app.engine.shadow_ledger import ShadowLedgerManager


@dataclass
class ShadowReconciliationResult:
    """Complete results from the Value-Flow Reconstruction Engine."""

    batch_id: str
    total_records: int
    matched_count: int
    exception_count: int
    auto_resolved_count: int
    human_review_count: int
    unresolved_count: int

    total_volume_inr: Decimal
    explained_volume_inr: Decimal
    unexplained_volume_inr: Decimal

    baseline_match_rate: float
    enhanced_resolution_rate: float

    processing_time_ms: float
    throughput_records_per_sec: float

    cases: list[Case] = field(default_factory=list)
    shadow_events: list[Event] = field(default_factory=list)
    pattern_clusters: list[PatternCluster] = field(default_factory=list)
    baseline_match_groups: list[MatchGroup] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)


class ValueFlowReconstructionEngine:
    """Master engine orchestrating value-flow reconstruction and shadow ledger reasoning."""

    def __init__(
        self,
        auto_resolve_threshold: float = 0.82,
        review_threshold: float = 0.50,
        materiality_limit: Decimal = Decimal("10000.00"),
    ) -> None:
        self.reconciler = DeterministicReconciler()
        self.miner = ExceptionMiner()
        self.graph_builder = ValueFlowGraphBuilder()
        self.hypothesis_engine = LatentHypothesisEngine()
        self.scorer = EvidenceScorer()
        self.decision_gate = DecisionRiskGate(
            auto_resolve_threshold=auto_resolve_threshold,
            review_threshold=review_threshold,
            materiality_limit=materiality_limit,
        )
        self.shadow_ledger = ShadowLedgerManager()
        self.pattern_engine = CrossCasePatternEngine()

    def process_batch(
        self,
        batch_id: str,
        observations: list[Observation],
        inventory_moves: list[InventoryMove] | None = None,
    ) -> ShadowReconciliationResult:
        """Execute full 7-stage Value-Flow Reconstruction pipeline."""
        start_time = time.perf_counter()

        inv_moves = inventory_moves or []
        total_records = len(observations)
        total_volume = sum((o.amount for o in observations), Decimal("0.00"))

        if not observations:
            return ShadowReconciliationResult(
                batch_id=batch_id,
                total_records=0,
                matched_count=0,
                exception_count=0,
                auto_resolved_count=0,
                human_review_count=0,
                unresolved_count=0,
                total_volume_inr=Decimal("0.00"),
                explained_volume_inr=Decimal("0.00"),
                unexplained_volume_inr=Decimal("0.00"),
                baseline_match_rate=0.0,
                enhanced_resolution_rate=0.0,
                processing_time_ms=0.0,
                throughput_records_per_sec=0.0,
            )

        # -------------------------------------------------------------
        # Stage 1: Deterministic Baseline Reconciliation
        # -------------------------------------------------------------
        baseline_result = self.reconciler.reconcile_batch(observations, inv_moves)
        baseline_matches = baseline_result.match_groups
        baseline_cases = baseline_result.cases

        # Map observations by ID for quick lookup
        obs_map = {o.observation_id: o for o in observations}
        inv_map: dict[str, list[InventoryMove]] = {}
        for inv in inv_moves:
            inv_map.setdefault(inv.observation_id, []).append(inv)

        # -------------------------------------------------------------
        # Stages 2 - 6: Latent-Event Reconstruction for Exception Cases
        # -------------------------------------------------------------
        processed_cases: list[Case] = []
        all_shadow_events: list[Event] = []

        auto_resolved_count = 0
        human_review_count = 0
        unresolved_count = 0

        # Account for baseline exact matches as already auto-resolved
        explained_volume = sum(
            (mg.total_volume for mg in baseline_matches if mg.status == ReconciliationStatus.MATCHED),
            Decimal("0.00"),
        )

        for base_case in baseline_cases:
            case_obs = [obs_map[oid] for oid in base_case.observation_ids if oid in obs_map]
            case_inv: list[InventoryMove] = []
            for oid in base_case.observation_ids:
                case_inv.extend(inv_map.get(oid, []))

            # Stage 2: Exception Mining
            case = self.miner.mine_case(
                batch_id=batch_id,
                observations=case_obs,
                inventory_moves=case_inv,
                case_id=base_case.case_id,
            )

            # Stage 4: Latent Hypothesis Generation
            raw_hypotheses = self.hypothesis_engine.generate_hypotheses(
                case_id=case.case_id,
                observations=case_obs,
                inventory_moves=case_inv,
            )

            # Stage 5: Multi-Dimensional Evidence Scoring
            scored_hypotheses: list[Any] = []
            for hyp in raw_hypotheses:
                scored_hyp = self.scorer.score_hypothesis(hyp, case_obs, case_inv)
                scored_hypotheses.append(scored_hyp)

            case.hypotheses = scored_hypotheses

            # Stage 6: Decision Risk Gate
            decision = self.decision_gate.evaluate_decision(case.case_id, scored_hypotheses)
            case.decision = decision

            # Determine Winning Hypothesis
            winning_hyp = None
            if decision.winning_hypothesis_id:
                for h in scored_hypotheses:
                    if h.hypothesis_id == decision.winning_hypothesis_id:
                        winning_hyp = h
                        break

            # Stage 3: Case-Local NetworkX Value-Flow Graph
            nx_graph = self.graph_builder.build_case_graph(
                observations=case_obs,
                inventory_moves=case_inv,
                hypotheses=scored_hypotheses,
                winning_hypothesis=winning_hyp,
            )
            case.graph_json = self.graph_builder.serialize_graph(nx_graph)

            # Materialize Shadow Ledger Events
            shadow_events = self.shadow_ledger.create_shadow_events_for_case(
                case=case,
                winning_hypothesis=winning_hyp,
                decision=decision,
            )
            case.shadow_events = shadow_events
            all_shadow_events.extend(shadow_events)

            # Track outcome counts and volume
            if decision.decision == DecisionType.AUTO_RESOLVE:
                auto_resolved_count += 1
                case_volume = sum((o.amount for o in case_obs), Decimal("0.00"))
                explained_volume += case_volume
                case.status = "auto_resolved"
            elif decision.decision == DecisionType.HUMAN_REVIEW:
                human_review_count += 1
                case.status = "human_review"
            else:
                unresolved_count += 1
                case.status = "unresolved"

            processed_cases.append(case)

        # -------------------------------------------------------------
        # Stage 7: Cross-Case Pattern Engine (P0)
        # -------------------------------------------------------------
        pattern_clusters = self.pattern_engine.discover_patterns(batch_id, processed_cases)

        elapsed_s = time.perf_counter() - start_time
        elapsed_ms = elapsed_s * 1000.0
        throughput = total_records / elapsed_s if elapsed_s > 0 else 0.0

        # Metrics computation
        baseline_match_count = baseline_result.matched_count
        total_exceptions = baseline_result.exception_count

        # Total resolved cases = baseline exact matches + shadow ledger auto-resolved
        total_resolved_obs = baseline_match_count + sum(
            len(c.observation_ids) for c in processed_cases if c.decision and c.decision.decision == DecisionType.AUTO_RESOLVE
        )

        baseline_match_rate = (baseline_match_count / total_records) * 100.0 if total_records > 0 else 0.0
        enhanced_resolution_rate = (total_resolved_obs / total_records) * 100.0 if total_records > 0 else 0.0

        unexplained_volume = max(Decimal("0.00"), total_volume - explained_volume)

        return ShadowReconciliationResult(
            batch_id=batch_id,
            total_records=total_records,
            matched_count=baseline_match_count,
            exception_count=total_exceptions,
            auto_resolved_count=auto_resolved_count,
            human_review_count=human_review_count,
            unresolved_count=unresolved_count,
            total_volume_inr=total_volume,
            explained_volume_inr=explained_volume,
            unexplained_volume_inr=unexplained_volume,
            baseline_match_rate=round(baseline_match_rate, 2),
            enhanced_resolution_rate=round(enhanced_resolution_rate, 2),
            processing_time_ms=round(elapsed_ms, 2),
            throughput_records_per_sec=round(throughput, 1),
            cases=processed_cases,
            shadow_events=all_shadow_events,
            pattern_clusters=pattern_clusters,
            baseline_match_groups=baseline_matches,
            observations=observations,
        )
