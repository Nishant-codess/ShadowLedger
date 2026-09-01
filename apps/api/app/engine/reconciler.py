"""Deterministic Reconciliation Engine.

Authoritative baseline using transparent rules, exact ID linking, fee/refund math,
window matching, and explicit reason codes. Zero LLM involvement.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal
from typing import Any

from app.domain.enums import (
    ActionRisk,
    DecisionType,
    EventType,
    ReconciliationStatus,
    ValuationBasis,
)
from app.domain.models import Case, Decision, InventoryMove, Observation


@dataclass
class MatchGroup:
    """A set of related observations processed under deterministic rules."""

    group_key: str
    status: ReconciliationStatus
    reason_code: str
    observations: list[Observation]
    residual_amount: Decimal = Decimal("0.00")
    total_volume: Decimal = Decimal("0.00")
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReconciliationResult:
    """Full outcome of a deterministic reconciliation pass."""

    batch_id: str
    total_observations: int
    matched_count: int
    exception_count: int
    match_rate: float
    total_volume_inr: Decimal
    explained_volume_inr: Decimal
    unexplained_volume_inr: Decimal
    match_groups: list[MatchGroup]
    cases: list[Case]
    duplicate_observation_ids: list[str]


class DeterministicReconciler:
    """Pure rule-based baseline reconciler."""

    def __init__(self, time_window_hours: int = 24, fee_tolerance: Decimal = Decimal("0.05")):
        self.time_window = timedelta(hours=time_window_hours)
        self.fee_tolerance = fee_tolerance

    def reconcile_batch(
        self,
        observations: list[Observation],
        inventory_moves: list[InventoryMove] | None = None,
        batch_id: str = "default",
    ) -> ReconciliationResult:
        """Execute deterministic matching across all observations in a batch."""
        inv_by_order: dict[str, list[InventoryMove]] = defaultdict(list)
        if inventory_moves:
            for inv in inventory_moves:
                if inv.linked_order_id:
                    inv_by_order[inv.linked_order_id].append(inv)

        # 1. Detect duplicates first
        duplicates: list[str] = []
        seen_fingerprints: dict[tuple[str, str, Decimal], Observation] = {}
        unique_observations: list[Observation] = []

        for obs in observations:
            # Fingerprint: (source_system, entity_key, amount)
            entity_key = (
                obs.entity_ids.get("order_id")
                or obs.entity_ids.get("payment_id")
                or obs.source_record_id
            )
            fp = (obs.source_system, entity_key, obs.amount)

            if fp in seen_fingerprints:
                prev = seen_fingerprints[fp]
                # Check if timestamp is within 30 seconds -> true duplicate broadcast
                if abs((obs.timestamp - prev.timestamp).total_seconds()) <= 30:
                    duplicates.append(obs.observation_id)
                    continue
            seen_fingerprints[fp] = obs
            unique_observations.append(obs)

        # 2. Partition observations by connected entity identifiers (graph components)
        # Build adjacency across all shared entity keys
        parent: dict[str, str] = {}

        def find(x: str) -> str:
            if x not in parent:
                parent[x] = x
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x: str, y: str) -> None:
            root_x = find(x)
            root_y = find(y)
            if root_x != root_y:
                parent[root_y] = root_x

        # Group observations by connecting any shared entity ID
        for obs in unique_observations:
            keys: list[str] = []
            for k, v in obs.entity_ids.items():
                if v and k in ("order_id", "payment_id", "ride_id", "batch_ref"):
                    keys.append(f"{k}:{v}")

            if not keys:
                # Fallback to observation's own unique ID if no entity keys
                keys.append(f"obs:{obs.observation_id}")

            for i in range(len(keys) - 1):
                union(keys[i], keys[i + 1])

        # Cluster observations into their root connected group
        grouped_by_root: dict[str, list[Observation]] = defaultdict(list)
        for obs in unique_observations:
            keys = [f"{k}:{v}" for k, v in obs.entity_ids.items() if v and k in ("order_id", "payment_id", "ride_id", "batch_ref")]
            if keys:
                root = find(keys[0])
            else:
                root = find(f"obs:{obs.observation_id}")
            grouped_by_root[root].append(obs)

        match_groups: list[MatchGroup] = []
        cases: list[Case] = []

        matched_obs_count = 0
        total_volume = Decimal("0.00")
        explained_volume = Decimal("0.00")
        unexplained_volume = Decimal("0.00")

        # 3. Process each connected group
        for root_key, group_obs in grouped_by_root.items():
            # Derive human-friendly display key from entity IDs
            display_key = (
                group_obs[0].entity_ids.get("order_id")
                or group_obs[0].entity_ids.get("payment_id")
                or group_obs[0].entity_ids.get("ride_id")
                or group_obs[0].entity_ids.get("batch_ref")
                or root_key
            )
            group_volume = sum((abs(o.amount) for o in group_obs), Decimal("0.00"))
            total_volume += group_volume

            # Check single record group (unmatched orphan)
            if len(group_obs) == 1:
                obs = group_obs[0]
                unexplained_volume += abs(obs.amount)
                mg = MatchGroup(
                    group_key=display_key,
                    status=ReconciliationStatus.UNMATCHED,
                    reason_code="ORPHAN_SINGLE_RECORD",
                    observations=group_obs,
                    residual_amount=abs(obs.amount),
                    total_volume=group_volume,
                )
                match_groups.append(mg)

                case = self._create_case(
                    batch_id=batch_id,
                    group_key=display_key,
                    observations=group_obs,
                    residual=abs(obs.amount),
                    reason="ORPHAN_SINGLE_RECORD",
                )
                cases.append(case)
                continue

            # Multi-record group: Evaluate deterministic balance rules
            payments = [o for o in group_obs if o.event_type == EventType.PAYMENT]
            settlements = [o for o in group_obs if o.event_type == EventType.SETTLEMENT]
            fees = [o for o in group_obs if o.event_type == EventType.FEE]
            refunds = [o for o in group_obs if o.event_type == EventType.REFUND]

            # In multi-source financial logs (e.g. POS + Gateway + Bank):
            # When POS and Gateway both record the identical payment amount for the same order/entity,
            # they represent dual-recorded legs of the single economic payment, not two additive charges.
            pos_payments = [p for p in payments if p.source_system == "pos"]
            gtw_payments = [p for p in payments if p.source_system == "gateway"]
            if (
                pos_payments
                and gtw_payments
                and len(pos_payments) == 1
                and len(gtw_payments) == 1
                and pos_payments[0].amount == gtw_payments[0].amount
            ):
                pos_or_gateway_total = pos_payments[0].amount
            else:
                pos_or_gateway_total = sum((p.amount for p in payments), Decimal("0.00"))

            bank_settlement_total = sum((s.amount for s in settlements), Decimal("0.00"))
            fee_total = sum((f.amount for f in fees), Decimal("0.00"))

            # Rule A: Exact 1-to-1 Match (Payment == Settlement)
            if (
                pos_or_gateway_total > 0
                and bank_settlement_total > 0
                and pos_or_gateway_total == bank_settlement_total
                and not fees
                and not refunds
            ):
                matched_obs_count += len(group_obs)
                explained_volume += group_volume
                match_groups.append(
                    MatchGroup(
                        group_key=display_key,
                        status=ReconciliationStatus.MATCHED,
                        reason_code="EXACT_ID_AND_AMOUNT_MATCH",
                        observations=group_obs,
                        residual_amount=Decimal("0.00"),
                        total_volume=group_volume,
                    )
                )
                continue

            # Rule B: Fee-Balanced Match (Gross Payment - Fee == Net Settlement)
            net_expected_with_fee = pos_or_gateway_total + fee_total  # fees are negative
            if (
                bank_settlement_total > 0
                and abs(net_expected_with_fee - bank_settlement_total) <= self.fee_tolerance
            ):
                matched_obs_count += len(group_obs)
                explained_volume += group_volume
                match_groups.append(
                    MatchGroup(
                        group_key=display_key,
                        status=ReconciliationStatus.MATCHED,
                        reason_code="EXACT_FEE_ADJUSTMENT_MATCH",
                        observations=group_obs,
                        residual_amount=Decimal("0.00"),
                        total_volume=group_volume,
                    )
                )
                continue

            # Rule C: Explicit Linked Inventory Match (e.g. Kirana Chocolate Change)
            distinct_orders = {o.entity_ids.get("order_id") for o in group_obs if o.entity_ids.get("order_id")}
            linked_inv: list[InventoryMove] = []
            for ord_id in distinct_orders:
                if ord_id and ord_id in inv_by_order:
                    linked_inv.extend(inv_by_order[ord_id])

            inv_retail_total = sum(
                (inv.retail_value for inv in linked_inv if inv.retail_value and inv.valuation_basis == ValuationBasis.RETAIL),
                Decimal("0.00"),
            )

            if linked_inv and inv_retail_total > 0:
                # Tendered cash (bank deposit) == Bill amount + chocolate retail
                if abs((pos_or_gateway_total + inv_retail_total) - bank_settlement_total) <= Decimal("0.01"):
                    matched_obs_count += len(group_obs)
                    explained_volume += group_volume
                    match_groups.append(
                        MatchGroup(
                            group_key=display_key,
                            status=ReconciliationStatus.MATCHED,
                            reason_code="INVENTORY_SETTLEMENT_EXACT",
                            observations=group_obs,
                            residual_amount=Decimal("0.00"),
                            total_volume=group_volume,
                        )
                    )
                    continue

            # Discrepancy Found: Calculate residual and create Case
            diff = abs(pos_or_gateway_total - bank_settlement_total)
            unexplained_volume += diff
            explained_volume += (group_volume - diff)

            reason_code = "AMOUNT_DISCREPANCY_UNRESOLVED"
            if pos_or_gateway_total > bank_settlement_total:
                reason_code = "POS_EXCEEDS_SETTLEMENT_POSSIBLE_REFUND"
            elif bank_settlement_total > pos_or_gateway_total:
                reason_code = "SETTLEMENT_EXCEEDS_POS_POSSIBLE_SURCHARGE"

            match_groups.append(
                MatchGroup(
                    group_key=display_key,
                    status=ReconciliationStatus.UNMATCHED,
                    reason_code=reason_code,
                    observations=group_obs,
                    residual_amount=diff,
                    total_volume=group_volume,
                )
            )

            case = self._create_case(
                batch_id=batch_id,
                group_key=display_key,
                observations=group_obs,
                residual=diff,
                reason=reason_code,
            )
            cases.append(case)

        match_rate = (matched_obs_count / len(observations) * 100.0) if observations else 0.0

        return ReconciliationResult(
            batch_id=batch_id,
            total_observations=len(observations),
            matched_count=matched_obs_count,
            exception_count=len(observations) - matched_obs_count,
            match_rate=round(match_rate, 2),
            total_volume_inr=total_volume.quantize(Decimal("0.01")),
            explained_volume_inr=explained_volume.quantize(Decimal("0.01")),
            unexplained_volume_inr=unexplained_volume.quantize(Decimal("0.01")),
            match_groups=match_groups,
            cases=cases,
            duplicate_observation_ids=duplicates,
        )

    def _create_case(
        self,
        batch_id: str,
        group_key: str,
        observations: list[Observation],
        residual: Decimal,
        reason: str,
    ) -> Case:
        """Construct an investigation Case object from an unmatched observation cluster."""
        return Case(
            batch_id=batch_id,
            observation_ids=[o.observation_id for o in observations],
            residual_amount=residual,
            financial_impact=residual,
            scenario_id=observations[0].entity_ids.get("order_id", group_key),
            decision=Decision(
                case_id=f"case_{group_key}",
                decision=DecisionType.UNRESOLVED,
                reason_codes=[reason],
                evidence_ids=[o.observation_id for o in observations],
                evidence_confidence=0.0,
                financial_materiality=residual,
                action_risk=ActionRisk.HIGH if residual > Decimal("1000") else ActionRisk.LOW,
            ),
        )
