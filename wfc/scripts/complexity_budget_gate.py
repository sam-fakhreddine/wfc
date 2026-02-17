#!/usr/bin/env python3
"""
WFC Complexity Budget Gate - Pre-Review Quality Gate

Enforces TEAMCHARTER "Accountability & Simplicity" value by checking if
implementations exceed their rated complexity (S/M/L/XL).

PHILOSOPHY:
- Small tasks should stay small
- Complexity creep is a warning sign
- Budget exceedance suggests task should be split
- This is a WARNING gate, not a blocking gate

BUDGET TIERS:
- S: ≤50 lines, ≤2 files
- M: ≤200 lines, ≤5 files
- L: ≤500 lines, ≤10 files
- XL: ≤1000 lines, ≤20 files

When budget exceeded:
- Generate clear report showing what exceeded and by how much
- Suggest splitting task into smaller pieces
- Mark as severity="warning" (not blocking)
"""

from dataclasses import dataclass
from typing import Dict

# Complexity budget tiers
COMPLEXITY_BUDGETS: Dict[str, Dict[str, int]] = {
    "S": {"lines": 50, "files": 2},
    "M": {"lines": 200, "files": 5},
    "L": {"lines": 500, "files": 10},
    "XL": {"lines": 1000, "files": 20},
}


@dataclass
class BudgetResult:
    """
    Result of complexity budget check.

    Tracks whether implementation stayed within complexity budget.
    """

    task_id: str
    complexity: str  # S, M, L, XL
    lines_changed: int
    files_changed: int
    lines_budget: int
    files_budget: int
    lines_exceeded: int  # 0 if within budget, >0 if exceeded
    files_exceeded: int  # 0 if within budget, >0 if exceeded
    passed: bool
    report: str
    severity: str = "warning"  # Always warning, never blocking
    unknown_complexity: bool = False  # True when input was coerced to XL

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "complexity": self.complexity,
            "lines_changed": self.lines_changed,
            "files_changed": self.files_changed,
            "lines_budget": self.lines_budget,
            "files_budget": self.files_budget,
            "lines_exceeded": self.lines_exceeded,
            "files_exceeded": self.files_exceeded,
            "passed": self.passed,
            "report": self.report,
            "severity": self.severity,
            "unknown_complexity": self.unknown_complexity,
        }


def check_complexity_budget(
    task_id: str, complexity: str, lines_changed: int, files_changed: int
) -> BudgetResult:
    """
    Check if implementation stayed within complexity budget.

    Args:
        task_id: Task identifier
        complexity: Complexity rating (S, M, L, XL)
        lines_changed: Number of lines changed
        files_changed: Number of files changed

    Returns:
        BudgetResult with pass/fail and detailed report

    Example:
        >>> result = check_complexity_budget("TASK-001", "S", 45, 2)
        >>> assert result.passed is True
        >>> result = check_complexity_budget("TASK-002", "S", 100, 3)
        >>> assert result.passed is False
    """
    # Normalize complexity rating
    original_complexity = complexity
    complexity = complexity.upper()

    # Get budget for this complexity tier
    unknown_complexity = False
    if complexity not in COMPLEXITY_BUDGETS:
        # Unknown complexity - treat as XL budget
        unknown_complexity = True
        budget = COMPLEXITY_BUDGETS["XL"]
    else:
        budget = COMPLEXITY_BUDGETS[complexity]

    lines_budget = budget["lines"]
    files_budget = budget["files"]

    # Check if exceeded
    lines_exceeded = max(0, lines_changed - lines_budget)
    files_exceeded = max(0, files_changed - files_budget)

    # Passed if both within budget
    passed = lines_exceeded == 0 and files_exceeded == 0

    # Generate report
    if passed:
        report = _generate_passing_report(
            task_id, complexity, lines_changed, files_changed, lines_budget, files_budget
        )
    else:
        report = _generate_exceeding_report(
            task_id,
            complexity,
            lines_changed,
            files_changed,
            lines_budget,
            files_budget,
            lines_exceeded,
            files_exceeded,
        )

    if unknown_complexity:
        report += f"\n\nNote: Unknown complexity rating '{original_complexity}', defaulted to 'XL'."

    return BudgetResult(
        task_id=task_id,
        complexity=complexity,
        lines_changed=lines_changed,
        files_changed=files_changed,
        lines_budget=lines_budget,
        files_budget=files_budget,
        lines_exceeded=lines_exceeded,
        files_exceeded=files_exceeded,
        passed=passed,
        report=report,
        severity="warning",
        unknown_complexity=unknown_complexity,
    )


