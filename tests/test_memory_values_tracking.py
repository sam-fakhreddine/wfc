"""
Tests for WFC Memory TEAMCHARTER values alignment tracking.

Verifies that ReflexionEntry and OperationalPattern support
team values impact tracking with backward compatibility.
"""

from wfc.scripts.memory.schemas import ReflexionEntry, OperationalPattern, WorkflowMetric


class TestReflexionEntryValuesTracking:
    """Test TEAMCHARTER values tracking in ReflexionEntry."""

    def test_reflexion_entry_with_team_values_impact(self):
        """Test ReflexionEntry with team_values_impact set."""
        entry = ReflexionEntry(
            timestamp="2026-02-15T12:00:00Z",
            task_id="TASK-001",
            mistake="Merged code without tests",
            evidence="No test files in commit",
            fix="Added comprehensive test suite",
            rule="Always require tests before merge",
            severity="high",
            team_values_impact={"accountability": "violated", "quality": "compromised"},
        )

        assert entry.team_values_impact == {
            "accountability": "violated",
            "quality": "compromised",
        }
        assert entry.severity == "high"
        assert entry.task_id == "TASK-001"

    def test_reflexion_entry_without_team_values_impact(self):
        """Test ReflexionEntry without team_values_impact (backward compat)."""
        entry = ReflexionEntry(
            timestamp="2026-02-15T12:00:00Z",
            task_id="TASK-002",
            mistake="Typo in variable name",
            evidence="Linter error",
            fix="Renamed variable",
            rule="Run linter before commit",
        )

        # Should default to None
        assert entry.team_values_impact is None
        assert entry.severity == "medium"  # Default severity

    def test_reflexion_entry_to_dict_includes_team_values_impact(self):
        """Test to_dict includes team_values_impact."""
        entry = ReflexionEntry(
            timestamp="2026-02-15T12:00:00Z",
            task_id="TASK-003",
            mistake="Skipped code review",
            evidence="Direct push to main",
            fix="Implemented branch protection",
            rule="All changes require PR review",
            team_values_impact={"collaboration": "skipped"},
        )

        data = entry.to_dict()

        assert "team_values_impact" in data
        assert data["team_values_impact"] == {"collaboration": "skipped"}
        assert data["task_id"] == "TASK-003"
        assert data["severity"] == "medium"

    def test_reflexion_entry_to_dict_without_values_impact(self):
        """Test to_dict when team_values_impact is None."""
        entry = ReflexionEntry(
            timestamp="2026-02-15T12:00:00Z",
            task_id="TASK-004",
            mistake="Minor formatting issue",
            evidence="CI failed",
            fix="Ran formatter",
            rule="Run formatter pre-commit",
        )

        data = entry.to_dict()

        assert "team_values_impact" in data
        assert data["team_values_impact"] is None

    def test_reflexion_entry_from_dict_with_old_data(self):
        """Test from_dict with old data (no team_values_impact) - MUST NOT crash."""
        old_data = {
            "timestamp": "2026-02-15T12:00:00Z",
            "task_id": "TASK-005",
            "mistake": "Missing documentation",
            "evidence": "No docstrings",
            "fix": "Added docstrings",
            "rule": "Require docstrings for public APIs",
            "severity": "low",
            # NOTE: No team_values_impact field
        }

        entry = ReflexionEntry.from_dict(old_data)

        # Should create successfully with team_values_impact defaulting to None
        assert entry.task_id == "TASK-005"
        assert entry.severity == "low"
        assert entry.team_values_impact is None

    def test_reflexion_entry_from_dict_with_new_data(self):
        """Test from_dict with new data (has team_values_impact)."""
        new_data = {
            "timestamp": "2026-02-15T12:00:00Z",
            "task_id": "TASK-006",
            "mistake": "Deployed untested code",
            "evidence": "Production outage",
            "fix": "Implemented staging environment",
            "rule": "Test in staging before production",
            "severity": "critical",
            "team_values_impact": {"customer_focus": "violated", "reliability": "failed"},
        }

        entry = ReflexionEntry.from_dict(new_data)

        assert entry.task_id == "TASK-006"
        assert entry.severity == "critical"
        assert entry.team_values_impact == {
            "customer_focus": "violated",
            "reliability": "failed",
        }

    def test_reflexion_entry_from_dict_with_extra_fields(self):
        """Test from_dict ignores unknown fields (backward compat)."""
        data_with_extra = {
            "timestamp": "2026-02-15T12:00:00Z",
            "task_id": "TASK-007",
            "mistake": "Performance regression",
            "evidence": "Slow API response",
            "fix": "Optimized query",
            "rule": "Benchmark before deploy",
            "severity": "high",
            "team_values_impact": {"performance": "degraded"},
            "unknown_field": "should be ignored",
            "another_unknown": 12345,
        }

        entry = ReflexionEntry.from_dict(data_with_extra)

        # Should create successfully, ignoring unknown fields
        assert entry.task_id == "TASK-007"
        assert entry.severity == "high"
        assert entry.team_values_impact == {"performance": "degraded"}
        # Unknown fields should not be set
        assert not hasattr(entry, "unknown_field")
        assert not hasattr(entry, "another_unknown")


