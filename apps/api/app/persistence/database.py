"""DuckDB persistence manager and schema DDL."""

from pathlib import Path
from typing import Any

import duckdb


class DatabaseManager:
    """Manages embedded DuckDB connection and schema initialization."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(database=db_path)
        self.init_schema()

    def init_schema(self) -> None:
        """Initialize all relational tables in DuckDB."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                observation_id VARCHAR PRIMARY KEY,
                source_system VARCHAR NOT NULL,
                source_record_id VARCHAR NOT NULL,
                raw_payload VARCHAR,
                event_type VARCHAR NOT NULL,
                amount DECIMAL(18, 2) NOT NULL,
                currency VARCHAR DEFAULT 'INR',
                timestamp TIMESTAMP NOT NULL,
                entity_ids VARCHAR,
                description VARCHAR,
                batch_id VARCHAR NOT NULL,
                ingested_at TIMESTAMP NOT NULL
            );

            CREATE TABLE IF NOT EXISTS inventory_moves (
                move_id VARCHAR PRIMARY KEY,
                observation_id VARCHAR NOT NULL,
                sku VARCHAR,
                item_description VARCHAR NOT NULL,
                quantity DECIMAL(18, 4) NOT NULL,
                unit_cost DECIMAL(18, 2),
                retail_value DECIMAL(18, 2),
                valuation_basis VARCHAR NOT NULL,
                linked_order_id VARCHAR,
                timestamp TIMESTAMP NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                event_id VARCHAR PRIMARY KEY,
                status VARCHAR NOT NULL,
                event_type VARCHAR NOT NULL,
                amount DECIMAL(18, 2) NOT NULL,
                currency VARCHAR DEFAULT 'INR',
                timestamp TIMESTAMP NOT NULL,
                entity_ids VARCHAR,
                source_observation_ids VARCHAR,
                confidence DOUBLE,
                hypothesis_type VARCHAR,
                contradiction_ids VARCHAR,
                batch_id VARCHAR NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cases (
                case_id VARCHAR PRIMARY KEY,
                batch_id VARCHAR NOT NULL,
                observation_ids VARCHAR NOT NULL,
                residual_amount DECIMAL(18, 2) NOT NULL,
                financial_impact DECIMAL(18, 2) NOT NULL,
                pattern_cluster_id VARCHAR,
                scenario_id VARCHAR,
                status VARCHAR DEFAULT 'open',
                graph_json VARCHAR,
                created_at TIMESTAMP NOT NULL
            );

            CREATE TABLE IF NOT EXISTS decisions (
                decision_id VARCHAR PRIMARY KEY,
                case_id VARCHAR NOT NULL,
                decision VARCHAR NOT NULL,
                winning_hypothesis_id VARCHAR,
                reason_codes VARCHAR,
                evidence_ids VARCHAR,
                evidence_confidence DOUBLE,
                contradiction_severity DOUBLE,
                financial_materiality DECIMAL(18, 2),
                action_risk VARCHAR,
                engine_version VARCHAR,
                model_version VARCHAR,
                decided_at TIMESTAMP NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pattern_clusters (
                cluster_id VARCHAR PRIMARY KEY,
                batch_id VARCHAR NOT NULL,
                case_ids VARCHAR NOT NULL,
                pattern_signature VARCHAR NOT NULL,
                exception_count INTEGER NOT NULL,
                total_value_at_risk DECIMAL(18, 2) NOT NULL,
                likely_common_cause VARCHAR NOT NULL,
                evidence_strength DOUBLE NOT NULL,
                created_at TIMESTAMP NOT NULL
            );

            CREATE TABLE IF NOT EXISTS batches (
                batch_id VARCHAR PRIMARY KEY,
                seed INTEGER,
                record_count INTEGER NOT NULL,
                matched_count INTEGER NOT NULL,
                exception_count INTEGER NOT NULL,
                resolved_count INTEGER NOT NULL,
                review_count INTEGER NOT NULL,
                unresolved_count INTEGER NOT NULL,
                total_volume_inr DECIMAL(18, 2) NOT NULL,
                explained_volume_inr DECIMAL(18, 2) NOT NULL,
                unexplained_volume_inr DECIMAL(18, 2) NOT NULL,
                processing_time_ms DOUBLE NOT NULL,
                created_at TIMESTAMP NOT NULL
            );
        """)

    def execute(self, query: str, params: list[Any] | None = None) -> duckdb.DuckDBPyConnection:
        if params:
            return self.conn.execute(query, params)
        return self.conn.execute(query)

    def close(self) -> None:
        self.conn.close()
