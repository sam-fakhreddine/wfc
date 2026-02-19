#!/usr/bin/env python3
"""
Advanced Metrics Tracking for WFC

Tracks and analyzes:
- Token efficiency metrics
- Task completion rates
- Agent performance
- Quality trends
- Time-to-completion
"""

import json
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class MetricsSummary:
    """Summary of metrics over a time period."""

    period: str  # day, week, month
    tasks_completed: int = 0
    tasks_failed: int = 0
    success_rate: float = 0.0

    # Token metrics
    total_tokens: int = 0
    avg_tokens_per_task: float = 0.0
    token_efficiency_vs_baseline: float = 0.0  # % reduction

    # Time metrics
    total_time_ms: int = 0
    avg_time_per_task_ms: float = 0.0
    median_time_per_task_ms: float = 0.0

    # Quality metrics
    avg_quality_score: float = 0.0
    avg_test_coverage: float = 0.0
    critical_issues: int = 0

    # Agent metrics
    agent_utilization: float = 0.0  # % of max agents used
    parallel_efficiency: float = 0.0  # actual vs theoretical speedup


class AdvancedMetricsTracker:
    """
    Advanced metrics tracking and analysis.

    Provides insights into:
    - Performance trends
    - Token efficiency
    - Quality metrics
    - Optimization opportunities
    """

    def __init__(self, memory_dir: Path = None):
        if memory_dir:
            self.memory_dir = Path(memory_dir)
        else:
            self.memory_dir = Path(__file__).parent.parent / "memory"

        self.metrics_file = self.memory_dir / "workflow_metrics.jsonl"
        self.analytics_file = self.memory_dir / "analytics.json"

    def get_summary(self, period: str = "week") -> MetricsSummary:
        """Get metrics summary for period (day, week, month, all)."""
        if not self.metrics_file.exists():
            return MetricsSummary(period=period)

        # Load metrics
        metrics = self._load_metrics(period)

        if not metrics:
            return MetricsSummary(period=period)

        # Calculate summary
        summary = MetricsSummary(period=period)

        summary.tasks_completed = sum(1 for m in metrics if m.get("success", False))
        summary.tasks_failed = len(metrics) - summary.tasks_completed
        summary.success_rate = summary.tasks_completed / len(metrics) if metrics else 0.0

        # Token metrics
        tokens = [m.get("tokens_total", 0) for m in metrics]
        summary.total_tokens = sum(tokens)
        summary.avg_tokens_per_task = statistics.mean(tokens) if tokens else 0.0

        # Baseline: 150k tokens (old approach)
        # WFC: ~1.5k tokens (99% reduction)
        baseline = 150000
        if summary.avg_tokens_per_task > 0:
            summary.token_efficiency_vs_baseline = (
                (baseline - summary.avg_tokens_per_task) / baseline * 100
            )

        # Time metrics
        times = [m.get("duration_ms", 0) for m in metrics]
        summary.total_time_ms = sum(times)
        summary.avg_time_per_task_ms = statistics.mean(times) if times else 0.0
        summary.median_time_per_task_ms = statistics.median(times) if times else 0.0

        # Quality metrics
        quality_scores = [
            m.get("confidence_score", 0) for m in metrics if m.get("confidence_score")
        ]
        summary.avg_quality_score = statistics.mean(quality_scores) if quality_scores else 0.0

        coverage = [m.get("test_coverage", 0) for m in metrics if m.get("test_coverage")]
        summary.avg_test_coverage = statistics.mean(coverage) if coverage else 0.0

        summary.critical_issues = sum(m.get("quality_issues_found", 0) for m in metrics)

        return summary

    def get_trends(self) -> Dict[str, List[float]]:
        """Get trend data for visualization."""
        if not self.metrics_file.exists():
            return {}

        # Load all metrics
        metrics = self._load_metrics("all")

        # Group by day
        daily_metrics = {}
        for m in metrics:
            timestamp = m.get("timestamp", "")
            if not timestamp:
                continue

            date = timestamp.split("T")[0]  # Get YYYY-MM-DD

            if date not in daily_metrics:
                daily_metrics[date] = []

            daily_metrics[date].append(m)

        # Calculate daily trends
        trends = {
            "dates": [],
            "success_rate": [],
            "avg_tokens": [],
            "avg_duration": [],
            "quality_score": [],
        }

        for date in sorted(daily_metrics.keys()):
            day_metrics = daily_metrics[date]

            trends["dates"].append(date)

            # Success rate
            successes = sum(1 for m in day_metrics if m.get("success", False))
            trends["success_rate"].append(successes / len(day_metrics) if day_metrics else 0.0)

            # Average tokens
            tokens = [m.get("tokens_total", 0) for m in day_metrics]
            trends["avg_tokens"].append(statistics.mean(tokens) if tokens else 0.0)

            # Average duration
            durations = [m.get("duration_ms", 0) for m in day_metrics]
            trends["avg_duration"].append(statistics.mean(durations) if durations else 0.0)

            # Quality score
            scores = [m.get("confidence_score", 0) for m in day_metrics]
            trends["quality_score"].append(statistics.mean(scores) if scores else 0.0)

        return trends

    def get_complexity_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Analyze metrics by task complexity."""
        if not self.metrics_file.exists():
            return {}

        metrics = self._load_metrics("all")

        breakdown = {}

        for complexity in ["S", "M", "L", "XL"]:
            complexity_metrics = [m for m in metrics if m.get("complexity") == complexity]

            if not complexity_metrics:
                continue

            tokens = [m.get("tokens_total", 0) for m in complexity_metrics]
            times = [m.get("duration_ms", 0) for m in complexity_metrics]
            successes = sum(1 for m in complexity_metrics if m.get("success", False))

            breakdown[complexity] = {
                "count": len(complexity_metrics),
                "success_rate": successes / len(complexity_metrics),
                "avg_tokens": statistics.mean(tokens) if tokens else 0,
                "median_tokens": statistics.median(tokens) if tokens else 0,
                "avg_time_ms": statistics.mean(times) if times else 0,
                "median_time_ms": statistics.median(times) if times else 0,
            }

        return breakdown

    def generate_report(self) -> str:
        """Generate comprehensive metrics report."""
        lines = [
            "# WFC Metrics Report",
            f"**Generated**: {datetime.now().isoformat()}",
            "",
            "## Weekly Summary",
            "",
        ]

        # Weekly summary
        week = self.get_summary("week")

        lines.extend(
            [
                f"- **Tasks Completed**: {week.tasks_completed}",
                f"- **Tasks Failed**: {week.tasks_failed}",
                f"- **Success Rate**: {week.success_rate*100:.1f}%",
                "",
                f"- **Total Tokens**: {week.total_tokens:,}",
                f"- **Avg Tokens/Task**: {week.avg_tokens_per_task:,.0f}",
                f"- **Token Efficiency**: {week.token_efficiency_vs_baseline:.1f}% reduction vs baseline",
                "",
                f"- **Total Time**: {week.total_time_ms/1000/60:.1f} minutes",
                f"- **Avg Time/Task**: {week.avg_time_per_task_ms/1000:.1f}s",
                f"- **Median Time/Task**: {week.median_time_per_task_ms/1000:.1f}s",
                "",
                f"- **Avg Quality Score**: {week.avg_quality_score:.1f}/100",
                f"- **Avg Test Coverage**: {week.avg_test_coverage:.1f}%",
                f"- **Critical Issues**: {week.critical_issues}",
                "",
                "## Complexity Breakdown",
                "",
            ]
        )

        # Complexity breakdown
        breakdown = self.get_complexity_breakdown()

        for complexity, stats in breakdown.items():
            lines.extend(
                [
                    f"### {complexity} (Simple/Medium/Large/XL)",
                    f"- **Count**: {stats['count']} tasks",
                    f"- **Success Rate**: {stats['success_rate']*100:.1f}%",
                    f"- **Avg Tokens**: {stats['avg_tokens']:,.0f}",
                    f"- **Avg Time**: {stats['avg_time_ms']/1000:.1f}s",
                    "",
                ]
            )

        # Trends
        lines.extend(["## Trends (Last 7 Days)", ""])

        trends = self.get_trends()
        if trends and trends.get("dates"):
            last_7 = trends["dates"][-7:]
            success = trends["success_rate"][-7:]

            lines.append("| Date | Success Rate | Avg Tokens | Avg Duration |")
            lines.append("|------|--------------|------------|--------------|")

            for i, date in enumerate(last_7):
                lines.append(
                    f"| {date} | {success[i]*100:.1f}% | "
                    f"{trends['avg_tokens'][-(7-i)]:.0f} | "
                    f"{trends['avg_duration'][-(7-i)]/1000:.1f}s |"
                )

        lines.extend(["", "---", "", "**This is World Fucking Class.** 🚀"])

        return "\n".join(lines)

    def _load_metrics(self, period: str) -> List[Dict[str, Any]]:
        """Load metrics for period."""
        if not self.metrics_file.exists():
            return []

        metrics = []

        # Determine cutoff date
        if period == "day":
            cutoff = datetime.now() - timedelta(days=1)
        elif period == "week":
            cutoff = datetime.now() - timedelta(weeks=1)
        elif period == "month":
            cutoff = datetime.now() - timedelta(days=30)
        else:  # all
            cutoff = datetime.min

        with open(self.metrics_file, "r") as f:
            for line in f:
                try:
                    metric = json.loads(line.strip())

                    # Check if within period
                    timestamp = metric.get("timestamp", "")
                    if timestamp:
                        metric_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        if metric_date < cutoff:
                            continue

                    metrics.append(metric)

                except (json.JSONDecodeError, ValueError):
                    continue

        return metrics


if __name__ == "__main__":
    # Test metrics tracking
    tracker = AdvancedMetricsTracker()

    # Generate report
    report = tracker.generate_report()
    print(report)
