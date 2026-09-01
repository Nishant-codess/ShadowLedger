"""Stage 5: Evidence Scoring & Calibration Engine.

Computes multi-dimensional factual evidence scores for candidate hypotheses,
strictly separating factual evidence confidence from financial decision risk.
"""

from decimal import Decimal

from app.domain.enums import EventType, HypothesisType
from app.domain.models import Hypothesis, InventoryMove, Observation


class EvidenceScorer:
    """Evaluates the factual evidence supporting a candidate latent hypothesis."""

    # Calibration weights (sum = 1.0 for positive components)
    W_COVERAGE = 0.25
    W_AMOUNT = 0.25
    W_TEMPORAL = 0.15
    W_ENTITY = 0.15
    W_BUSINESS_RULE = 0.10
    W_ASSUMPTION_PENALTY = 0.05
    W_CONTRADICTION_PENALTY = 0.20

    def score_hypothesis(
        self,
        hypothesis: Hypothesis,
        observations: list[Observation],
        inventory_moves: list[InventoryMove] | None = None,
    ) -> Hypothesis:
        """Calculate the 7-dimension evidence score and calibrated confidence for a hypothesis."""
        inv_moves = inventory_moves or []

        # 1. Evidence Coverage (Fraction of involved observations supported)
        if observations:
            explained_ids = set(hypothesis.evidence_ids + hypothesis.indirect_evidence_ids)
            coverage = min(1.0, len(explained_ids) / len(observations))
        else:
            coverage = 0.0

        # 2. Amount Consistency (Does the mathematics close conservation equation?)
        amount_consistency = self._score_amount_consistency(hypothesis, observations, inv_moves)

        # 3. Temporal Consistency (Plausibility of sequence and timestamp intervals)
        temporal_consistency = self._score_temporal_consistency(hypothesis, observations)

        # 4. Entity Consistency (Shared order/customer/merchant identifiers)
        entity_consistency = self._score_entity_consistency(hypothesis, observations)

        # 5. Business Rule Fit (Fit to standard commercial practices)
        business_rule_fit = self._score_business_rule_fit(hypothesis, observations, inv_moves)

        # 6. Assumption Cost (Parsimony penalty for unobserved latent assumptions)
        assumption_cost = self._score_assumption_cost(hypothesis)

        # 7. Contradiction Cost (Contradictory timestamps, negative amounts, mutually exclusive facts)
        contradiction_cost = self._score_contradiction_cost(hypothesis, observations)

        # Compute Raw Evidence Score
        raw_score = (
            (self.W_COVERAGE * coverage)
            + (self.W_AMOUNT * amount_consistency)
            + (self.W_TEMPORAL * temporal_consistency)
            + (self.W_ENTITY * entity_consistency)
            + (self.W_BUSINESS_RULE * business_rule_fit)
            - (self.W_ASSUMPTION_PENALTY * assumption_cost)
            - (self.W_CONTRADICTION_PENALTY * contradiction_cost)
        )

        # Calibrated Confidence in [0.0, 1.0]
        calibrated_confidence = max(0.0, min(1.0, raw_score))

        # Update hypothesis dimensions
        hypothesis.evidence_coverage = round(coverage, 4)
        hypothesis.amount_consistency = round(amount_consistency, 4)
        hypothesis.temporal_consistency = round(temporal_consistency, 4)
        hypothesis.entity_consistency = round(entity_consistency, 4)
        hypothesis.business_rule_fit = round(business_rule_fit, 4)
        hypothesis.assumption_cost = round(assumption_cost, 4)
        hypothesis.contradiction_cost = round(contradiction_cost, 4)
        hypothesis.evidence_score = round(raw_score, 4)
        hypothesis.evidence_confidence = round(calibrated_confidence, 4)

        # Populate satisfied and violated constraints
        satisfied: list[str] = []
        violated: list[str] = []

        if amount_consistency >= 0.90:
            satisfied.append("CONSERVATION_OF_VALUE_CLOSED")
        else:
            violated.append("RESIDUAL_AMOUNT_MISMATCH")

        if temporal_consistency >= 0.80:
            satisfied.append("TEMPORAL_SEQUENCE_PLAUSIBLE")
        else:
            violated.append("TEMPORAL_ANOMALY")

        if entity_consistency >= 0.80:
            satisfied.append("ENTITY_CHAIN_LINKED")
        else:
            violated.append("ENTITY_LINKAGE_WEAK")

        if contradiction_cost > 0.0:
            violated.append("CONTRADICTION_DETECTED")
        else:
            satisfied.append("ZERO_DIRECT_CONTRADICTIONS")

        hypothesis.constraints_satisfied = satisfied
        hypothesis.constraints_violated = violated

        return hypothesis

    def _score_amount_consistency(
        self,
        hypothesis: Hypothesis,
        observations: list[Observation],
        inv_moves: list[InventoryMove],
    ) -> float:
        payments = [o for o in observations if o.event_type == EventType.PAYMENT]
        settlements = [o for o in observations if o.event_type == EventType.SETTLEMENT]
        fees = [o for o in observations if o.event_type == EventType.FEE]
        refunds = [o for o in observations if o.event_type == EventType.REFUND]

        total_p = sum((p.amount for p in payments), Decimal("0.00"))
        total_s = sum((s.amount for s in settlements), Decimal("0.00"))
        total_f = sum((f.amount for f in fees), Decimal("0.00"))
        total_r = sum((r.amount for r in refunds), Decimal("0.00"))

        gen_amt = hypothesis.generated_event.amount
        htype = hypothesis.hypothesis_type

        if htype in (HypothesisType.REFUND, HypothesisType.FEE_ADJUSTMENT, HypothesisType.STORE_CREDIT):
            # Equation: Total Payment == Settlement + Fees + Inferred Latent
            residual = abs(total_p - (total_s + total_f + total_r + gen_amt))
            if residual <= Decimal("0.01"):
                return 1.0
            elif residual <= Decimal("1.00"):
                return 0.90
            elif residual <= Decimal("10.00"):
                return 0.60
            return 0.20

        elif htype == HypothesisType.INVENTORY_SETTLEMENT:
            # Check inventory retail value exact closure
            inv_total = sum((inv.retail_value or inv.unit_cost or Decimal("0.00") for inv in inv_moves), Decimal("0.00"))
            residual = abs(total_p - (total_s + inv_total))
            if residual <= Decimal("0.01"):
                return 1.0
            return 0.50

        elif htype == HypothesisType.OFF_LEDGER_DEVIATION:
            # Off-ledger deviations represent unrecorded gaps; amount matches observed difference
            residual = abs(total_p - total_s)
            if abs(residual - gen_amt) <= Decimal("0.01"):
                return 0.95
            return 0.70

        elif htype == HypothesisType.DUPLICATE_REVERSAL:
            return 1.0

        elif htype == HypothesisType.TIMING_OFFSET:
            if abs(total_p - total_s) <= Decimal("0.01"):
                return 1.0
            return 0.80

        return 0.50

    def _score_temporal_consistency(self, hypothesis: Hypothesis, observations: list[Observation]) -> float:
        if len(observations) < 2:
            return 0.80

        timestamps = [o.timestamp for o in observations]
        t_min, t_max = min(timestamps), max(timestamps)
        duration_hours = (t_max - t_min).total_seconds() / 3600.0

        htype = hypothesis.hypothesis_type
        if htype == HypothesisType.TIMING_OFFSET:
            # Expected delay is between 12h and 72h (T+1 to T+3 business days)
            if 12.0 <= duration_hours <= 96.0:
                return 1.0
            return 0.60
        else:
            # Standard intra-day transactions should settle within 48h
            if duration_hours <= 48.0:
                return 1.0
            elif duration_hours <= 96.0:
                return 0.80
            return 0.40

    def _score_entity_consistency(self, hypothesis: Hypothesis, observations: list[Observation]) -> float:
        if not observations:
            return 0.0

        # Collect keys across observations
        order_sets = [set(o.entity_ids["order_id"].split()) for o in observations if "order_id" in o.entity_ids]
        payment_sets = [set(o.entity_ids["payment_id"].split()) for o in observations if "payment_id" in o.entity_ids]
        ride_sets = [set(o.entity_ids["ride_id"].split()) for o in observations if "ride_id" in o.entity_ids]

        has_common_order = bool(set.intersection(*order_sets)) if order_sets else False
        has_common_payment = bool(set.intersection(*payment_sets)) if payment_sets else False
        has_common_ride = bool(set.intersection(*ride_sets)) if ride_sets else False

        if has_common_order or has_common_payment or has_common_ride:
            return 1.0

        # Partial entity linkage (e.g. shared customer or merchant)
        merchants = {o.entity_ids["merchant_id"] for o in observations if "merchant_id" in o.entity_ids}
        if len(merchants) == 1:
            return 0.85

        return 0.50

    def _score_business_rule_fit(
        self,
        hypothesis: Hypothesis,
        observations: list[Observation],
        inv_moves: list[InventoryMove],
    ) -> float:
        htype = hypothesis.hypothesis_type

        if htype == HypothesisType.FEE_ADJUSTMENT:
            # Does fee match standard ~2.0% MDR?
            payments = [o for o in observations if o.event_type == EventType.PAYMENT]
            if payments:
                tot_p = sum((p.amount for p in payments), Decimal("0.00"))
                ratio = hypothesis.generated_event.amount / tot_p if tot_p > 0 else Decimal("0.00")
                if Decimal("0.015") <= ratio <= Decimal("0.035"):
                    return 1.0
            return 0.70

        elif htype == HypothesisType.INVENTORY_SETTLEMENT:
            # Kirana chocolate change: ₹1 to ₹10 standard price points
            amt = hypothesis.generated_event.amount
            if amt in (Decimal("1.00"), Decimal("2.00"), Decimal("5.00"), Decimal("10.00")):
                return 1.0
            return 0.75

        elif htype == HypothesisType.REFUND:
            if any(o.source_system in ("ride_platform", "external_trace", "driver_upi", "ola", "uber") or "ride_id" in o.entity_ids for o in observations):
                return 0.40  # Incongruent: Retail product return rule applied to mobility ride platform
            return 0.90

        elif htype == HypothesisType.OFF_LEDGER_DEVIATION:
            # Fits known mobility cash overcharge pattern (₹20 to ₹200)
            amt = hypothesis.generated_event.amount
            if Decimal("10.00") <= amt <= Decimal("500.00"):
                return 0.95
            return 0.60

        return 0.70

    def _score_assumption_cost(self, hypothesis: Hypothesis) -> float:
        # Penalize unverified multi-step assumptions
        if hypothesis.hypothesis_type in (HypothesisType.UNKNOWN, HypothesisType.MISSING_PAYMENT):
            return 0.80
        elif hypothesis.hypothesis_type == HypothesisType.OFF_LEDGER_DEVIATION:
            # Absence of direct record incurs modest parsimony penalty
            return 0.30
        return 0.10

    def _score_contradiction_cost(self, hypothesis: Hypothesis, observations: list[Observation]) -> float:
        # Negative amount contradiction
        if hypothesis.generated_event.amount <= Decimal("0.00"):
            return 1.0

        # Scenario 12: Adversarial deceptive mismatch (e.g. ₹500 diff on ₹505 vs ₹500 with incompatible keys)
        if len(observations) >= 2:
            merchants = {o.entity_ids.get("merchant_id") for o in observations if "merchant_id" in o.entity_ids}
            if len(merchants) > 1:
                return 0.90  # Strong contradiction: Different merchants

        return 0.0
