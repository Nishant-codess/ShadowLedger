"""Batch-level normalization coordinator."""

from typing import Any

from app.domain.models import InventoryMove, Observation
from app.engine.normalizer import normalize_record


def normalize_batch(
    raw_records: list[dict[str, Any]], batch_id: str = "default"
) -> tuple[list[Observation], list[InventoryMove]]:
    """Convert a batch of raw record dictionaries into validated domain observations."""
    observations: list[Observation] = []
    inventory_moves: list[InventoryMove] = []

    for raw in raw_records:
        obs, inv = normalize_record(raw, batch_id=batch_id)
        observations.append(obs)
        if inv:
            inventory_moves.append(inv)

    return observations, inventory_moves
