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

from .manager import MemoryManager
from .metrics import MetricsLogger
from .ops_tasks import OpsTasksGenerator
from .pattern_detector import PatternDetector
from .reflexion import ReflexionLogger
from .saydo import (
    aggregate_values_alignment,
    compute_say_do_ratio,
    generate_values_mermaid_chart,
    generate_values_recommendations,
)
from .schemas import OperationalPattern, ReflexionEntry, WorkflowMetric

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
