"""Unit tests for the Local AI Narrative Generator and Fallback."""

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.enums import ActionRisk, DecisionType, EventStatus, EventType, HypothesisType
from app.domain.models import Case, Decision, Event, Hypothesis, Observation
from app.engine.local_ai import LocalAIExplainer


def test_local_ai_deterministic_synthesis_fallback():
    """Verify that when Ollama is offline, deterministic narrative synthesis generates audit-ready briefing."""
    # Point to nonexistent port to test offline fallback
    explainer = LocalAIExplainer(ollama_base_url="http://localhost:99999", timeout_seconds=0.1)
    t0 = datetime(2026, 9, 1, 10, 0, 0, tzinfo=UTC)

    obs = [
        Observation(
            observation_id="obs_p1",
            source_system="pos",
            source_record_id="p1",
            event_type=EventType.PAYMENT,
            amount=Decimal("100.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-1"},
        ),
        Observation(
            observation_id="obs_s1",
            source_system="bank",
            source_record_id="s1",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("98.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-1"},
        ),
    ]

    case = Case(
        case_id="case_ai_1",
        batch_id="batch_ai_1",
        observation_ids=["obs_p1", "obs_s1"],
        residual_amount=Decimal("2.00"),
    )

    hyp = Hypothesis(
        hypothesis_id="h1",
        hypothesis_type=HypothesisType.INVENTORY_SETTLEMENT,
        case_id=case.case_id,
        generated_event=Event(
            status=EventStatus.INFERRED_LATENT,
            event_type=EventType.INVENTORY_MOVE,
            amount=Decimal("2.00"),
            timestamp=t0,
        ),
        evidence_confidence=0.95,
    )

    decision = Decision(
        case_id=case.case_id,
        decision=DecisionType.AUTO_RESOLVE,
        winning_hypothesis_id=hyp.hypothesis_id,
        evidence_confidence=0.95,
        financial_materiality=Decimal("2.00"),
        action_risk=ActionRisk.LOW,
    )

    briefing = explainer.generate_case_explanation(case, obs, hyp, decision)

    assert briefing["provider"] == "deterministic_synthesis_fallback"
    assert "Non-Monetary Retail Settlement" in briefing["headline"]
    assert "₹2.00" in briefing["deterministic_narrative"]
    assert briefing["decision"] == "auto_resolve"
    assert briefing["evidence_confidence"] == 0.95
