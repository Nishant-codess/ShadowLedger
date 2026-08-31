"""Unit tests for the Multi-Dimensional Evidence Scorer."""

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.enums import EventStatus, EventType, HypothesisType
from app.domain.models import Event, Hypothesis, Observation
from app.engine.evidence_scorer import EvidenceScorer


def test_evidence_scorer_calibrated_confidence():
    """Verify calculating 7-dimension evidence score and calibrated bounds in [0.0, 1.0]."""
    scorer = EvidenceScorer()
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)

    obs = [
        Observation(
            observation_id="obs_1",
            source_system="pos",
            source_record_id="p1",
            event_type=EventType.PAYMENT,
            amount=Decimal("1000.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-FEE-1", "merchant_id": "M1"},
        ),
        Observation(
            observation_id="obs_2",
            source_system="bank",
            source_record_id="s1",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("980.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-FEE-1", "merchant_id": "M1"},
        ),
    ]

    fee_evt = Event(
        event_id="evt_fee_1",
        status=EventStatus.DERIVED,
        event_type=EventType.FEE,
        amount=Decimal("20.00"),
        timestamp=t0,
        hypothesis_type=HypothesisType.FEE_ADJUSTMENT,
    )

    hyp = Hypothesis(
        hypothesis_id="hyp_fee_1",
        hypothesis_type=HypothesisType.FEE_ADJUSTMENT,
        case_id="case_fee_1",
        generated_event=fee_evt,
        evidence_ids=["obs_1", "obs_2"],
        financial_impact=Decimal("20.00"),
    )

    scored_hyp = scorer.score_hypothesis(hyp, obs)

    assert 0.80 <= scored_hyp.evidence_confidence <= 1.0
    assert scored_hyp.amount_consistency == 1.0
    assert scored_hyp.entity_consistency == 1.0
    assert scored_hyp.business_rule_fit == 1.0
    assert "CONSERVATION_OF_VALUE_CLOSED" in scored_hyp.constraints_satisfied
    assert "ZERO_DIRECT_CONTRADICTIONS" in scored_hyp.constraints_satisfied


def test_evidence_scoring_is_independent_of_financial_amount():
    """Verify that evidence confidence measures factual support, not financial risk."""
    scorer = EvidenceScorer()
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)

    # 1. Small amount: ₹100 payment, ₹98 settlement, ₹2 fee
    obs_small = [
        Observation(
            observation_id="s1",
            source_system="pos",
            source_record_id="p1",
            event_type=EventType.PAYMENT,
            amount=Decimal("100.00"),
            timestamp=t0,
            entity_ids={"order_id": "O1", "merchant_id": "M1"},
        ),
        Observation(
            observation_id="s2",
            source_system="bank",
            source_record_id="s1",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("98.00"),
            timestamp=t0,
            entity_ids={"order_id": "O1", "merchant_id": "M1"},
        ),
    ]
    hyp_small = Hypothesis(
        hypothesis_id="h_small",
        hypothesis_type=HypothesisType.FEE_ADJUSTMENT,
        case_id="c1",
        generated_event=Event(
            status=EventStatus.DERIVED,
            event_type=EventType.FEE,
            amount=Decimal("2.00"),
            timestamp=t0,
        ),
        evidence_ids=["s1", "s2"],
    )

    # 2. Large amount: ₹10,000,000 payment, ₹9,800,000 settlement, ₹200,000 fee
    obs_large = [
        Observation(
            observation_id="l1",
            source_system="pos",
            source_record_id="p2",
            event_type=EventType.PAYMENT,
            amount=Decimal("10000000.00"),
            timestamp=t0,
            entity_ids={"order_id": "O2", "merchant_id": "M2"},
        ),
        Observation(
            observation_id="l2",
            source_system="bank",
            source_record_id="s2",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("9800000.00"),
            timestamp=t0,
            entity_ids={"order_id": "O2", "merchant_id": "M2"},
        ),
    ]
    hyp_large = Hypothesis(
        hypothesis_id="h_large",
        hypothesis_type=HypothesisType.FEE_ADJUSTMENT,
        case_id="c2",
        generated_event=Event(
            status=EventStatus.DERIVED,
            event_type=EventType.FEE,
            amount=Decimal("200000.00"),
            timestamp=t0,
        ),
        evidence_ids=["l1", "l2"],
    )

    scored_small = scorer.score_hypothesis(hyp_small, obs_small)
    scored_large = scorer.score_hypothesis(hyp_large, obs_large)

    # Both have identical structural support, so their evidence confidence must match
    assert abs(scored_small.evidence_confidence - scored_large.evidence_confidence) < 0.05
