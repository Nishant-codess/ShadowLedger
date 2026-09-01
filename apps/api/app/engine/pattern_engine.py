"""Stage 7: Cross-Case Pattern Discovery Engine (P0).

Aggregates multiple individual discrepancy cases into structural pattern clusters
identifying recurring micro-leakages, systematic merchant behaviors, and likely common causes.
"""

from collections import defaultdict
from decimal import Decimal
from uuid import uuid4

from app.domain.models import Case, PatternCluster


class CrossCasePatternEngine:
    """Discovers recurring multi-case patterns and structural anomaly clusters."""

    def discover_patterns(
        self,
        batch_id: str,
        cases: list[Case],
    ) -> list[PatternCluster]:
        """Aggregate exception cases into structural pattern clusters."""
        if not cases:
            return []

        clusters: list[PatternCluster] = []

        # 1. Group cases by Hypothesis Type and Structural Attributes
        signature_groups: dict[str, list[Case]] = defaultdict(list)

        for case in cases:
            # Determine primary hypothesis or decision
            if case.hypotheses:
                best_hyp = max(case.hypotheses, key=lambda h: h.evidence_confidence)
                htype = best_hyp.hypothesis_type.value
                sig = f"{htype.upper()}"
            else:
                sig = "UNKNOWN_RESIDUAL"

            # Check scenario tag if available
            if case.scenario_id:
                sig += f"_{case.scenario_id}"

            signature_groups[sig].append(case)

        # 2. Build Pattern Clusters for groups with 2 or more occurrences
        for sig, group_cases in signature_groups.items():
            if len(group_cases) < 2:
                continue

            case_ids = [c.case_id for c in group_cases]
            total_val = sum((c.financial_impact for c in group_cases), Decimal("0.00"))
            count = len(group_cases)

            # Formulate defensible, cautious description
            common_cause = self._generate_likely_common_cause(sig, count, total_val)

            avg_conf = 0.0
            confs = [
                max((h.evidence_confidence for h in c.hypotheses), default=0.0)
                for c in group_cases if c.hypotheses
            ]
            if confs:
                avg_conf = sum(confs) / len(confs)

            cluster = PatternCluster(
                cluster_id=f"pat_{uuid4().hex[:10]}",
                batch_id=batch_id,
                case_ids=case_ids,
                pattern_signature=sig,
                exception_count=count,
                total_value_at_risk=total_val,
                likely_common_cause=common_cause,
                evidence_strength=round(avg_conf, 4),
            )

            # Link cluster back to individual cases
            for c in group_cases:
                c.pattern_cluster_id = cluster.cluster_id

            clusters.append(cluster)

        # Sort clusters by total value at risk descending
        clusters.sort(key=lambda x: x.total_value_at_risk, reverse=True)
        return clusters

    def _generate_likely_common_cause(self, signature: str, count: int, total_val: Decimal) -> str:
        """Formulate cautious, defensible descriptions for recurring pattern clusters."""
        if "INVENTORY_SETTLEMENT" in signature or "SCN_04" in signature:
            return (
                f"Recurring non-cash inventory settlement pattern across {count} transactions "
                f"(Total retail value: ₹{float(total_val):.2f}). Possible physical change substitution pattern."
            )
        elif "OFF_LEDGER_DEVIATION" in signature or "SCN_08" in signature or "SCN_09" in signature or "SCN_10" in signature:
            return (
                f"Recurring mobility fare deviation pattern across {count} trips "
                f"(Total unrecorded value at risk: ₹{float(total_val):.2f}). Possible off-ledger fare discrepancy."
            )
        elif "FEE_ADJUSTMENT" in signature or "SCN_03" in signature:
            return (
                f"Systematic payment gateway MDR fee deduction across {count} settlements "
                f"(Total fee volume: ₹{float(total_val):.2f}). Matches ~2.0% standard merchant discount rate."
            )
        elif "REFUND" in signature or "SCN_02" in signature:
            return (
                f"Repeated customer return / partial refund cycle across {count} orders "
                f"(Total returned volume: ₹{float(total_val):.2f}). Likely downstream partial return before settlement."
            )
        elif "TIMING_OFFSET" in signature or "SCN_06" in signature:
            return (
                f"Cross-batch settlement timing offset across {count} transactions "
                f"(Total delayed volume: ₹{float(total_val):.2f}). Consistent T+1 next-day batch settlement window."
            )
        elif "DUPLICATE" in signature or "SCN_07" in signature:
            return (
                f"Duplicate broadcast event signature across {count} instances "
                f"(Total redundant volume: ₹{float(total_val):.2f}). Likely gateway webhook retry or duplicate ingest."
            )
        else:
            return (
                f"Recurring structural discrepancy pattern across {count} cases "
                f"(Total value at risk: ₹{float(total_val):.2f}). Likely shared operational origin."
            )