class TestOperationalPatternValuesTracking:
    """Test TEAMCHARTER values tracking in OperationalPattern."""

    def test_operational_pattern_with_values_alignment(self):
        """Test OperationalPattern with values_alignment set."""
        pattern = OperationalPattern(
            pattern_id="PATTERN-001",
            first_detected="2026-02-15T10:00:00Z",
            last_detected="2026-02-15T12:00:00Z",
            occurrence_count=3,
            error_type="missing_tests",
            description="Code merged without tests multiple times",
            fix="Implement pre-merge test requirement",
            impact="Quality degradation",
            severity="high",
            values_alignment="quality_first",
        )

        assert pattern.values_alignment == "quality_first"
        assert pattern.pattern_id == "PATTERN-001"
        assert pattern.occurrence_count == 3

    def test_operational_pattern_without_values_alignment(self):
        """Test OperationalPattern without values_alignment (backward compat)."""
        pattern = OperationalPattern(
            pattern_id="PATTERN-002",
            first_detected="2026-02-15T11:00:00Z",
            last_detected="2026-02-15T11:30:00Z",
            occurrence_count=1,
            error_type="docker_version_obsolete",
            description="Using old docker-compose v1",
            fix="Upgrade to docker compose v2",
            impact="Compatibility issues",
        )

        # Should default to None
        assert pattern.values_alignment is None
        assert pattern.severity == "medium"  # Default severity
        assert pattern.status == "READY_FOR_PLAN"  # Default status

    def test_operational_pattern_to_dict_includes_values_alignment(self):
        """Test to_dict includes values_alignment."""
        pattern = OperationalPattern(
            pattern_id="PATTERN-003",
            first_detected="2026-02-15T09:00:00Z",
            last_detected="2026-02-15T12:00:00Z",
            occurrence_count=5,
            error_type="slow_ci",
            description="CI pipeline takes too long",
            fix="Optimize test suite",
            impact="Developer productivity",
            values_alignment="speed_to_market",
        )

        data = pattern.to_dict()

        assert "values_alignment" in data
        assert data["values_alignment"] == "speed_to_market"
        assert data["pattern_id"] == "PATTERN-003"
        assert data["occurrence_count"] == 5

    def test_operational_pattern_to_dict_without_values_alignment(self):
        """Test to_dict when values_alignment is None."""
        pattern = OperationalPattern(
            pattern_id="PATTERN-004",
            first_detected="2026-02-15T10:00:00Z",
            last_detected="2026-02-15T10:00:00Z",
            occurrence_count=1,
            error_type="typo",
            description="Typo in config",
            fix="Fix typo",
            impact="Minor",
        )

        data = pattern.to_dict()

        assert "values_alignment" in data
        assert data["values_alignment"] is None

    def test_operational_pattern_from_dict_with_old_data(self):
        """Test from_dict with old data (no values_alignment) - MUST NOT crash."""
        old_data = {
            "pattern_id": "PATTERN-005",
            "first_detected": "2026-02-15T08:00:00Z",
            "last_detected": "2026-02-15T12:00:00Z",
            "occurrence_count": 7,
            "error_type": "lint_failures",
            "description": "Code fails linting",
            "fix": "Run linter pre-commit",
            "impact": "Code quality",
            "status": "PLANNED",
            "severity": "medium",
            # NOTE: No values_alignment field
        }

        pattern = OperationalPattern.from_dict(old_data)

        # Should create successfully with values_alignment defaulting to None
        assert pattern.pattern_id == "PATTERN-005"
        assert pattern.occurrence_count == 7
        assert pattern.values_alignment is None

    def test_operational_pattern_from_dict_with_new_data(self):
        """Test from_dict with new data (has values_alignment)."""
        new_data = {
            "pattern_id": "PATTERN-006",
            "first_detected": "2026-02-15T07:00:00Z",
            "last_detected": "2026-02-15T12:00:00Z",
            "occurrence_count": 10,
            "error_type": "security_vulnerability",
            "description": "Dependency vulnerabilities",
            "fix": "Update dependencies",
            "impact": "Security risk",
            "status": "READY_FOR_PLAN",
            "severity": "critical",
            "values_alignment": "security_first",
        }

        pattern = OperationalPattern.from_dict(new_data)

        assert pattern.pattern_id == "PATTERN-006"
        assert pattern.severity == "critical"
        assert pattern.values_alignment == "security_first"

    def test_operational_pattern_from_dict_with_extra_fields(self):
        """Test from_dict ignores unknown fields (backward compat)."""
        data_with_extra = {
            "pattern_id": "PATTERN-007",
            "first_detected": "2026-02-15T06:00:00Z",
            "last_detected": "2026-02-15T12:00:00Z",
            "occurrence_count": 2,
            "error_type": "flaky_tests",
            "description": "Tests fail intermittently",
            "fix": "Fix test isolation",
            "impact": "CI reliability",
            "severity": "high",
            "values_alignment": "reliability",
            "unknown_metric": 99.9,
            "extra_data": {"some": "value"},
        }

        pattern = OperationalPattern.from_dict(data_with_extra)

        # Should create successfully, ignoring unknown fields
        assert pattern.pattern_id == "PATTERN-007"
        assert pattern.values_alignment == "reliability"
        # Unknown fields should not be set
        assert not hasattr(pattern, "unknown_metric")
        assert not hasattr(pattern, "extra_data")


