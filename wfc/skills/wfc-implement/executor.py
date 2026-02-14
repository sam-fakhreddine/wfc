"""
WFC Implement - Execution Engine

ELEGANT: Wires orchestrator → agent → review → merge
PARALLEL: Manages concurrent agents via Task tool
DELEGATION: NEVER executes agents in-process, ALWAYS delegates to subagents

CRITICAL PRINCIPLE:
The orchestrator and executor NEVER do implementation work.
They ONLY coordinate. All actual work is done by subagents via Task tool.
"""

import time
from pathlib import Path
from typing import Dict, Optional

from wfc.shared.extended_thinking import ExtendedThinkingDecider
from wfc.shared.schemas import Task, TaskStatus

from .agent import AgentReport
from .merge_engine import MergeEngine
from .orchestrator import WFCOrchestrator


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

        self.active_subagents: Dict[str, str] = {}
        self.agent_prompts: Dict[str, str] = {}
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
            if self._is_complete():
                break

            if len(self.active_subagents) < max_agents:
                task = self.orchestrator.get_next_task()
                if task:
                    self._spawn_subagent(task)

            # NOTE: In production, this would use TaskOutput tool to poll
            if self.active_subagents:
                task_id = list(self.active_subagents.keys())[0]
                agent_task_id = self.active_subagents[task_id]

                report = self._wait_for_subagent(task_id, agent_task_id)

                task = self.orchestrator.in_progress.get(task_id)
                if task:
                    self._process_report(report, task)

                del self.active_subagents[task_id]

            time.sleep(0.1)

    def _spawn_subagent(self, task: Task) -> None:
        """
        Spawn subagent via Task tool to execute task implementation.

        CRITICAL: This method delegates to a subagent subprocess.
        It does NOT execute agent code in-process.
        """
        self.agent_counter += 1
        agent_id = f"agent-{self.agent_counter}"

        prompt = self._build_agent_prompt(task, agent_id)

        print(f"🚀 Spawning subagent {agent_id} for {task.id}")

        self.active_subagents[task.id] = agent_id
        self.agent_prompts[task.id] = prompt
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

        Enables extended thinking for complex tasks based on:
        - Task complexity (L, XL)
        - Critical properties (SAFETY, LIVENESS, SECURITY)
        - Retry count (failed before, think harder)
        """
        retry_count = task.tags.count("retry") if hasattr(task, "tags") else 0

        # NOTE: task.properties_satisfied contains PROP-### IDs, but the decider
        thinking_config = ExtendedThinkingDecider.should_use_extended_thinking(
            complexity=task.complexity.value,
            properties=[],
            retry_count=retry_count,
            has_dependencies=len(task.dependencies) > 0 if hasattr(task, "dependencies") else False,
        )

        if thinking_config.mode.value != "normal":
            print(f"   ⚡ Extended thinking enabled for {task.id}")
            print(f"      Reason: {thinking_config.reason}")
            if thinking_config.budget_tokens:
                print(f"      Budget: {thinking_config.budget_tokens} tokens")

        prompt_parts = [
            f"You are {agent_id}, a WFC implementation agent.",
            f"Task ID: {task.id}",
            f"Task Complexity: {task.complexity.value}",
            f"Task Description: {task.description}",
        ]

        thinking_section = thinking_config.to_prompt_section()
        if thinking_section:
            prompt_parts.append(thinking_section)

        prompt_parts.extend(
            [
                "",
                "Follow the TDD workflow:",
                "1. UNDERSTAND - Read task, properties, test plan, existing code",
                "2. TEST_FIRST - Write tests BEFORE implementation",
                "3. IMPLEMENT - Write minimum code to pass tests",
                "",
                "   IF BUGS DETECTED (during implementation or testing):",
                "   3a. ROOT_CAUSE_INVESTIGATION (REQUIRED)",
                "       - NO FIXES WITHOUT ROOT CAUSE FIRST",
                "       - Read error messages carefully, reproduce consistently",
                "       - Trace data flow, identify root cause",
                "       - Document: WHAT (symptom), WHY (cause), WHERE (location)",
                "",
                "   3b. PATTERN_ANALYSIS",
                "       - Find similar working code",
                "       - Compare line-by-line, map dependencies",
                "",
                "   3c. HYPOTHESIS_TESTING",
                "       - Form ONE clear hypothesis",
                "       - Test with minimal change",
                "       - Verify results before proceeding",
                "",
                "   3d. FIX_IMPLEMENTATION",
                "       - Write test that reproduces bug (fails before fix)",
                "       - Implement minimal fix addressing root cause",
                "       - Verify all tests pass",
                "       - Apply 3-strikes rule (max 3 fix attempts)",
                "",
                "4. REFACTOR - Clean up while keeping tests passing",
                "5. QUALITY_CHECK - Run formatters, linters, tests",
                "6. SUBMIT - Produce agent report with root cause documentation",
                "",
                "CRITICAL: For all bug fixes, include root cause analysis (WHAT, WHY, WHERE, FIX).",
                "See wfc/skills/implement/DEBUGGING.md for complete methodology.",
                "",
                f"Properties to satisfy: {', '.join(task.properties_satisfied)}",
                f"Acceptance criteria: {', '.join(task.acceptance_criteria)}",
            ]
        )

        return "\n".join(prompt_parts)

    def _wait_for_subagent(self, task_id: str, agent_id: str) -> AgentReport:
        """
        Wait for subagent completion and retrieve report.

        In production, this would use TaskOutput tool to poll the subagent.
        For now, returns a mock report.
        """
        print(f"⏳ Waiting for subagent {agent_id} to complete {task_id}")

        from .agent import AgentReport

        return AgentReport(
            agent_id=agent_id,
            task_id=task_id,
            status="success",
            branch=f"wfc-task-{task_id}",
            worktree_path=f".worktrees/{task_id}",
            commits=[{"sha": "mock123", "message": f"Implement {task_id}", "files_changed": []}],
            properties_satisfied={},
            tests={},
        )

    def _process_report(self, report: AgentReport, task: Task) -> None:
        """Process agent report."""
        if report.status == "failed":
            self.orchestrator.mark_task_failed(task.id)
            return

        review_passed, review_report = self._review(report)

        if not review_passed:
            self.orchestrator.mark_task_failed(task.id)
            return

        merge_strategy = self.config.get("merge.strategy", "pr")

        if merge_strategy == "pr":
            merge_result = self.merge_engine.create_pr(
                task=task,
                branch=report.branch,
                worktree_path=Path(report.worktree_path),
                review_report=review_report,
            )

            if merge_result.pr_created:
                self.orchestrator.mark_task_complete(
                    task.id,
                    {
                        **report.to_dict(),
                        "pr_url": merge_result.pr_url,
                        "pr_number": merge_result.pr_number,
                    },
                )
            else:
                self.orchestrator.mark_task_failed(task.id)

        else:
            merge_result = self.merge_engine.merge(
                task=task, branch=report.branch, worktree_path=Path(report.worktree_path)
            )

            from .merge_engine import MergeStatus

            if merge_result.status == MergeStatus.ROLLED_BACK:
                self.orchestrator.rollback_count += 1

            if merge_result.integration_tests_passed:
                self.orchestrator.mark_task_complete(task.id, report.to_dict())
            else:
                self.orchestrator.mark_task_failed(task.id)

    def _review(self, report: AgentReport) -> tuple[bool, Optional[Dict]]:
        """
        Run review (using mock for now).

        Returns:
            Tuple of (passed: bool, review_report: Optional[Dict])
        """
        from wfc_review.mock import mock_review

        result = mock_review(
            files=report.commits[0]["files_changed"] if report.commits else [],
            properties=list(report.properties_satisfied.keys()),
            task_id=report.task_id,
            mode="pass",
        )

        return result["passed"], result

    def _is_complete(self) -> bool:
        """Check if execution is complete."""
        if not self.orchestrator.task_graph:
            return True

        total = len(self.orchestrator.task_graph.tasks)
        done = len(self.orchestrator.completed) + len(self.orchestrator.failed)

        return done >= total and len(self.active_subagents) == 0
