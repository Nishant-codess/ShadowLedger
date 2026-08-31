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
    match_rate: float
    throughput_records_per_sec: float
    total_volume_inr: float
    explained_volume_inr: float
    unexplained_volume_inr: float
    processing_time_ms: float
    reason_code_breakdown: dict[str, int] = Field(default_factory=dict)


class CaseDetailResponse(BaseModel):
    """Detail of an investigated discrepancy case."""

    case_id: str
    batch_id: str
    observation_ids: list[str]
    residual_amount: float
    financial_impact: float
    scenario_id: str | None = None
    status: str = "open"
    decision: dict[str, Any] | None = None
    observations: list[dict[str, Any]] = Field(default_factory=list)
