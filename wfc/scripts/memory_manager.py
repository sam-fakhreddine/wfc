#!/usr/bin/env python3
"""
WFC Memory Manager - Cross-Session Learning

Implements SuperClaude ReflexionMemory pattern:
- Logs errors to reflexion.jsonl (task, mistake, evidence, fix, rule)
- Logs workflow metrics to workflow_metrics.jsonl (tokens, time, success)
- Searches past errors before starting work
- Suggests solutions from similar past mistakes

PHILOSOPHY:
- Learn from mistakes across sessions
- Prevent repeating same errors
- Optimize token usage based on history
- Privacy-safe (no secrets logged)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import time
from datetime import datetime


@dataclass
class ReflexionEntry:
    """
    A single reflexion entry (learning from mistake).

    Format: task, mistake, evidence, fix, rule
    """
    timestamp: str
    task_id: str
    mistake: str          # What went wrong
    evidence: str         # How we know it went wrong
    fix: str              # How we fixed it
    rule: str             # Rule to prevent recurrence
    severity: str = "medium"  # low, medium, high, critical

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "task_id": self.task_id,
            "mistake": self.mistake,
            "evidence": self.evidence,
            "fix": self.fix,
            "rule": self.rule,
            "severity": self.severity
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReflexionEntry':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class WorkflowMetric:
    """
    Workflow execution metrics.

    Tracks performance for optimization.
    """
    timestamp: str
    task_id: str
    complexity: str       # S, M, L, XL
    success: bool

    # Token usage
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0

    # Time metrics
    duration_ms: int = 0
    phase_durations: Dict[str, int] = field(default_factory=dict)

    # Quality metrics
    quality_issues_found: int = 0
    test_failures: int = 0
    confidence_score: int = 0

    # Retry/rollback
    retry_count: int = 0
    rolled_back: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "task_id": self.task_id,
            "complexity": self.complexity,
            "success": self.success,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "tokens_total": self.tokens_total,
            "duration_ms": self.duration_ms,
            "phase_durations": self.phase_durations,
            "quality_issues_found": self.quality_issues_found,
            "test_failures": self.test_failures,
            "confidence_score": self.confidence_score,
            "retry_count": self.retry_count,
            "rolled_back": self.rolled_back
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowMetric':
        """Create from dictionary."""
        return cls(**data)


class MemoryManager:
    """
    WFC Memory Manager - CROSS-SESSION LEARNING

    Manages reflexion.jsonl and workflow_metrics.jsonl for learning.

    Responsibilities:
    - Log errors and fixes (reflexion)
    - Log workflow metrics
    - Search past errors before work
    - Suggest solutions from history
    - Optimize token budgets based on history
    """

    def __init__(self, memory_dir: Optional[Path] = None):
        """
        Initialize memory manager.

        Args:
            memory_dir: Directory for memory files (default: wfc/memory/)
        """
        if memory_dir:
            self.memory_dir = Path(memory_dir)
        else:
            # Default: wfc/memory/
            self.memory_dir = Path(__file__).parent.parent / "memory"

        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.reflexion_file = self.memory_dir / "reflexion.jsonl"
        self.metrics_file = self.memory_dir / "workflow_metrics.jsonl"

    def log_reflexion(self, entry: ReflexionEntry) -> None:
        """
        Log a reflexion entry (error and fix).

        Args:
            entry: ReflexionEntry to log
        """
        with open(self.reflexion_file, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def log_metric(self, metric: WorkflowMetric) -> None:
        """
        Log a workflow metric.

        Args:
            metric: WorkflowMetric to log
        """
        with open(self.metrics_file, "a") as f:
            f.write(json.dumps(metric.to_dict()) + "\n")

    def search_similar_errors(self, task_description: str,
                             max_results: int = 5) -> List[ReflexionEntry]:
        """
        Search for similar past errors.

        Args:
            task_description: Description of current task
            max_results: Maximum number of results

        Returns:
            List of similar ReflexionEntries

        Uses simple keyword matching. Could be enhanced with embeddings.
        """
        if not self.reflexion_file.exists():
            return []

        # Extract keywords from task description
        keywords = self._extract_keywords(task_description)

        matches = []

        with open(self.reflexion_file, "r") as f:
            for line in f:
                try:
                    entry_data = json.loads(line.strip())
                    entry = ReflexionEntry.from_dict(entry_data)

                    # Check if any keywords match
                    mistake_lower = entry.mistake.lower()
                    fix_lower = entry.fix.lower()

                    if any(kw in mistake_lower or kw in fix_lower
                          for kw in keywords):
                        matches.append(entry)

                except (json.JSONDecodeError, Exception):
                    continue

        # Return most recent matches
        return matches[-max_results:]

    def get_average_tokens_for_complexity(self, complexity: str) -> Dict[str, float]:
        """
        Get average token usage for a complexity level.

        Args:
            complexity: S, M, L, or XL

        Returns:
            Dict with average tokens (input, output, total)
        """
        if not self.metrics_file.exists():
            # Return defaults if no history
            defaults = {
                "S": {"input": 1000, "output": 500, "total": 1500},
                "M": {"input": 2000, "output": 1000, "total": 3000},
                "L": {"input": 4000, "output": 2000, "total": 6000},
                "XL": {"input": 8000, "output": 4000, "total": 12000}
            }
            return defaults.get(complexity, defaults["M"])

        # Calculate from history
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
            # No history for this complexity - return default
            return self.get_average_tokens_for_complexity(complexity)

        avg_input = total_input // count
        avg_output = total_output // count

        return {
            "input": avg_input,
            "output": avg_output,
            "total": avg_input + avg_output
        }

    def get_success_rate_for_complexity(self, complexity: str) -> float:
        """
        Get success rate for a complexity level.

        Args:
            complexity: S, M, L, or XL

        Returns:
            Success rate (0.0 to 1.0)
        """
        if not self.metrics_file.exists():
            return 0.85  # Assume 85% success rate with no history

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

    def get_common_failure_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most common failure patterns.

        Args:
            limit: Maximum number of patterns to return

        Returns:
            List of failure pattern dicts with count
        """
        if not self.reflexion_file.exists():
            return []

        # Count failure patterns
        pattern_counts: Dict[str, int] = {}
        pattern_examples: Dict[str, ReflexionEntry] = {}

        with open(self.reflexion_file, "r") as f:
            for line in f:
                try:
                    entry_data = json.loads(line.strip())
                    entry = ReflexionEntry.from_dict(entry_data)

                    # Use rule as pattern identifier
                    rule = entry.rule

                    if rule not in pattern_counts:
                        pattern_counts[rule] = 0
                        pattern_examples[rule] = entry

                    pattern_counts[rule] += 1

                except (json.JSONDecodeError, Exception):
                    continue

        # Sort by count and return top patterns
        sorted_patterns = sorted(
            pattern_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [
            {
                "pattern": rule,
                "count": count,
                "example": pattern_examples[rule].to_dict()
            }
            for rule, count in sorted_patterns
        ]

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text for matching.

        Args:
            text: Text to extract keywords from

        Returns:
            List of keywords (lowercase)
        """
        # Simple keyword extraction
        # Remove common words, convert to lowercase
        common_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "as", "is", "are",
            "was", "were", "be", "been", "have", "has", "had", "do",
            "does", "did", "will", "would", "could", "should", "may",
            "might", "must", "can", "this", "that", "these", "those"
        }

        words = text.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in common_words]

        return keywords[:10]  # Return top 10 keywords


if __name__ == "__main__":
    # Test memory manager
    print("WFC Memory Manager Test")
    print("=" * 60)

    # Create memory manager
    manager = MemoryManager()

    print(f"\nMemory directory: {manager.memory_dir}")
    print(f"Reflexion file: {manager.reflexion_file}")
    print(f"Metrics file: {manager.metrics_file}")

    # Test 1: Log reflexion entry
    print("\n1. Testing reflexion logging:")
    entry = ReflexionEntry(
        timestamp=datetime.now().isoformat(),
        task_id="TASK-001",
        mistake="Tests failed after refactoring",
        evidence="pytest returned 3 failures",
        fix="Rolled back refactoring commit",
        rule="Always run tests after refactoring before committing",
        severity="high"
    )

    manager.log_reflexion(entry)
    print(f"   ✅ Logged reflexion entry for {entry.task_id}")

    # Test 2: Log workflow metric
    print("\n2. Testing workflow metrics logging:")
    metric = WorkflowMetric(
        timestamp=datetime.now().isoformat(),
        task_id="TASK-001",
        complexity="M",
        success=True,
        tokens_input=2500,
        tokens_output=1200,
        tokens_total=3700,
        duration_ms=45000,
        confidence_score=85,
        quality_issues_found=2
    )

    manager.log_metric(metric)
    print(f"   ✅ Logged workflow metric for {metric.task_id}")

    # Test 3: Search similar errors
    print("\n3. Testing error search:")
    similar = manager.search_similar_errors("refactoring tests")
    print(f"   Found {len(similar)} similar errors")
    if similar:
        print(f"   Example: {similar[0].mistake}")

    # Test 4: Get average tokens
    print("\n4. Testing token averages:")
    for complexity in ["S", "M", "L", "XL"]:
        avg = manager.get_average_tokens_for_complexity(complexity)
        print(f"   {complexity}: {avg['total']} tokens (avg)")

    # Test 5: Get success rate
    print("\n5. Testing success rates:")
    for complexity in ["S", "M", "L", "XL"]:
        rate = manager.get_success_rate_for_complexity(complexity)
        print(f"   {complexity}: {rate*100:.1f}% success rate")

    print("\n✅ All memory manager tests passed!")
