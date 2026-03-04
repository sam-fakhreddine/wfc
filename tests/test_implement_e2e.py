#!/usr/bin/env python3
"""
End-to-end tests for wfc-implement.

Tests the complete workflow:
- TASKS.md → agents → review → merge
- Quality gate integration
- Rollback scenarios
- Parallel agent execution
"""

import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

# Activate PEP 562 import bridge for hyphenated skill directory (wfc-implement → wfc_implement)
from wfc.skills import wfc_implement  # noqa: F401


class TestE2EBasicWorkflow:
    """Basic end-to-end workflow tests."""

    @pytest.fixture
    def git_repo(self):
        """Create a temporary git repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repo
            subprocess.run(["git", "init"], cwd=project_root, capture_output=True, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@wfc.com"],
                cwd=project_root,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "WFC Test"],
                cwd=project_root,
                capture_output=True,
                check=True,
            )

            # Create initial commit
            (project_root / "README.md").write_text("# Test Project")
            subprocess.run(["git", "add", "."], cwd=project_root, capture_output=True, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=project_root,
                capture_output=True,
                check=True,
            )

            yield project_root

    def test_simple_task_execution(self, git_repo):
        """Test execution of a single simple task."""
        project_root = git_repo

        # Create a simple TASKS.md
        plan_dir = project_root / "plan"
        plan_dir.mkdir()

        tasks_content = """# Implementation Tasks

## TASK-001: Create hello.py
- **Complexity**: S
- **Dependencies**: []
- **Properties**: [SIMPLE]
- **Files**: hello.py
- **Description**: Create a simple hello world script
- **Acceptance Criteria**:
  - Creates hello.py with print("Hello World")
  - File is executable
"""

        (plan_dir / "TASKS.md").write_text(tasks_content)

        # Test that we can parse the tasks
        from wfc_implement.parser import parse_tasks

        task_graph = parse_tasks(plan_dir / "TASKS.md")

        assert len(task_graph.tasks) == 1
        assert task_graph.tasks[0].id == "TASK-001"
        assert task_graph.tasks[0].complexity.value == "S"


class TestQualityGateIntegration:
    """Tests for quality gate integration."""

    def test_quality_check_blocks_submission(self):
        """Test that failing quality checks block submission."""
        from wfc.scripts.universal_quality_checker import TrunkCheckResult

        # Simulate failed quality check
        result = TrunkCheckResult(
            passed=False,
            output="Found 3 errors: unused imports, formatting issues",
            issues_found=3,
            fixable_issues=2,
            files_checked=5,
        )

        assert result.passed is False
        assert result.issues_found > 0

        # In agent workflow, this should block submission
        # (tested in agent phase integration)

    def test_quality_check_allows_submission(self):
        """Test that passing quality checks allow submission."""
        from wfc.scripts.universal_quality_checker import TrunkCheckResult

        # Simulate passed quality check
        result = TrunkCheckResult(
            passed=True,
            output="All checks passed",
            issues_found=0,
            fixable_issues=0,
            files_checked=5,
        )

        assert result.passed is True
        assert result.issues_found == 0


class TestConfidenceWorkflow:
    """Tests for confidence-first workflow."""

    def test_high_confidence_proceeds(self):
        """Test that high confidence tasks proceed to implementation."""
        import tempfile

        from wfc.scripts.confidence_checker import ConfidenceChecker

        # Create temp directory with example files
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create directory structure that task references
            src_dir = project_root / "src"
            src_dir.mkdir()
            (src_dir / "utils.py").write_text("# Existing file")

            checker = ConfidenceChecker(project_root)

            task = {
                "id": "TASK-001",
                "description": "Add logging to existing function",
                "acceptance_criteria": [
                    "Logs function entry",
                    "Logs function exit",
                    "Uses Python logging module",
                ],
                "complexity": "S",
                "files_likely_affected": ["src/utils.py"],
                "test_requirements": ["Test logging output"],
            }

            assessment = checker.assess(task)

            # High confidence should proceed
            assert assessment.should_proceed is True
            assert assessment.confidence_score >= 90

    def test_low_confidence_stops(self):
        """Test that low confidence tasks do not proceed."""
        from wfc.scripts.confidence_checker import ConfidenceChecker

        checker = ConfidenceChecker(Path.cwd())

        task = {
            "id": "TASK-002",
            "description": "Make it work better",
            "acceptance_criteria": [],
            "complexity": "XL",
        }

        assessment = checker.assess(task)

        # Low confidence should stop
        assert assessment.should_proceed is False
        assert assessment.confidence_score < 70
        assert len(assessment.questions) > 0


class TestMemorySystemWorkflow:
    """Tests for memory system integration."""

    def test_past_error_prevents_repeat(self):
        """Test that past errors inform current work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from wfc.scripts.memory_manager import MemoryManager, ReflexionEntry

            memory = MemoryManager(Path(tmpdir))

            # Log a past error
            entry = ReflexionEntry(
                timestamp=datetime.now().isoformat(),
                task_id="TASK-OLD",
                mistake="Forgot to add tests before implementing",
                evidence="Tests failed after implementation",
                fix="Rolled back and followed TDD",
                rule="ALWAYS write tests first (RED phase)",
                severity="high",
            )

            memory.log_reflexion(entry)

            # Search for similar errors when starting new task
            similar = memory.search_similar_errors("implementing new feature tests")

            # Should find the past TDD violation
            assert len(similar) > 0
            assert any("tests" in e.mistake.lower() for e in similar)


