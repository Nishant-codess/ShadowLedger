"""Global and latest batch metrics endpoints."""

from typing import Any

from fastapi import APIRouter, Depends

from app.api.routes.batches import get_case_repo
from app.persistence.case_repo import CaseRepository

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])


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
        "match_rate": match_rate,
        "throughput_records_per_sec": throughput,
        "total_volume_inr": float(latest.total_volume_inr),
        "explained_volume_inr": float(latest.explained_volume_inr),
        "unexplained_volume_inr": float(latest.unexplained_volume_inr),
        "processing_time_ms": round(latest.processing_time_ms, 2),
        "created_at": latest.created_at.isoformat(),
    }
