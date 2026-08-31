#!/usr/bin/env python3
"""Synthetic financial dataset generator.

Generates realistic multi-source financial logs (POS, Gateway, Bank, Inventory, Platform)
alongside an isolated hidden ground-truth file for evaluation.
"""

import argparse
import csv
import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add apps/api to sys.path so we can import domain scenarios
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "apps" / "api"))

from app.domain.scenarios import SCENARIOS


def generate_dataset(rows: int, seed: int, output_dir: Path, truth_dir: Path, batch_name: str | None = None) -> tuple[Path, Path, Path]:
    """Generate multi-source financial logs and hidden ground truth."""
    output_dir.mkdir(parents=True, exist_ok=True)
    truth_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    base_time = datetime(2026, 8, 31, 9, 0, 0, tzinfo=UTC)
    batch_id = batch_name or f"batch_s{seed}_r{rows}"

    # Scenario distribution reflecting realistic business mix
    scenario_weights = [
        ("SCN_01", 50),  # 50% Clean match
        ("SCN_02", 10),  # 10% Partial refund
        ("SCN_03", 10),  # 10% Fee adjustment
        ("SCN_04", 5),   # 5% Kirana non-cash inventory settlement
        ("SCN_05", 5),   # 5% Store credit carry-forward
        ("SCN_06", 5),   # 5% Next-day timing offset
        ("SCN_07", 5),   # 5% Duplicate broadcast
        ("SCN_08", 3),   # 3% Ride digital trace deviation
        ("SCN_09", 2),   # 2% Ride cash invisible deviation
        ("SCN_10", 2),   # 2% Recurring micro-deviation pattern
        ("SCN_11", 1),   # 1% Upstream batch surcharge
        ("SCN_12", 2),   # 2% Adversarial near-match
    ]

    pool = [s for s, w in scenario_weights for _ in range(w)]
    observed_records: list[dict] = []
    ground_truth_records: list[dict] = []

    idx = 0
    while len(observed_records) < rows:
        scn_id = rng.choice(pool)
        defn = SCENARIOS[scn_id]
        time_offset = base_time.timestamp() + (idx * 15)
        case_time = datetime.fromtimestamp(time_offset, tz=UTC)

        obs_items, truth = defn.generator(rng, idx, case_time)
        for item in obs_items:
            item["batch_id"] = batch_id
            observed_records.append(item)
            if len(observed_records) >= rows:
                break
        ground_truth_records.append(truth)
        idx += 1

    # Save observed records to JSON
    json_path = output_dir / f"{batch_id}_observed.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"batch_id": batch_id, "seed": seed, "records": observed_records}, f, indent=2)

    # Save observed records to CSV
    csv_path = output_dir / f"{batch_id}_observed.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["source_system", "source_record_id", "event_type", "amount", "currency", "timestamp", "description", "entity_ids", "batch_id"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in observed_records:
            row_dict = dict(r)
            if "entity_ids" in row_dict and isinstance(row_dict["entity_ids"], dict):
                row_dict["entity_ids"] = json.dumps(row_dict["entity_ids"])
            writer.writerow(row_dict)

    # Save isolated hidden ground truth
    truth_path = truth_dir / f"{batch_id}_truth.json"
    with open(truth_path, "w", encoding="utf-8") as f:
        json.dump({"batch_id": batch_id, "seed": seed, "ground_truth": ground_truth_records}, f, indent=2)

    return json_path, csv_path, truth_path


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic financial batches for ShadowLedger")
    parser.add_argument("--rows", type=int, default=1000, help="Number of records to generate (default: 1000)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic generation (default: 42)")
    parser.add_argument("--batch-name", type=str, default=None, help="Custom batch identifier")
    parser.add_argument("--output-dir", type=str, default="data/generated", help="Directory for observed data")
    parser.add_argument("--truth-dir", type=str, default="data/truth", help="Directory for hidden truth")

    args = parser.parse_args()
    out_dir = repo_root / args.output_dir
    tr_dir = repo_root / args.truth_dir

    print(f"Generating synthetic batch ({args.rows} rows, seed={args.seed})...")
    json_p, csv_p, truth_p = generate_dataset(args.rows, args.seed, out_dir, tr_dir, args.batch_name)

    print(f"Observed JSON: {json_p}")
    print(f"Observed CSV:  {csv_p}")
    print(f"Hidden Truth:  {truth_p}")
    print("Dataset generation complete.")


if __name__ == "__main__":
    main()
