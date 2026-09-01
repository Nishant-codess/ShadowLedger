"""Hero demo endpoints for 1-click deterministic showcase."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.routes.batches import get_case_repo, get_obs_repo
from app.api.schemas.api_models import (
    BatchSummaryResponse,
    CaseDetailResponse,
    HeroDemoResponse,
    PatternClusterResponse,
)
from app.data.normalize import normalize_batch
from app.domain.hero_scenarios import HERO_SCENARIOS
from app.domain.models import BatchMetadata
from app.engine.shadow_engine import ValueFlowReconstructionEngine
from app.persistence.case_repo import CaseRepository
from app.persistence.observation_repo import ObservationRepository

router = APIRouter(prefix="/api/demo", tags=["Hero Demos"])


@router.post("/hero/{hero_id}", response_model=HeroDemoResponse)
def run_hero_demo(
    hero_id: str,
    obs_repo: ObservationRepository = Depends(get_obs_repo),
    case_repo: CaseRepository = Depends(get_case_repo),
) -> HeroDemoResponse:
    """Execute a reproducible 1-click hero demonstration scenario."""
    if hero_id not in HERO_SCENARIOS:
        raise HTTPException(
            status_code=404,
            detail=f"Hero scenario '{hero_id}' not found. Available: {list(HERO_SCENARIOS.keys())}",
        )

    # 1. Generate deterministic records
    gen_fn = HERO_SCENARIOS[hero_id]
    batch_id, raw_records, hero_meta = gen_fn()

    # 2. Normalize
    observations, inventory_moves = normalize_batch(raw_records, batch_id=batch_id)

    # 3. Persist observations & inventory
    obs_repo.save_observations(observations)
    if inventory_moves:
        obs_repo.save_inventory_moves(inventory_moves)

    # 4. Execute Value-Flow Engine
    engine = ValueFlowReconstructionEngine()
    result = engine.process_batch(
        batch_id=batch_id,
        observations=observations,
        inventory_moves=inventory_moves,
    )

    # 5. Persist batch, cases, events, pattern clusters
    reason_breakdown: dict[str, int] = {}
    for c in result.cases:
        if c.decision:
            for rc in c.decision.reason_codes:
                reason_breakdown[rc] = reason_breakdown.get(rc, 0) + 1

    batch_meta = BatchMetadata(
        batch_id=result.batch_id,
        record_count=result.total_records,
        matched_count=result.matched_count,
        exception_count=result.exception_count,
        resolved_count=result.auto_resolved_count + result.matched_count,
        review_count=result.human_review_count,
        unresolved_count=result.unresolved_count,
        total_volume_inr=result.total_volume_inr,
        explained_volume_inr=result.explained_volume_inr,
        unexplained_volume_inr=result.unexplained_volume_inr,
        processing_time_ms=result.processing_time_ms,
    )
    case_repo.save_batch_metadata(batch_meta)
    case_repo.save_cases(result.cases)

    # Save events and pattern clusters
    all_events = [evt for c in result.cases for evt in c.shadow_events]
    if all_events:
        case_repo.save_events(all_events)
    if result.pattern_clusters:
        case_repo.save_pattern_clusters(result.pattern_clusters)

    # 6. Format Response
    summary_resp = BatchSummaryResponse(
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
        reason_code_breakdown=reason_breakdown,
        pattern_clusters=[
            {
                "cluster_id": pc.cluster_id,
                "signature": pc.pattern_signature,
                "exceptions": pc.exception_count,
                "value_at_risk": float(pc.total_value_at_risk),
                "likely_common_cause": pc.likely_common_cause,
            }
            for pc in result.pattern_clusters
        ],
    )

    cases_resp = [
        CaseDetailResponse(
            case_id=c.case_id,
            batch_id=c.batch_id,
            observation_ids=c.observation_ids,
            residual_amount=float(c.residual_amount),
            financial_impact=float(c.financial_impact),
            scenario_id=c.scenario_id,
            status=c.status,
            pattern_cluster_id=c.pattern_cluster_id,
            graph_json=c.graph_json,
            shadow_events=[se.model_dump(mode="json") for se in c.shadow_events],
            decision=c.decision.model_dump(mode="json") if c.decision else None,
            observations=[o.model_dump(mode="json") for o in observations if o.observation_id in c.observation_ids],
        )
        for c in result.cases
    ]

    clusters_resp = [
        PatternClusterResponse(
            cluster_id=pc.cluster_id,
            batch_id=pc.batch_id,
            case_ids=pc.case_ids,
            pattern_signature=pc.pattern_signature,
            exception_count=pc.exception_count,
            total_value_at_risk=float(pc.total_value_at_risk),
            likely_common_cause=pc.likely_common_cause,
            evidence_strength=pc.evidence_strength,
            created_at=pc.created_at,
        )
        for pc in result.pattern_clusters
    ]

    return HeroDemoResponse(
        hero_id=hero_id,
        title=hero_meta["title"],
        description=hero_meta["description"],
        batch_summary=summary_resp,
        cases=cases_resp,
        pattern_clusters=clusters_resp,
    )
