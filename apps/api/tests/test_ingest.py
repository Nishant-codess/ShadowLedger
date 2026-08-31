"""Unit tests for file and memory ingestion."""

import json
from pathlib import Path

from app.data.ingest import (
    ingest_from_csv_file,
    ingest_from_dicts,
    ingest_from_json_file,
)


def test_ingest_from_dicts_isolates_malformed_rows():
    """Verify malformed records with missing amounts or non-dicts are cleanly tracked."""
    records = [
        {"source_system": "pos", "amount": 100, "description": "Valid 1"},
        "not a dict string",
        {"source_system": "bank"},  # Missing amount
        {"source_system": "gateway", "amount": "200.50", "description": "Valid 2"},
    ]

    res = ingest_from_dicts(records)
    assert res.total_count == 4
    assert len(res.valid_records) == 2
    assert len(res.malformed_records) == 2
    assert res.error_count == 2


def test_ingest_from_json_file(tmp_path: Path):
    """Verify loading records from JSON file on disk."""
    file_p = tmp_path / "test_batch.json"
    data = [
        {"source_system": "pos", "amount": 500, "source_record_id": "p1"},
        {"source_system": "bank", "amount": 500, "source_record_id": "b1"},
    ]
    with open(file_p, "w", encoding="utf-8") as f:
        json.dump(data, f)

    res = ingest_from_json_file(file_p)
    assert len(res.valid_records) == 2
    assert res.error_count == 0


def test_ingest_from_csv_file(tmp_path: Path):
    """Verify loading records from CSV file with column mapping."""
    file_p = tmp_path / "test_batch.csv"
    with open(file_p, "w", encoding="utf-8") as f:
        f.write("source_system,amount,source_record_id,description\n")
        f.write("pos,1200.00,pos_csv_1,POS CSV Sale\n")
        f.write("bank,1200.00,bnk_csv_1,Bank Settlement\n")

    res = ingest_from_csv_file(file_p)
    assert len(res.valid_records) == 2
    assert res.valid_records[0]["amount"] == "1200.00"
