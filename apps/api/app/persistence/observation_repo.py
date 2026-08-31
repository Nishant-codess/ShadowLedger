"""Observation and InventoryMove repository for DuckDB."""

import json
from decimal import Decimal

from app.domain.enums import EventType, ValuationBasis
from app.domain.models import InventoryMove, Observation
from app.persistence.database import DatabaseManager


class ObservationRepository:
    """CRUD operations for raw source observations and inventory moves."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def save_observations(self, observations: list[Observation]) -> None:
        """Batch insert observations into DuckDB."""
        if not observations:
            return

        data = [
            (
                obs.observation_id,
                obs.source_system,
                obs.source_record_id,
                json.dumps(obs.raw_payload),
                obs.event_type.value,
                float(obs.amount),
                obs.currency,
                obs.timestamp,
                json.dumps(obs.entity_ids),
                obs.description,
                obs.batch_id,
                obs.ingested_at,
            )
            for obs in observations
        ]

        self.db.conn.executemany(
            """
            INSERT OR REPLACE INTO observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            data,
        )

    def save_inventory_moves(self, moves: list[InventoryMove]) -> None:
        """Batch insert inventory movement records into DuckDB."""
        if not moves:
            return

        data = [
            (
                m.move_id,
                m.observation_id,
                m.sku,
                m.item_description,
                float(m.quantity),
                float(m.unit_cost) if m.unit_cost is not None else None,
                float(m.retail_value) if m.retail_value is not None else None,
                m.valuation_basis.value,
                m.linked_order_id,
                m.timestamp,
            )
            for m in moves
        ]

        self.db.conn.executemany(
            """
            INSERT OR REPLACE INTO inventory_moves VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            data,
        )

    def get_by_batch(self, batch_id: str) -> list[Observation]:
        """Fetch all observations for a given batch ID."""
        rows = self.db.conn.execute(
            """
            SELECT observation_id, source_system, source_record_id, raw_payload,
                   event_type, amount, currency, timestamp, entity_ids,
                   description, batch_id, ingested_at
            FROM observations WHERE batch_id = ?
            ORDER BY timestamp ASC
            """,
            [batch_id],
        ).fetchall()

        results: list[Observation] = []
        for r in rows:
            results.append(
                Observation(
                    observation_id=r[0],
                    source_system=r[1],
                    source_record_id=r[2],
                    raw_payload=json.loads(r[3]) if r[3] else {},
                    event_type=EventType(r[4]),
                    amount=Decimal(str(r[5])),
                    currency=r[6],
                    timestamp=r[7],
                    entity_ids=json.loads(r[8]) if r[8] else {},
                    description=r[9] or "",
                    batch_id=r[10],
                    ingested_at=r[11],
                )
            )
        return results

    def get_inventory_by_batch(self, batch_id: str) -> list[InventoryMove]:
        """Fetch all inventory moves connected to observations in a batch."""
        rows = self.db.conn.execute(
            """
            SELECT m.move_id, m.observation_id, m.sku, m.item_description,
                   m.quantity, m.unit_cost, m.retail_value, m.valuation_basis,
                   m.linked_order_id, m.timestamp
            FROM inventory_moves m
            JOIN observations o ON m.observation_id = o.observation_id
            WHERE o.batch_id = ?
            """,
            [batch_id],
        ).fetchall()

        results: list[InventoryMove] = []
        for r in rows:
            results.append(
                InventoryMove(
                    move_id=r[0],
                    observation_id=r[1],
                    sku=r[2],
                    item_description=r[3],
                    quantity=Decimal(str(r[4])),
                    unit_cost=Decimal(str(r[5])) if r[5] is not None else None,
                    retail_value=Decimal(str(r[6])) if r[6] is not None else None,
                    valuation_basis=ValuationBasis(r[7]),
                    linked_order_id=r[8],
                    timestamp=r[9],
                )
            )
        return results
