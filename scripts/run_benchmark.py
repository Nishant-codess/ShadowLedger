#!/usr/bin/env python3
"""Evaluation Benchmark Harness for ShadowLedger Baseline.

Evaluates deterministic reconciliation performance, throughput, match rate,
precision, recall, and safety against ground truth across scenario families.
"""

import argparse
import json
import sys
import time
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "apps" / "api"))

from app.data.ingest import ingest_from_json_file
from app.data.normalize import normalize_batch
from app.engine.reconciler import DeterministicReconciler
from app.metrics.evaluator import compute_metrics
from app.metrics.reporter import metrics_to_dict, print_evaluation_report

from scripts.generate_dataset import generate_dataset


def run_benchmark(rows: int = 1000, seed: int = 42, json_file: str | None = None) -> dict:
    """Run full deterministic reconciliation benchmark."""
    out_dir = repo_root / "data" / "generated"
    truth_dir = repo_root / "data" / "truth"

    if json_file:
        data_path = Path(json_file)
        batch_id = data_path.stem.replace("_observed", "")
        truth_path = truth_dir / f"{batch_id}_truth.json"
    else:
        batch_id = f"benchmark_s{seed}_r{rows}"
        data_path = out_dir / f"{batch_id}_observed.json"
        truth_path = truth_dir / f"{batch_id}_truth.json"

        if not data_path.exists() or not truth_path.exists():
            print(f"Generating benchmark dataset ({rows} rows, seed={seed})...")
            data_path, _, truth_path = generate_dataset(rows, seed, out_dir, truth_dir, batch_id)

    # 1. Ingest
    print(f"Ingesting observed batch from: {data_path.name}...")
    ingest_result = ingest_from_json_file(data_path)

    # 2. Load ground truth for independent validation
    ground_truth = []
    if truth_path.exists():
        with open(truth_path, encoding="utf-8") as f:
            gt_data = json.load(f)
            ground_truth = gt_data.get("ground_truth", [])

    # 3. Normalize
    print(f"Normalizing {len(ingest_result.valid_records)} records...")
    observations, inventory_moves = normalize_batch(ingest_result.valid_records, batch_id=batch_id)

    # 4. Reconcile
    print("Running Deterministic Reconciliation Engine...")
    reconciler = DeterministicReconciler()
    t0 = time.perf_counter()
    reconcile_result = reconciler.reconcile_batch(
        observations=observations,
        inventory_moves=inventory_moves,
        batch_id=batch_id,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    # 5. Compute Metrics
    metrics = compute_metrics(
        result=reconcile_result,
        processing_time_ms=elapsed_ms,
        ground_truth_list=ground_truth,
    )

    # 6. Render Report
    print_evaluation_report(metrics)

    # 7. Export result
    res_dict = metrics_to_dict(metrics)
    results_path = repo_root / "data" / "benchmark_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(res_dict, f, indent=2)
    print(f"Benchmark results saved to: {results_path}")

    return res_dict


def main():
    parser = argparse.ArgumentParser(description="Run ShadowLedger baseline reconciliation benchmark")
    parser.add_argument("--rows", type=int, default=1000, help="Number of records to evaluate (default: 1000)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--file", type=str, default=None, help="Optional path to existing observed JSON file")

    args = parser.parse_args()
    run_benchmark(rows=args.rows, seed=args.seed, json_file=args.file)


if __name__ == "__main__":
    main()
