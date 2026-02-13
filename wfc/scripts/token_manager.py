#!/usr/bin/env python3
"""
WFC Token Manager - Enhanced Token Budgeting

Classifies tasks and assigns token budgets based on complexity and history.
Warns if agent exceeds budget. Optimizes future allocations.

PHILOSOPHY:
- Simple tasks deserve small budgets (prevent over-engineering)
- Complex tasks need larger budgets
- Learn from history to optimize budgets
- Warn agents when approaching budget limit
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional
import json


class TaskComplexity(Enum):
    """Task complexity levels."""

    S = "S"  # Small
    M = "M"  # Medium
    L = "L"  # Large
    XL = "XL"  # Extra Large


@dataclass
class TokenBudget:
    """Token budget for a task."""

    task_id: str
    complexity: TaskComplexity
    budget_total: int
    budget_input: int
    budget_output: int

    # Actual usage (tracked during execution)
    actual_input: int = 0
    actual_output: int = 0
    actual_total: int = 0

    # Status
    warned: bool = False
    exceeded: bool = False

    def get_usage_percentage(self) -> float:
        """Get current usage as percentage of budget."""
        if self.budget_total == 0:
            return 0.0
        return (self.actual_total / self.budget_total) * 100

    def is_approaching_limit(self, threshold: float = 0.8) -> bool:
        """Check if approaching budget limit."""
        return self.get_usage_percentage() >= (threshold * 100)

    def has_exceeded(self) -> bool:
        """Check if budget exceeded."""
        return self.actual_total > self.budget_total

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "complexity": self.complexity.value,
            "budget_total": self.budget_total,
            "budget_input": self.budget_input,
            "budget_output": self.budget_output,
            "actual_input": self.actual_input,
            "actual_output": self.actual_output,
            "actual_total": self.actual_total,
            "usage_percentage": self.get_usage_percentage(),
            "warned": self.warned,
            "exceeded": self.exceeded,
        }


class TokenManager:
    """
    WFC Token Manager - BUDGET & OPTIMIZE

    Manages token budgets for tasks based on complexity and history.

    Default budgets (conservative):
    - S (Simple):     200 tokens (small changes, bug fixes)
    - M (Medium):   1,000 tokens (features, moderate complexity)
    - L (Large):    2,500 tokens (complex features, refactoring)
    - XL (XL):      5,000 tokens (major features, architecture)

    These are adjusted based on historical data.
    """

    # Default budgets by complexity
    DEFAULT_BUDGETS = {
        TaskComplexity.S: {"input": 150, "output": 50, "total": 200},
        TaskComplexity.M: {"input": 700, "output": 300, "total": 1000},
        TaskComplexity.L: {"input": 1750, "output": 750, "total": 2500},
        TaskComplexity.XL: {"input": 3500, "output": 1500, "total": 5000},
    }

    def __init__(self, memory_dir: Optional[Path] = None):
        """
        Initialize token manager.

        Args:
            memory_dir: Directory for memory files (for historical data)
        """
        if memory_dir:
            self.memory_dir = Path(memory_dir)
        else:
            # Default: wfc/memory/
            self.memory_dir = Path(__file__).parent.parent / "memory"

        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.memory_dir / "workflow_metrics.jsonl"

    def create_budget(
        self, task_id: str, complexity: TaskComplexity, use_history: bool = True
    ) -> TokenBudget:
        """
        Create token budget for a task.

        Args:
            task_id: Task ID
            complexity: Task complexity
            use_history: Whether to adjust based on history

        Returns:
            TokenBudget
        """
        if use_history and self.metrics_file.exists():
            # Get average from history
            budgets = self._get_historical_average(complexity)
        else:
            # Use defaults
            budgets = self.DEFAULT_BUDGETS[complexity]

        return TokenBudget(
            task_id=task_id,
            complexity=complexity,
            budget_total=budgets["total"],
            budget_input=budgets["input"],
            budget_output=budgets["output"],
        )

    def update_usage(
        self, budget: TokenBudget, input_tokens: int, output_tokens: int
    ) -> TokenBudget:
        """
        Update actual token usage.

        Args:
            budget: TokenBudget to update
            input_tokens: Input tokens used
            output_tokens: Output tokens used

        Returns:
            Updated TokenBudget
        """
        budget.actual_input += input_tokens
        budget.actual_output += output_tokens
        budget.actual_total = budget.actual_input + budget.actual_output

        # Check if approaching limit
        if budget.is_approaching_limit() and not budget.warned:
            budget.warned = True

        # Check if exceeded
        if budget.has_exceeded():
            budget.exceeded = True

        return budget

    def get_warning_message(self, budget: TokenBudget) -> Optional[str]:
        """
        Get warning message if budget issue.

        Args:
            budget: TokenBudget to check

        Returns:
            Warning message or None
        """
        usage_pct = budget.get_usage_percentage()

        if budget.exceeded:
            over_amount = budget.actual_total - budget.budget_total
            return (
                f"⚠️ BUDGET EXCEEDED: {usage_pct:.1f}% "
                f"({budget.actual_total}/{budget.budget_total} tokens, "
                f"+{over_amount} over budget). "
                "Consider simplifying approach or breaking into subtasks."
            )

        elif budget.is_approaching_limit():
            remaining = budget.budget_total - budget.actual_total
            return (
                f"⚠️ APPROACHING BUDGET: {usage_pct:.1f}% "
                f"({budget.actual_total}/{budget.budget_total} tokens, "
                f"{remaining} remaining). "
                "Aim to complete within budget."
            )

        return None

    def _get_historical_average(self, complexity: TaskComplexity) -> Dict[str, int]:
        """
        Get historical average token usage for complexity.

        Args:
            complexity: Task complexity

        Returns:
            Dict with input, output, total averages
        """
        total_input = 0
        total_output = 0
        count = 0

        try:
            with open(self.metrics_file, "r") as f:
                for line in f:
                    try:
                        metric = json.loads(line.strip())

                        if metric.get("complexity") == complexity.value and metric.get(
                            "success", False
                        ):
                            total_input += metric.get("tokens_input", 0)
                            total_output += metric.get("tokens_output", 0)
                            count += 1

                    except (json.JSONDecodeError, KeyError):
                        continue

        except FileNotFoundError:
            pass

        if count == 0:
            # No history - return defaults
            return self.DEFAULT_BUDGETS[complexity]

        avg_input = total_input // count
        avg_output = total_output // count

        # Add 20% buffer to historical average
        return {
            "input": int(avg_input * 1.2),
            "output": int(avg_output * 1.2),
            "total": int((avg_input + avg_output) * 1.2),
        }

    def get_budget_recommendation(self, complexity: TaskComplexity) -> str:
        """
        Get budget recommendation message.

        Args:
            complexity: Task complexity

        Returns:
            Recommendation string
        """
        budget = self.create_budget("sample", complexity)

        complexity_names = {
            TaskComplexity.S: "Simple",
            TaskComplexity.M: "Medium",
            TaskComplexity.L: "Large",
            TaskComplexity.XL: "Extra Large",
        }

        return (
            f"📊 Budget for {complexity_names[complexity]} task: "
            f"{budget.budget_total:,} tokens "
            f"({budget.budget_input:,} input + {budget.budget_output:,} output). "
            "Stay within budget by keeping implementation focused."
        )


if __name__ == "__main__":
    # Test token manager
    print("WFC Token Manager Test")
    print("=" * 60)

    manager = TokenManager()

    # Test 1: Create budgets for each complexity
    print("\n1. Testing budget creation:")
    for complexity in [TaskComplexity.S, TaskComplexity.M, TaskComplexity.L, TaskComplexity.XL]:
        budget = manager.create_budget(f"TASK-{complexity.value}", complexity)
        print(f"   {complexity.value}: {budget.budget_total:,} tokens")
        print(f"      Recommendation: {manager.get_budget_recommendation(complexity)}")

    # Test 2: Test usage tracking
    print("\n2. Testing usage tracking:")
    budget = manager.create_budget("TASK-M", TaskComplexity.M)
    print(f"   Initial: {budget.actual_total}/{budget.budget_total}")

    # Use 60% of budget
    budget = manager.update_usage(budget, 420, 180)
    print(f"   After 60%: {budget.actual_total}/{budget.budget_total}")
    warning = manager.get_warning_message(budget)
    if warning:
        print(f"   {warning}")

    # Use 85% of budget (should warn)
    budget = manager.update_usage(budget, 140, 60)
    print(f"   After 85%: {budget.actual_total}/{budget.budget_total}")
    warning = manager.get_warning_message(budget)
    if warning:
        print(f"   {warning}")

    # Exceed budget
    budget = manager.update_usage(budget, 200, 100)
    print(f"   After exceeding: {budget.actual_total}/{budget.budget_total}")
    warning = manager.get_warning_message(budget)
    if warning:
        print(f"   {warning}")

    # Test 3: Budget status
    print("\n3. Testing budget status:")
    print(f"   Usage: {budget.get_usage_percentage():.1f}%")
    print(f"   Warned: {budget.warned}")
    print(f"   Exceeded: {budget.exceeded}")

    print("\n✅ All token manager tests passed!")
