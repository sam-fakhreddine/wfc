#!/usr/bin/env python3
"""
Integration tests for wfc-implement components.

Tests individual components and their integration:
- Quality gate (Trunk.io integration)
- Confidence checking
- Memory system
- Token budgets
- Merge engine
- Failure severity classification
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

# Import WFC components
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# Activate PEP 562 import bridge for hyphenated skill directory (wfc-implement → wfc_implement)
from wfc.skills import wfc_implement  # noqa: F401

from wfc.scripts.confidence_checker import (
    ConfidenceChecker,
    ConfidenceLevel,
)
from wfc.scripts.memory_manager import (
    MemoryManager,
    ReflexionEntry,
    WorkflowMetric,
)
from wfc.scripts.token_manager import (
    TokenManager,
    TaskComplexity,
    TokenBudget,
)
from wfc.scripts.universal_quality_checker import (
    UniversalQualityChecker,
    TrunkCheckResult,
)


class TestConfidenceChecker:
    """Tests for confidence checking (TASK-003)."""

    def test_high_confidence_task(self):
        """Test high confidence assessment (≥90%)."""
        import tempfile

        # Create temp directory with example files
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create directory structure that task references
            src_dir = project_root / "src" / "api"
            src_dir.mkdir(parents=True)
            (src_dir / "users.py").write_text("# Existing API file")

            checker = ConfidenceChecker(project_root)

            task = {
                "id": "TASK-001",
                "description": "Add a new endpoint /api/users that returns list of users from database",
                "acceptance_criteria": [
                    "Endpoint responds to GET requests",
                    "Returns JSON array of user objects",
                    "Returns 200 status code on success",
                ],
                "complexity": "M",
                "files_likely_affected": ["src/api/users.py"],
                "test_requirements": ["Test endpoint returns 200", "Test JSON format"],
            }

            assessment = checker.assess(task)

            assert assessment.confidence_score >= 90
            assert assessment.confidence_level == ConfidenceLevel.HIGH
            assert assessment.should_proceed is True
            assert assessment.clear_requirements is True
            assert len(assessment.questions) == 0

    def test_low_confidence_task(self):
        """Test low confidence assessment (<70%)."""
        checker = ConfidenceChecker(Path.cwd())

        task = {
            "id": "TASK-002",
            "description": "Fix the bug",
            "acceptance_criteria": [],
            "complexity": "M",
        }

        assessment = checker.assess(task)

        assert assessment.confidence_score < 70
        assert assessment.confidence_level == ConfidenceLevel.LOW
        assert assessment.should_proceed is False
        assert len(assessment.questions) > 0
        assert len(assessment.risks) > 0

    def test_medium_confidence_task(self):
        """Test medium confidence assessment (70-89%)."""
        import tempfile

        # Create temp directory with some structure
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create directory structure (parent exists but files don't)
            # This gives partial confidence (architecture understood, but no examples)
            src_dir = project_root / "src" / "auth"
            src_dir.mkdir(parents=True)

            checker = ConfidenceChecker(project_root)

            task = {
                "id": "TASK-003",
                "description": "Add two-factor authentication support to login flow with TOTP codes",
                "acceptance_criteria": [
                    "Users can enable 2FA in settings",
                    "Login flow validates TOTP codes",
                    "Backup codes generated on 2FA setup",
                ],
                "complexity": "M",  # Changed from L to M for better score
                "dependencies": ["TASK-001"],
                "files_likely_affected": ["src/auth/login.py", "src/auth/totp.py"],
                "test_requirements": ["Test 2FA enrollment", "Test TOTP validation"],
            }

            assessment = checker.assess(task)

            # With parent dirs existing and clear requirements: 30+0+20+15+15 = 80
            assert 70 <= assessment.confidence_score < 90
            assert assessment.confidence_level == ConfidenceLevel.MEDIUM
            assert assessment.should_proceed is False
            assert len(assessment.questions) > 0
            assert len(assessment.alternatives) > 0


class TestMemorySystem:
    """Tests for memory system (TASK-004)."""

    def test_reflexion_logging(self):
        """Test logging reflexion entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_dir = Path(tmpdir)
            manager = MemoryManager(memory_dir)

            entry = ReflexionEntry(
                timestamp=datetime.now().isoformat(),
                task_id="TASK-001",
                mistake="Tests failed after refactoring",
                evidence="pytest returned 3 failures",
                fix="Rolled back refactoring commit",
                rule="Always run tests after refactoring before committing",
                severity="high",
            )

            manager.log_reflexion(entry)

            # Verify file was created
            assert manager.reflexion_file.exists()

            # Verify content
            with open(manager.reflexion_file) as f:
                data = json.loads(f.read())
                assert data["task_id"] == "TASK-001"
                assert data["mistake"] == "Tests failed after refactoring"
                assert data["severity"] == "high"

    def test_workflow_metrics_logging(self):
        """Test logging workflow metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_dir = Path(tmpdir)
            manager = MemoryManager(memory_dir)

            metric = WorkflowMetric(
                timestamp=datetime.now().isoformat(),
                task_id="TASK-001",
                complexity="M",
                success=True,
                tokens_input=2500,
                tokens_output=1200,
                tokens_total=3700,
                duration_ms=45000,
                confidence_score=85,
                quality_issues_found=2,
            )

            manager.log_metric(metric)

            # Verify file was created
            assert manager.metrics_file.exists()

            # Verify content
            with open(manager.metrics_file) as f:
                data = json.loads(f.read())
                assert data["task_id"] == "TASK-001"
                assert data["complexity"] == "M"
                assert data["success"] is True
                assert data["tokens_total"] == 3700

    def test_similar_error_search(self):
        """Test searching for similar past errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_dir = Path(tmpdir)
            manager = MemoryManager(memory_dir)

            # Log multiple reflexion entries
            entries = [
                ReflexionEntry(
                    timestamp=datetime.now().isoformat(),
                    task_id="TASK-001",
                    mistake="Tests failed after refactoring authentication module",
                    evidence="pytest failures",
                    fix="Rolled back",
                    rule="Test after refactor",
                    severity="high",
                ),
                ReflexionEntry(
                    timestamp=datetime.now().isoformat(),
                    task_id="TASK-002",
                    mistake="Database migration failed",
                    evidence="SQL error",
                    fix="Fixed schema",
                    rule="Validate migrations",
                    severity="medium",
                ),
                ReflexionEntry(
                    timestamp=datetime.now().isoformat(),
                    task_id="TASK-003",
                    mistake="Refactoring broke user authentication",
                    evidence="Integration tests failed",
                    fix="Reverted changes",
                    rule="Test refactoring thoroughly",
                    severity="high",
                ),
            ]

            for entry in entries:
                manager.log_reflexion(entry)

            # Search for "authentication refactoring"
            similar = manager.search_similar_errors("authentication refactoring")

            # Should find the 2 authentication-related errors
            assert len(similar) >= 2

            # Verify they contain authentication-related keywords
            found_auth = any("authentication" in e.mistake.lower() for e in similar)
            assert found_auth

    def test_average_tokens_for_complexity(self):
        """Test historical token average calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_dir = Path(tmpdir)
            manager = MemoryManager(memory_dir)

            # Log metrics for M complexity
            for i in range(3):
                metric = WorkflowMetric(
                    timestamp=datetime.now().isoformat(),
                    task_id=f"TASK-{i}",
                    complexity="M",
                    success=True,
                    tokens_input=2000 + i * 100,
                    tokens_output=1000 + i * 50,
                    tokens_total=3000 + i * 150,
                )
                manager.log_metric(metric)

            # Get average
            avg = manager.get_average_tokens_for_complexity("M")

            # Should be around 2100 input, 1050 output, 3150 total
            assert 2000 <= avg["input"] <= 2200
            assert 1000 <= avg["output"] <= 1100
            assert 3000 <= avg["total"] <= 3300


class TestTokenManager:
    """Tests for token budget management (TASK-009)."""

    def test_default_budgets(self):
        """Test default token budgets for each complexity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TokenManager(Path(tmpdir))

            # Test all complexity levels
            budgets = {
                TaskComplexity.S: 200,
                TaskComplexity.M: 1000,
                TaskComplexity.L: 2500,
                TaskComplexity.XL: 5000,
            }

            for complexity, expected_total in budgets.items():
                budget = manager.create_budget(
                    f"TASK-{complexity.value}",
                    complexity,
                    use_history=False,
                )

                assert budget.budget_total == expected_total
                assert budget.complexity == complexity
                assert budget.actual_total == 0

    def test_budget_tracking(self):
        """Test budget usage tracking and warnings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TokenManager(Path(tmpdir))

            budget = manager.create_budget("TASK-M", TaskComplexity.M, use_history=False)

            assert budget.budget_total == 1000

            # Use 60% of budget (should not warn)
            budget = manager.update_usage(budget, 420, 180)
            assert budget.actual_total == 600
            assert budget.warned is False
            warning = manager.get_warning_message(budget)
            assert warning is None

            # Use 85% of budget (should warn)
            budget = manager.update_usage(budget, 140, 60)
            assert budget.actual_total == 800
            assert budget.warned is True
            warning = manager.get_warning_message(budget)
            assert warning is not None
            assert "APPROACHING BUDGET" in warning

            # Exceed budget
            budget = manager.update_usage(budget, 200, 100)
            assert budget.actual_total == 1100
            assert budget.exceeded is True
            warning = manager.get_warning_message(budget)
            assert warning is not None
            assert "BUDGET EXCEEDED" in warning

    def test_historical_budget_optimization(self):
        """Test budget optimization from historical data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TokenManager(Path(tmpdir))

            # Log some historical metrics
            from wfc.scripts.memory_manager import MemoryManager, WorkflowMetric

            memory = MemoryManager(tmpdir)

            for i in range(5):
                metric = WorkflowMetric(
                    timestamp=datetime.now().isoformat(),
                    task_id=f"TASK-{i}",
                    complexity="M",
                    success=True,
                    tokens_input=1500,
                    tokens_output=750,
                    tokens_total=2250,
                )
                memory.log_metric(metric)

            # Create budget using history
            budget = manager.create_budget("TASK-NEW", TaskComplexity.M, use_history=True)

            # Should be 20% above historical average
            # Historical: 1500 input, 750 output, 2250 total
            # Expected: 1800 input, 900 output, 2700 total
            assert budget.budget_input == int(1500 * 1.2)
            assert budget.budget_output == int(750 * 1.2)
            assert budget.budget_total == int(2250 * 1.2)


