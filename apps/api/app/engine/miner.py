"""Stage 2: Exception Mining Engine.

Analyzes unmatched connected-component observation clusters to calculate
residuals, identify structural anomaly signatures, and assemble investigation Cases.
"""

from decimal import Decimal

from app.domain.enums import EventType
from app.domain.models import Case, InventoryMove, Observation


class ExceptionMiner:
    """Computes residuals and extracts anomaly features from observation clusters."""

    def mine_case(
        self,
        batch_id: str,
        observations: list[Observation],
        inventory_moves: list[InventoryMove] | None = None,
        case_id: str | None = None,
    ) -> Case:
        """Analyze an observation cluster to create an enriched Case."""
        inv_moves = inventory_moves or []
        obs_ids = [o.observation_id for o in observations]

        # Group observations by event type
        payments = [o for o in observations if o.event_type == EventType.PAYMENT]
        settlements = [o for o in observations if o.event_type == EventType.SETTLEMENT]
        fees = [o for o in observations if o.event_type == EventType.FEE]
        refunds = [o for o in observations if o.event_type == EventType.REFUND]
        adjustments = [o for o in observations if o.event_type == EventType.ADJUSTMENT]

        total_payments = sum((p.amount for p in payments), Decimal("0.00"))
        total_settlements = sum((s.amount for s in settlements), Decimal("0.00"))
        total_fees = sum((f.amount for f in fees), Decimal("0.00"))
        total_refunds = sum((r.amount for r in refunds), Decimal("0.00"))
        total_adjustments = sum((a.amount for a in adjustments), Decimal("0.00"))

        # Inventory retail and cost totals
        total_inventory_retail = Decimal("0.00")
        for inv in inv_moves:
            if inv.retail_value is not None:
                total_inventory_retail += inv.retail_value
            elif inv.unit_cost is not None:
                total_inventory_retail += inv.unit_cost

        # Mathematical Residual Equation:
        # What is recorded in payment vs what cleared in settlement + fee + inventory + refund + adjustments
        # Net residual shortfall:
        residual = (
            total_payments
            - total_settlements
            - total_fees
            - total_refunds
            - total_adjustments
            - total_inventory_retail
        )

        financial_impact = max(
            abs(residual),
            abs(total_payments - total_settlements),
            total_payments,
            total_settlements,
        )

        # Detect scenario tag if present in raw payload for benchmark evaluation
        scenario_tag = None
        for o in observations:
            if "scenario_id" in o.raw_payload:
                scenario_tag = o.raw_payload["scenario_id"]
                break

        case = Case(
            case_id=case_id or f"case_{batch_id[:8]}_{obs_ids[0][:8]}",
            batch_id=batch_id,
            observation_ids=obs_ids,
            residual_amount=abs(residual),
            financial_impact=financial_impact,
            scenario_id=scenario_tag,
            status="investigating",
        )

        return case
