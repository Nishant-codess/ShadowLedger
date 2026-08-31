"""Shadow Ledger: Append-Only Inferred Event Store & Provenance Manager.

Maintains immutable separation between official source observations and
reconstructed latent economic events, tracking complete audit provenance.
"""

from typing import Any
from uuid import uuid4

from app.domain.enums import EventStatus
from app.domain.models import Case, Decision, Event, Hypothesis, Observation


class ShadowLedgerManager:
    """Manages the lifecycle and provenance of inferred latent events."""

    def create_shadow_events_for_case(
        self,
        case: Case,
        winning_hypothesis: Hypothesis | None,
        decision: Decision,
    ) -> list[Event]:
        """Generate verified Shadow Ledger events from the winning hypothesis."""
        if not winning_hypothesis:
            return []

        shadow_events: list[Event] = []
        gen = winning_hypothesis.generated_event

        # Ensure correct taxonomy status based on hypothesis type and decision
        if winning_hypothesis.hypothesis_type.value == "off_ledger_deviation":
            status = EventStatus.UNOBSERVED_DEVIATION
        elif winning_hypothesis.hypothesis_type.value in ("fee_adjustment", "timing_offset", "duplicate_reversal"):
            status = EventStatus.DERIVED
        else:
            status = EventStatus.INFERRED_LATENT

        shadow_event = Event(
            event_id=f"shd_{uuid4().hex[:12]}",
            status=status,
            event_type=gen.event_type,
            amount=gen.amount,
            currency=gen.currency,
            timestamp=gen.timestamp,
            entity_ids=gen.entity_ids,
            source_observation_ids=case.observation_ids,
            confidence=winning_hypothesis.evidence_confidence,
            hypothesis_type=winning_hypothesis.hypothesis_type,
            contradiction_ids=winning_hypothesis.contradiction_ids,
            batch_id=case.batch_id,
        )

        shadow_events.append(shadow_event)
        return shadow_events

    def build_audit_trail(
        self,
        case: Case,
        observations: list[Observation],
        shadow_events: list[Event],
        decision: Decision,
    ) -> list[dict[str, Any]]:
        """Construct chronological provenance audit entries for a case."""
        trail: list[dict[str, Any]] = []

        # 1. Source observations (Official Ledger)
        for obs in observations:
            trail.append({
                "entry_type": "OFFICIAL_LEDGER_SOURCE",
                "record_id": obs.observation_id,
                "timestamp": obs.timestamp.isoformat(),
                "source_system": obs.source_system,
                "amount": float(obs.amount),
                "description": obs.description or f"{obs.source_system} {obs.event_type.value}",
                "status": EventStatus.OBSERVED.value,
                "confidence": 1.0,
            })

        # 2. Reconstructed Shadow Events (Shadow Ledger)
        for se in shadow_events:
            trail.append({
                "entry_type": "SHADOW_LEDGER_INFERENCE",
                "record_id": se.event_id,
                "timestamp": se.timestamp.isoformat(),
                "source_system": "shadow_ledger_engine",
                "amount": float(se.amount),
                "description": f"Inferred {se.event_type.value} [{se.hypothesis_type.value if se.hypothesis_type else 'unknown'}]",
                "status": se.status.value,
                "confidence": se.confidence or 0.0,
                "decision": decision.decision.value,
                "reason_codes": decision.reason_codes,
            })

        # Sort chronologically
        trail.sort(key=lambda x: x["timestamp"])
        return trail