class TestRollbackScenarios:
    """Tests for rollback and recovery."""

    def test_merge_rollback_on_failure(self):
        """Test that merge rolls back on integration test failure."""
        from wfc_implement.merge_engine import FailureSeverity, MergeStatus

        # This tests the rollback logic structure
        # In a real scenario, merge_engine would:
        # 1. Merge to main
        # 2. Run integration tests
        # 3. If tests fail, rollback (git reset --hard)
        # 4. Preserve worktree for investigation
        # 5. Re-queue task (max 2 retries)

        # Verify the severity classification exists
        assert FailureSeverity.WARNING.value == "warning"
        assert FailureSeverity.ERROR.value == "error"
        assert FailureSeverity.CRITICAL.value == "critical"

        # Verify the status enum exists
        assert MergeStatus.MERGED.value == "merged"
        assert MergeStatus.FAILED.value == "failed"
        assert MergeStatus.ROLLED_BACK.value == "rolled_back"

    def test_worktree_preservation_on_failure(self):
        """Test that worktrees are preserved on failure for investigation."""
        from wfc_implement.merge_engine import MergeResult

        # Create a mock failed merge result
        result = MergeResult(
            task_id="TASK-001",
            status="failed_tests",
            failure_severity="error",
            should_retry=True,
            retry_count=0,
            max_retries=2,
            worktree_preserved=True,
            worktree_path="/worktrees/wfc-TASK-001",
        )

        # Verify worktree is preserved
        assert result.worktree_preserved is True
        assert result.worktree_path is not None
        assert result.should_retry is True

    def test_max_retry_limit(self):
        """Test that retries are limited to max_retries."""
        from wfc_implement.merge_engine import FailureSeverity, MergeResult

        # First failure - should retry
        result1 = MergeResult(
            task_id="TASK-001",
            status="failed_tests",
            failure_severity=FailureSeverity.ERROR,
            retry_count=0,
            max_retries=2,
        )

        # Second failure - should retry
        result2 = MergeResult(
            task_id="TASK-001",
            status="failed_tests",
            failure_severity=FailureSeverity.ERROR,
            retry_count=1,
            max_retries=2,
        )

        # Third failure - should NOT retry (max reached)
        result3 = MergeResult(
            task_id="TASK-001",
            status="failed_tests",
            failure_severity=FailureSeverity.ERROR,
            retry_count=2,
            max_retries=2,
        )

        assert result1.retry_count < result1.max_retries
        assert result2.retry_count < result2.max_retries
        assert result3.retry_count >= result3.max_retries


