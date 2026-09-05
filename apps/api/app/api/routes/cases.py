"""Case inquiry and investigation endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.routes.batches import get_case_repo, get_obs_repo
from app.api.schemas.api_models import AIExplainResponse, CaseActionRequest, CaseDetailResponse
from app.persistence.case_repo import CaseRepository
from app.persistence.observation_repo import ObservationRepository

router = APIRouter(prefix="/api/cases", tags=["Cases"])


@router.get("", response_model=list[CaseDetailResponse])
def list_cases(
    batch_id: str | None = None,
    case_repo: CaseRepository = Depends(get_case_repo),
) -> list[CaseDetailResponse]:
    """Retrieve all discrepancy cases, optionally filtered by batch."""
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
            pattern_cluster_id=c.pattern_cluster_id,
            graph_json=c.graph_json,
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
    """Fetch complete detail for a specific case including connected observations and graph."""
    c = case_repo.get_case_by_id(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    # Fetch connected observations
    all_obs = obs_repo.get_by_batch(c.batch_id)
    connected = [o.model_dump(mode="json") for o in all_obs if o.observation_id in c.observation_ids]

    # Fetch shadow events if any
    shadow_events_serialized = [se.model_dump(mode="json") for se in c.shadow_events]

    return CaseDetailResponse(
        case_id=c.case_id,
        batch_id=c.batch_id,
        observation_ids=c.observation_ids,
        residual_amount=float(c.residual_amount),
        financial_impact=float(c.financial_impact),
        scenario_id=c.scenario_id,
        status=c.status,
        pattern_cluster_id=c.pattern_cluster_id,
        graph_json=c.graph_json,
        shadow_events=shadow_events_serialized,
        decision=c.decision.model_dump(mode="json") if c.decision else None,
        observations=connected,
    )


@router.post("/{case_id}/explain", response_model=AIExplainResponse)
def explain_case(
    case_id: str,
    style: str = "standard",
    case_repo: CaseRepository = Depends(get_case_repo),
    obs_repo: ObservationRepository = Depends(get_obs_repo),
) -> AIExplainResponse:
    """Generate an evidence-grounded natural language investigation narrative."""
    c = case_repo.get_case_by_id(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    all_obs = obs_repo.get_by_batch(c.batch_id)
    case_obs = [o for o in all_obs if o.observation_id in c.observation_ids]

    winning_hyp = None
    if c.decision and c.decision.winning_hypothesis_id and c.hypotheses:
        winning_hyp = next((h for h in c.hypotheses if h.hypothesis_id == c.decision.winning_hypothesis_id), None)
    if not winning_hyp and c.hypotheses:
        winning_hyp = c.hypotheses[0]

    if not winning_hyp and c.shadow_events:
        se = c.shadow_events[0]
        from app.domain.models import Hypothesis
        indirect_ids = [
            o.observation_id for o in case_obs
            if o.source_system in ("external_trace", "driver_upi")
            or "external" in o.raw_payload.get("source_type", "")
        ]
        winning_hyp = Hypothesis(
            hypothesis_id=c.decision.winning_hypothesis_id if c.decision else "hyp_win",
            hypothesis_type=se.hypothesis_type,
            case_id=c.case_id,
            generated_event=se,
            evidence_ids=[o.observation_id for o in case_obs if o.observation_id not in indirect_ids],
            indirect_evidence_ids=indirect_ids,
            financial_impact=se.amount,
            evidence_confidence=se.confidence,
        )
    elif not winning_hyp and c.graph_json and "nodes" in c.graph_json:
        winner_node = next((n for n in c.graph_json["nodes"] if n.get("is_winner") is True), None)
        if winner_node and "hypothesis_type" in winner_node:
            from app.domain.enums import HypothesisType
            from app.domain.models import Hypothesis
            winning_hyp = Hypothesis(
                hypothesis_id=winner_node.get("hypothesis_id", "hyp_win"),
                hypothesis_type=HypothesisType(winner_node["hypothesis_type"]),
                case_id=c.case_id,
                financial_impact=Decimal(str(winner_node.get("amount", c.residual_amount))),
                evidence_confidence=winner_node.get("confidence", 0.9),
            )

    from app.engine.local_ai import LocalAIExplainer

    explainer = LocalAIExplainer()
    briefing = explainer.generate_case_explanation(
        case=c,
        observations=case_obs,
        winning_hypothesis=winning_hyp,
        decision=c.decision,
        style_variant=style,
    )

    return AIExplainResponse(**briefing)


@router.post("/{case_id}/action", response_model=CaseDetailResponse)
def perform_case_action(
    case_id: str,
    action_req: CaseActionRequest,
    case_repo: CaseRepository = Depends(get_case_repo),
    obs_repo: ObservationRepository = Depends(get_obs_repo),
) -> CaseDetailResponse:
    """Operator human-in-the-loop action on a case (confirm, escalate, reject)."""
    c = case_repo.get_case_by_id(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    if action_req.action == "confirm_settlement":
        c.status = "manually_confirmed"
    elif action_req.action == "escalate_ops":
        c.status = "escalated_to_supervisor"
    elif action_req.action == "reject_hypothesis":
        c.status = "rejected"
    else:
        c.status = f"action_{action_req.action}"

    # Update in duckdb
    case_repo.save_cases([c])

    all_obs = obs_repo.get_by_batch(c.batch_id)
    connected = [o.model_dump(mode="json") for o in all_obs if o.observation_id in c.observation_ids]
    shadow_events_serialized = [se.model_dump(mode="json") for se in c.shadow_events]

    return CaseDetailResponse(
        case_id=c.case_id,
        batch_id=c.batch_id,
        observation_ids=c.observation_ids,
        residual_amount=float(c.residual_amount),
        financial_impact=float(c.financial_impact),
        scenario_id=c.scenario_id,
        status=c.status,
        pattern_cluster_id=c.pattern_cluster_id,
        graph_json=c.graph_json,
        shadow_events=shadow_events_serialized,
        decision=c.decision.model_dump(mode="json") if c.decision else None,
        observations=connected,
    )
