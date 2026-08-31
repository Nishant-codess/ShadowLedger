"""Batch ingestion and reconciliation endpoints."""

import random
import time
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas.api_models import BatchSummaryResponse, ProcessBatchRequest
from app.data.normalize import normalize_batch
from app.domain.models import BatchMetadata
from app.domain.scenarios import SCENARIOS
from app.engine.reconciler import DeterministicReconciler
from app.metrics.evaluator import compute_metrics
from app.persistence.case_repo import CaseRepository
from app.persistence.database import DatabaseManager
from app.persistence.observation_repo import ObservationRepository

router = APIRouter(prefix="/api/batches", tags=["Batches"])

# Global Database Singleton for in-app state
_db_manager = DatabaseManager()
_obs_repo = ObservationRepository(_db_manager)
_case_repo = CaseRepository(_db_manager)
_reconciler = DeterministicReconciler()


def get_db() -> DatabaseManager:
    return _db_manager


def get_obs_repo() -> ObservationRepository:
    return _obs_repo


def get_case_repo() -> CaseRepository:
    return _case_repo


def generate_synthetic_records(seed: int, target_rows: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Generate multi-source records according to standard scenario distribution."""
    rng = random.Random(seed)
    base_time = datetime(2026, 8, 31, 9, 0, 0, tzinfo=UTC)

    # Scenario distribution weights
    scenario_weights = [
        ("SCN_01", 50),  # 50% Clean match
        ("SCN_02", 10),  # 10% Partial refund
        ("SCN_03", 10),  # 10% Fee adjustment
        ("SCN_04", 5),   # 5% Kirana chocolate change
        ("SCN_05", 5),   # 5% Store credit
        ("SCN_06", 5),   # 5% Next-day timing
        ("SCN_07", 5),   # 5% Duplicate
        ("SCN_08", 3),   # 3% Ride digital trace
        ("SCN_09", 2),   # 2% Ride cash invisible
        ("SCN_10", 2),   # 2% Recurring micro pattern
        ("SCN_11", 1),   # 1% Batch adjustment
        ("SCN_12", 2),   # 2% Adversarial near match
    ]

    scenario_pool = [s for s, w in scenario_weights for _ in range(w)]
    observed_all: list[dict[str, Any]] = []
    truth_all: list[dict[str, Any]] = []

    idx = 0
    while len(observed_all) < target_rows:
        scn_id = rng.choice(scenario_pool)
        defn = SCENARIOS[scn_id]
        obs_list, truth = defn.generator(rng, idx, base_time + (idx * datetime.resolution * 1000))
        observed_all.extend(obs_list)
        truth_all.append(truth)
        idx += 1

    return observed_all[:target_rows], truth_all


@router.post("/process", response_model=BatchSummaryResponse)
def process_batch(
    req: ProcessBatchRequest,
    obs_repo: ObservationRepository = Depends(get_obs_repo),
    case_repo: CaseRepository = Depends(get_case_repo),
) -> BatchSummaryResponse:
    """Ingest, normalize, and execute deterministic baseline reconciliation."""
    t0 = time.perf_counter()
    batch_id = req.batch_id or f"batch_{uuid4().hex[:8]}"

    ground_truth = None
    if req.records:
        raw_records = req.records
    else:
        seed = req.seed if req.seed is not None else 42
        raw_records, ground_truth = generate_synthetic_records(seed=seed, target_rows=req.rows)

    # 1. Normalize
    observations, inventory_moves = normalize_batch(raw_records, batch_id=batch_id)

    # 2. Persist raw records
    obs_repo.save_observations(observations)
    if inventory_moves:
        obs_repo.save_inventory_moves(inventory_moves)

    # 3. Deterministic Reconciliation
    result = _reconciler.reconcile_batch(
        observations=observations,
        inventory_moves=inventory_moves,
        batch_id=batch_id,
    )

    # 4. Save Discrepancy Cases
    case_repo.save_cases(result.cases)

    # 5. Compute Metrics & Save Batch Metadata
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    metrics = compute_metrics(result=result, processing_time_ms=elapsed_ms, ground_truth_list=ground_truth)

    meta = BatchMetadata(
        batch_id=batch_id,
        seed=req.seed,
        record_count=result.total_observations,
        matched_count=result.matched_count,
        exception_count=result.exception_count,
        resolved_count=result.matched_count,
        review_count=0,
        unresolved_count=result.exception_count,
        total_volume_inr=result.total_volume_inr,
        explained_volume_inr=result.explained_volume_inr,
        unexplained_volume_inr=result.unexplained_volume_inr,
        processing_time_ms=elapsed_ms,
    )
    case_repo.save_batch_metadata(meta)

    return BatchSummaryResponse(
        batch_id=batch_id,
        record_count=result.total_observations,
        matched_count=result.matched_count,
        exception_count=result.exception_count,
        match_rate=result.match_rate,
        throughput_records_per_sec=metrics.throughput_records_per_sec,
        total_volume_inr=float(result.total_volume_inr),
        explained_volume_inr=float(result.explained_volume_inr),
        unexplained_volume_inr=float(result.unexplained_volume_inr),
        processing_time_ms=round(elapsed_ms, 2),
        reason_code_breakdown=metrics.reason_code_breakdown,
    )


@router.get("", response_model=list[BatchSummaryResponse])
def list_batches(case_repo: CaseRepository = Depends(get_case_repo)) -> list[BatchSummaryResponse]:
    """Retrieve history of all processed batches."""
    batches = case_repo.list_all_batches()
    return [
        BatchSummaryResponse(
            batch_id=b.batch_id,
            record_count=b.record_count,
            matched_count=b.matched_count,
            exception_count=b.exception_count,
            match_rate=round((b.matched_count / b.record_count * 100.0), 2) if b.record_count > 0 else 0.0,
            throughput_records_per_sec=(
                round(b.record_count / (b.processing_time_ms / 1000.0), 1)
                if b.processing_time_ms > 0
                else 0.0
            ),
            total_volume_inr=float(b.total_volume_inr),
            explained_volume_inr=float(b.explained_volume_inr),
            unexplained_volume_inr=float(b.unexplained_volume_inr),
            processing_time_ms=b.processing_time_ms,
        )
        for b in batches
    ]


@router.get("/{batch_id}", response_model=BatchSummaryResponse)
def get_batch(batch_id: str, case_repo: CaseRepository = Depends(get_case_repo)) -> BatchSummaryResponse:
    """Fetch details of a single processed batch."""
    b = case_repo.get_batch_metadata(batch_id)
    if not b:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")

    return BatchSummaryResponse(
        batch_id=b.batch_id,
        record_count=b.record_count,
        matched_count=b.matched_count,
        exception_count=b.exception_count,
        match_rate=round((b.matched_count / b.record_count * 100.0), 2) if b.record_count > 0 else 0.0,
        throughput_records_per_sec=(
            round(b.record_count / (b.processing_time_ms / 1000.0), 1)
            if b.processing_time_ms > 0
            else 0.0
        ),
        total_volume_inr=float(b.total_volume_inr),
        explained_volume_inr=float(b.explained_volume_inr),
        unexplained_volume_inr=float(b.unexplained_volume_inr),
        processing_time_ms=b.processing_time_ms,
    )
