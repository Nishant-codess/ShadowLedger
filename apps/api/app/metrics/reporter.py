"""Console reporting and benchmark result formatters."""

from typing import Any

from rich.console import Console
from rich.table import Table

from app.metrics.evaluator import EvaluationMetrics


def print_evaluation_report(metrics: EvaluationMetrics) -> None:
    """Render a summary table of the baseline evaluation metrics in terminal."""
    console = Console()

    table = Table(title=f"ShadowLedger Reconciliation Report [Batch: {metrics.batch_id}]")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Total Records Ingested", f"{metrics.record_count:,}")
    table.add_row("Deterministic Matches", f"{metrics.matched_count:,}")
    table.add_row("Unmatched Exceptions", f"{metrics.exception_count:,}")
    table.add_row("Baseline Match Rate", f"{metrics.match_rate:.2f}%")
    table.add_row("Enhanced Resolution Rate", f"{metrics.enhanced_resolution_rate:.2f}%")
    table.add_row("Auto-Resolved Inferred", f"{metrics.auto_resolved_count:,}")
    table.add_row("Human Review Escalated", f"{metrics.human_review_count:,}")
    table.add_row("Unresolved Cases", f"{metrics.unresolved_count:,}")
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
        reason_table = Table(title="Decision & Reason Code Breakdown")
        reason_table.add_column("Reason Code", style="yellow")
        reason_table.add_column("Cases Affected", style="white")

        for code, count in sorted(metrics.reason_code_breakdown.items(), key=lambda x: x[1], reverse=True)[:10]:
            reason_table.add_row(code, f"{count:,}")
        console.print(reason_table)


def print_comparison_report(baseline: EvaluationMetrics, enhanced: EvaluationMetrics) -> None:
    """Render a side-by-side comparison between Baseline and Enhanced ShadowLedger Engine."""
    console = Console()

    table = Table(title=f"ShadowLedger: Deterministic Baseline vs Value-Flow Reconstruction [Batch: {enhanced.batch_id}]")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Chunk 1 Baseline (Pure Rules)", style="yellow")
    table.add_column("Chunk 2 ShadowLedger (Value-Flow Engine)", style="green")
    table.add_column("Delta / Impact", style="magenta")

    table.add_row("Total Ingested Records", f"{baseline.record_count:,}", f"{enhanced.record_count:,}", "-")
    table.add_row(
        "Match / Resolution Rate",
        f"{baseline.match_rate:.2f}%",
        f"{enhanced.enhanced_resolution_rate:.2f}%",
        f"+{enhanced.enhanced_resolution_rate - baseline.match_rate:.2f}%",
    )
    table.add_row(
        "Unmatched Exceptions",
        f"{baseline.exception_count:,}",
        f"{enhanced.unresolved_count + enhanced.human_review_count:,}",
        f"-{baseline.exception_count - (enhanced.unresolved_count + enhanced.human_review_count):,}",
    )
    table.add_row(
        "Auto-Resolved Inferences",
        "0 (Rules only)",
        f"{enhanced.auto_resolved_count:,} cases",
        f"+{enhanced.auto_resolved_count:,}",
    )
    table.add_row(
        "Human Review Escalations",
        "0 (All exceptions unranked)",
        f"{enhanced.human_review_count:,} cases",
        "Prioritized with Evidence",
    )
    table.add_row(
        "Explained Volume (INR)",
        f"₹{baseline.explained_volume_inr:,.2f}",
        f"₹{enhanced.explained_volume_inr:,.2f}",
        f"+₹{enhanced.explained_volume_inr - baseline.explained_volume_inr:,.2f}",
    )
    table.add_row(
        "Unexplained Value at Risk",
        f"₹{baseline.unexplained_volume_inr:,.2f}",
        f"₹{enhanced.unexplained_volume_inr:,.2f}",
        f"-₹{baseline.unexplained_volume_inr - enhanced.unexplained_volume_inr:,.2f}",
    )

    if baseline.ground_truth_precision is not None and enhanced.ground_truth_precision is not None:
        table.add_row(
            "Ground Truth Precision",
            f"{baseline.ground_truth_precision:.2f}%",
            f"{enhanced.ground_truth_precision:.2f}%",
            f"{enhanced.ground_truth_precision - baseline.ground_truth_precision:+.2f}%",
        )
    if baseline.ground_truth_recall is not None and enhanced.ground_truth_recall is not None:
        table.add_row(
            "Ground Truth Recall",
            f"{baseline.ground_truth_recall:.2f}%",
            f"{enhanced.ground_truth_recall:.2f}%",
            f"+{enhanced.ground_truth_recall - baseline.ground_truth_recall:.2f}%",
        )

    table.add_row(
        "Unsafe Auto-Resolutions",
        f"{baseline.unsafe_resolutions_count}",
        f"{enhanced.unsafe_resolutions_count}",
        "0 (100% Safe)" if enhanced.unsafe_resolutions_count == 0 else f"{enhanced.unsafe_resolutions_count}",
    )
    table.add_row(
        "Processing Throughput",
        f"{baseline.throughput_records_per_sec:,.1f} r/s",
        f"{enhanced.throughput_records_per_sec:,.1f} r/s",
        "-",
    )

    console.print(table)


def metrics_to_dict(metrics: EvaluationMetrics) -> dict[str, Any]:
    """Convert EvaluationMetrics instance to dictionary for API responses."""
    return {
        "batch_id": metrics.batch_id,
        "record_count": metrics.record_count,
        "matched_count": metrics.matched_count,
        "exception_count": metrics.exception_count,
        "auto_resolved_count": metrics.auto_resolved_count,
        "human_review_count": metrics.human_review_count,
        "unresolved_count": metrics.unresolved_count,
        "match_rate": metrics.match_rate,
        "enhanced_resolution_rate": metrics.enhanced_resolution_rate,
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
