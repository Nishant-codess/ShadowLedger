"""Data package exports."""

from app.data.ingest import (
    IngestionResult,
    ingest_from_csv_file,
    ingest_from_dicts,
    ingest_from_json_file,
)
from app.data.normalize import normalize_batch

__all__ = [
    "IngestionResult",
    "ingest_from_dicts",
    "ingest_from_json_file",
    "ingest_from_csv_file",
    "normalize_batch",
]