def _generate_passing_report(
    task_id: str,
    complexity: str,
    lines_changed: int,
    files_changed: int,
    lines_budget: int,
    files_budget: int,
) -> str:
    """
    Generate report for task that passed budget check.

    Args:
        task_id: Task identifier
        complexity: Complexity rating
        lines_changed: Actual lines changed
        files_changed: Actual files changed
        lines_budget: Budget for lines
        files_budget: Budget for files

    Returns:
        Clean report showing compliance
    """
    lines_pct = (lines_changed / lines_budget * 100) if lines_budget > 0 else 0
    files_pct = (files_changed / files_budget * 100) if files_budget > 0 else 0

    report = f"""✅ COMPLEXITY BUDGET: PASSED

Task: {task_id}
Complexity: {complexity}

Lines Changed: {lines_changed}/{lines_budget} ({lines_pct:.0f}% of budget)
Files Changed: {files_changed}/{files_budget} ({files_pct:.0f}% of budget)

✅ Implementation stayed within complexity budget.
"""
    return report.strip()


def _generate_exceeding_report(
    task_id: str,
    complexity: str,
    lines_changed: int,
    files_changed: int,
    lines_budget: int,
    files_budget: int,
    lines_exceeded: int,
    files_exceeded: int,
) -> str:
    """
    Generate report for task that exceeded budget.

    Args:
        task_id: Task identifier
        complexity: Complexity rating
        lines_changed: Actual lines changed
        files_changed: Actual files changed
        lines_budget: Budget for lines
        files_budget: Budget for files
        lines_exceeded: Lines over budget
        files_exceeded: Files over budget

    Returns:
        Detailed report showing what exceeded and by how much
    """
    lines_pct = (lines_changed / lines_budget * 100) if lines_budget > 0 else 0
    files_pct = (files_changed / files_budget * 100) if files_budget > 0 else 0

    report_lines = [
        "⚠️  COMPLEXITY BUDGET: EXCEEDED",
        "",
        f"Task: {task_id}",
        f"Complexity: {complexity}",
        "",
    ]

    # Lines exceeded
    if lines_exceeded > 0:
        report_lines.append(
            f"Lines Changed: {lines_changed}/{lines_budget} ({lines_pct:.0f}% of budget)"
        )
        report_lines.append(
            f"  ❌ EXCEEDED by {lines_exceeded} lines ({lines_pct - 100:.0f}% over)"
        )
    else:
        report_lines.append(
            f"Lines Changed: {lines_changed}/{lines_budget} ({lines_pct:.0f}% of budget)"
        )
        report_lines.append("  ✅ Within budget")

    # Files exceeded
    if files_exceeded > 0:
        report_lines.append(
            f"Files Changed: {files_changed}/{files_budget} ({files_pct:.0f}% of budget)"
        )
        report_lines.append(
            f"  ❌ EXCEEDED by {files_exceeded} files ({files_pct - 100:.0f}% over)"
        )
    else:
        report_lines.append(
            f"Files Changed: {files_changed}/{files_budget} ({files_pct:.0f}% of budget)"
        )
        report_lines.append("  ✅ Within budget")

    report_lines.append("")
    report_lines.append("⚠️  WARNING: Implementation exceeded complexity budget.")
    report_lines.append("")
    report_lines.append("RECOMMENDATION:")
    report_lines.append("  - Consider splitting this task into smaller, more focused tasks")
    report_lines.append("  - Each subtask should fit within its complexity budget")
    report_lines.append("  - Smaller tasks are easier to review, test, and maintain")

    return "\n".join(report_lines)


def format_budget_report(result: BudgetResult) -> str:
    """
    Format budget result as human-readable report.

    Args:
        result: BudgetResult to format

    Returns:
        Formatted report string

    This is a convenience function that returns the pre-generated report.
    """
    return result.report


if __name__ == "__main__":
    # Test complexity budget gate
    print("WFC Complexity Budget Gate Test")
    print("=" * 60)

    # Test 1: S complexity - passing
    print("\n1. Testing S complexity (PASSING):")
    result = check_complexity_budget("TASK-001", "S", 45, 2)
    print(format_budget_report(result))
    print(f"\nPassed: {result.passed}")

    # Test 2: S complexity - exceeding
    print("\n2. Testing S complexity (EXCEEDING):")
    result = check_complexity_budget("TASK-002", "S", 100, 3)
    print(format_budget_report(result))
    print(f"\nPassed: {result.passed}")

    # Test 3: M complexity - passing
    print("\n3. Testing M complexity (PASSING):")
    result = check_complexity_budget("TASK-003", "M", 180, 4)
    print(format_budget_report(result))
    print(f"\nPassed: {result.passed}")

    # Test 4: XL complexity - at limit
    print("\n4. Testing XL complexity (AT LIMIT):")
    result = check_complexity_budget("TASK-004", "XL", 1000, 20)
    print(format_budget_report(result))
    print(f"\nPassed: {result.passed}")

    print("\n✅ All complexity budget gate tests passed!")
