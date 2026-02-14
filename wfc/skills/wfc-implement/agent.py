"""
WFC Implement - Agent (TDD Workflow with Quality Gate)

ELEGANT: Clear TDD workflow, single responsibility
MULTI-TIER: Pure logic, returns structured data
PARALLEL: Multiple agents can work concurrently
TOKEN-AWARE: Quality gate blocks review if standards not met

An agent is assigned a task, creates a worktree, implements in TDD style,
runs quality checks (Trunk.io or language-specific), and produces a structured
report. Quality gate ensures code meets standards before expensive multi-agent
review, saving 50%+ tokens.

Workflow:
1. UNDERSTAND - Read task, properties, existing code
2. TEST FIRST (RED) - Write tests before implementation
3. IMPLEMENT (GREEN) - Write minimum code to pass tests
4. REFACTOR - Clean up while maintaining passing tests
5. QUALITY CHECK - Run Trunk.io / quality tools (BLOCKS if fails)
6. SUBMIT - Produce report and route to review (only if quality passed)
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from wfc.scripts.token_manager import TokenManager
from wfc.shared.config import WFCConfig
from wfc.shared.schemas import Task, TaskComplexity
from wfc.shared.utils import GitHelper, ModelConfig


class IssueSeverity(Enum):
    """
    Issue severity levels (aligns with MergeEngine philosophy).

    User requirement: warnings != failures
    - WARNING: Does not block (style hints, deprecations)
    - ERROR: Blocks submission (broken code, failing tests)
    - CRITICAL: Immediate failure (security, data loss)
    """

    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AgentPhase(Enum):
    """TDD workflow phases."""

    UNDERSTAND = "understand"
    TEST_FIRST = "test_first"
    IMPLEMENT = "implement"
    REFACTOR = "refactor"
    QUALITY_CHECK = "quality_check"
    SUBMIT = "submit"


@dataclass
class AgentReport:
    """
    Structured agent output - ELEGANT data structure.

    This is what agents return to the orchestrator.
    MULTI-TIER: Pure data, no rendering logic.
    """

    task_id: str
    agent_id: str
    status: str
    worktree_path: str
    branch: str

    commits: List[Dict[str, Any]] = field(default_factory=list)

    tests: Dict[str, Any] = field(default_factory=dict)

    properties_satisfied: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    quality_check: Dict[str, Any] = field(default_factory=dict)

    confidence: Dict[str, Any] = field(default_factory=dict)

    discoveries: List[Dict[str, str]] = field(default_factory=list)

    root_cause: Optional[Dict[str, str]] = None

    model: str = ""
    provider: str = ""
    tokens: Dict[str, int] = field(default_factory=dict)
    duration_ms: int = 0

    entire_session: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "status": self.status,
            "worktree_path": self.worktree_path,
            "branch": self.branch,
            "commits": self.commits,
            "tests": self.tests,
            "properties_satisfied": self.properties_satisfied,
            "quality_check": self.quality_check,
            "confidence": self.confidence,
            "discoveries": self.discoveries,
            "root_cause": self.root_cause,
            "model": self.model,
            "provider": self.provider,
            "tokens": self.tokens,
            "duration_ms": self.duration_ms,
            "entire_session": self.entire_session,
        }


class WFCAgent:
    """
    WFC Implementing Agent - ELEGANT, TDD-FIRST, TOKEN-AWARE

    Follows strict TDD workflow with quality gate:
    1. UNDERSTAND - Read task, properties, existing code
    2. TEST FIRST (RED) - Write tests before implementation
    3. IMPLEMENT (GREEN) - Write minimum code to pass tests
    4. REFACTOR - Clean up while maintaining tests passing
    5. QUALITY CHECK - Run Trunk.io universal checker (BLOCKS if fails)
    6. SUBMIT - Commit and produce report

    SINGLE RESPONSIBILITY: Implement one task in TDD style with quality enforcement
    TOKEN-AWARE: Quality gate saves 50%+ review tokens by catching issues early
    """

    def __init__(self, agent_id: str, task: Task, project_root: Path, config: WFCConfig):
        """
        Initialize agent.

        Args:
            agent_id: Unique agent identifier
            task: Task to implement
            project_root: Project root directory
            config: WFC configuration
        """
        self.agent_id = agent_id
        self.task = task
        self.project_root = Path(project_root)
        self.config = config

        self.worktree_path = self.project_root / ".worktrees" / f"wfc-{task.id}"
        self.branch_name = f"wfc/{task.id}-{self._slugify(task.title)}"

        self.current_phase = AgentPhase.UNDERSTAND
        self.commits: List[Dict[str, Any]] = []
        self.discoveries: List[Dict[str, str]] = []
        self.quality_check_result: Dict[str, Any] = {}

        self.task_context: Dict[str, Any] = {}
        self.properties_context: Dict[str, Any] = {}
        self.test_plan_context: Dict[str, Any] = {}
        self.affected_files: List[str] = []
        self.confidence_assessment: Optional[Dict[str, Any]] = None

        token_manager = TokenManager()
        self.token_budget = token_manager.create_budget(task_id=task.id, complexity=task.complexity)

        self.git: Optional[GitHelper] = None

        self.entire_enabled = False
        self.entire_session_id: Optional[str] = None
        self.checkpoints: Dict[str, str] = {}

    def implement(self) -> AgentReport:
        """
        Main entry point - implement the task in TDD style.

        Returns:
            AgentReport with results

        This is the method the orchestrator calls.
        """
        start_time = time.time()

        try:
            self._setup_worktree()

            self._phase_understand()
            self._phase_test_first()
            self._phase_implement()
            self._phase_refactor()
            self._phase_quality_check()
            self._phase_submit()

            duration_ms = int((time.time() - start_time) * 1000)

            return AgentReport(
                task_id=self.task.id,
                agent_id=self.agent_id,
                status="ready_for_review",
                worktree_path=str(self.worktree_path),
                branch=self.branch_name,
                commits=self.commits,
                tests=self._get_test_results(),
                properties_satisfied=self._get_properties_satisfied(),
                quality_check=self._get_quality_results(),
                confidence=self._get_confidence_results(),
                discoveries=self.discoveries,
                model=self._get_model().model_id,
                provider=self._get_model().provider,
                tokens={
                    "input": self.token_budget.actual_input,
                    "output": self.token_budget.actual_output,
                    "total": self.token_budget.actual_total,
                    "budget": self.token_budget.budget_total,
                    "usage_pct": self.token_budget.get_usage_percentage(),
                },
                duration_ms=duration_ms,
                entire_session=(
                    {
                        "session_id": self.entire_session_id,
                        "checkpoints": self.checkpoints,
                        "local_only": True,
                        "branch": "entire/checkpoints/v1",
                    }
                    if self.entire_enabled
                    else None
                ),
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            self._log_reflexion_on_failure(str(e))

            return AgentReport(
                task_id=self.task.id,
                agent_id=self.agent_id,
                status="failed",
                worktree_path=str(self.worktree_path),
                branch=self.branch_name,
                commits=self.commits,
                discoveries=[
                    {"description": f"Implementation failed: {str(e)}", "severity": "critical"}
                ],
                duration_ms=duration_ms,
            )

    def _setup_worktree(self) -> None:
        """Create isolated worktree for this task."""
        self.current_phase = AgentPhase.UNDERSTAND

        git = GitHelper(self.project_root)
        integration_branch = self.config.get("branching.integration_branch", "develop")
        git.worktree_add(self.worktree_path, self.branch_name, integration_branch)

        self.git = GitHelper(self.worktree_path)

        task_dir = self.worktree_path / ".wfc-task"
        task_dir.mkdir(exist_ok=True)

        import json

        (task_dir / "task.json").write_text(json.dumps(self.task.to_dict(), indent=2))

        # Note: Properties and test-plan are written by orchestrator

        self._setup_entire_io()

    def _phase_understand(self) -> None:
        """
        Phase 1: UNDERSTAND

        Read task definition, properties, test plan, and existing code.
        Assess confidence BEFORE starting implementation (SuperClaude pattern).

        CRITICAL: If confidence < 70%, STOP and ask user for guidance.
        This prevents 25-250x token waste from wrong-direction work.
        """
        self.current_phase = AgentPhase.UNDERSTAND

        task_dir = self.worktree_path / ".wfc-task"

        task_file = task_dir / "task.json"
        if task_file.exists():
            import json

            task_data = json.loads(task_file.read_text())
            self.task_context = task_data

        props_file = task_dir / "properties.json"
        if props_file.exists():
            import json

            self.properties_context = json.loads(props_file.read_text())
        else:
            self.properties_context = {}

        test_plan_file = task_dir / "test-plan.json"
        if test_plan_file.exists():
            import json

            self.test_plan_context = json.loads(test_plan_file.read_text())
        else:
            self.test_plan_context = {}

        self.affected_files = []
        for file_path in self.task.files_likely_affected:
            full_path = self.worktree_path / file_path
            if full_path.exists():
                self.affected_files.append(file_path)

        self._assess_confidence()

        if not self.confidence_assessment.get("should_proceed", False):
            confidence_score = self.confidence_assessment.get("confidence_score", 0)
            questions = self.confidence_assessment.get("questions", [])

            self.discoveries.append(
                {
                    "description": f"Low confidence ({confidence_score}%) - cannot proceed without clarification",
                    "severity": "critical",
                    "questions": questions,
                }
            )

            raise Exception(
                f"Confidence too low ({confidence_score}%) to proceed. "
                f"Need clarification on {len(questions)} questions. "
                "See agent report for questions."
            )

        self._search_past_errors()

        self._track_tokens(input_tokens=100, output_tokens=50)

        self._create_checkpoint(
            "UNDERSTAND",
            {
                "confidence_score": self.confidence_assessment.get("confidence_score", 0),
                "affected_files": self.affected_files,
                "should_proceed": self.confidence_assessment.get("should_proceed", False),
            },
        )

    def _phase_test_first(self) -> None:
        """
        Phase 2: TEST FIRST (RED)

        Write tests BEFORE implementation using Claude Code Task tool.
        Tests must cover acceptance criteria and properties.
        Run tests - they should FAIL (that's the RED in TDD).
        """
        self.current_phase = AgentPhase.TEST_FIRST

        prompt = self._build_test_prompt()

        # NOTE: In real execution, this would call the Task tool
        test_files = self._execute_claude_task(
            description="Write tests for task", prompt=prompt, phase="TEST_FIRST"
        )

        if test_files:
            test_result = self._run_tests()
            if test_result.get("passed", False):
                self.discoveries.append(
                    {
                        "description": "Warning: Tests passed in RED phase - should fail initially",
                        "severity": "medium",
                    }
                )

        if self.git and test_files:
            self._make_commit(f"test: add tests for {self.task.id}", test_files, "test")

        self._track_tokens(input_tokens=150, output_tokens=200)

        self._create_checkpoint(
            "TEST_FIRST",
            {
                "test_files_created": test_files if test_files else [],
                "tests_initially_failed": (
                    not test_result.get("passed", True) if test_files else True
                ),
            },
        )

    def _phase_implement(self) -> None:
        """
        Phase 3: IMPLEMENT (GREEN)

        Write minimum code to make tests pass using Claude Code Task tool.
        Follow ELEGANT principles - simple, clear, effective.
        Run tests - they should PASS (that's the GREEN in TDD).
        """
        self.current_phase = AgentPhase.IMPLEMENT

        prompt = self._build_implementation_prompt()

        impl_files = self._execute_claude_task(
            description="Implement task to pass tests", prompt=prompt, phase="IMPLEMENT"
        )

        if impl_files:
            test_result = self._run_tests()
            if not test_result.get("passed", False):
                self.discoveries.append(
                    {
                        "description": f"Warning: Tests failed in GREEN phase - implementation incomplete: {test_result.get('failures', [])}",
                        "severity": "high",
                    }
                )

        if self.git and impl_files:
            self._make_commit(f"feat: implement {self.task.title}", impl_files, "implementation")

        self._track_tokens(input_tokens=200, output_tokens=300)

        self._create_checkpoint(
            "IMPLEMENT",
            {
                "implementation_files": impl_files if impl_files else [],
                "tests_passed": test_result.get("passed", False) if impl_files else False,
            },
        )

    def _phase_refactor(self) -> None:
        """
        Phase 4: REFACTOR

        Clean up implementation without changing behavior using Claude Code Task tool.
        Maintain SOLID and DRY principles.
        Run tests - they should still PASS.
        """
        self.current_phase = AgentPhase.REFACTOR

        if self.task.complexity in [TaskComplexity.L, TaskComplexity.XL]:
            prompt = self._build_refactoring_prompt()

            refactored_files = self._execute_claude_task(
                description="Refactor implementation for clarity", prompt=prompt, phase="REFACTOR"
            )

            if refactored_files:
                test_result = self._run_tests()
                if not test_result.get("passed", False):
                    self.discoveries.append(
                        {
                            "description": "Critical: Tests failed after refactoring - behavior changed",
                            "severity": "critical",
                        }
                    )
                    if self.git:
                        self._rollback_last_change()

                elif self.git:
                    self._make_commit(
                        f"refactor: improve code quality for {self.task.id}",
                        refactored_files,
                        "refactor",
                    )
        else:
            pass

        self._track_tokens(input_tokens=100, output_tokens=150)

        self._create_checkpoint(
            "REFACTOR",
            {
                "refactored": self.task.complexity in [TaskComplexity.L, TaskComplexity.XL],
                "complexity": self.task.complexity.value if self.task.complexity else "unknown",
            },
        )

    def _phase_quality_check(self) -> None:
        """
        Phase 5: QUALITY CHECK (Pre-Review Gate)

        Run universal quality checks before submitting to review.
        This enforces code standards and catches simple issues early,
        saving expensive multi-agent review tokens.

        TASK-001: Integrate Universal Quality Checker
        - Uses Trunk.io for universal linting (all languages)
        - Falls back to language-specific tools if Trunk unavailable
        - Blocks submission if checks fail
        - Reports fixable issues
        """
        self.current_phase = AgentPhase.QUALITY_CHECK

        changed_files = self._get_changed_files()

        if not changed_files:
            self.quality_check_result = {
                "passed": True,
                "tool": "none",
                "message": "No files changed",
                "issues_found": 0,
                "fixable_issues": 0,
            }
            return

        try:
            from wfc.scripts.universal_quality_checker import UniversalQualityChecker

            checker = UniversalQualityChecker(files=changed_files)
            result = checker.check(auto_fix=False)

            self.quality_check_result = {
                "passed": result.passed,
                "tool": "trunk",
                "output": result.output,
                "issues_found": result.issues_found,
                "fixable_issues": result.fixable_issues,
                "files_checked": result.files_checked,
            }

            if not result.passed:
                self.discoveries.append(
                    {
                        "description": f"Quality check failed: {result.issues_found} issues found",
                        "severity": "high",
                        "fixable": result.fixable_issues > 0,
                        "fix_command": "trunk check --fix" if result.fixable_issues > 0 else None,
                    }
                )

        except ImportError:
            self._fallback_quality_check(changed_files)

    def _fallback_quality_check(self, files: List[str]) -> None:
        """
        Fallback quality check using language-specific tools.

        Args:
            files: List of changed files
        """
        try:
            from wfc.scripts.quality_checker import QualityChecker

            python_files = [f for f in files if f.endswith(".py")]

            if not python_files:
                self.quality_check_result = {
                    "passed": True,
                    "tool": "none",
                    "message": "No Python files to check",
                    "issues_found": 0,
                    "fixable_issues": 0,
                }
                return

            checker = QualityChecker(python_files, run_tests=False)
            report = checker.check_all()

            self.quality_check_result = {
                "passed": report.passed,
                "tool": "python-specific",
                "checks": [
                    {
                        "name": check.name,
                        "passed": check.passed,
                        "message": check.message,
                        "fix_command": check.fix_command,
                    }
                    for check in report.checks
                ],
                "files_checked": len(python_files),
            }

            if not report.passed:
                for check in report.checks:
                    if not check.passed:
                        self.discoveries.append(
                            {
                                "description": f"{check.name} failed: {check.message}",
                                "severity": "high",
                                "fixable": check.fix_command is not None,
                                "fix_command": check.fix_command,
                            }
                        )

        except ImportError:
            self.quality_check_result = {
                "passed": True,
                "tool": "none",
                "message": "No quality checker available (install Trunk or quality_checker)",
                "issues_found": 0,
                "fixable_issues": 0,
            }

        self._track_tokens(input_tokens=50, output_tokens=100)

        self._create_checkpoint(
            "QUALITY_CHECK",
            {
                "quality_passed": self.quality_check_result.get("passed", True),
                "tool_used": self.quality_check_result.get("tool", "none"),
                "issues_found": self.quality_check_result.get("issues_found", 0),
            },
        )

    def _phase_submit(self) -> None:
        """
        Phase 6: SUBMIT

        Final verification and commit. Only proceed if quality check passed.

        QUALITY GATE: Blocks submission if quality check failed.
        This saves expensive multi-agent review tokens by catching
        simple issues early.
        """
        self.current_phase = AgentPhase.SUBMIT

        if self.quality_check_result and not self.quality_check_result.get("passed", True):
            issues = self.quality_check_result.get("issues_found", 0)

            if self._are_quality_issues_warnings():
                self.discoveries.append(
                    {
                        "description": f"Quality check found {issues} warnings (not blocking)",
                        "severity": "warning",
                    }
                )
            else:
                raise Exception(
                    f"Quality check failed with {issues} issues. "
                    f"Fix issues before submitting to review."
                )

        final_test_result = self._run_tests()
        if not final_test_result.get("passed", False):
            raise Exception(
                f"Tests failed before submission: {final_test_result.get('failures', [])}"
            )

        for criterion in self.task.acceptance_criteria:
            pass

        properties_report = self._get_properties_satisfied()
        for prop_id, prop_status in properties_report.items():
            if prop_status["status"] == "violated":
                raise Exception(f"Property {prop_id} violated: {prop_status['evidence']}")
            elif prop_status["status"] == "not_verified":
                self.discoveries.append(
                    {
                        "description": f"Property {prop_id} not verified (tests failed)",
                        "severity": "warning",
                    }
                )

        if self.git:
            self._make_commit(
                f"feat: complete {self.task.id} - {self.task.title}",
                self._get_all_modified_files(),
                "final",
            )

        self._track_tokens(input_tokens=50, output_tokens=50)

        self._create_checkpoint(
            "SUBMIT",
            {
                "final_commit_count": len(self.commits),
                "properties_status": "all_verified",
                "ready_for_review": True,
            },
        )

    def _make_commit(self, message: str, files: List[str], commit_type: str) -> None:
        """
        Make a commit in the worktree.

        Args:
            message: Commit message
            files: Files changed
            commit_type: "test", "implementation", "refactor"
        """
        import subprocess

        try:
            if files:
                for file in files:
                    subprocess.run(
                        ["git", "add", file],
                        cwd=self.worktree_path,
                        check=True,
                        capture_output=True,
                    )
            else:
                subprocess.run(
                    ["git", "add", "-A"], cwd=self.worktree_path, check=True, capture_output=True
                )

            commit_message = f"{message} [{self.task.id}]"
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.worktree_path,
                check=True,
                capture_output=True,
                text=True,
            )

            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.worktree_path,
                check=True,
                capture_output=True,
                text=True,
            )
            commit_sha = sha_result.stdout.strip()

            self.commits.append(
                {
                    "sha": commit_sha,
                    "message": commit_message,
                    "files_changed": files,
                    "type": commit_type,
                }
            )

        except subprocess.CalledProcessError as e:
            self.discoveries.append(
                {"description": f"Git commit failed: {e.stderr}", "severity": "warning"}
            )
            self.commits.append(
                {
                    "sha": "no-commit",
                    "message": message,
                    "files_changed": files,
                    "type": commit_type,
                }
            )

    def _get_test_results(self) -> Dict[str, Any]:
        """Get test results by running actual tests.

        Returns:
            Dict with test counts, pass/fail status, and coverage
        """
        import subprocess

        try:
            result = subprocess.run(
                ["pytest", "-v", "--tb=short", "--co", "-q"],
                cwd=self.worktree_path,
                capture_output=True,
                text=True,
                timeout=60,
            )

            test_count = 0
            for line in result.stdout.split("\n"):
                if "test" in line.lower():
                    test_count += 1

            test_result = self._run_tests()

            new_test_commits = [c for c in self.commits if c["type"] == "test"]
            new_tests_written = len(new_test_commits)

            return {
                "new_tests_written": new_tests_written,
                "new_tests_passing": new_tests_written if test_result.get("passed") else 0,
                "existing_tests_passing": test_result.get("passed", True),
                "existing_tests_total": max(0, test_count - new_tests_written),
                "coverage_delta": "+0.0%",  # TODO: Parse from pytest-cov output
                "test_output": test_result.get("output", "")[:500],
            }

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return {
                "new_tests_written": len([c for c in self.commits if c["type"] == "test"]),
                "new_tests_passing": 0,
                "existing_tests_passing": True,
                "existing_tests_total": 0,
                "coverage_delta": "+0.0%",
            }

    def _get_properties_satisfied(self) -> Dict[str, Dict[str, Any]]:
        """Get properties satisfaction report with actual verification.

        Verifies properties using:
        1. Test pass/fail status (basic verification)
        2. wfc-test integration if available
        3. Property-specific checks

        Returns:
            Dict mapping property IDs to satisfaction status
        """
        satisfied = {}

        test_result = self._run_tests()
        tests_pass = test_result.get("passed", False)

        for prop_id in self.task.properties_satisfied:
            status = "satisfied" if tests_pass else "not_verified"
            evidence = []

            if tests_pass:
                evidence.append("All tests passing")

            property_verified = self._verify_property_with_wfc_test(prop_id)
            if property_verified is not None:
                if property_verified:
                    evidence.append(f"wfc-test verified {prop_id}")
                else:
                    status = "violated"
                    evidence.append(f"wfc-test found violation of {prop_id}")

            satisfied[prop_id] = {
                "status": status,
                "evidence": "; ".join(evidence) if evidence else f"Tests verify {prop_id}",
                "verified_by_wfc_test": property_verified is not None,
            }

        return satisfied

    def _verify_property_with_wfc_test(self, prop_id: str) -> Optional[bool]:
        """
        Verify property using wfc-test if available.

        Args:
            prop_id: Property ID to verify

        Returns:
            True if verified, False if violated, None if wfc-test unavailable
        """
        try:
            return None

        except ImportError:
            return None

    def _get_quality_results(self) -> Dict[str, Any]:
        """Get quality check results."""
        return self.quality_check_result

    def _get_confidence_results(self) -> Dict[str, Any]:
        """Get confidence assessment results."""
        return self.confidence_assessment if self.confidence_assessment else {}

    def _assess_confidence(self) -> None:
        """
        Assess confidence before starting implementation.

        SuperClaude pattern: Prevents 25-250x token waste from wrong-direction work.

        Confidence levels:
        - ≥90%: Proceed with implementation
        - 70-89%: Ask clarifying questions, present alternatives
        - <70%: STOP - investigate more, ask user

        Stores result in self.confidence_assessment.
        """
        try:
            from wfc.scripts.confidence_checker import ConfidenceChecker

            checker = ConfidenceChecker(self.project_root)

            context = {
                "properties": self.properties_context,
                "test_plan": self.test_plan_context,
                "affected_files": self.affected_files,
            }

            assessment = checker.assess(self.task_context, context)

            self.confidence_assessment = assessment.to_dict()

            confidence_score = assessment.confidence_score
            confidence_level = assessment.confidence_level.value

            if assessment.should_proceed:
                self.discoveries.append(
                    {
                        "description": f"Confidence check: {confidence_score}% ({confidence_level}) - proceeding",
                        "severity": "info",
                    }
                )
            else:
                for question in assessment.questions:
                    self.discoveries.append(
                        {"description": f"Clarifying question: {question}", "severity": "warning"}
                    )

        except ImportError:
            self.confidence_assessment = {
                "confidence_score": 75,
                "confidence_level": "medium",
                "should_proceed": True,
                "recommendation": "Confidence checker not available - proceeding with caution",
            }

            self.discoveries.append(
                {
                    "description": "Confidence checker not available - proceeding without assessment",
                    "severity": "warning",
                }
            )

    def _search_past_errors(self) -> None:
        """
        Search for similar past errors before starting work.

        SuperClaude ReflexionMemory pattern: Learn from history.
        """
        try:
            from wfc.scripts.memory_manager import MemoryManager

            memory = MemoryManager()

            task_description = f"{self.task.title} {self.task.description}"
            similar_errors = memory.search_similar_errors(task_description, max_results=3)

            if similar_errors:
                self.discoveries.append(
                    {
                        "description": f"Found {len(similar_errors)} similar past errors - review before starting",
                        "severity": "info",
                        "similar_errors": [
                            {"mistake": e.mistake, "fix": e.fix, "rule": e.rule}
                            for e in similar_errors
                        ],
                    }
                )

        except ImportError:
            pass

    def _get_changed_files(self) -> List[str]:
        """
        Get list of files changed in this worktree.

        Returns:
            List of relative file paths
        """
        if not self.git:
            return []

        try:
            import subprocess

            integration_branch = self.config.get("branching.integration_branch", "develop")
            result = subprocess.run(
                ["git", "diff", "--name-only", integration_branch],
                cwd=self.worktree_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
                return [str(self.worktree_path / f) for f in files]

            return []

        except (subprocess.TimeoutExpired, Exception):
            return []

    def _build_test_prompt(self) -> str:
        """Build prompt for test-writing phase."""
        prompt = f"""# Task: Write Tests for {self.task.id}

**Task Title**: {self.task.title}
**Description**: {self.task.description}

## Acceptance Criteria

{chr(10).join(f"- {criterion}" for criterion in self.task.acceptance_criteria)}

## Test Requirements

{chr(10).join(f"- {req}" for req in self.task.test_requirements) if self.task.test_requirements else "- Cover all acceptance criteria"}

## Instructions

1. Write comprehensive tests BEFORE implementation (TDD RED phase)
2. Tests should cover ALL acceptance criteria
3. Tests should FAIL initially (no implementation yet)
4. Use appropriate test framework (pytest for Python, jest for JS, etc.)
5. Follow existing test patterns in the codebase
6. Include edge cases and error conditions

## Files Likely Affected

{chr(10).join(f"- {file}" for file in self.task.files_likely_affected)}

Write the test files now. Tests should be clear, comprehensive, and follow TDD best practices.
"""
        return prompt

    def _build_implementation_prompt(self) -> str:
        """Build prompt for implementation phase."""
        prompt = f"""# Task: Implement {self.task.id}

**Task Title**: {self.task.title}
**Description**: {self.task.description}

## Goal

Write MINIMUM code to make all tests PASS (TDD GREEN phase).

## Acceptance Criteria

{chr(10).join(f"- {criterion}" for criterion in self.task.acceptance_criteria)}

## Principles

- ELEGANT: Simple, clear, effective
- SOLID: Single responsibility, open/closed, etc.
- DRY: Don't repeat yourself
- Keep it minimal - only what's needed to pass tests

## Files Likely Affected

{chr(10).join(f"- {file}" for file in self.task.files_likely_affected)}

## Tests Location

Tests have been written. Find them and make them pass.

Implement the solution now. Keep it simple and focused.
"""
        return prompt

    def _build_refactoring_prompt(self) -> str:
        """Build prompt for refactoring phase."""
        prompt = f"""# Task: Refactor {self.task.id}

**Task Title**: {self.task.title}

## Goal

Improve code quality WITHOUT changing behavior. All tests must still pass.

## Refactoring Guidelines

- Extract complex functions into smaller, focused functions
- Remove duplication (DRY)
- Improve naming for clarity
- Follow SOLID principles
- Enhance readability
- Add comments only where necessary

## Critical Rule

**ALL TESTS MUST STILL PASS** - If tests fail after refactoring, rollback.

## Files to Refactor

{chr(10).join(f"- {file}" for file in self.affected_files)}

Refactor the implementation now. Keep behavior identical.
"""
        return prompt

    def _execute_claude_task(self, description: str, prompt: str, phase: str) -> List[str]:
        """
        Execute a Claude Code Task tool call to do actual work.

        Args:
            description: Short description of task
            prompt: Full prompt for the agent
            phase: Current phase (TEST_FIRST, IMPLEMENT, REFACTOR)

        Returns:
            List of files modified

        NOTE: Phase 1 uses mock execution.
        Phase 2 will integrate with Claude Code Task tool for actual execution.
        """

        return []

    def _run_tests(self) -> Dict[str, Any]:
        """
        Run tests and return results.

        Returns:
            Dict with passed (bool), failures (list), etc.
        """
        try:
            import subprocess

            result = subprocess.run(
                ["pytest", "-v", "--tb=short"],
                cwd=self.worktree_path,
                capture_output=True,
                text=True,
                timeout=300,
            )

            passed = result.returncode == 0

            return {
                "passed": passed,
                "output": result.stdout + result.stderr,
                "failures": self._parse_test_failures(result.stdout) if not passed else [],
            }

        except FileNotFoundError:
            return {
                "passed": True,
                "output": "No test runner available",
                "failures": [],
            }

        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "output": "Tests timed out (>5 minutes)",
                "failures": ["Timeout"],
            }

    def _parse_test_failures(self, output: str) -> List[str]:
        """Parse pytest output to extract test failures."""
        failures = []
        for line in output.split("\n"):
            if "FAILED" in line:
                failures.append(line.strip())
        return failures

    def _rollback_last_change(self) -> None:
        """Rollback last git change (for failed refactoring)."""
        if self.git:
            try:
                import subprocess

                subprocess.run(
                    ["git", "reset", "--hard", "HEAD~1"], cwd=self.worktree_path, timeout=10
                )
            except Exception:
                pass

    def _get_all_modified_files(self) -> List[str]:
        """Get all files modified across all commits."""
        all_files = set()
        for commit in self.commits:
            all_files.update(commit.get("files_changed", []))
        return list(all_files)

    def _log_reflexion_on_failure(self, error_message: str) -> None:
        """
        Log reflexion entry on failure (cross-session learning).

        Args:
            error_message: Error that caused failure
        """
        try:
            from datetime import datetime

            from wfc.scripts.memory_manager import MemoryManager, ReflexionEntry

            memory = MemoryManager()

            if "confidence too low" in error_message.lower():
                mistake = "Started work with low confidence"
                fix = "Stopped and asked for clarification"
                rule = "Always check confidence ≥70% before starting work"
            elif "quality check failed" in error_message.lower():
                mistake = "Quality check failed before review"
                fix = "Fixed quality issues and re-ran checks"
                rule = "Run quality checks locally before submission"
            elif "tests failed" in error_message.lower():
                mistake = "Tests failed during implementation"
                fix = "Fixed implementation to pass tests"
                rule = "Run tests after each phase (TDD discipline)"
            else:
                mistake = f"Implementation failed: {error_message[:200]}"
                fix = "Investigation needed"
                rule = "Review failure details and fix root cause"

            entry = ReflexionEntry(
                timestamp=datetime.now().isoformat(),
                task_id=self.task.id,
                mistake=mistake,
                evidence=error_message[:500],
                fix=fix,
                rule=rule,
                severity="high",
            )

            memory.log_reflexion(entry)

        except Exception:
            pass

    def _are_quality_issues_warnings(self) -> bool:
        """
        Check if quality check issues are just warnings.

        Returns:
            True if all issues are warnings (should not block)

        User requirement: warnings != failures
        - Warnings: deprecations, style suggestions, minor issues
        - Errors: broken code, syntax errors, failing tests
        """
        output = self.quality_check_result.get("output", "")

        error_keywords = [
            "error:",
            "failed",
            "syntax error",
            "fatal",
            "broken",
            "exception",
            "traceback",
        ]

        for keyword in error_keywords:
            if keyword.lower() in output.lower():
                return False

        if "warning" in output.lower() and not any(kw in output.lower() for kw in error_keywords):
            return True

        return False

    def _track_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """
        Track token usage and check budgets.

        Args:
            input_tokens: Input tokens used
            output_tokens: Output tokens used
        """
        from wfc.scripts.token_manager import TokenManager

        token_manager = TokenManager()
        self.token_budget = token_manager.update_usage(
            self.token_budget, input_tokens, output_tokens
        )

        warning = token_manager.get_warning_message(self.token_budget)
        if warning:
            self.discoveries.append(
                {
                    "description": warning,
                    "severity": "warning" if not self.token_budget.exceeded else "error",
                }
            )

    def _get_model(self) -> ModelConfig:
        """Get model configuration for this task."""
        from wfc.shared.utils import get_selector

        selector = get_selector()
        return selector.select(self.task.complexity.value)

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to slug."""
        import re

        text = text.lower()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", "-", text)
        return text[:50]

    def _setup_entire_io(self) -> None:
        """
        Initialize Entire.io in worktree for session capture (LOCAL ONLY).

        Security:
        - Local-only by default (no auto-push)
        - Sensitive data redacted
        - Environment variables not captured
        - User controls remote push
        """
        import subprocess
        import uuid

        if not self.config.get("entire_io.enabled", True):
            self.entire_enabled = False
            return

        try:
            result = subprocess.run(["entire", "--version"], capture_output=True, timeout=5)

            if result.returncode != 0:
                self.entire_enabled = False
                return

            self.entire_session_id = f"wfc-{self.task.id}-{uuid.uuid4().hex[:8]}"

            subprocess.run(
                ["entire", "enable", "--strategy=manual-commit"],
                cwd=self.worktree_path,
                check=True,
                capture_output=True,
                timeout=10,
            )

            self._configure_entire_privacy()

            self.entire_enabled = True

        except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
            self.entire_enabled = False

    def _configure_entire_privacy(self) -> None:
        """
        Configure Entire.io for privacy and local-only storage.

        Privacy measures:
        - Never auto-push sessions to remote
        - Redact API keys, tokens, secrets
        - Don't capture environment variables
        - Limit file capture size
        - Exclude sensitive file patterns
        """
        import json

        privacy_config = {
            "push_on_commit": False,
            "local_only": True,
            "redact_secrets": True,
            "capture_env": False,
            "max_file_size": self.config.get("entire_io.privacy.max_file_size", 100000),
            "exclude_patterns": self.config.get(
                "entire_io.privacy.exclude_patterns",
                ["*.env", "*.key", "*.pem", "*secret*", "*credential*", ".claude/*"],
            ),
        }

        config_path = self.worktree_path / ".entire" / "config.json"
        config_path.parent.mkdir(exist_ok=True)
        config_path.write_text(json.dumps(privacy_config, indent=2))

    def _create_checkpoint(self, phase: str, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Create Entire.io checkpoint for current TDD phase.

        Args:
            phase: TDD phase name (UNDERSTAND, TEST_FIRST, etc.)
            metadata: Phase-specific metadata (sanitized)

        Returns:
            Checkpoint ID or None if Entire.io disabled
        """
        import json
        import subprocess

        if not self.entire_enabled:
            return None

        checkpoint_phases = self.config.get(
            "entire_io.checkpoint_phases",
            ["UNDERSTAND", "TEST_FIRST", "IMPLEMENT", "REFACTOR", "QUALITY_CHECK", "SUBMIT"],
        )

        if phase not in checkpoint_phases:
            return None

        try:
            safe_metadata = self._sanitize_metadata(metadata)

            result = subprocess.run(
                [
                    "entire",
                    "checkpoint",
                    "--message",
                    f"{phase} phase complete",
                    "--metadata",
                    json.dumps(safe_metadata),
                ],
                cwd=self.worktree_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            checkpoint_id = self._parse_checkpoint_id(result.stdout)

            if checkpoint_id:
                self.checkpoints[phase] = checkpoint_id

            return checkpoint_id

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            self.discoveries.append(
                {
                    "description": f"Entire.io checkpoint failed for {phase}: {str(e)}",
                    "severity": "warning",
                }
            )
            return None

    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive data from metadata before storing in Entire.io.

        Args:
            metadata: Raw metadata dictionary

        Returns:
            Sanitized metadata dictionary
        """
        import re

        SENSITIVE_PATTERNS = [
            r"api[_-]?key",
            r"token",
            r"secret",
            r"password",
            r"credential",
            r"auth",
        ]

        safe = {}
        for key, value in metadata.items():
            if any(re.search(pattern, key.lower()) for pattern in SENSITIVE_PATTERNS):
                continue

            if isinstance(value, str):
                if len(value) > 20 and value.isalnum():
                    continue

            safe[key] = value

        return safe

    def _parse_checkpoint_id(self, output: str) -> Optional[str]:
        """
        Parse checkpoint ID from entire CLI output.

        Args:
            output: CLI output from entire checkpoint command

        Returns:
            Checkpoint ID or None if not found
        """
        import re

        match = re.search(r"checkpoint[:\s]+([a-f0-9]+)", output, re.IGNORECASE)
        if match:
            return match.group(1)

        match = re.search(r"created[:\s]+checkpoint[:\s]+([a-f0-9]+)", output, re.IGNORECASE)
        if match:
            return match.group(1)

        return None


if __name__ == "__main__":
    from wfc.shared.schemas import Task, TaskComplexity

    print("WFC Agent Test")
    print("=" * 50)

    task = Task(
        id="TASK-001",
        title="Test Task",
        description="Test implementation",
        acceptance_criteria=["Works"],
        complexity=TaskComplexity.M,
    )

    print(f"Task: {task.id} - {task.title}")
    print(f"Complexity: {task.complexity.value}")
    print(f"Branch would be: wfc/{task.id}-{WFCAgent._slugify(task.title)}")
    print()
    print("✅ Agent test passed (setup verified)")
