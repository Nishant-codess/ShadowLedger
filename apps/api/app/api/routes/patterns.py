"""Pattern cluster discovery endpoints."""

from fastapi import APIRouter, Depends

from app.api.routes.batches import get_case_repo
from app.api.schemas.api_models import PatternClusterResponse
from app.persistence.case_repo import CaseRepository

router = APIRouter(prefix="/api/patterns", tags=["Patterns"])


@router.get("", response_model=list[PatternClusterResponse])
def list_patterns(
    batch_id: str | None = None,
    case_repo: CaseRepository = Depends(get_case_repo),
) -> list[PatternClusterResponse]:
    """Retrieve recurring structural pattern clusters discovered across cases."""
    if not batch_id:
        batches = case_repo.list_all_batches()
        if not batches:
            return []
        batch_id = batches[0].batch_id

    clusters = case_repo.get_pattern_clusters_by_batch(batch_id)
    return [
        PatternClusterResponse(
            cluster_id=c.cluster_id,
            batch_id=c.batch_id,
            case_ids=c.case_ids,
            pattern_signature=c.pattern_signature,
            exception_count=c.exception_count,
            total_value_at_risk=float(c.total_value_at_risk),
            likely_common_cause=c.likely_common_cause,
            evidence_strength=c.evidence_strength,
            created_at=c.created_at,
        )
        for c in clusters
    ]
