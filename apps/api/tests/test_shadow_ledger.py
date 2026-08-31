"""Unit tests for the Shadow Ledger Manager & Provenance."""

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.enums import DecisionType, EventStatus, EventType, HypothesisType
from app.domain.models import Case, Decision, Event, Hypothesis, Observation
from app.engine.shadow_ledger import ShadowLedgerManager


def test_shadow_events_and_audit_trail_provenance():
    """Verify generating shadow events and constructing chronological audit trails."""
    manager = ShadowLedgerManager()
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)

    obs = [
        Observation(
            observation_id="obs_p1",
            source_system="pos",
            source_record_id="pos_1",
            event_type=EventType.PAYMENT,
            amount=Decimal("5000.00"),
            timestamp=t0,
        ),
    ]

    case = Case(
        case_id="case_prov_1",
        batch_id="batch_prov_1",
        observation_ids=["obs_p1"],
        residual_amount=Decimal("100.00"),
    )

    hyp = Hypothesis(
        hypothesis_id="hyp_fee_prov",
        hypothesis_type=HypothesisType.FEE_ADJUSTMENT,
        case_id=case.case_id,
        generated_event=Event(
            status=EventStatus.DERIVED,
            event_type=EventType.FEE,
            amount=Decimal("100.00"),
            timestamp=t0,
        ),
        evidence_confidence=0.92,
    )

    decision = Decision(
        case_id=case.case_id,
        decision=DecisionType.AUTO_RESOLVE,
        winning_hypothesis_id=hyp.hypothesis_id,
        reason_codes=["AUTO_RESOLVED_FEE_ADJUSTMENT"],
        evidence_confidence=0.92,
    )

    shadow_events = manager.create_shadow_events_for_case(case, hyp, decision)
    assert len(shadow_events) == 1
    assert shadow_events[0].status == EventStatus.DERIVED
    assert shadow_events[0].amount == Decimal("100.00")

    trail = manager.build_audit_trail(case, obs, shadow_events, decision)
    assert len(trail) == 2
    assert trail[0]["entry_type"] == "OFFICIAL_LEDGER_SOURCE"
    assert trail[1]["entry_type"] == "SHADOW_LEDGER_INFERENCE"
