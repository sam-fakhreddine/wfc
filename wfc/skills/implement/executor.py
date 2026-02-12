"""
WFC Implement - Execution Engine

ELEGANT: Wires orchestrator → agent → review → merge
PARALLEL: Manages concurrent agents via Task tool
DELEGATION: NEVER executes agents in-process, ALWAYS delegates to subagents

CRITICAL PRINCIPLE:
The orchestrator and executor NEVER do implementation work.
They ONLY coordinate. All actual work is done by subagents via Task tool.
"""

from pathlib import Path
from typing import Dict, List, Optional
import time
import json

from wfc.shared.config import WFCConfig
from wfc.shared.schemas import Task, TaskStatus

from .orchestrator import WFCOrchestrator
from .agent import AgentReport
from .merge_engine import MergeEngine, MergeResult


class ExecutionEngine:
    """
    Execution engine - wires everything together.

    CRITICAL: This class ONLY orchestrates via Task tool.
    It NEVER executes agent code directly.

    All agent work happens in subagents spawned via Task tool.
    This ensures true parallelism, isolation, and follows
    Claude Code best practices.
    """

    def __init__(self, orchestrator: WFCOrchestrator):
        """Initialize with orchestrator."""
        self.orchestrator = orchestrator
        self.config = orchestrator.config
        self.project_root = orchestrator.project_root

        self.merge_engine = MergeEngine(self.project_root, self.config)

        # Active subagent tasks (task_id -> agent_task_id mapping)
        self.active_subagents: Dict[str, str] = {}
        self.agent_counter = 0

    def execute(self) -> None:
        """
        Execute all tasks via subagents.

        CRITICAL: This method NEVER does implementation work.
        It ONLY spawns subagents via Task tool and coordinates results.
        """
        max_agents = self.config.get("orchestration.max_agents", 5)

        print(f"\n🎯 Execution Strategy: Delegate to {max_agents} parallel subagents")
        print("   Orchestrator will NEVER do work, only coordinate\n")

        while True:
            # Check if done
            if self._is_complete():
                break

            # Check if we can start more subagents
            if len(self.active_subagents) < max_agents:
                task = self.orchestrator.get_next_task()
                if task:
                    self._spawn_subagent(task)

            # Check completed subagents
            # NOTE: In production, this would use TaskOutput tool to poll
            # For now, we'll process sequentially
            if self.active_subagents:
                task_id = list(self.active_subagents.keys())[0]
                agent_task_id = self.active_subagents[task_id]

                # Wait for subagent completion (via TaskOutput in real impl)
                report = self._wait_for_subagent(task_id, agent_task_id)

                # Process report
                task = self.orchestrator.in_progress.get(task_id)
                if task:
                    self._process_report(report, task)

                # Remove from active
                del self.active_subagents[task_id]

            # Small delay (in event-driven system, would use callbacks)
            time.sleep(0.1)

    def _spawn_subagent(self, task: Task) -> None:
        """
        Spawn subagent via Task tool to execute task implementation.

        CRITICAL: This method delegates to a subagent subprocess.
        It does NOT execute agent code in-process.
        """
        self.agent_counter += 1
        agent_id = f"agent-{self.agent_counter}"

        # Build prompt for subagent
        agent_prompt = self._build_agent_prompt(task, agent_id)

        # Spawn subagent via Task tool (would be actual tool call in production)
        # For now, we'll use a placeholder that simulates the delegation
        print(f"🚀 Spawning subagent {agent_id} for {task.id}")

        # Track active subagent
        self.active_subagents[task.id] = agent_id
        self.orchestrator.in_progress[task.id] = task
        task.status = TaskStatus.IN_PROGRESS

    def _build_agent_prompt(self, task: Task, agent_id: str) -> str:
        """
        Build prompt for subagent Task tool invocation.

        Returns a complete prompt that instructs the subagent to:
        1. Understand the task
        2. Follow TDD workflow (TEST_FIRST → IMPLEMENT → REFACTOR)
        3. Run quality checks
        4. Submit agent report
        """
        prompt_parts = [
            f"You are {agent_id}, a WFC implementation agent.",
            f"Task ID: {task.id}",
            f"Task Description: {task.description}",
            "",
            "Follow the TDD workflow:",
            "1. UNDERSTAND - Read task, properties, test plan, existing code",
            "2. TEST_FIRST - Write tests BEFORE implementation",
            "3. IMPLEMENT - Write minimum code to pass tests",
            "4. REFACTOR - Clean up while keeping tests passing",
            "5. QUALITY_CHECK - Run formatters, linters, tests",
            "6. SUBMIT - Produce agent report",
            "",
            f"Properties to satisfy: {', '.join(task.properties)}",
            f"Acceptance criteria: {', '.join(task.acceptance_criteria)}",
        ]

        return "\n".join(prompt_parts)

    def _wait_for_subagent(self, task_id: str, agent_id: str) -> AgentReport:
        """
        Wait for subagent completion and retrieve report.

        In production, this would use TaskOutput tool to poll the subagent.
        For now, returns a mock report.
        """
        print(f"⏳ Waiting for subagent {agent_id} to complete {task_id}")

        # In production: Use TaskOutput tool to poll subagent progress
        # For now, return mock report
        from .agent import AgentReport

        return AgentReport(
            agent_id=agent_id,
            task_id=task_id,
            status="success",
            branch=f"wfc-task-{task_id}",
            worktree_path=f".worktrees/{task_id}",
            commits=[{
                "sha": "mock123",
                "message": f"Implement {task_id}",
                "files_changed": []
            }],
            properties_satisfied={},
            tests_passed=True,
            test_results={}
        )

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

        return done >= total and len(self.active_subagents) == 0
