"""Stage 6: Decision Risk Gate Engine.

Evaluates evidence confidence against financial materiality, contradiction severity,
and strict safety constraints to produce transparent decision outcomes.
"""

from decimal import Decimal

from app.domain.enums import ActionRisk, DecisionType, HypothesisType
from app.domain.models import Decision, Hypothesis


class DecisionRiskGate:
    """Multi-dimensional safety gate deciding between AUTO_RESOLVE, HUMAN_REVIEW, and UNRESOLVED."""

    def __init__(
        self,
        auto_resolve_threshold: float = 0.82,
        review_threshold: float = 0.50,
        materiality_limit: Decimal = Decimal("10000.00"),
    ) -> None:
        self.auto_resolve_threshold = auto_resolve_threshold
        self.review_threshold = review_threshold
        self.materiality_limit = materiality_limit

    def evaluate_decision(self, case_id: str, hypotheses: list[Hypothesis]) -> Decision:
        """Evaluate candidate hypotheses for a case and decide the resolution action."""
        if not hypotheses:
            return Decision(
                case_id=case_id,
                decision=DecisionType.UNRESOLVED,
                reason_codes=["NO_PLAUSIBLE_HYPOTHESIS_GENERATED"],
                evidence_confidence=0.0,
                contradiction_severity=1.0,
                financial_materiality=Decimal("0.00"),
                action_risk=ActionRisk.HIGH,
            )

        # Select the highest-scoring candidate hypothesis
        best_hyp = max(hypotheses, key=lambda h: h.evidence_confidence)
        conf = best_hyp.evidence_confidence
        htype = best_hyp.hypothesis_type
        materiality = best_hyp.financial_impact
        contradiction = best_hyp.contradiction_cost

        # Determine Action Risk
        if materiality > self.materiality_limit or htype == HypothesisType.OFF_LEDGER_DEVIATION:
            action_risk = ActionRisk.HIGH
        elif materiality > Decimal("1000.00") or conf < self.auto_resolve_threshold:
            action_risk = ActionRisk.MEDIUM
        else:
            action_risk = ActionRisk.LOW

        reason_codes: list[str] = []

        # RULE 1: OFF_LEDGER_DEVIATION is strictly PROHIBITED from AUTO_RESOLVE
        if htype == HypothesisType.OFF_LEDGER_DEVIATION:
            if best_hyp.indirect_evidence_ids or conf >= self.review_threshold:
                outcome = DecisionType.HUMAN_REVIEW
                reason_codes.append("OFF_LEDGER_DEVIATION_INDIRECT_TRACE_ESCALATED")
                reason_codes.append("PROHIBITED_FROM_AUTO_RESOLVE")
            else:
                outcome = DecisionType.UNRESOLVED
                reason_codes.append("OFF_LEDGER_DEVIATION_ZERO_TRACE_UNRESOLVED")

        # RULE 2: High Financial Materiality Ceiling (Safety Net)
        elif materiality > self.materiality_limit:
            outcome = DecisionType.HUMAN_REVIEW
            reason_codes.append("HIGH_MATERIALITY_CEILING_EXCEEDED")
            reason_codes.append(f"MATERIALITY_INR_{float(materiality):.2f}_ESCALATED_FOR_SUPERVISOR")

        # RULE 3: Hard Contradiction Detected
        elif contradiction >= 0.50:
            outcome = DecisionType.UNRESOLVED
            reason_codes.append("CONTRADICTION_DETECTED_UNRESOLVED")

        # RULE 4: High Confidence Auto-Resolution
        elif conf >= self.auto_resolve_threshold and best_hyp.can_auto_resolve and contradiction == 0.0:
            outcome = DecisionType.AUTO_RESOLVE
            reason_codes.append(f"AUTO_RESOLVED_{htype.value.upper()}_HIGH_CONFIDENCE")
            reason_codes.append("ZERO_CONTRADICTIONS_CLOSED_CONSERVATION")

        # RULE 5: Medium Confidence Human Review
        elif conf >= self.review_threshold:
            outcome = DecisionType.HUMAN_REVIEW
            reason_codes.append(f"MEDIUM_CONFIDENCE_{htype.value.upper()}_ESCALATED")

        # RULE 6: Low Confidence Unresolved
        else:
            outcome = DecisionType.UNRESOLVED
            reason_codes.append("INSUFFICIENT_EVIDENCE_CONFIDENCE_UNRESOLVED")

        # Add constraints info to reasons
        for sat in best_hyp.constraints_satisfied:
            reason_codes.append(f"SATISFIED_{sat}")
        for viol in best_hyp.constraints_violated:
            reason_codes.append(f"VIOLATED_{viol}")

        return Decision(
            case_id=case_id,
            decision=outcome,
            winning_hypothesis_id=best_hyp.hypothesis_id,
            reason_codes=reason_codes,
            evidence_ids=best_hyp.evidence_ids + best_hyp.indirect_evidence_ids,
            evidence_confidence=conf,
            contradiction_severity=contradiction,
            financial_materiality=materiality,
            action_risk=action_risk,
        )
