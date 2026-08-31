"""Pydantic v2 domain models for ShadowLedger."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import (
    ActionRisk,
    DecisionType,
    EventStatus,
    EventType,
    HypothesisType,
    ValuationBasis,
    ValueType,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class DomainBase(BaseModel):
    """Base model with JSON serialization configuration for Decimal/datetime."""

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class Observation(DomainBase):
    """Immutable source record ingested directly from upstream systems."""

    observation_id: str = Field(default_factory=lambda: f"obs_{uuid4().hex[:12]}")
    source_system: str
    source_record_id: str
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    event_type: EventType
    amount: Decimal
    currency: str = "INR"
    timestamp: datetime
    entity_ids: dict[str, str] = Field(default_factory=dict)
    description: str = ""
    batch_id: str = "default"
    ingested_at: datetime = Field(default_factory=_utc_now)


class InventoryMove(DomainBase):
    """Inventory asset movement with rigorous valuation breakdown for change settlements."""

    move_id: str = Field(default_factory=lambda: f"inv_{uuid4().hex[:12]}")
    observation_id: str
    sku: str | None = None
    item_description: str
    quantity: Decimal = Decimal("1.0")
    unit_cost: Decimal | None = None
    retail_value: Decimal | None = None
    valuation_basis: ValuationBasis = ValuationBasis.UNKNOWN
    linked_order_id: str | None = None
    timestamp: datetime = Field(default_factory=_utc_now)


class Event(DomainBase):
    """Normalized financial event classified across the 4-level event taxonomy."""

    event_id: str = Field(default_factory=lambda: f"evt_{uuid4().hex[:12]}")
    status: EventStatus
    event_type: EventType
    amount: Decimal
    currency: str = "INR"
    timestamp: datetime
    entity_ids: dict[str, str] = Field(default_factory=dict)
    source_observation_ids: list[str] = Field(default_factory=list)
    confidence: float | None = None
    hypothesis_type: HypothesisType | None = None
    contradiction_ids: list[str] = Field(default_factory=list)
    batch_id: str = "default"

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float | None, info: Any) -> float | None:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v


class ValueFlow(DomainBase):
    """Directed edge in a value-flow graph representing conservation of economic value."""

    flow_id: str = Field(default_factory=lambda: f"flow_{uuid4().hex[:12]}")
    source_event_id: str
    target_event_id: str
    amount: Decimal
    value_type: ValueType = ValueType.CASH
    direction: str = "transfer"
    evidence_ids: list[str] = Field(default_factory=list)
    valuation_basis: ValuationBasis | None = None


class Hypothesis(DomainBase):
    """Candidate latent economic event with explicit evidence scoring separated from decision risk."""

    hypothesis_id: str = Field(default_factory=lambda: f"hyp_{uuid4().hex[:12]}")
    hypothesis_type: HypothesisType
    case_id: str
    generated_event: Event
    evidence_ids: list[str] = Field(default_factory=list)
    contradiction_ids: list[str] = Field(default_factory=list)
    indirect_evidence_ids: list[str] = Field(default_factory=list)

    # Pure evidence scoring dimensions (how strongly facts support H)
    evidence_coverage: float = 0.0
    amount_consistency: float = 0.0
    temporal_consistency: float = 0.0
    entity_consistency: float = 0.0
    business_rule_fit: float = 0.0
    assumption_cost: float = 0.0
    contradiction_cost: float = 0.0
    evidence_score: float = 0.0
    evidence_confidence: float = 0.0

    # Decision risk dimensions (how dangerous to act if wrong)
    financial_impact: Decimal = Decimal("0.00")
    constraints_satisfied: list[str] = Field(default_factory=list)
    constraints_violated: list[str] = Field(default_factory=list)
    can_auto_resolve: bool = True

    @field_validator("can_auto_resolve")
    @classmethod
    def enforce_off_ledger_safety(cls, v: bool, info: Any) -> bool:
        # Off-ledger payment deviation can NEVER auto-resolve
        if info.data.get("hypothesis_type") == HypothesisType.OFF_LEDGER_DEVIATION:
            return False
        return v


class Decision(DomainBase):
    """Decision gate outcome incorporating evidence confidence and decision risk."""

    decision_id: str = Field(default_factory=lambda: f"dec_{uuid4().hex[:12]}")
    case_id: str
    decision: DecisionType
    winning_hypothesis_id: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)

    # Independent evaluation dimensions
    evidence_confidence: float = 0.0
    contradiction_severity: float = 0.0
    financial_materiality: Decimal = Decimal("0.00")
    action_risk: ActionRisk = ActionRisk.LOW

    engine_version: str = "0.1.0"
    model_version: str | None = None
    decided_at: datetime = Field(default_factory=_utc_now)


class Case(DomainBase):
    """Unit of discrepancy investigation containing connected evidence and candidate hypotheses."""

    case_id: str = Field(default_factory=lambda: f"case_{uuid4().hex[:12]}")
    batch_id: str
    observation_ids: list[str] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    decision: Decision | None = None
    residual_amount: Decimal = Decimal("0.00")
    financial_impact: Decimal = Decimal("0.00")
    pattern_cluster_id: str | None = None
    scenario_id: str | None = None
    status: str = "open"
    graph_json: dict[str, Any] | None = None
    shadow_events: list[Event] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)


class PatternCluster(DomainBase):
    """Recurring structural pattern across multiple discrepancy cases."""

    cluster_id: str = Field(default_factory=lambda: f"pat_{uuid4().hex[:12]}")
    batch_id: str
    case_ids: list[str] = Field(default_factory=list)
    pattern_signature: str
    exception_count: int = 0
    total_value_at_risk: Decimal = Decimal("0.00")
    likely_common_cause: str = ""
    evidence_strength: float = 0.0
    created_at: datetime = Field(default_factory=_utc_now)


class BatchMetadata(DomainBase):
    """Summary metrics and configuration for an ingested and processed batch."""

    batch_id: str
    seed: int | None = None
    record_count: int = 0
    matched_count: int = 0
    exception_count: int = 0
    resolved_count: int = 0
    review_count: int = 0
    unresolved_count: int = 0
    total_volume_inr: Decimal = Decimal("0.00")
    explained_volume_inr: Decimal = Decimal("0.00")
    unexplained_volume_inr: Decimal = Decimal("0.00")
    processing_time_ms: float = 0.0
    created_at: datetime = Field(default_factory=_utc_now)