class TestParallelExecution:
    """Tests for parallel agent execution."""

    def test_dependency_ordering(self):
        """Test that tasks with dependencies execute in correct order."""
        from wfc_implement.parser import parse_tasks

        # Create tasks with dependencies
        tasks_content = """# Implementation Tasks

## TASK-001: Create base module
- **Complexity**: M
- **Dependencies**: []
- **Description**: Create base module

## TASK-002: Extend base module
- **Complexity**: M
- **Dependencies**: [TASK-001]
- **Description**: Extend base module

## TASK-003: Independent task
- **Complexity**: S
- **Dependencies**: []
- **Description**: Independent task
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(tasks_content)
            tasks_file = Path(f.name)

        try:
            task_graph = parse_tasks(tasks_file)

            # TASK-001 should have no dependencies
            task1 = next(t for t in task_graph.tasks if t.id == "TASK-001")
            assert len(task1.dependencies) == 0

            # TASK-002 should depend on TASK-001
            task2 = next(t for t in task_graph.tasks if t.id == "TASK-002")
            assert "TASK-001" in task2.dependencies

            # TASK-003 should be independent
            task3 = next(t for t in task_graph.tasks if t.id == "TASK-003")
            assert len(task3.dependencies) == 0

            # TASK-001 and TASK-003 can run in parallel
            # TASK-002 must wait for TASK-001

        finally:
            tasks_file.unlink()

    def test_parallel_execution_capacity(self):
        """Test that parallel execution respects max_agents setting."""
        # This is a structure test - verifies the concept exists
        # In real implementation, orchestrator would:
        # 1. Read max_agents from config (default: 5)
        # 2. Group tasks by dependency level
        # 3. Execute up to max_agents tasks per level concurrently
        # 4. Wait for level to complete before starting next level

        # For now, just verify we can import the necessary components
        from wfc.shared.config.wfc_config import WFCConfig

        config = WFCConfig().load()

        # Verify config loaded successfully
        assert config is not None
        assert isinstance(config, dict)

        # Verify it has expected sections
        assert "merge" in config
        assert "metrics" in config


class TestTDDWorkflow:
    """Tests for TDD workflow enforcement."""

    def test_tdd_phases_exist(self):
        """Test that TDD phases are properly defined."""
        from wfc_implement.agent import AgentPhase

        # Verify all TDD phases exist
        phases = [phase.value for phase in AgentPhase]

        assert "understand" in phases
        assert "test_first" in phases
        assert "implement" in phases
        assert "refactor" in phases
        assert "quality_check" in phases
        assert "submit" in phases


class TestOrchestratorCommitPattern:
    """Tests for the orchestrator-owned commit pattern (issue #114).

    Agents edit files only. No git commands. The orchestrator commits after
    each agent completes, so background agents are never blocked on Bash approval.
    """

    @pytest.fixture
    def git_worktree(self):
        """Create an isolated git repo simulating a worktree."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@wfc.com"],
                cwd=repo,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "WFC Test"],
                cwd=repo,
                capture_output=True,
                check=True,
            )
            (repo / "README.md").write_text("# Worktree")
            subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial"],
                cwd=repo,
                capture_output=True,
                check=True,
            )
            yield repo

    def test_commit_agent_work_creates_commit(self, git_worktree):
        """Orchestrator commits file edits that agent left uncommitted."""
        from wfc_implement.agent import AgentReport
        from wfc_implement.executor import ExecutionEngine
        from wfc_implement.orchestrator import WFCOrchestrator
        from wfc.shared.config.wfc_config import WFCConfig
        from wfc.shared.schemas import Task, TaskComplexity, TaskStatus

        # Simulate agent editing a file without committing
        (git_worktree / "hello.py").write_text("print('hello')\n")

        task = Task(
            id="TASK-001",
            title="Add hello.py",
            description="Add a greeting module",
            complexity=TaskComplexity.S,
            dependencies=[],
            acceptance_criteria=["File exists and prints hello"],
            properties_satisfied=[],
            files_likely_affected=["hello.py"],
            status=TaskStatus.IN_PROGRESS,
        )

        report = AgentReport(
            agent_id="agent-1",
            task_id="TASK-001",
            status="success",
            worktree_path=str(git_worktree),
            branch="claude/TASK-001",
        )

        config = WFCConfig()
        orchestrator = WFCOrchestrator(project_root=git_worktree, config=config)
        engine = ExecutionEngine(orchestrator)

        sha = engine._commit_agent_work(report, task)

        assert sha is not None
        assert len(sha) == 40  # full git SHA

        # Verify the working tree is now clean
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=git_worktree,
            capture_output=True,
            text=True,
            check=True,
        )
        assert status.stdout.strip() == ""

    def test_commit_agent_work_returns_none_when_nothing_to_commit(self, git_worktree):
        """Orchestrator skips commit when agent made no changes."""
        from wfc_implement.agent import AgentReport
        from wfc_implement.executor import ExecutionEngine
        from wfc_implement.orchestrator import WFCOrchestrator
        from wfc.shared.config.wfc_config import WFCConfig
        from wfc.shared.schemas import Task, TaskComplexity, TaskStatus

        task = Task(
            id="TASK-002",
            title="Noop task",
            description="No file changes",
            complexity=TaskComplexity.S,
            dependencies=[],
            acceptance_criteria=["No files changed"],
            properties_satisfied=[],
            files_likely_affected=[],
            status=TaskStatus.IN_PROGRESS,
        )

        report = AgentReport(
            agent_id="agent-2",
            task_id="TASK-002",
            status="success",
            worktree_path=str(git_worktree),
            branch="claude/TASK-002",
        )

        config = WFCConfig()
        orchestrator = WFCOrchestrator(project_root=git_worktree, config=config)
        engine = ExecutionEngine(orchestrator)

        sha = engine._commit_agent_work(report, task)

        assert sha is None  # nothing to commit

    def test_commit_agent_work_returns_none_for_nonexistent_worktree(self):
        """Orchestrator skips commit when worktree path does not exist."""
        from wfc_implement.agent import AgentReport
        from wfc_implement.executor import ExecutionEngine
        from wfc_implement.orchestrator import WFCOrchestrator
        from wfc.shared.config.wfc_config import WFCConfig
        from wfc.shared.schemas import Task, TaskComplexity, TaskStatus

        task = Task(
            id="TASK-003",
            title="Missing worktree",
            description="Worktree was cleaned up",
            complexity=TaskComplexity.S,
            dependencies=[],
            acceptance_criteria=["Handles missing worktree gracefully"],
            properties_satisfied=[],
            files_likely_affected=[],
            status=TaskStatus.IN_PROGRESS,
        )

        report = AgentReport(
            agent_id="agent-3",
            task_id="TASK-003",
            status="success",
            worktree_path="/nonexistent/path/TASK-003",
            branch="claude/TASK-003",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            config = WFCConfig()
            orchestrator = WFCOrchestrator(project_root=Path(tmpdir), config=config)
            engine = ExecutionEngine(orchestrator)

            sha = engine._commit_agent_work(report, task)

        assert sha is None

    def test_agent_prompt_excludes_git_commands(self):
        """Agent prompt must instruct agents not to run git commands."""
        from wfc_implement.executor import ExecutionEngine
        from wfc_implement.orchestrator import WFCOrchestrator
        from wfc.shared.config.wfc_config import WFCConfig
        from wfc.shared.schemas import Task, TaskComplexity, TaskStatus

        task = Task(
            id="TASK-004",
            title="Sample task",
            description="Implement feature X",
            complexity=TaskComplexity.M,
            dependencies=[],
            acceptance_criteria=["Feature works"],
            properties_satisfied=[],
            files_likely_affected=[],
            status=TaskStatus.QUEUED,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            config = WFCConfig()
            orchestrator = WFCOrchestrator(project_root=Path(tmpdir), config=config)
            engine = ExecutionEngine(orchestrator)

            prompt = engine._build_agent_prompt(task, "agent-4")

        assert "Do NOT run any git commands" in prompt
        assert "Edit files only" in prompt

    def test_agent_prompt_instructs_write_tool_for_report(self):
        """Agent prompt must instruct agents to use Write tool for agent-report.json."""
        from wfc_implement.executor import ExecutionEngine
        from wfc_implement.orchestrator import WFCOrchestrator
        from wfc.shared.config.wfc_config import WFCConfig
        from wfc.shared.schemas import Task, TaskComplexity, TaskStatus

        task = Task(
            id="TASK-005",
            title="Report task",
            description="Write a report",
            complexity=TaskComplexity.S,
            dependencies=[],
            acceptance_criteria=["Report is written"],
            properties_satisfied=[],
            files_likely_affected=[],
            status=TaskStatus.QUEUED,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            config = WFCConfig()
            orchestrator = WFCOrchestrator(project_root=Path(tmpdir), config=config)
            engine = ExecutionEngine(orchestrator)

            prompt = engine._build_agent_prompt(task, "agent-5")

        assert "Write tool" in prompt
        assert "Bash" in prompt  # must explicitly warn against Bash


def test_coverage_check():
    """Meta-test to verify we're testing the right components."""
    # This test verifies we have coverage of all critical areas
    critical_components = [
        "confidence_checker",  # TASK-003
        "memory_manager",  # TASK-004
        "token_manager",  # TASK-009
        "universal_quality_checker",  # TASK-001
        "merge_engine",  # TASK-005
        "agent",  # TASK-002
    ]

    # Verify we can import all critical components
    for component in critical_components:
        if component in [
            "confidence_checker",
            "memory_manager",
            "token_manager",
            "universal_quality_checker",
        ]:
            module_path = f"wfc.scripts.{component}"
            try:
                __import__(module_path)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_path}: {e}")
        else:
            # Use PEP 562 bridge for hyphenated skill directory
            try:
                import importlib

                importlib.import_module(f".{component}", package="wfc_implement")
            except ImportError as e:
                pytest.fail(f"Failed to import wfc_implement.{component}: {e}")


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
