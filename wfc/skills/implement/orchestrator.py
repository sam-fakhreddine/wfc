"""
WFC Implement - Orchestrator (Logic Tier)

ELEGANT: Task queue management, agent assignment, dependency execution
MULTI-TIER: Pure logic, no UI concerns
PARALLEL: Manages N agents working concurrently

This is the brain of wfc-implement - coordinates everything but doesn't
do the actual implementation (that's the agents' job).
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
import time

from wfc.shared.config import WFCConfig
from wfc.shared.telemetry import TelemetryRecord
from wfc.shared.schemas import Task, TaskGraph, TaskStatus, TaskComplexity
from wfc.shared.utils import get_git, get_selector


class AgentStrategy(Enum):
    """Agent assignment strategies."""
    ONE_PER_TASK = "one_per_task"  # One agent per task, max N parallel
    POOL = "pool"                   # N agents pick from queue
    SMART = "smart"                 # Group by file overlap


@dataclass
class RunResult:
    """Result of an implementation run - ELEGANT data structure."""
    run_id: str
    tasks_completed: int
    tasks_failed: int
    tasks_rolled_back: int
    duration_ms: int
    total_tokens: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for presentation tier."""
        return {
            "run_id": self.run_id,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_rolled_back": self.tasks_rolled_back,
            "duration_ms": self.duration_ms,
            "total_tokens": self.total_tokens
        }


