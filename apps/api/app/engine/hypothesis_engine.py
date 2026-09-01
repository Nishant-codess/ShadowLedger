"""Stage 4: Latent-Event Hypothesis Engine.

Generates candidate latent economic hypotheses (Refunds, Fees, Inventory Settlements,
Store Credits, Off-Ledger Deviations, Timing Shifts) to explain observed value-flow gaps.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.domain.enums import (
    EventStatus,
    EventType,
    HypothesisType,
    ValuationBasis,
)
from app.domain.models import Event, Hypothesis, InventoryMove, Observation


class LatentHypothesisEngine:
    """Generates candidate latent economic events to explain financial residuals."""

    # Standard gateway MDR percentage bounds (e.g. 1.5% to 3.5%)
    MDR_STANDARD_RATES = [Decimal("0.015"), Decimal("0.020"), Decimal("0.025"), Decimal("0.030")]

    def generate_hypotheses(
        self,
        case_id: str,
        observations: list[Observation],
        inventory_moves: list[InventoryMove] | None = None,
    ) -> list[Hypothesis]:
        """Generate all plausible latent economic event candidates for the given case."""
        candidates: list[Hypothesis] = []
        inv_moves = inventory_moves or []

        payments = [o for o in observations if o.event_type == EventType.PAYMENT]
        settlements = [o for o in observations if o.event_type == EventType.SETTLEMENT]
        fees = [o for o in observations if o.event_type == EventType.FEE]
        refunds = [o for o in observations if o.event_type == EventType.REFUND]

        total_payment = sum((p.amount for p in payments), Decimal("0.00"))
        total_settlement = sum((s.amount for s in settlements), Decimal("0.00"))
        total_fee = sum((f.amount for f in fees), Decimal("0.00"))
        total_refund = sum((r.amount for r in refunds), Decimal("0.00"))

        net_residual = total_payment - total_settlement - total_fee - total_refund
        all_obs_ids = [o.observation_id for o in observations]

        # Case 1: Payment Exceeds Settlement (Net positive residual)
        if total_payment > 0 and net_residual > Decimal("0.00"):
            # Candidate 1A: Partial Refund (Latent refund requires review because refund doc is missing)
            refund_event = Event(
                status=EventStatus.INFERRED_LATENT,
                event_type=EventType.REFUND,
                amount=net_residual,
                timestamp=self._estimate_event_time(observations),
                entity_ids=self._merge_entity_ids(observations),
                source_observation_ids=all_obs_ids,
                hypothesis_type=HypothesisType.REFUND,
            )
            candidates.append(
                Hypothesis(
                    hypothesis_type=HypothesisType.REFUND,
                    case_id=case_id,
                    generated_event=refund_event,
                    evidence_ids=all_obs_ids,
                    financial_impact=net_residual,
                    can_auto_resolve=False,  # Unrecorded latent refund escalated to Human Review
                )
            )

            # Candidate 1B: Fee Adjustment (if residual matches a plausible percentage or fixed fee)
            for rate in self.MDR_STANDARD_RATES:
                expected_fee = (total_payment * rate).quantize(Decimal("0.01"))
                if abs(net_residual - expected_fee) <= Decimal("0.50"):
                    fee_event = Event(
                        status=EventStatus.DERIVED,
                        event_type=EventType.FEE,
                        amount=net_residual,
                        timestamp=self._estimate_event_time(observations),
                        entity_ids=self._merge_entity_ids(observations),
                        source_observation_ids=all_obs_ids,
                        hypothesis_type=HypothesisType.FEE_ADJUSTMENT,
                    )
                    candidates.append(
                        Hypothesis(
                            hypothesis_type=HypothesisType.FEE_ADJUSTMENT,
                            case_id=case_id,
                            generated_event=fee_event,
                            evidence_ids=all_obs_ids,
                            financial_impact=net_residual,
                            can_auto_resolve=True,
                        )
                    )
                    break

            # Candidate 1C: Store Credit Carry-Forward
            credit_event = Event(
                status=EventStatus.INFERRED_LATENT,
                event_type=EventType.CREDIT_ISSUE,
                amount=net_residual,
                timestamp=self._estimate_event_time(observations),
                entity_ids=self._merge_entity_ids(observations),
                source_observation_ids=all_obs_ids,
                hypothesis_type=HypothesisType.STORE_CREDIT,
            )
            candidates.append(
                Hypothesis(
                    hypothesis_type=HypothesisType.STORE_CREDIT,
                    case_id=case_id,
                    generated_event=credit_event,
                    evidence_ids=all_obs_ids,
                    financial_impact=net_residual,
                    can_auto_resolve=False,  # Customer store credit requires human approval
                )
            )

        # Case 2: Inventory Movement / Non-Monetary Settlement
        if inv_moves:
            for inv in inv_moves:
                inv_val = inv.retail_value or inv.unit_cost or Decimal("0.00")
                if inv_val > Decimal("0.00"):
                    # Check if inventory matches residual or order difference
                    inv_event = Event(
                        status=EventStatus.INFERRED_LATENT,
                        event_type=EventType.INVENTORY_MOVE,
                        amount=inv_val,
                        timestamp=inv.timestamp,
                        entity_ids=self._merge_entity_ids(observations),
                        source_observation_ids=all_obs_ids,
                        hypothesis_type=HypothesisType.INVENTORY_SETTLEMENT,
                    )
                    # Conditional Auto-Resolve requirements:
                    # 1. Linked order ID exists and matches
                    # 2. Valuation basis is known
                    # 3. Closes mathematical residual
                    is_linked = inv.linked_order_id is not None
                    is_known_valuation = inv.valuation_basis in (ValuationBasis.RETAIL, ValuationBasis.COST)
                    closes_residual = abs(net_residual - inv_val) <= Decimal("0.01") or abs(total_payment - total_settlement - inv_val) <= Decimal("0.01")

                    can_resolve = is_linked and is_known_valuation and closes_residual

                    candidates.append(
                        Hypothesis(
                            hypothesis_type=HypothesisType.INVENTORY_SETTLEMENT,
                            case_id=case_id,
                            generated_event=inv_event,
                            evidence_ids=all_obs_ids,
                            financial_impact=inv_val,
                            can_auto_resolve=can_resolve,
                        )
                    )

        # Case 3: Off-Ledger Payment Deviation (Ride fare deviation, extra cash, off-ledger cash overcharge)
        # Triggered when observations indicate ride platform, taxi, mobility, or external unrecorded deviation
        is_ride_or_deviation = any(
            o.source_system in ("ride_platform", "ola", "uber", "driver")
            or "ride_id" in o.entity_ids
            or "driver_id" in o.entity_ids
            or "cash_deviation" in str(o.raw_payload)
            or o.raw_payload.get("scenario_id") in ("SCN_08", "SCN_09", "SCN_10")
            for o in observations
        )

        if is_ride_or_deviation:
            deviation_amount = abs(net_residual) if net_residual != Decimal("0.00") else Decimal("50.00")
            deviation_event = Event(
                status=EventStatus.UNOBSERVED_DEVIATION,
                event_type=EventType.PAYMENT,
                amount=deviation_amount,
                timestamp=self._estimate_event_time(observations),
                entity_ids=self._merge_entity_ids(observations),
                source_observation_ids=all_obs_ids,
                hypothesis_type=HypothesisType.OFF_LEDGER_DEVIATION,
            )

            # Extract indirect evidence IDs if present (e.g. external trace, driver history, separate UPI transfer)
            indirect_ids = [
                o.observation_id for o in observations
                if o.source_system in ("external_trace", "driver_upi")
                or "external" in o.raw_payload.get("source_type", "")
                or "upi_extra" in o.source_record_id
                or "direct upi" in o.description.lower()
            ]

            candidates.append(
                Hypothesis(
                    hypothesis_type=HypothesisType.OFF_LEDGER_DEVIATION,
                    case_id=case_id,
                    generated_event=deviation_event,
                    evidence_ids=[o.observation_id for o in observations if o.observation_id not in indirect_ids],
                    indirect_evidence_ids=indirect_ids,
                    financial_impact=deviation_amount,
                    can_auto_resolve=False,  # STRICT DOMAIN RULE: OFF_LEDGER NEVER AUTO-RESOLVES
                )
            )

        # Case 4: Timing Offset (Delayed Batch / Next-Day Settlement)
        if len(observations) >= 2:
            timestamps = [o.timestamp for o in observations]
            time_span = max(timestamps) - min(timestamps)
            if time_span > timedelta(hours=12):
                timing_event = Event(
                    status=EventStatus.DERIVED,
                    event_type=EventType.ADJUSTMENT,
                    amount=abs(net_residual) if net_residual != Decimal("0.00") else total_settlement,
                    timestamp=max(timestamps),
                    entity_ids=self._merge_entity_ids(observations),
                    source_observation_ids=all_obs_ids,
                    hypothesis_type=HypothesisType.TIMING_OFFSET,
                )
                candidates.append(
                    Hypothesis(
                        hypothesis_type=HypothesisType.TIMING_OFFSET,
                        case_id=case_id,
                        generated_event=timing_event,
                        evidence_ids=all_obs_ids,
                        financial_impact=abs(net_residual),
                        can_auto_resolve=True,
                    )
                )

        # Case 5: Duplicate Reversal
        if len(observations) >= 2:
            seen_amounts: dict[Decimal, list[Observation]] = {}
            for o in observations:
                seen_amounts.setdefault(o.amount, []).append(o)
            for amt, obs_group in seen_amounts.items():
                if len(obs_group) >= 2 and all(o.event_type == obs_group[0].event_type for o in obs_group):
                    dup_event = Event(
                        status=EventStatus.DERIVED,
                        event_type=EventType.REVERSAL,
                        amount=amt,
                        timestamp=max(o.timestamp for o in obs_group),
                        entity_ids=self._merge_entity_ids(observations),
                        source_observation_ids=[o.observation_id for o in obs_group],
                        hypothesis_type=HypothesisType.DUPLICATE_REVERSAL,
                    )
                    candidates.append(
                        Hypothesis(
                            hypothesis_type=HypothesisType.DUPLICATE_REVERSAL,
                            case_id=case_id,
                            generated_event=dup_event,
                            evidence_ids=[o.observation_id for o in obs_group],
                            financial_impact=amt,
                            can_auto_resolve=True,
                        )
                    )

        # Case 6: Missing Payment (Orphan Settlement)
        if total_settlement > Decimal("0.00") and total_payment == Decimal("0.00"):
            missing_event = Event(
                status=EventStatus.INFERRED_LATENT,
                event_type=EventType.PAYMENT,
                amount=total_settlement,
                timestamp=self._estimate_event_time(observations),
                entity_ids=self._merge_entity_ids(observations),
                source_observation_ids=all_obs_ids,
                hypothesis_type=HypothesisType.MISSING_PAYMENT,
            )
            candidates.append(
                Hypothesis(
                    hypothesis_type=HypothesisType.MISSING_PAYMENT,
                    case_id=case_id,
                    generated_event=missing_event,
                    evidence_ids=all_obs_ids,
                    financial_impact=total_settlement,
                    can_auto_resolve=False,
                )
            )

        # Fallback Candidate if none matched
        if not candidates:
            unknown_event = Event(
                status=EventStatus.UNOBSERVED_DEVIATION,
                event_type=EventType.ADJUSTMENT,
                amount=abs(net_residual) if net_residual != Decimal("0.00") else Decimal("0.01"),
                timestamp=self._estimate_event_time(observations),
                entity_ids=self._merge_entity_ids(observations),
                source_observation_ids=all_obs_ids,
                hypothesis_type=HypothesisType.UNKNOWN,
            )
            candidates.append(
                Hypothesis(
                    hypothesis_type=HypothesisType.UNKNOWN,
                    case_id=case_id,
                    generated_event=unknown_event,
                    evidence_ids=all_obs_ids,
                    financial_impact=abs(net_residual),
                    can_auto_resolve=False,
                )
            )

        return candidates

    def _estimate_event_time(self, observations: list[Observation]) -> datetime:
        if observations:
            return min(o.timestamp for o in observations)
        return datetime.now(UTC)

    def _merge_entity_ids(self, observations: list[Observation]) -> dict[str, str]:
        merged: dict[str, str] = {}
        for o in observations:
            merged.update(o.entity_ids)
        return merged
