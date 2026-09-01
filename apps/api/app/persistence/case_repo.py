"""Case, Decision, and Batch repository for DuckDB."""

import json
from decimal import Decimal

from app.domain.enums import ActionRisk, DecisionType
from app.domain.models import BatchMetadata, Case, Decision, Event, PatternCluster
from app.persistence.database import DatabaseManager


class CaseRepository:
    """CRUD operations for discrepancy Cases, Decisions, Batches, Events, and Pattern Clusters."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def save_cases(self, cases: list[Case]) -> None:
        """Batch save cases and associated decisions."""
        if not cases:
            return

        case_data = [
            (
                c.case_id,
                c.batch_id,
                json.dumps(c.observation_ids),
                float(c.residual_amount),
                float(c.financial_impact),
                c.pattern_cluster_id,
                c.scenario_id,
                c.status,
                json.dumps(c.graph_json) if c.graph_json else None,
                c.created_at,
            )
            for c in cases
        ]

        self.db.executemany(
            """
            INSERT OR REPLACE INTO cases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            case_data,
        )

        # Save decisions if present
        decisions_to_save: list[Decision] = [c.decision for c in cases if c.decision]
        if decisions_to_save:
            dec_data = [
                (
                    d.decision_id,
                    d.case_id,
                    d.decision.value,
                    d.winning_hypothesis_id,
                    json.dumps(d.reason_codes),
                    json.dumps(d.evidence_ids),
                    d.evidence_confidence,
                    d.contradiction_severity,
                    float(d.financial_materiality),
                    d.action_risk.value,
                    d.engine_version,
                    d.model_version,
                    d.decided_at,
                )
                for d in decisions_to_save
            ]
            self.db.executemany(
                """
                INSERT OR REPLACE INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                dec_data,
            )

        # Save shadow events if attached
        all_shadow_events: list[Event] = []
        for c in cases:
            all_shadow_events.extend(c.shadow_events)
        if all_shadow_events:
            self.save_events(all_shadow_events)

    def get_cases_by_batch(self, batch_id: str) -> list[Case]:
        """Fetch all cases for a batch with their decisions attached."""
        rows = self.db.query_all(
            """
            SELECT c.case_id, c.batch_id, c.observation_ids, c.residual_amount,
                   c.financial_impact, c.pattern_cluster_id, c.scenario_id,
                   c.status, c.graph_json, c.created_at,
                   d.decision_id, d.decision, d.winning_hypothesis_id,
                   d.reason_codes, d.evidence_ids, d.evidence_confidence,
                   d.contradiction_severity, d.financial_materiality, d.action_risk,
                   d.engine_version, d.model_version, d.decided_at
            FROM cases c
            LEFT JOIN decisions d ON c.case_id = d.case_id
            WHERE c.batch_id = ?
            ORDER BY c.financial_impact DESC
            """,
            [batch_id],
        )

        cases: list[Case] = []
        for r in rows:
            decision = None
            if r[10]:  # If decision_id exists
                decision = Decision(
                    decision_id=r[10],
                    case_id=r[0],
                    decision=DecisionType(r[11]),
                    winning_hypothesis_id=r[12],
                    reason_codes=json.loads(r[13]) if r[13] else [],
                    evidence_ids=json.loads(r[14]) if r[14] else [],
                    evidence_confidence=r[15] or 0.0,
                    contradiction_severity=r[16] or 0.0,
                    financial_materiality=Decimal(str(r[17] or "0.00")),
                    action_risk=ActionRisk(r[18] or "low"),
                    engine_version=r[19] or "0.1.0",
                    model_version=r[20],
                    decided_at=r[21],
                )

            cases.append(
                Case(
                    case_id=r[0],
                    batch_id=r[1],
                    observation_ids=json.loads(r[2]) if r[2] else [],
                    residual_amount=Decimal(str(r[3])),
                    financial_impact=Decimal(str(r[4])),
                    pattern_cluster_id=r[5],
                    scenario_id=r[6],
                    status=r[7],
                    graph_json=json.loads(r[8]) if r[8] else None,
                    created_at=r[9],
                    decision=decision,
                )
            )
        return cases

    def get_case_by_id(self, case_id: str) -> Case | None:
        """Fetch a single case by ID."""
        row = self.db.query_one(
            """
            SELECT c.case_id, c.batch_id, c.observation_ids, c.residual_amount,
                   c.financial_impact, c.pattern_cluster_id, c.scenario_id,
                   c.status, c.graph_json, c.created_at,
                   d.decision_id, d.decision, d.winning_hypothesis_id,
                   d.reason_codes, d.evidence_ids, d.evidence_confidence,
                   d.contradiction_severity, d.financial_materiality, d.action_risk,
                   d.engine_version, d.model_version, d.decided_at
            FROM cases c
            LEFT JOIN decisions d ON c.case_id = d.case_id
            WHERE c.case_id = ?
            """,
            [case_id],
        )

        if not row:
            return None

        decision = None
        if row[10]:
            decision = Decision(
                decision_id=row[10],
                case_id=row[0],
                decision=DecisionType(row[11]),
                winning_hypothesis_id=row[12],
                reason_codes=json.loads(row[13]) if row[13] else [],
                evidence_ids=json.loads(row[14]) if row[14] else [],
                evidence_confidence=row[15] or 0.0,
                contradiction_severity=row[16] or 0.0,
                financial_materiality=Decimal(str(row[17] or "0.00")),
                action_risk=ActionRisk(row[18] or "low"),
                engine_version=row[19] or "0.1.0",
                model_version=row[20],
                decided_at=row[21],
            )

        return Case(
            case_id=row[0],
            batch_id=row[1],
            observation_ids=json.loads(row[2]) if row[2] else [],
            residual_amount=Decimal(str(row[3])),
            financial_impact=Decimal(str(row[4])),
            pattern_cluster_id=row[5],
            scenario_id=row[6],
            status=row[7],
            graph_json=json.loads(row[8]) if row[8] else None,
            created_at=row[9],
            decision=decision,
        )

    def save_events(self, events: list[Event]) -> None:
        """Insert or replace normalized financial and shadow ledger events."""
        if not events:
            return

        event_data = [
            (
                e.event_id,
                e.status.value,
                e.event_type.value,
                float(e.amount),
                e.currency,
                e.timestamp,
                json.dumps(e.entity_ids),
                json.dumps(e.source_observation_ids),
                e.confidence,
                e.hypothesis_type.value if e.hypothesis_type else None,
                json.dumps(e.contradiction_ids),
                e.batch_id,
            )
            for e in events
        ]

        self.db.executemany(
            """
            INSERT OR REPLACE INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            event_data,
        )

    def save_pattern_clusters(self, clusters: list[PatternCluster]) -> None:
        """Insert or replace pattern clusters."""
        if not clusters:
            return

        cluster_data = [
            (
                c.cluster_id,
                c.batch_id,
                json.dumps(c.case_ids),
                c.pattern_signature,
                c.exception_count,
                float(c.total_value_at_risk),
                c.likely_common_cause,
                c.evidence_strength,
                c.created_at,
            )
            for c in clusters
        ]

        self.db.executemany(
            """
            INSERT OR REPLACE INTO pattern_clusters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            cluster_data,
        )

    def get_pattern_clusters_by_batch(self, batch_id: str) -> list[PatternCluster]:
        """Fetch all pattern clusters for a batch."""
        rows = self.db.query_all(
            """
            SELECT cluster_id, batch_id, case_ids, pattern_signature,
                   exception_count, total_value_at_risk, likely_common_cause,
                   evidence_strength, created_at
            FROM pattern_clusters
            WHERE batch_id = ?
            ORDER BY total_value_at_risk DESC
            """,
            [batch_id],
        )

        return [
            PatternCluster(
                cluster_id=r[0],
                batch_id=r[1],
                case_ids=json.loads(r[2]) if r[2] else [],
                pattern_signature=r[3],
                exception_count=r[4],
                total_value_at_risk=Decimal(str(r[5])),
                likely_common_cause=r[6],
                evidence_strength=r[7],
                created_at=r[8],
            )
            for r in rows
        ]

    def save_batch_metadata(self, meta: BatchMetadata) -> None:
        """Insert or update batch processing summary."""
        self.db.execute(
            """
            INSERT OR REPLACE INTO batches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                meta.batch_id,
                meta.seed,
                meta.record_count,
                meta.matched_count,
                meta.exception_count,
                meta.resolved_count,
                meta.review_count,
                meta.unresolved_count,
                float(meta.total_volume_inr),
                float(meta.explained_volume_inr),
                float(meta.unexplained_volume_inr),
                meta.processing_time_ms,
                meta.created_at,
            ],
        )

    def get_batch_metadata(self, batch_id: str) -> BatchMetadata | None:
        """Retrieve batch summary by ID."""
        row = self.db.query_one(
            """
            SELECT batch_id, seed, record_count, matched_count, exception_count,
                   resolved_count, review_count, unresolved_count,
                   total_volume_inr, explained_volume_inr, unexplained_volume_inr,
                   processing_time_ms, created_at
            FROM batches WHERE batch_id = ?
            """,
            [batch_id],
        )

        if not row:
            return None

        return BatchMetadata(
            batch_id=row[0],
            seed=row[1],
            record_count=row[2],
            matched_count=row[3],
            exception_count=row[4],
            resolved_count=row[5],
            review_count=row[6],
            unresolved_count=row[7],
            total_volume_inr=Decimal(str(row[8])),
            explained_volume_inr=Decimal(str(row[9])),
            unexplained_volume_inr=Decimal(str(row[10])),
            processing_time_ms=row[11],
            created_at=row[12],
        )

    def list_all_batches(self) -> list[BatchMetadata]:
        """List all processed batches ordered by creation time."""
        rows = self.db.query_all(
            """
            SELECT batch_id, seed, record_count, matched_count, exception_count,
                   resolved_count, review_count, unresolved_count,
                   total_volume_inr, explained_volume_inr, unexplained_volume_inr,
                   processing_time_ms, created_at
            FROM batches ORDER BY created_at DESC
            """
        )

        return [
            BatchMetadata(
                batch_id=r[0],
                seed=r[1],
                record_count=r[2],
                matched_count=r[3],
                exception_count=r[4],
                resolved_count=r[5],
                review_count=r[6],
                unresolved_count=r[7],
                total_volume_inr=Decimal(str(r[8])),
                explained_volume_inr=Decimal(str(r[9])),
                unexplained_volume_inr=Decimal(str(r[10])),
                processing_time_ms=r[11],
                created_at=r[12],
            )
            for r in rows
        ]