class WFCOrchestrator:
    """
    WFC Implement Orchestrator - ELEGANT & MULTI-TIER

    Responsibilities (SINGLE):
    - Manage task queue and dependencies
    - Assign tasks to agents
    - Track execution state
    - Coordinate review and merge

    Does NOT:
    - Render UI (presentation tier)
    - Store data directly (uses data tier)
    - Implement code (that's agents)
    """

    def __init__(self, config: Optional[WFCConfig] = None,
                 project_root: Optional[Path] = None):
        """
        Initialize orchestrator.

        Args:
            config: WFC configuration
            project_root: Project root directory
        """
        self.config = config or WFCConfig()
        self.project_root = Path(project_root) if project_root else Path.cwd()

        # Git helper
        self.git = get_git(self.project_root)

        # Model selector
        self.selector = get_selector()

        # Execution state
        self.task_graph: Optional[TaskGraph] = None
        self.ready_queue: List[Task] = []
        self.in_progress: Dict[str, Task] = {}
        self.completed: Set[str] = set()
        self.failed: Set[str] = set()
        self.agent_reports: Dict[str, Dict[str, Any]] = {}  # Store agent reports for aggregation
        self.rollback_count: int = 0  # Track rollback events

        # Telemetry
        self.telemetry = TelemetryRecord("implement", run_id=self._generate_run_id())

    def run(self, tasks_file: Path) -> RunResult:
        """
        Run implementation - main entry point.

        Args:
            tasks_file: Path to TASKS.md

        Returns:
            RunResult with execution summary

        This is the method the presentation tier calls.
        """
        start_time = time.time()

        # Initialize
        self._load_tasks(tasks_file)
        self._validate_dag()
        self._initialize_queue()

        # Execute with execution engine
        from .executor import ExecutionEngine
        executor = ExecutionEngine(self)
        executor.execute()

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Build result
        # Aggregate tokens from all agent reports
        total_input = 0
        total_output = 0
        for report in self.agent_reports.values():
            tokens = report.get("tokens", {})
            total_input += tokens.get("input", 0)
            total_output += tokens.get("output", 0)

        result = RunResult(
            run_id=self.telemetry.data.get("run_id", "unknown"),
            tasks_completed=len(self.completed),
            tasks_failed=len(self.failed),
            tasks_rolled_back=self.rollback_count,  # Actual rollback events from merge_engine
            duration_ms=duration_ms,
            total_tokens={
                "input": total_input,
                "output": total_output,
                "total": total_input + total_output
            }
        )

        # Aggregate session metadata (if any agents used Entire.io)
        sessions_summary = self._aggregate_sessions()
        if sessions_summary:
            self.telemetry.add("entire_sessions", sessions_summary)

        # Record telemetry
        self.telemetry.add("result", result.to_dict())
        self.telemetry.save()

        return result

    def _load_tasks(self, tasks_file: Path) -> None:
        """Load tasks from TASKS.md."""
        from .parser import parse_tasks
        self.task_graph = parse_tasks(tasks_file)

    def _validate_dag(self) -> None:
        """Validate task graph is a DAG (no cycles)."""
        if not self.task_graph:
            raise ValueError("Task graph not loaded")

        if not self.task_graph.validate_dag():
            raise ValueError("Task graph contains cycles - cannot execute")

    def _initialize_queue(self) -> None:
        """Initialize ready queue with Level 0 tasks (no dependencies)."""
        if not self.task_graph:
            return

        levels = self.task_graph.get_dependency_levels()

        # Add all level 0 tasks to ready queue
        for task in self.task_graph.tasks:
            if levels.get(task.id, 0) == 0:
                self.ready_queue.append(task)
                task.status = TaskStatus.QUEUED

    def _generate_run_id(self) -> str:
        """Generate unique run ID."""
        import uuid
        return f"run-{uuid.uuid4().hex[:8]}"

    def get_next_task(self) -> Optional[Task]:
        """
        Get next task from ready queue.

        Returns:
            Next task to execute, or None if queue empty
        """
        if not self.ready_queue:
            return None
        return self.ready_queue.pop(0)

    def mark_task_complete(self, task_id: str, agent_report: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark task as complete and promote dependent tasks.

        Args:
            task_id: Task that completed
            agent_report: Optional agent report for token aggregation
        """
        self.completed.add(task_id)

        # Store agent report for token aggregation
        if agent_report:
            self.agent_reports[task_id] = agent_report

        # Remove from in_progress
        if task_id in self.in_progress:
            del self.in_progress[task_id]

        # Promote newly unblocked tasks to ready queue
        self._promote_unblocked_tasks()

    def mark_task_failed(self, task_id: str) -> None:
        """
        Mark task as failed.

        Args:
            task_id: Task that failed
        """
        self.failed.add(task_id)

        # Remove from in_progress
        if task_id in self.in_progress:
            del self.in_progress[task_id]

    def _promote_unblocked_tasks(self) -> None:
        """Promote tasks whose dependencies are now satisfied."""
        if not self.task_graph:
            return

        for task in self.task_graph.tasks:
            # Skip if already processed
            if (task.id in self.completed or
                task.id in self.failed or
                task.id in self.in_progress or
                task in self.ready_queue):
                continue

            # Check if all dependencies are completed
            if all(dep_id in self.completed for dep_id in task.dependencies):
                self.ready_queue.append(task)
                task.status = TaskStatus.QUEUED

    def _aggregate_sessions(self) -> Dict[str, Any]:
        """
        Aggregate Entire.io session metadata from agent reports (NO DATA EXPOSURE).

        Returns:
            Dictionary with session metadata summary
        """
        sessions = {}

        for task_id, report in self.agent_reports.items():
            entire_session = report.get("entire_session")
            if entire_session:
                sessions[task_id] = {
                    "session_id": entire_session.get("session_id"),
                    "checkpoints": list(entire_session.get("checkpoints", {}).keys()),
                    "local_only": True,  # Emphasize no remote push
                    "branch": "entire/checkpoints/v1"
                }

        return sessions


# Convenience function for presentation tier
def run_implementation(tasks_file: Path, config: Optional[WFCConfig] = None,
                      project_root: Optional[Path] = None) -> RunResult:
    """
    Run implementation (convenience function for CLI/API).

    Args:
        tasks_file: Path to TASKS.md
        config: Optional WFC configuration
        project_root: Optional project root

    Returns:
        RunResult
    """
    orchestrator = WFCOrchestrator(config, project_root)
    return orchestrator.run(tasks_file)


if __name__ == "__main__":
    # Simple test
    print("WFC Orchestrator Test")
    print("=" * 50)

    # Create mock task graph
    from wfc.shared.schemas import Task, TaskComplexity

    task1 = Task(
        id="TASK-001",
        title="Setup",
        description="Setup project",
        acceptance_criteria=["Directory created"],
        complexity=TaskComplexity.S
    )

    task2 = Task(
        id="TASK-002",
        title="Implement",
        description="Implement feature",
        acceptance_criteria=["Feature works"],
        complexity=TaskComplexity.M,
        dependencies=["TASK-001"]
    )

    orchestrator = WFCOrchestrator()
    orchestrator.task_graph = TaskGraph()
    orchestrator.task_graph.add(task1)
    orchestrator.task_graph.add(task2)

    # Validate and initialize
    orchestrator._validate_dag()
    orchestrator._initialize_queue()

    print(f"✅ DAG valid: {orchestrator.task_graph.validate_dag()}")
    print(f"✅ Ready queue: {len(orchestrator.ready_queue)} tasks")
    print(f"✅ Dependency levels: {orchestrator.task_graph.get_dependency_levels()}")

    # Get next task
    next_task = orchestrator.get_next_task()
    if next_task:
        print(f"✅ Next task: {next_task.id}")
        orchestrator.in_progress[next_task.id] = next_task

        # Mark complete
        orchestrator.mark_task_complete(next_task.id)
        print(f"✅ Completed: {next_task.id}")

        # Get next (should be TASK-002 now)
        next_task = orchestrator.get_next_task()
        if next_task:
            print(f"✅ Next task after dependency: {next_task.id}")

    print("\n✅ Orchestrator test passed!")
