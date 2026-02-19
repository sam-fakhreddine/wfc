"""Tests for wfc.scripts.schemas.llm_output -- LLM output boundary validation."""
from __future__ import annotations

import pytest




class TestValidateFinding:
    """Test single finding validation and coercion."""

    def test_valid_finding_passes(self):
        from wfc.scripts.schemas.llm_output import validate_finding

        finding = {
            "file": "app.py",
            "line_start": 10,
            "category": "security",
            "severity": 7.5,
            "description": "SQL injection risk",
        }
        result = validate_finding(finding)
        assert result is not None
        assert result["file"] == "app.py"
        assert result["severity"] == 7.5

    def test_coerces_string_severity_to_float(self):
        from wfc.scripts.schemas.llm_output import validate_finding

        finding = {
            "file": "app.py",
            "line_start": 10,
            "category": "bug",
            "severity": "8",
            "description": "issue",
        }
        result = validate_finding(finding)
        assert result is not None
        assert isinstance(result["severity"], float)
        assert result["severity"] == 8.0

    def test_coerces_string_line_start_to_int(self):
        from wfc.scripts.schemas.llm_output import validate_finding

        finding = {
            "file": "app.py",
            "line_start": "42",
            "category": "bug",
            "severity": 5,
            "description": "issue",
        }
        result = validate_finding(finding)
        assert result is not None
        assert isinstance(result["line_start"], int)
        assert result["line_start"] == 42

    def test_clamps_severity_above_10(self):
        from wfc.scripts.schemas.llm_output import validate_finding

        finding = {
            "file": "app.py",
            "line_start": 1,
            "category": "bug",
            "severity": 15.0,
            "description": "issue",
        }
        result = validate_finding(finding)
        assert result is not None
        assert result["severity"] == 10.0

    def test_clamps_severity_below_0(self):
        from wfc.scripts.schemas.llm_output import validate_finding

        finding = {
            "file": "app.py",
            "line_start": 1,
            "category": "bug",
            "severity": -3.0,
            "description": "issue",
        }
        result = validate_finding(finding)
        assert result is not None
        assert result["severity"] == 0.0

    def test_missing_file_returns_none(self):
        from wfc.scripts.schemas.llm_output import validate_finding

        finding = {
            "line_start": 10,
            "category": "bug",
            "severity": 5,
            "description": "issue",
        }
        assert validate_finding(finding) is None

    def test_missing_description_returns_none(self):
        from wfc.scripts.schemas.llm_output import validate_finding

        finding = {
            "file": "app.py",
            "line_start": 10,
            "category": "bug",
            "severity": 5,
        }
        assert validate_finding(finding) is None

    def test_empty_dict_returns_none(self):
        from wfc.scripts.schemas.llm_output import validate_finding

        assert validate_finding({}) is None

    def test_non_dict_returns_none(self):
        from wfc.scripts.schemas.llm_output import validate_finding

        assert validate_finding("not a dict") is None
        assert validate_finding(42) is None
        assert validate_finding(None) is None

    def test_defaults_line_start_to_0(self):
        from wfc.scripts.schemas.llm_output import validate_finding

        finding = {
            "file": "app.py",
            "category": "bug",
            "severity": 5,
            "description": "issue",
        }
        result = validate_finding(finding)
        assert result is not None
        assert result["line_start"] == 0

    def test_defaults_category_to_general(self):
        from wfc.scripts.schemas.llm_output import validate_finding

        finding = {
            "file": "app.py",
            "line_start": 1,
            "severity": 5,
            "description": "issue",
        }
        result = validate_finding(finding)
        assert result is not None
        assert result["category"] == "general"

    def test_defaults_confidence_to_5(self):
        from wfc.scripts.schemas.llm_output import validate_finding

        finding = {
            "file": "app.py",
            "line_start": 1,
            "category": "bug",
            "severity": 5,
            "description": "issue",
        }
        result = validate_finding(finding)
        assert result is not None
        assert result["confidence"] == 5.0

    def test_preserves_optional_fields(self):
        from wfc.scripts.schemas.llm_output import validate_finding

        finding = {
            "file": "app.py",
            "line_start": 10,
            "line_end": 20,
            "category": "security",
            "severity": 7,
            "confidence": 9,
            "description": "issue",
            "remediation": "fix it",
        }
        result = validate_finding(finding)
        assert result is not None
        assert result["line_end"] == 20
        assert result["confidence"] == 9.0
        assert result["remediation"] == "fix it"

    def test_non_numeric_severity_returns_none(self):
        from wfc.scripts.schemas.llm_output import validate_finding

        finding = {
            "file": "app.py",
            "line_start": 1,
            "category": "bug",
            "severity": "critical",
            "description": "issue",
        }
        assert validate_finding(finding) is None




