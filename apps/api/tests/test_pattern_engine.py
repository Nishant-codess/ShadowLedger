"""Unit tests for the Cross-Case Pattern Discovery Engine."""

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.enums import EventStatus, EventType, HypothesisType
from app.domain.models import Case, Event, Hypothesis
from app.engine.pattern_engine import CrossCasePatternEngine


def test_discover_patterns_groups_recurring_cases():
    """Verify aggregating individual discrepancy cases into structural pattern clusters."""
    engine = CrossCasePatternEngine()
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)

    cases = []
    # Create 5 recurring Kirana non-cash inventory cases
    for i in range(5):
        hyp = Hypothesis(
            hypothesis_id=f"h_kir_{i}",
            hypothesis_type=HypothesisType.INVENTORY_SETTLEMENT,
            case_id=f"case_kir_{i}",
            generated_event=Event(
                status=EventStatus.INFERRED_LATENT,
                event_type=EventType.INVENTORY_MOVE,
                amount=Decimal("2.00"),
                timestamp=t0,
            ),
            financial_impact=Decimal("2.00"),
            evidence_confidence=0.95,
        )
        cases.append(
            Case(
                case_id=f"case_kir_{i}",
                batch_id="batch_pat_1",
                observation_ids=[f"obs_{i}"],
                residual_amount=Decimal("2.00"),
                financial_impact=Decimal("2.00"),
                scenario_id="SCN_04",
                hypotheses=[hyp],
            )
        )

    # Create 3 recurring mobility deviation cases
    for i in range(3):
        hyp = Hypothesis(
            hypothesis_id=f"h_ride_{i}",
            hypothesis_type=HypothesisType.OFF_LEDGER_DEVIATION,
            case_id=f"case_ride_{i}",
            generated_event=Event(
                status=EventStatus.UNOBSERVED_DEVIATION,
                event_type=EventType.PAYMENT,
                amount=Decimal("50.00"),
                timestamp=t0,
            ),
            financial_impact=Decimal("50.00"),
            evidence_confidence=0.85,
        )
        cases.append(
            Case(
                case_id=f"case_ride_{i}",
                batch_id="batch_pat_1",
                observation_ids=[f"obs_r_{i}"],
                residual_amount=Decimal("50.00"),
                financial_impact=Decimal("50.00"),
                scenario_id="SCN_10",
                hypotheses=[hyp],
            )
        )

    clusters = engine.discover_patterns("batch_pat_1", cases)

    assert len(clusters) == 2
    signatures = [c.pattern_signature for c in clusters]
    assert any("INVENTORY_SETTLEMENT" in s for s in signatures)
    assert any("OFF_LEDGER_DEVIATION" in s for s in signatures)

    # Check that individual cases have been back-linked to their cluster
    for c in cases:
        assert c.pattern_cluster_id is not None