class TestWorkflowMetricUnchanged:
    """Test that WorkflowMetric remains unchanged (no new fields)."""

    def test_workflow_metric_no_new_fields(self):
        """Test WorkflowMetric has no new values-related fields."""
        metric = WorkflowMetric(
            timestamp="2026-02-15T12:00:00Z",
            task_id="TASK-100",
            complexity="M",
            success=True,
            tokens_input=1000,
            tokens_output=500,
            confidence_score=95,
        )

        # Should not have values-related fields
        assert not hasattr(metric, "team_values_impact")
        assert not hasattr(metric, "values_alignment")

        # Should have normal fields
        assert metric.task_id == "TASK-100"
        assert metric.success is True
        assert metric.confidence_score == 95

    def test_workflow_metric_to_dict_no_values_fields(self):
        """Test to_dict does not include values-related fields."""
        metric = WorkflowMetric(
            timestamp="2026-02-15T12:00:00Z",
            task_id="TASK-101",
            complexity="L",
            success=False,
            retry_count=2,
        )

        data = metric.to_dict()

        # Should not have values-related fields
        assert "team_values_impact" not in data
        assert "values_alignment" not in data

        # Should have normal fields
        assert data["task_id"] == "TASK-101"
        assert data["success"] is False
        assert data["retry_count"] == 2

    def test_workflow_metric_from_dict_unchanged(self):
        """Test from_dict works normally (no backward compat needed)."""
        data = {
            "timestamp": "2026-02-15T12:00:00Z",
            "task_id": "TASK-102",
            "complexity": "XL",
            "success": True,
            "tokens_total": 5000,
            "duration_ms": 120000,
        }

        metric = WorkflowMetric.from_dict(data)

        assert metric.task_id == "TASK-102"
        assert metric.complexity == "XL"
        assert metric.success is True
        assert metric.tokens_total == 5000


class TestRoundTripSerialization:
    """Test round-trip serialization (to_dict -> from_dict)."""

    def test_reflexion_entry_roundtrip_with_values(self):
        """Test ReflexionEntry round-trip with team_values_impact."""
        original = ReflexionEntry(
            timestamp="2026-02-15T12:00:00Z",
            task_id="TASK-200",
            mistake="Broke production",
            evidence="Error logs",
            fix="Rolled back",
            rule="Test in staging",
            severity="critical",
            team_values_impact={"customer_focus": "violated"},
        )

        data = original.to_dict()
        restored = ReflexionEntry.from_dict(data)

        assert restored.task_id == original.task_id
        assert restored.severity == original.severity
        assert restored.team_values_impact == original.team_values_impact

    def test_reflexion_entry_roundtrip_without_values(self):
        """Test ReflexionEntry round-trip without team_values_impact."""
        original = ReflexionEntry(
            timestamp="2026-02-15T12:00:00Z",
            task_id="TASK-201",
            mistake="Typo",
            evidence="User report",
            fix="Fixed typo",
            rule="Proofread",
        )

        data = original.to_dict()
        restored = ReflexionEntry.from_dict(data)

        assert restored.task_id == original.task_id
        assert restored.team_values_impact is None

    def test_operational_pattern_roundtrip_with_values(self):
        """Test OperationalPattern round-trip with values_alignment."""
        original = OperationalPattern(
            pattern_id="PATTERN-200",
            first_detected="2026-02-15T10:00:00Z",
            last_detected="2026-02-15T12:00:00Z",
            occurrence_count=4,
            error_type="security_issue",
            description="Security vulnerability",
            fix="Apply security patch",
            impact="High risk",
            values_alignment="security_first",
        )

        data = original.to_dict()
        restored = OperationalPattern.from_dict(data)

        assert restored.pattern_id == original.pattern_id
        assert restored.occurrence_count == original.occurrence_count
        assert restored.values_alignment == original.values_alignment

    def test_operational_pattern_roundtrip_without_values(self):
        """Test OperationalPattern round-trip without values_alignment."""
        original = OperationalPattern(
            pattern_id="PATTERN-201",
            first_detected="2026-02-15T09:00:00Z",
            last_detected="2026-02-15T09:30:00Z",
            occurrence_count=1,
            error_type="config_error",
            description="Wrong config",
            fix="Fix config",
            impact="Minor",
        )

        data = original.to_dict()
        restored = OperationalPattern.from_dict(data)

        assert restored.pattern_id == original.pattern_id
        assert restored.values_alignment is None
