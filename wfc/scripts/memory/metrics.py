"""
WFC Metrics Logger - Performance Tracking

SOLID: Single Responsibility - Only handles workflow metrics
"""

import json
from pathlib import Path
from typing import Dict
from .schemas import WorkflowMetric


class MetricsLogger:
    """
    Logs and analyzes workflow metrics.

    Single Responsibility: Workflow metric management
    """

    # Default token budgets by complexity
    DEFAULT_BUDGETS = {
        "S": {"input": 1000, "output": 500, "total": 1500},
        "M": {"input": 2000, "output": 1000, "total": 3000},
        "L": {"input": 4000, "output": 2000, "total": 6000},
        "XL": {"input": 8000, "output": 4000, "total": 12000},
    }

    def __init__(self, metrics_file: Path):
        """
        Initialize metrics logger.

        Args:
            metrics_file: Path to workflow_metrics.jsonl
        """
        self.metrics_file = metrics_file

    def log(self, metric: WorkflowMetric) -> None:
        """
        Log a workflow metric.

        Args:
            metric: WorkflowMetric to log
        """
        with open(self.metrics_file, "a") as f:
            f.write(json.dumps(metric.to_dict()) + "\n")

    def get_average_tokens(self, complexity: str) -> Dict[str, float]:
        """
        Get average token usage for a complexity level.

        Args:
            complexity: S, M, L, or XL

        Returns:
            Dict with average tokens (input, output, total)
        """
        if not self.metrics_file.exists():
            return self.DEFAULT_BUDGETS.get(complexity, self.DEFAULT_BUDGETS["M"])

        total_input = 0
        total_output = 0
        count = 0

        with open(self.metrics_file, "r") as f:
            for line in f:
                try:
                    metric_data = json.loads(line.strip())
                    metric = WorkflowMetric.from_dict(metric_data)

                    if metric.complexity == complexity and metric.success:
                        total_input += metric.tokens_input
                        total_output += metric.tokens_output
                        count += 1

                except (json.JSONDecodeError, Exception):
                    continue

        if count == 0:
            return self.DEFAULT_BUDGETS.get(complexity, self.DEFAULT_BUDGETS["M"])

        return {
            "input": total_input // count,
            "output": total_output // count,
            "total": (total_input + total_output) // count,
        }

    def get_success_rate(self, complexity: str) -> float:
        """
        Get success rate for a complexity level.

        Args:
            complexity: S, M, L, or XL

        Returns:
            Success rate (0.0 to 1.0)
        """
        if not self.metrics_file.exists():
            return 0.85

        successes = 0
        total = 0

        with open(self.metrics_file, "r") as f:
            for line in f:
                try:
                    metric_data = json.loads(line.strip())
                    metric = WorkflowMetric.from_dict(metric_data)

                    if metric.complexity == complexity:
                        total += 1
                        if metric.success:
                            successes += 1

                except (json.JSONDecodeError, Exception):
                    continue

        if total == 0:
            return 0.85

        return successes / total
