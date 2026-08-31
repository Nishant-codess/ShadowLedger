"""Unit tests for the Decision Risk Gate."""

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.enums import ActionRisk, DecisionType, EventStatus, EventType, HypothesisType
from app.domain.models import Event, Hypothesis
from app.engine.decision_gate import DecisionRiskGate


def test_decision_gate_off_ledger_never_auto_resolves():
    """Verify strict safety rule: OFF_LEDGER_DEVIATION can never produce AUTO_RESOLVE."""
    gate = DecisionRiskGate()
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)

    # High confidence off-ledger deviation with indirect trace
    hyp = Hypothesis(
        hypothesis_id="h_dev_1",
        hypothesis_type=HypothesisType.OFF_LEDGER_DEVIATION,
        case_id="c_dev_1",
        generated_event=Event(
            status=EventStatus.UNOBSERVED_DEVIATION,
            event_type=EventType.PAYMENT,
            amount=Decimal("50.00"),
            timestamp=t0,
        ),
        evidence_ids=["obs_ride_1"],
        indirect_evidence_ids=["obs_upi_1"],
        evidence_confidence=0.95,
        can_auto_resolve=False,
    )

    dec = gate.evaluate_decision("c_dev_1", [hyp])

    assert dec.decision != DecisionType.AUTO_RESOLVE
    assert dec.decision == DecisionType.HUMAN_REVIEW
    assert "PROHIBITED_FROM_AUTO_RESOLVE" in dec.reason_codes
    assert dec.action_risk == ActionRisk.HIGH


def test_decision_gate_materiality_ceiling():
    """Verify that cases exceeding materiality limit (> ₹10,000) escalate to HUMAN_REVIEW regardless of confidence."""
    gate = DecisionRiskGate(materiality_limit=Decimal("10000.00"))
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)

    # 1. Low value (₹500), high confidence (0.95) -> AUTO_RESOLVE
    hyp_low_val = Hypothesis(
        hypothesis_id="h_low",
        hypothesis_type=HypothesisType.FEE_ADJUSTMENT,
        case_id="c_low",
        generated_event=Event(
            status=EventStatus.DERIVED,
            event_type=EventType.FEE,
            amount=Decimal("10.00"),
            timestamp=t0,
        ),
        financial_impact=Decimal("500.00"),
        evidence_confidence=0.95,
        can_auto_resolve=True,
    )
    dec_low = gate.evaluate_decision("c_low", [hyp_low_val])
    assert dec_low.decision == DecisionType.AUTO_RESOLVE

    # 2. High value (₹500,000), high confidence (0.95) -> HUMAN_REVIEW (Safety Net)
    hyp_high_val = Hypothesis(
        hypothesis_id="h_high",
        hypothesis_type=HypothesisType.FEE_ADJUSTMENT,
        case_id="c_high",
        generated_event=Event(
            status=EventStatus.DERIVED,
            event_type=EventType.FEE,
            amount=Decimal("10000.00"),
            timestamp=t0,
        ),
        financial_impact=Decimal("500000.00"),
        evidence_confidence=0.95,
        can_auto_resolve=True,
    )
    dec_high = gate.evaluate_decision("c_high", [hyp_high_val])
    assert dec_high.decision == DecisionType.HUMAN_REVIEW
    assert "HIGH_MATERIALITY_CEILING_EXCEEDED" in dec_high.reason_codes
