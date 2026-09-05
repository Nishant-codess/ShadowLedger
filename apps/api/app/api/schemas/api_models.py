"""API request and response schemas."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check endpoint response."""

    status: str = "ok"
    version: str = "0.1.0"
    engine: str = "deterministic_baseline"
    database: str = "duckdb_embedded"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProcessBatchRequest(BaseModel):
    """Parameters for generating and processing a synthetic financial batch."""

    seed: int | None = 42
    rows: int = 100
    batch_id: str | None = None
    records: list[dict[str, Any]] | None = None


class BatchSummaryResponse(BaseModel):
    """Summary of a processed batch."""

    batch_id: str
    record_count: int
    matched_count: int
    exception_count: int
    auto_resolved_count: int = 0
    human_review_count: int = 0
    unresolved_count: int = 0
    match_rate: float
    enhanced_resolution_rate: float = 0.0
    throughput_records_per_sec: float
    total_volume_inr: float
    explained_volume_inr: float
    unexplained_volume_inr: float
    processing_time_ms: float
    reason_code_breakdown: dict[str, int] = Field(default_factory=dict)
    pattern_clusters: list[dict[str, Any]] = Field(default_factory=list)


class CaseDetailResponse(BaseModel):
    """Detail of an investigated discrepancy case."""

    case_id: str
    batch_id: str
    observation_ids: list[str]
    residual_amount: float
    financial_impact: float
    scenario_id: str | None = None
    status: str = "open"
    pattern_cluster_id: str | None = None
    graph_json: dict[str, Any] | None = None
    shadow_events: list[dict[str, Any]] = Field(default_factory=list)
    decision: dict[str, Any] | None = None
    observations: list[dict[str, Any]] = Field(default_factory=list)


class PatternClusterResponse(BaseModel):
    """Recurring structural pattern cluster response."""

    cluster_id: str
    batch_id: str
    case_ids: list[str]
    pattern_signature: str
    exception_count: int
    total_value_at_risk: float
    likely_common_cause: str
    evidence_strength: float
    created_at: datetime


class HeroDemoResponse(BaseModel):
    """Instant 1-click hero scenario response."""

    hero_id: str
    title: str
    description: str
    batch_summary: BatchSummaryResponse
    cases: list[CaseDetailResponse] = Field(default_factory=list)
    pattern_clusters: list[PatternClusterResponse] = Field(default_factory=list)


class AIExplainResponse(BaseModel):
    """Evidence-grounded natural language investigation narrative."""

    case_id: str
    headline: str
    economic_story: str
    policy_action: str
    narrative: str
    simple_narrative: str | None = None
    auditor_narrative: str | None = None
    deterministic_narrative: str | None = None
    provider: str
    hypothesis_type: str
    taxonomy_level: str
    evidence_confidence: float
    decision: str
    reason_codes: list[str] = Field(default_factory=list)
    total_payment: float
    total_settlement: float
    residual_amount: float


class CaseActionRequest(BaseModel):
    """Operator action to confirm, escalate, or override a case decision."""

    action: str  # e.g. "confirm_settlement", "escalate_ops", "reject_hypothesis"
    operator_notes: str | None = None
    operator_id: str = "FIN_OPS_USER"

