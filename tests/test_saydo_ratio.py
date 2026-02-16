"""
Tests for WFC Say:Do Ratio and TEAMCHARTER Values Alignment metrics.

TDD: Tests written FIRST before implementation.
Covers: compute_say_do_ratio, aggregate_values_alignment,
        generate_values_mermaid_chart, generate_values_recommendations
"""

from wfc.scripts.memory.schemas import ReflexionEntry
from wfc.scripts.memory.saydo import (
    compute_say_do_ratio,
    aggregate_values_alignment,
    generate_values_mermaid_chart,
    generate_values_recommendations,
)

# ---------------------------------------------------------------------------
# compute_say_do_ratio
# ---------------------------------------------------------------------------


class TestComputeSayDoRatio:
    """Tests for Say:Do ratio computation."""

    def test_say_do_ratio_perfect(self):
        """All tasks completed at estimated complexity -> 1.0."""
        tasks = [
            {
                "task_id": "TASK-001",
                "estimated_complexity": "S",
                "actual_complexity": "S",
                "quality_gate_passed": True,
                "re_estimated": False,
            },
            {
                "task_id": "TASK-002",
                "estimated_complexity": "M",
                "actual_complexity": "M",
                "quality_gate_passed": True,
                "re_estimated": False,
            },
            {
                "task_id": "TASK-003",
                "estimated_complexity": "L",
                "actual_complexity": "L",
                "quality_gate_passed": True,
                "re_estimated": False,
            },
        ]
        assert compute_say_do_ratio(tasks) == 1.0

    def test_say_do_ratio_partial(self):
        """Some tasks re-estimated or failed quality -> ratio < 1.0."""
        tasks = [
            {
                "task_id": "TASK-001",
                "estimated_complexity": "S",
                "actual_complexity": "S",
                "quality_gate_passed": True,
                "re_estimated": False,
            },
            {
                "task_id": "TASK-002",
                "estimated_complexity": "S",
                "actual_complexity": "M",
                "quality_gate_passed": True,
                "re_estimated": True,
            },
            {
                "task_id": "TASK-003",
                "estimated_complexity": "M",
                "actual_complexity": "M",
                "quality_gate_passed": False,
                "re_estimated": False,
            },
            {
                "task_id": "TASK-004",
                "estimated_complexity": "L",
                "actual_complexity": "L",
                "quality_gate_passed": True,
                "re_estimated": False,
            },
        ]
        # TASK-001 and TASK-004 are on-estimate (2/4 = 0.5)
        assert compute_say_do_ratio(tasks) == 0.5

    def test_say_do_ratio_empty(self):
        """No tasks -> 0.0 (graceful handling)."""
        assert compute_say_do_ratio([]) == 0.0

    def test_say_do_ratio_all_failed(self):
        """All tasks failed quality gates -> 0.0."""
        tasks = [
            {
                "task_id": "TASK-001",
                "estimated_complexity": "M",
                "actual_complexity": "L",
                "quality_gate_passed": False,
                "re_estimated": True,
            },
        ]
        assert compute_say_do_ratio(tasks) == 0.0

    def test_say_do_ratio_quality_gate_failure_counts_against(self):
        """Task with matching complexity but failed quality gate counts against."""
        tasks = [
            {
                "task_id": "TASK-001",
                "estimated_complexity": "M",
                "actual_complexity": "M",
                "quality_gate_passed": False,
                "re_estimated": False,
            },
        ]
        assert compute_say_do_ratio(tasks) == 0.0

    def test_say_do_ratio_re_estimation_counts_against(self):
        """Task that was re-estimated counts against even if final complexity matches."""
        tasks = [
            {
                "task_id": "TASK-001",
                "estimated_complexity": "M",
                "actual_complexity": "M",
                "quality_gate_passed": True,
                "re_estimated": True,
            },
        ]
        assert compute_say_do_ratio(tasks) == 0.0

    def test_say_do_ratio_missing_fields_defaults(self):
        """Tasks with missing optional fields use safe defaults."""
        tasks = [
            {
                "task_id": "TASK-001",
                "estimated_complexity": "S",
                "actual_complexity": "S",
                # quality_gate_passed and re_estimated missing
            },
        ]
        # Missing quality_gate_passed defaults to True,
        # missing re_estimated defaults to False
        # So complexity matches + defaults => on-estimate
        assert compute_say_do_ratio(tasks) == 1.0


# ---------------------------------------------------------------------------
# aggregate_values_alignment
# ---------------------------------------------------------------------------


