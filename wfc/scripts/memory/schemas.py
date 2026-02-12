"""
WFC Memory Schemas - Data Definitions

SOLID: Single Responsibility - Just data structures, no logic
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class ReflexionEntry:
    """
    A single reflexion entry (learning from mistake).

    Format: task, mistake, evidence, fix, rule
    """

    timestamp: str
    task_id: str
    mistake: str  # What went wrong
    evidence: str  # How we know it went wrong
    fix: str  # How we fixed it
    rule: str  # Rule to prevent recurrence
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
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReflexionEntry":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class OperationalPattern:
    """
    SEE SOMETHING SAY SOMETHING - Recurring operational error pattern.

    Detected from reflexion entries and command errors.
    Used to generate OPS_TASKS.md for systematic fixes.
    """

    pattern_id: str  # e.g., "PATTERN-001"
    first_detected: str  # ISO timestamp
    last_detected: str  # ISO timestamp
    occurrence_count: int
    error_type: str  # e.g., "docker-compose version obsolete"
    description: str  # Human-readable description
    fix: str  # How to fix
    impact: str  # Why it matters
    status: str = "READY_FOR_PLAN"  # READY_FOR_PLAN, PLANNED, FIXED, IGNORED
    severity: str = "medium"  # low, medium, high, critical

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "first_detected": self.first_detected,
            "last_detected": self.last_detected,
            "occurrence_count": self.occurrence_count,
            "error_type": self.error_type,
            "description": self.description,
            "fix": self.fix,
            "impact": self.impact,
            "status": self.status,
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OperationalPattern":
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
    complexity: str  # S, M, L, XL
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
            "rolled_back": self.rolled_back,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowMetric":
        """Create from dictionary."""
        return cls(**data)
