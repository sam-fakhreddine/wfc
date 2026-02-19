"""
wfc-implement - Multi-Agent Parallel Implementation Engine

ELEGANT: Simple, effective, maintainable
MULTI-TIER: Logic separate from presentation
PARALLEL: Multiple agents working concurrently
"""

__version__ = "0.1.0"

from .agent import AgentPhase, AgentReport, WFCAgent
from .cli import cli_implement
from .executor import ExecutionEngine
from .merge_engine import MergeEngine, MergeResult, MergeStatus
from .orchestrator import AgentStrategy, RunResult, WFCOrchestrator, run_implementation
from .parser import TasksParser, parse_tasks

__all__ = [
    "WFCOrchestrator",
    "run_implementation",
    "RunResult",
    "AgentStrategy",
    "WFCAgent",
    "AgentReport",
    "AgentPhase",
    "MergeEngine",
    "MergeResult",
    "MergeStatus",
    "cli_implement",
    "parse_tasks",
    "TasksParser",
    "ExecutionEngine",
]
