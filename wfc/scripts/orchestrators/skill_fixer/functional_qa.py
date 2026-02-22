"""Functional QA - optional skill execution testing."""

from pathlib import Path
from typing import List, Optional

from .schemas import AggregateScores, FunctionalQAResult, TestCase


class FunctionalQA:
    """
    Optionally execute skill against test cases.

    This is SLOW and requires actual skill execution.
    Most validation is done in Structural QA.
    """

    def evaluate(
        self,
        original_skill_path: Path,
        rewritten_files: dict[str, str],
        test_cases: Optional[List[TestCase]] = None,
    ) -> FunctionalQAResult:
        """
        Evaluate skill functionality.

        Args:
            original_skill_path: Path to original skill
            rewritten_files: Rewritten skill files
            test_cases: Test cases to run (or generate if None)

        Returns:
            FunctionalQAResult with test outcomes
        """

        return FunctionalQAResult(
            test_cases_run=0,
            test_cases_source="none",
            results=[],
            aggregate=AggregateScores(
                avg_task_completion=0.0,
                avg_quality=0.0,
                avg_adherence=0.0,
                avg_edge_case_handling=0.0,
                total_avg=0.0,
                regression_count=0,
            ),
            verdict="INCONCLUSIVE",
            failure_reason="Functional QA not implemented (optional phase)",
        )
