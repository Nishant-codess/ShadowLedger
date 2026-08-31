"""Batch data ingestion module supporting JSON and CSV formats."""

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class IngestionResult:
    """Outcome of parsing raw batch data files."""

    valid_records: list[dict[str, Any]]
    malformed_records: list[dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    error_count: int = 0


def ingest_from_dicts(records: list[dict[str, Any]]) -> IngestionResult:
    """Ingest and validate in-memory list of dictionary records."""
    valid: list[dict[str, Any]] = []
    malformed: list[dict[str, Any]] = []

    for idx, r in enumerate(records):
        if not isinstance(r, dict):
            malformed.append({"row_index": idx, "raw": str(r), "error": "Record is not a dictionary"})
            continue

        # Basic structural checks
        if "amount" not in r:
            malformed.append({"row_index": idx, "raw": r, "error": "Missing required field 'amount'"})
            continue

        valid.append(r)

    return IngestionResult(
        valid_records=valid,
        malformed_records=malformed,
        total_count=len(records),
        error_count=len(malformed),
    )


def ingest_from_json_file(file_path: str | Path) -> IngestionResult:
    """Read and parse records from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found at: {file_path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "records" in data:
        data = data["records"]

    if not isinstance(data, list):
        raise ValueError(f"Expected a list of JSON records in {file_path}")

    return ingest_from_dicts(data)


def ingest_from_csv_file(file_path: str | Path) -> IngestionResult:
    """Read and parse records from a CSV file with automatic column normalization."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found at: {file_path}")

    records: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse any embedded JSON in entity_ids or raw_payload
            record: dict[str, Any] = {}
            for k, v in row.items():
                if k == "entity_ids" and v:
                    try:
                        record[k] = json.loads(v)
                    except json.JSONDecodeError:
                        record[k] = {"raw": v}
                elif k == "amount":
                    record[k] = v
                else:
                    record[k] = v
            records.append(record)

    return ingest_from_dicts(records)
