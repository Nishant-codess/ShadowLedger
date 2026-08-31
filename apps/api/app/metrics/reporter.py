"""Console reporting and benchmark result formatters."""

from typing import Any

from rich.console import Console
from rich.table import Table

from app.metrics.evaluator import EvaluationMetrics


def print_evaluation_report(metrics: EvaluationMetrics) -> None:
    """Render a clean, professional summary table of the evaluation metrics in terminal."""
    console = Console()

    table = Table(title=f"ShadowLedger Baseline Reconciliation Report [Batch: {metrics.batch_id}]")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Total Records Ingested", f"{metrics.record_count:,}")
    table.add_row("Deterministic Matches", f"{metrics.matched_count:,}")
    table.add_row("Unmatched Exceptions", f"{metrics.exception_count:,}")
    table.add_row("Baseline Match Rate", f"{metrics.match_rate:.2f}%")
    table.add_row("Processing Throughput", f"{metrics.throughput_records_per_sec:,.1f} records/sec")
    table.add_row("Total Volume (INR)", f"₹{metrics.total_volume_inr:,.2f}")
    table.add_row("Explained Volume (INR)", f"₹{metrics.explained_volume_inr:,.2f}")
    table.add_row("Unexplained Residual (INR)", f"₹{metrics.unexplained_volume_inr:,.2f}")
    table.add_row("Processing Time", f"{metrics.processing_time_ms:.1f} ms")

    if metrics.ground_truth_precision is not None:
        table.add_row("Ground Truth Precision", f"{metrics.ground_truth_precision:.2f}%")
    if metrics.ground_truth_recall is not None:
        table.add_row("Ground Truth Recall", f"{metrics.ground_truth_recall:.2f}%")
    table.add_row("Unsafe Auto-Resolutions", f"{metrics.unsafe_resolutions_count}")

    console.print(table)

    if metrics.reason_code_breakdown:
        reason_table = Table(title="Reconciliation Reason Code Breakdown")
        reason_table.add_column("Reason Code", style="yellow")
        reason_table.add_column("Observations Affected", style="white")

        for code, count in sorted(metrics.reason_code_breakdown.items(), key=lambda x: x[1], reverse=True):
            reason_table.add_row(code, f"{count:,}")
        console.print(reason_table)


def metrics_to_dict(metrics: EvaluationMetrics) -> dict[str, Any]:
    """Convert EvaluationMetrics instance to dictionary for API responses."""
    return {
        "batch_id": metrics.batch_id,
        "record_count": metrics.record_count,
        "matched_count": metrics.matched_count,
        "exception_count": metrics.exception_count,
        "match_rate": metrics.match_rate,
        "throughput_records_per_sec": metrics.throughput_records_per_sec,
        "total_volume_inr": metrics.total_volume_inr,
        "explained_volume_inr": metrics.explained_volume_inr,
        "unexplained_volume_inr": metrics.unexplained_volume_inr,
        "processing_time_ms": metrics.processing_time_ms,
        "ground_truth_precision": metrics.ground_truth_precision,
        "ground_truth_recall": metrics.ground_truth_recall,
        "unsafe_resolutions_count": metrics.unsafe_resolutions_count,
        "reason_code_breakdown": metrics.reason_code_breakdown,
        "scenario_breakdown": metrics.scenario_breakdown,
    }
