"""
wfc-implement - Multi-Agent Parallel Implementation Engine

ELEGANT: Simple, effective, maintainable
MULTI-TIER: Logic separate from presentation
PARALLEL: Multiple agents working concurrently
"""

__version__ = "0.1.0"

from .orchestrator import WFCOrchestrator, run_implementation, RunResult, AgentStrategy
from .agent import WFCAgent, AgentReport, AgentPhase
from .merge_engine import MergeEngine, MergeResult, MergeStatus
from .cli import cli_implement
from .parser import parse_tasks, TasksParser
from .executor import ExecutionEngine

__all__ = [
    "WFCOrchestrator", "run_implementation", "RunResult", "AgentStrategy",
    "WFCAgent", "AgentReport", "AgentPhase",
    "MergeEngine", "MergeResult", "MergeStatus",
    "cli_implement",
    "parse_tasks", "TasksParser",
    "ExecutionEngine"
]