class TestValidateFindings:
    """Test batch finding validation."""

    def test_filters_invalid_findings(self):
        from wfc.scripts.schemas.llm_output import validate_findings

        raw = [
            {"file": "a.py", "line_start": 1, "category": "bug", "severity": 5, "description": "ok"},
            {"invalid": True},
            {"file": "b.py", "line_start": 2, "category": "perf", "severity": 3, "description": "ok"},
        ]
        valid = validate_findings(raw)
        assert len(valid) == 2
        assert valid[0]["file"] == "a.py"
        assert valid[1]["file"] == "b.py"

    def test_empty_list_returns_empty(self):
        from wfc.scripts.schemas.llm_output import validate_findings

        assert validate_findings([]) == []

    def test_all_invalid_returns_empty(self):
        from wfc.scripts.schemas.llm_output import validate_findings

        raw = [{"bad": True}, {"also": "bad"}]
        assert validate_findings(raw) == []

    def test_non_list_returns_empty(self):
        from wfc.scripts.schemas.llm_output import validate_findings

        assert validate_findings("not a list") == []
        assert validate_findings(None) == []




class TestPydanticDetection:
    """Test that the module works with or without pydantic."""

    def test_has_pydantic_flag(self):
        from wfc.scripts.schemas.llm_output import HAS_PYDANTIC

        assert isinstance(HAS_PYDANTIC, bool)

    def test_validate_finding_works_regardless_of_pydantic(self):
        """Core validation must work whether pydantic is installed or not."""
        from wfc.scripts.schemas.llm_output import validate_finding

        finding = {
            "file": "app.py",
            "line_start": 1,
            "category": "bug",
            "severity": 5.0,
            "description": "test",
        }
        result = validate_finding(finding)
        assert result is not None
        assert result["file"] == "app.py"




class TestValidateReviewerOutput:
    """Test full reviewer output validation (score + summary + findings)."""

    def test_valid_output(self):
        from wfc.scripts.schemas.llm_output import validate_reviewer_output

        output = {
            "score": 8.5,
            "summary": "Looks good overall",
            "findings": [
                {"file": "a.py", "line_start": 1, "category": "style", "severity": 2, "description": "minor"}
            ],
        }
        result = validate_reviewer_output(output)
        assert result is not None
        assert result["score"] == 8.5
        assert result["summary"] == "Looks good overall"
        assert len(result["findings"]) == 1

    def test_coerces_score(self):
        from wfc.scripts.schemas.llm_output import validate_reviewer_output

        output = {"score": "9", "summary": "ok", "findings": []}
        result = validate_reviewer_output(output)
        assert result is not None
        assert result["score"] == 9.0

    def test_clamps_score(self):
        from wfc.scripts.schemas.llm_output import validate_reviewer_output

        output = {"score": 15, "summary": "ok", "findings": []}
        result = validate_reviewer_output(output)
        assert result is not None
        assert result["score"] == 10.0

    def test_defaults_when_missing(self):
        from wfc.scripts.schemas.llm_output import validate_reviewer_output

        result = validate_reviewer_output({})
        assert result is not None
        assert result["score"] == 0.0
        assert result["summary"] == ""
        assert result["findings"] == []

    def test_non_dict_returns_default(self):
        from wfc.scripts.schemas.llm_output import validate_reviewer_output

        result = validate_reviewer_output("garbage")
        assert result is not None
        assert result["score"] == 0.0

    def test_filters_invalid_findings_within_output(self):
        from wfc.scripts.schemas.llm_output import validate_reviewer_output

        output = {
            "score": 7,
            "summary": "issues found",
            "findings": [
                {"file": "a.py", "severity": 5, "description": "ok", "line_start": 1, "category": "bug"},
                {"garbage": True},
            ],
        }
        result = validate_reviewer_output(output)
        assert len(result["findings"]) == 1
