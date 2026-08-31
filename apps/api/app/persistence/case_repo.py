"""Case, Decision, and Batch repository for DuckDB."""

import json
from decimal import Decimal

from app.domain.enums import ActionRisk, DecisionType
from app.domain.models import BatchMetadata, Case, Decision
from app.persistence.database import DatabaseManager


class CaseRepository:
    """CRUD operations for discrepancy Cases, Decisions, and Batches."""

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
                c.created_at,
            )
            for c in cases
        ]

        self.db.conn.executemany(
            """
            INSERT OR REPLACE INTO cases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            self.db.conn.executemany(
                """
                INSERT OR REPLACE INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                dec_data,
            )

    def get_cases_by_batch(self, batch_id: str) -> list[Case]:
        """Fetch all cases for a batch with their decisions attached."""
        rows = self.db.conn.execute(
            """
            SELECT c.case_id, c.batch_id, c.observation_ids, c.residual_amount,
                   c.financial_impact, c.pattern_cluster_id, c.scenario_id,
                   c.status, c.created_at,
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
        ).fetchall()

        cases: list[Case] = []
        for r in rows:
            decision = None
            if r[9]:  # If decision_id exists
                decision = Decision(
                    decision_id=r[9],
                    case_id=r[0],
                    decision=DecisionType(r[10]),
                    winning_hypothesis_id=r[11],
                    reason_codes=json.loads(r[12]) if r[12] else [],
                    evidence_ids=json.loads(r[13]) if r[13] else [],
                    evidence_confidence=r[14] or 0.0,
                    contradiction_severity=r[15] or 0.0,
                    financial_materiality=Decimal(str(r[16] or "0.00")),
                    action_risk=ActionRisk(r[17] or "low"),
                    engine_version=r[18] or "0.1.0",
                    model_version=r[19],
                    decided_at=r[20],
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
                    created_at=r[8],
                    decision=decision,
                )
            )
        return cases

    def save_batch_metadata(self, meta: BatchMetadata) -> None:
        """Insert or update batch processing summary."""
        self.db.conn.execute(
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
        row = self.db.conn.execute(
            """
            SELECT batch_id, seed, record_count, matched_count, exception_count,
                   resolved_count, review_count, unresolved_count,
                   total_volume_inr, explained_volume_inr, unexplained_volume_inr,
                   processing_time_ms, created_at
            FROM batches WHERE batch_id = ?
            """,
            [batch_id],
        ).fetchone()

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
        rows = self.db.conn.execute(
            """
            SELECT batch_id, seed, record_count, matched_count, exception_count,
                   resolved_count, review_count, unresolved_count,
                   total_volume_inr, explained_volume_inr, unexplained_volume_inr,
                   processing_time_ms, created_at
            FROM batches ORDER BY created_at DESC
            """
        ).fetchall()

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
