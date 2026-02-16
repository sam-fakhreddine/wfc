"""
WFC Memory System - Cross-Session Learning

SOLID Architecture:
- schemas.py: Data definitions (SRP)
- reflexion.py: Error learning (SRP)
- metrics.py: Performance tracking (SRP)
- pattern_detector.py: Pattern detection (SRP)
- ops_tasks.py: OPS_TASKS.md generation (SRP)
- manager.py: Orchestration (DIP)
"""

from .schemas import ReflexionEntry, WorkflowMetric, OperationalPattern
from .reflexion import ReflexionLogger
from .metrics import MetricsLogger
from .saydo import (
    compute_say_do_ratio,
    aggregate_values_alignment,
    generate_values_mermaid_chart,
    generate_values_recommendations,
)
from .pattern_detector import PatternDetector
from .ops_tasks import OpsTasksGenerator
from .manager import MemoryManager

__all__ = [
    "ReflexionEntry",
    "WorkflowMetric",
    "OperationalPattern",
    "ReflexionLogger",
    "MetricsLogger",
    "PatternDetector",
    "OpsTasksGenerator",
    "MemoryManager",
    "compute_say_do_ratio",
    "aggregate_values_alignment",
    "generate_values_mermaid_chart",
    "generate_values_recommendations",
]
