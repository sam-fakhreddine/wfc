"""Tests for wfc-doctor types module."""

from pathlib import Path

from wfc.skills import wfc_doctor  # noqa: F401 - Required for PEP 562 import registration
from wfc_doctor.types import CheckResult, HealthCheckResult


class TestCheckResult:
    """Test CheckResult dataclass."""

    def test_check_result_creation(self):
        """Test creating a CheckResult instance."""
        result = CheckResult(name="test_check", status="PASS", issues=[], fixes_applied=[])
        assert result.name == "test_check"
        assert result.status == "PASS"
        assert result.issues == []
        assert result.fixes_applied == []

    def test_check_result_with_issues(self):
        """Test CheckResult with issues and fixes."""
        result = CheckResult(
            name="test_check",
            status="WARN",
            issues=["Issue 1", "Issue 2"],
            fixes_applied=["Fixed issue 1"],
        )
        assert len(result.issues) == 2
        assert len(result.fixes_applied) == 1
        assert result.status == "WARN"


class TestHealthCheckResult:
    """Test HealthCheckResult dataclass."""

    def test_health_check_result_creation(self):
        """Test creating a HealthCheckResult instance."""
        check1 = CheckResult(name="check1", status="PASS", issues=[], fixes_applied=[])
        result = HealthCheckResult(
            status="PASS",
            checks={"check1": check1},
            report_path=Path("/tmp/report.md"),
            timestamp="2024-01-01 12:00:00",
        )
        assert result.status == "PASS"
        assert "check1" in result.checks
        assert result.report_path == Path("/tmp/report.md")
        assert result.timestamp == "2024-01-01 12:00:00"

    def test_health_check_result_multiple_checks(self):
        """Test HealthCheckResult with multiple checks."""
        check1 = CheckResult(name="check1", status="PASS", issues=[], fixes_applied=[])
        check2 = CheckResult(name="check2", status="WARN", issues=["warning"], fixes_applied=[])
        check3 = CheckResult(name="check3", status="FAIL", issues=["error"], fixes_applied=[])

        result = HealthCheckResult(
            status="FAIL",
            checks={"check1": check1, "check2": check2, "check3": check3},
            report_path=Path("/tmp/report.md"),
            timestamp="2024-01-01 12:00:00",
        )
        assert len(result.checks) == 3
        assert result.checks["check1"].status == "PASS"
        assert result.checks["check2"].status == "WARN"
        assert result.checks["check3"].status == "FAIL"
