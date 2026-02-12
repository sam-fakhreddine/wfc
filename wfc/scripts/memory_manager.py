"""
WFC Memory Manager - Backwards Compatibility Wrapper

This file maintains backwards compatibility by re-exporting
from the new SOLID architecture in wfc/scripts/memory/

The memory system has been split into:
- memory/schemas.py: Data definitions
- memory/reflexion.py: Error learning
- memory/metrics.py: Performance tracking
- memory/pattern_detector.py: Pattern detection
- memory/ops_tasks.py: OPS_TASKS.md generation
- memory/manager.py: Orchestration

Import from here for compatibility, or directly from memory/ for new code.
"""

# Re-export everything from the new memory module
from .memory import (
    ReflexionEntry,
    WorkflowMetric,
    OperationalPattern,
    ReflexionLogger,
    MetricsLogger,
    PatternDetector,
    OpsTasksGenerator,
    MemoryManager,
)

__all__ = [
    "ReflexionEntry",
    "WorkflowMetric",
    "OperationalPattern",
    "ReflexionLogger",
    "MetricsLogger",
    "PatternDetector",
    "OpsTasksGenerator",
    "MemoryManager",
]