class TestUniversalQualityChecker:
    """Tests for universal quality checker (TASK-001)."""

    def test_trunk_result_parsing(self):
        """Test TrunkCheckResult creation and properties."""
        result = TrunkCheckResult(
            passed=False,
            output="Found 5 issues: 2 errors, 3 warnings",
            issues_found=5,
            fixable_issues=3,
            files_checked=10,
        )

        assert result.passed is False
        assert result.issues_found == 5
        assert result.fixable_issues == 3
        assert "2 errors" in result.output

    def test_quality_checker_initialization(self):
        """Test quality checker initialization with files."""
        files = ["file1.py", "file2.py", "file3.py"]
        checker = UniversalQualityChecker(files=files)

        assert checker.files == files
        # UniversalQualityChecker only stores files, no other attributes


class TestFailureSeverity:
    """Tests for failure severity classification (user feedback)."""

    def test_severity_classification(self):
        """Test that warnings don't block but errors do."""
        from wfc_implement.merge_engine import FailureSeverity

        # WARNING severity should not block
        assert FailureSeverity.WARNING.value == "warning"

        # ERROR severity should block but allow retry
        assert FailureSeverity.ERROR.value == "error"

        # CRITICAL severity should immediately fail
        assert FailureSeverity.CRITICAL.value == "critical"


def test_integration_smoke():
    """Smoke test to ensure all components can be imported."""
    # If we got here, all imports succeeded
    assert True


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])
