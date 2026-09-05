"""Metrics and Benchmark API routes."""

import json
import sys
import threading
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends

# Ensure repo root is on sys.path for scripts import
repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from scripts.run_benchmark import run_benchmark  # noqa: E402

from app.api.routes.batches import get_case_repo  # noqa: E402
from app.persistence.case_repo import CaseRepository  # noqa: E402

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])

_benchmark_lock = threading.Lock()


@router.get("")
def get_latest_metrics(case_repo: CaseRepository = Depends(get_case_repo)) -> dict[str, Any]:
    """Retrieve performance metrics from the most recent batch run."""
    batches = case_repo.list_all_batches()
    if not batches:
        return {
            "status": "no_batches_processed",
            "record_count": 0,
            "match_rate": 0.0,
            "throughput_records_per_sec": 0.0,
            "total_volume_inr": 0.0,
            "explained_volume_inr": 0.0,
            "unexplained_volume_inr": 0.0,
            "exception_count": 0,
        }

    latest = batches[0]
    match_rate = round((latest.matched_count / latest.record_count * 100.0), 2) if latest.record_count > 0 else 0.0
    throughput = (
        round(latest.record_count / (latest.processing_time_ms / 1000.0), 1)
        if latest.processing_time_ms > 0
        else 0.0
    )

    return {
        "status": "ready",
        "batch_id": latest.batch_id,
        "record_count": latest.record_count,
        "matched_count": latest.matched_count,
        "exception_count": latest.exception_count,
        "auto_resolved_count": latest.resolved_count,
        "human_review_count": latest.review_count,
        "unresolved_count": latest.unresolved_count,
        "match_rate": match_rate,
        "throughput_records_per_sec": throughput,
        "total_volume_inr": float(latest.total_volume_inr),
        "explained_volume_inr": float(latest.explained_volume_inr),
        "unexplained_volume_inr": float(latest.unexplained_volume_inr),
        "processing_time_ms": round(latest.processing_time_ms, 2),
        "created_at": latest.created_at.isoformat(),
    }


@router.get("/benchmark")
def get_benchmark_results(
    rows: int = 10000,
    seed: int = 42,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Retrieve formal benchmark metrics comparing Baseline vs ShadowLedger with thread safety."""
    results_path = repo_root / "data" / "benchmark_results.json"
    expected_batch = f"benchmark_s{seed}_r{rows}"

    def check_cache() -> dict[str, Any] | None:
        if results_path.exists() and not force_refresh:
            try:
                with open(results_path, encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("records") == rows and (
                        data.get("batch_id") == expected_batch or data.get("seed") == seed or rows == 10000
                    ):
                        return data
            except Exception:
                return None
        return None

    # Fast path: check cache before acquiring lock
    cached = check_cache()
    if cached is not None:
        return cached

    # Synchronized execution for concurrent benchmark requests
    with _benchmark_lock:
        # Re-check cache after lock acquisition in case another thread just completed
        cached = check_cache()
        if cached is not None:
            return cached

        # Run benchmark on-demand to produce live, dynamic metrics
        return run_benchmark(rows=rows, seed=seed)
