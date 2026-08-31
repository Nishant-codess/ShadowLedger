"""Case inquiry and investigation endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.routes.batches import get_case_repo, get_obs_repo
from app.api.schemas.api_models import CaseDetailResponse
from app.persistence.case_repo import CaseRepository
from app.persistence.observation_repo import ObservationRepository

router = APIRouter(prefix="/api/cases", tags=["Cases"])


@router.get("", response_model=list[CaseDetailResponse])
def list_cases(
    batch_id: str | None = None,
    case_repo: CaseRepository = Depends(get_case_repo),
) -> list[CaseDetailResponse]:
    """Retrieve all discrepancy cases, optionally filtered by batch."""
    if not batch_id:
        batches = case_repo.list_all_batches()
        if not batches:
            return []
        batch_id = batches[0].batch_id

    cases = case_repo.get_cases_by_batch(batch_id)
    return [
        CaseDetailResponse(
            case_id=c.case_id,
            batch_id=c.batch_id,
            observation_ids=c.observation_ids,
            residual_amount=float(c.residual_amount),
            financial_impact=float(c.financial_impact),
            scenario_id=c.scenario_id,
            status=c.status,
            decision=c.decision.model_dump(mode="json") if c.decision else None,
        )
        for c in cases
    ]


@router.get("/{case_id}", response_model=CaseDetailResponse)
def get_case(
    case_id: str,
    case_repo: CaseRepository = Depends(get_case_repo),
    obs_repo: ObservationRepository = Depends(get_obs_repo),
) -> CaseDetailResponse:
    """Fetch complete detail for a specific case including connected observations."""
    batches = case_repo.list_all_batches()
    for b in batches:
        cases = case_repo.get_cases_by_batch(b.batch_id)
        for c in cases:
            if c.case_id == case_id:
                # Fetch connected observations
                all_obs = obs_repo.get_by_batch(c.batch_id)
                connected = [o.model_dump(mode="json") for o in all_obs if o.observation_id in c.observation_ids]

                return CaseDetailResponse(
                    case_id=c.case_id,
                    batch_id=c.batch_id,
                    observation_ids=c.observation_ids,
                    residual_amount=float(c.residual_amount),
                    financial_impact=float(c.financial_impact),
                    scenario_id=c.scenario_id,
                    status=c.status,
                    decision=c.decision.model_dump(mode="json") if c.decision else None,
                    observations=connected,
                )

    raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
