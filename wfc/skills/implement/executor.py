"""
WFC Implement - Execution Engine

ELEGANT: Wires orchestrator → agent → review → merge
PARALLEL: Manages concurrent agents
"""

from pathlib import Path
from typing import Dict, List
import time

from wfc.shared.config import WFCConfig
from wfc.shared.schemas import Task, TaskStatus

from .orchestrator import WFCOrchestrator
from .agent import WFCAgent, AgentReport
from .merge_engine import MergeEngine, MergeResult


class ExecutionEngine:
    """
    Execution engine - wires everything together.

    This is where orchestrator → agent → review → merge happens.
    """

    def __init__(self, orchestrator: WFCOrchestrator):
        """Initialize with orchestrator."""
        self.orchestrator = orchestrator
        self.config = orchestrator.config
        self.project_root = orchestrator.project_root

        self.merge_engine = MergeEngine(self.project_root, self.config)

        # Active agents
        self.active_agents: Dict[str, WFCAgent] = {}
        self.agent_counter = 0

    def execute(self) -> None:
        """Execute all tasks."""
        max_agents = self.config.get("orchestration.max_agents", 5)

        while True:
            # Check if done
            if self._is_complete():
                break

            # Check if we can start more agents
            if len(self.active_agents) < max_agents:
                task = self.orchestrator.get_next_task()
                if task:
                    self._start_agent(task)

            # Check completed agents (in real impl, would be async)
            # For now, process one at a time
            if self.active_agents:
                agent_id = list(self.active_agents.keys())[0]
                agent = self.active_agents[agent_id]

                # Run agent
                report = agent.implement()

                # Process report
                self._process_report(report, agent.task)

                # Remove from active
                del self.active_agents[agent_id]

            # Small delay (in real impl, would be event-driven)
            time.sleep(0.1)

    def _start_agent(self, task: Task) -> None:
        """Start agent for task."""
        self.agent_counter += 1
        agent_id = f"agent-{self.agent_counter}"

        agent = WFCAgent(
            agent_id=agent_id,
            task=task,
            project_root=self.project_root,
            config=self.config
        )

        self.active_agents[agent_id] = agent
        self.orchestrator.in_progress[task.id] = task
        task.status = TaskStatus.IN_PROGRESS

    def _process_report(self, report: AgentReport, task: Task) -> None:
        """Process agent report."""
        if report.status == "failed":
            self.orchestrator.mark_task_failed(task.id)
            return

        # Route through review (using mock for now)
        review_passed = self._review(report)

        if not review_passed:
            # Phase 1: Mark as failed
            # Phase 2: Implement retry logic with agent feedback loop
            self.orchestrator.mark_task_failed(task.id)
            return

        # Merge
        merge_result = self.merge_engine.merge(
            task_id=task.id,
            branch=report.branch,
            worktree_path=Path(report.worktree_path)
        )

        # Track rollbacks
        from .merge_engine import MergeStatus
        if merge_result.status == MergeStatus.ROLLED_BACK:
            self.orchestrator.rollback_count += 1

        if merge_result.integration_tests_passed:
            self.orchestrator.mark_task_complete(task.id, report.to_dict())
        else:
            self.orchestrator.mark_task_failed(task.id)

    def _review(self, report: AgentReport) -> bool:
        """Run review (using mock for now)."""
        from wfc.skills.review.mock import mock_review

        result = mock_review(
            files=report.commits[0]["files_changed"] if report.commits else [],
            properties=list(report.properties_satisfied.keys()),
            task_id=report.task_id,
            mode="pass"  # For now, always pass
        )

        return result["passed"]

    def _is_complete(self) -> bool:
        """Check if execution is complete."""
        if not self.orchestrator.task_graph:
            return True

        total = len(self.orchestrator.task_graph.tasks)
        done = len(self.orchestrator.completed) + len(self.orchestrator.failed)

        return done >= total and len(self.active_agents) == 0