class TestAggregateValuesAlignment:
    """Tests for values alignment aggregation from ReflexionEntries."""

    def test_aggregate_values_alignment_basic(self):
        """Counts violated/upheld per value correctly."""
        entries = [
            ReflexionEntry(
                timestamp="2026-02-15T12:00:00Z",
                task_id="TASK-001",
                mistake="Broke prod",
                evidence="Errors",
                fix="Rolled back",
                rule="Test first",
                team_values_impact={"accountability": "violated", "quality": "upheld"},
            ),
            ReflexionEntry(
                timestamp="2026-02-15T13:00:00Z",
                task_id="TASK-002",
                mistake="Skipped review",
                evidence="Direct push",
                fix="Added protection",
                rule="PR required",
                team_values_impact={"accountability": "violated", "collaboration": "violated"},
            ),
        ]

        result = aggregate_values_alignment(entries)

        assert result["accountability"]["violated"] == 2
        assert result["accountability"].get("upheld", 0) == 0
        assert result["quality"]["upheld"] == 1
        assert result["collaboration"]["violated"] == 1

    def test_aggregate_values_alignment_empty(self):
        """Empty entries list -> empty dict."""
        result = aggregate_values_alignment([])
        assert result == {}

    def test_aggregate_values_alignment_no_values_impact(self):
        """Entries without team_values_impact are skipped."""
        entries = [
            ReflexionEntry(
                timestamp="2026-02-15T12:00:00Z",
                task_id="TASK-001",
                mistake="Typo",
                evidence="Linter",
                fix="Fixed",
                rule="Lint",
                team_values_impact=None,
            ),
        ]

        result = aggregate_values_alignment(entries)
        assert result == {}

    def test_aggregate_values_alignment_mixed(self):
        """Mix of entries with and without team_values_impact."""
        entries = [
            ReflexionEntry(
                timestamp="2026-02-15T12:00:00Z",
                task_id="TASK-001",
                mistake="Broke prod",
                evidence="Errors",
                fix="Fixed",
                rule="Test",
                team_values_impact={"simplicity": "violated"},
            ),
            ReflexionEntry(
                timestamp="2026-02-15T13:00:00Z",
                task_id="TASK-002",
                mistake="Typo",
                evidence="Linter",
                fix="Fixed",
                rule="Lint",
                team_values_impact=None,
            ),
            ReflexionEntry(
                timestamp="2026-02-15T14:00:00Z",
                task_id="TASK-003",
                mistake="Over-engineered",
                evidence="Complex code",
                fix="Simplified",
                rule="KISS",
                team_values_impact={"simplicity": "violated", "quality": "upheld"},
            ),
        ]

        result = aggregate_values_alignment(entries)
        assert result["simplicity"]["violated"] == 2
        assert result["quality"]["upheld"] == 1


# ---------------------------------------------------------------------------
# generate_values_mermaid_chart
# ---------------------------------------------------------------------------


class TestGenerateValuesMermaidChart:
    """Tests for Mermaid chart generation."""

    def test_mermaid_chart_generation(self):
        """Generates valid Mermaid syntax."""
        alignment = {
            "accountability": {"violated": 3, "upheld": 1},
            "quality": {"upheld": 5, "violated": 0},
            "simplicity": {"violated": 2, "upheld": 2},
        }

        chart = generate_values_mermaid_chart(alignment)

        # Must be valid Mermaid xychart-beta or bar chart
        assert "```mermaid" in chart
        assert "```" in chart
        # Should reference the values
        assert "accountability" in chart.lower() or "Accountability" in chart
        assert "quality" in chart.lower() or "Quality" in chart

    def test_mermaid_chart_empty(self):
        """Empty alignment -> still valid Mermaid (or placeholder message)."""
        chart = generate_values_mermaid_chart({})

        # Should either be valid mermaid or a "no data" message
        assert isinstance(chart, str)
        assert len(chart) > 0

    def test_mermaid_chart_single_value(self):
        """Single value produces valid chart."""
        alignment = {"transparency": {"upheld": 3, "violated": 1}}

        chart = generate_values_mermaid_chart(alignment)

        assert "```mermaid" in chart
        assert "transparency" in chart.lower() or "Transparency" in chart


# ---------------------------------------------------------------------------
# generate_values_recommendations
# ---------------------------------------------------------------------------


class TestGenerateValuesRecommendations:
    """Tests for actionable recommendations generation."""

    def test_recommendations_generation(self):
        """Recommendations mention specific values."""
        alignment = {
            "simplicity": {"violated": 5, "upheld": 1},
            "quality": {"upheld": 10, "violated": 0},
            "accountability": {"violated": 3, "upheld": 2},
        }

        recs = generate_values_recommendations(alignment)

        assert isinstance(recs, list)
        assert len(recs) > 0
        # Recommendations should mention values that were violated
        combined = " ".join(recs).lower()
        assert "simplicity" in combined
        # quality was fully upheld so might be mentioned positively or not at all
        # accountability was violated, should be mentioned
        assert "accountability" in combined

    def test_recommendations_empty(self):
        """Empty alignment -> empty recommendations."""
        recs = generate_values_recommendations({})
        assert isinstance(recs, list)
        assert len(recs) == 0

    def test_recommendations_no_violations(self):
        """All values upheld -> positive recommendations or empty."""
        alignment = {
            "quality": {"upheld": 10, "violated": 0},
            "accountability": {"upheld": 8, "violated": 0},
        }

        recs = generate_values_recommendations(alignment)

        assert isinstance(recs, list)
        # Should either be empty or contain positive feedback
        # No negative recommendations expected

    def test_recommendations_with_high_violation_rate(self):
        """Values with high violation rates get specific recommendations."""
        alignment = {
            "simplicity": {"violated": 8, "upheld": 2},
        }

        recs = generate_values_recommendations(alignment)

        assert len(recs) > 0
        combined = " ".join(recs).lower()
        assert "simplicity" in combined
