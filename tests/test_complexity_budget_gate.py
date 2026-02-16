"""
Tests for WFC Complexity Budget Gate

Verifies complexity budget enforcement for TEAMCHARTER "Accountability & Simplicity" value.
"""

from wfc.scripts.complexity_budget_gate import (
    check_complexity_budget,
    format_budget_report,
    COMPLEXITY_BUDGETS,
)


class TestComplexityBudgetGate:
    """Test complexity budget gate enforcement"""

    def test_budgets_match_spec(self):
        """TEST-001: Verify budget tiers match specification"""
        assert COMPLEXITY_BUDGETS["S"]["lines"] == 50
        assert COMPLEXITY_BUDGETS["S"]["files"] == 2

        assert COMPLEXITY_BUDGETS["M"]["lines"] == 200
        assert COMPLEXITY_BUDGETS["M"]["files"] == 5

        assert COMPLEXITY_BUDGETS["L"]["lines"] == 500
        assert COMPLEXITY_BUDGETS["L"]["files"] == 10

        assert COMPLEXITY_BUDGETS["XL"]["lines"] == 1000
        assert COMPLEXITY_BUDGETS["XL"]["files"] == 20

    def test_s_complexity_passing(self):
        """TEST-002: S complexity within budget passes"""
        result = check_complexity_budget("TASK-001", "S", 45, 2)

        assert result.passed is True
        assert result.task_id == "TASK-001"
        assert result.complexity == "S"
        assert result.lines_changed == 45
        assert result.files_changed == 2
        assert result.lines_budget == 50
        assert result.files_budget == 2
        assert result.lines_exceeded == 0
        assert result.files_exceeded == 0
        assert result.severity == "warning"
        assert "✅" in result.report
        assert "PASSED" in result.report

    def test_s_complexity_failing_lines(self):
        """TEST-003: S complexity exceeding lines fails"""
        result = check_complexity_budget("TASK-002", "S", 100, 2)

        assert result.passed is False
        assert result.lines_changed == 100
        assert result.files_changed == 2
        assert result.lines_budget == 50
        assert result.files_budget == 2
        assert result.lines_exceeded == 50
        assert result.files_exceeded == 0
        assert result.severity == "warning"
        assert "⚠️" in result.report
        assert "EXCEEDED" in result.report
        assert "50 lines" in result.report

    def test_s_complexity_failing_files(self):
        """TEST-004: S complexity exceeding files fails"""
        result = check_complexity_budget("TASK-003", "S", 30, 5)

        assert result.passed is False
        assert result.lines_changed == 30
        assert result.files_changed == 5
        assert result.lines_budget == 50
        assert result.files_budget == 2
        assert result.lines_exceeded == 0
        assert result.files_exceeded == 3
        assert "3 files" in result.report

    def test_s_complexity_failing_both(self):
        """TEST-005: S complexity exceeding both lines and files fails"""
        result = check_complexity_budget("TASK-004", "S", 100, 5)

        assert result.passed is False
        assert result.lines_exceeded == 50
        assert result.files_exceeded == 3
        assert "50 lines" in result.report
        assert "3 files" in result.report

    def test_m_complexity_passing(self):
        """TEST-006: M complexity within budget passes"""
        result = check_complexity_budget("TASK-005", "M", 180, 4)

        assert result.passed is True
        assert result.lines_budget == 200
        assert result.files_budget == 5
        assert result.lines_exceeded == 0
        assert result.files_exceeded == 0

    def test_m_complexity_failing(self):
        """TEST-007: M complexity exceeding budget fails"""
        result = check_complexity_budget("TASK-006", "M", 250, 7)

        assert result.passed is False
        assert result.lines_exceeded == 50
        assert result.files_exceeded == 2
        assert "EXCEEDED" in result.report

    def test_l_complexity_passing(self):
        """TEST-008: L complexity within budget passes"""
        result = check_complexity_budget("TASK-007", "L", 450, 8)

        assert result.passed is True
        assert result.lines_budget == 500
        assert result.files_budget == 10

    def test_l_complexity_failing(self):
        """TEST-009: L complexity exceeding budget fails"""
        result = check_complexity_budget("TASK-008", "L", 600, 12)

        assert result.passed is False
        assert result.lines_exceeded == 100
        assert result.files_exceeded == 2

    def test_xl_complexity_passing(self):
        """TEST-010: XL complexity within budget passes"""
        result = check_complexity_budget("TASK-009", "XL", 900, 18)

        assert result.passed is True
        assert result.lines_budget == 1000
        assert result.files_budget == 20

    def test_xl_complexity_failing(self):
        """TEST-011: XL complexity exceeding budget fails"""
        result = check_complexity_budget("TASK-010", "XL", 1200, 25)

        assert result.passed is False
        assert result.lines_exceeded == 200
        assert result.files_exceeded == 5

    def test_edge_case_zero_lines(self):
        """TEST-012: Edge case - 0 lines changed"""
        result = check_complexity_budget("TASK-011", "S", 0, 0)

        assert result.passed is True
        assert result.lines_exceeded == 0
        assert result.files_exceeded == 0

    def test_edge_case_exactly_at_limit(self):
        """TEST-013: Edge case - exactly at budget limit"""
        result = check_complexity_budget("TASK-012", "S", 50, 2)

        assert result.passed is True
        assert result.lines_changed == 50
        assert result.files_changed == 2
        assert result.lines_exceeded == 0
        assert result.files_exceeded == 0

    def test_edge_case_one_over_limit(self):
        """TEST-014: Edge case - 1 line/file over limit"""
        result = check_complexity_budget("TASK-013", "S", 51, 3)

        assert result.passed is False
        assert result.lines_exceeded == 1
        assert result.files_exceeded == 1

    def test_report_generation_passing(self):
        """TEST-015: Report generation for passing task"""
        result = check_complexity_budget("TASK-014", "M", 150, 3)

        assert result.passed is True
        report = format_budget_report(result)

        # Check report content
        assert "TASK-014" in report
        assert "M" in report
        assert "150/200" in report
        assert "3/5" in report
        assert "✅" in report
        assert "PASSED" in report
        assert "within complexity budget" in report

    def test_report_generation_exceeding(self):
        """TEST-016: Report generation for exceeding task"""
        result = check_complexity_budget("TASK-015", "S", 100, 5)

        assert result.passed is False
        report = format_budget_report(result)

        # Check report content
        assert "TASK-015" in report
        assert "S" in report
        assert "100/50" in report
        assert "5/2" in report
        assert "⚠️" in report
        assert "EXCEEDED" in report
        assert "50 lines" in report
        assert "3 files" in report
        assert "RECOMMENDATION" in report
        assert "splitting" in report.lower()

    def test_report_shows_what_exceeded(self):
        """TEST-017: Report clearly shows what exceeded and by how much"""
        # Only lines exceeded
        result = check_complexity_budget("TASK-016", "M", 300, 3)
        report = format_budget_report(result)

        assert "100 lines" in report  # 300 - 200 = 100
        assert "Files Changed: 3/5" in report
        assert "Within budget" in report  # Files within budget

        # Only files exceeded
        result = check_complexity_budget("TASK-017", "M", 150, 8)
        report = format_budget_report(result)

        assert "3 files" in report  # 8 - 5 = 3
        assert "Lines Changed: 150/200" in report
        assert "Within budget" in report  # Lines within budget

    def test_case_insensitive_complexity(self):
        """TEST-018: Complexity rating is case-insensitive"""
        result_lower = check_complexity_budget("TASK-018", "s", 40, 2)
        result_upper = check_complexity_budget("TASK-019", "S", 40, 2)

        assert result_lower.passed is True
        assert result_upper.passed is True
        assert result_lower.complexity == "S"
        assert result_upper.complexity == "S"

    def test_unknown_complexity_defaults_to_xl(self):
        """TEST-019: Unknown complexity defaults to XL budget with warning"""
        result = check_complexity_budget("TASK-020", "UNKNOWN", 800, 15)

        assert result.passed is True
        assert result.lines_budget == 1000  # XL budget
        assert result.files_budget == 20  # XL budget
        assert result.unknown_complexity is True
        assert "Unknown complexity rating" in result.report
        assert "'UNKNOWN'" in result.report
        assert "defaulted to 'XL'" in result.report

    def test_severity_always_warning(self):
        """TEST-020: Budget exceedance is always warning, never blocking"""
        # Passing task
        result_pass = check_complexity_budget("TASK-021", "S", 40, 2)
        assert result_pass.severity == "warning"

        # Failing task
        result_fail = check_complexity_budget("TASK-022", "S", 100, 5)
        assert result_fail.severity == "warning"

    def test_to_dict_serialization(self):
        """TEST-021: BudgetResult serializes to dict correctly"""
        result = check_complexity_budget("TASK-023", "M", 250, 6)

        data = result.to_dict()

        assert data["task_id"] == "TASK-023"
        assert data["complexity"] == "M"
        assert data["lines_changed"] == 250
        assert data["files_changed"] == 6
        assert data["lines_budget"] == 200
        assert data["files_budget"] == 5
        assert data["lines_exceeded"] == 50
        assert data["files_exceeded"] == 1
        assert data["passed"] is False
        assert data["severity"] == "warning"
        assert data["unknown_complexity"] is False
        assert isinstance(data["report"], str)

    def test_percentage_calculation_in_report(self):
        """TEST-022: Report includes percentage of budget used"""
        # 75% of budget
        result = check_complexity_budget("TASK-024", "M", 150, 4)
        report = format_budget_report(result)

        # Should show percentages
        assert "75%" in report or "80%" in report  # Lines: 150/200 = 75%, Files: 4/5 = 80%

    def test_multiple_budgets_independently_checked(self):
        """TEST-023: Lines and files budgets are checked independently"""
        # Within lines budget, over files budget
        result1 = check_complexity_budget("TASK-025", "S", 30, 5)
        assert result1.lines_exceeded == 0
        assert result1.files_exceeded == 3
        assert result1.passed is False

        # Over lines budget, within files budget
        result2 = check_complexity_budget("TASK-026", "S", 100, 1)
        assert result2.lines_exceeded == 50
        assert result2.files_exceeded == 0
        assert result2.passed is False

    def test_recommendation_in_exceeded_report(self):
        """TEST-024: Exceeded report includes splitting recommendation"""
        result = check_complexity_budget("TASK-027", "S", 100, 5)
        report = format_budget_report(result)

        assert "RECOMMENDATION" in report
        assert "splitting" in report.lower() or "split" in report.lower()
        assert "smaller" in report.lower()
        assert "focused" in report.lower() or "subtask" in report.lower()
