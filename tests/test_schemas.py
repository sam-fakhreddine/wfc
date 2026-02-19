"""Tests for wfc.scripts.schemas — finding and reviewer_response validation."""

from __future__ import annotations

import math

import pytest


class TestValidateFinding:
    """Tests for validate_finding() — both Pydantic and stdlib paths."""

    def test_valid_finding_returns_dict(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": 10,
            "category": "security",
            "severity": 7.5,
            "description": "SQL injection risk",
        }
        result = validate_finding(data)
        assert result is not None
        assert result["file"] == "main.py"
        assert result["line_start"] == 10
        assert result["severity"] == 7.5

    def test_missing_required_key_returns_none(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": 10,
        }
        assert validate_finding(data) is None

    def test_string_line_start_coerced_to_int(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": "5",
            "category": "bug",
            "severity": 3.0,
            "description": "off by one",
        }
        result = validate_finding(data)
        assert result is not None
        assert result["line_start"] == 5
        assert isinstance(result["line_start"], int)

    def test_string_severity_coerced_to_float(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": 1,
            "category": "bug",
            "severity": "6.5",
            "description": "issue",
        }
        result = validate_finding(data)
        assert result is not None
        assert result["severity"] == pytest.approx(6.5)

    def test_severity_clamped_to_10(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": 1,
            "category": "bug",
            "severity": 15.0,
            "description": "issue",
        }
        result = validate_finding(data)
        if result is not None:
            assert result["severity"] <= 10.0

    def test_severity_clamped_to_0(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": 1,
            "category": "bug",
            "severity": -2.0,
            "description": "issue",
        }
        result = validate_finding(data)
        if result is not None:
            assert result["severity"] >= 0.0

    def test_extra_fields_preserved(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": 1,
            "category": "bug",
            "severity": 5.0,
            "description": "issue",
            "custom_field": "extra_data",
        }
        result = validate_finding(data)
        assert result is not None
        assert result.get("custom_field") == "extra_data"

    def test_optional_fields_default(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": 1,
            "category": "bug",
            "severity": 5.0,
            "description": "issue",
        }
        result = validate_finding(data)
        assert result is not None
        assert result.get("confidence") == pytest.approx(0.0)

    def test_line_end_coerced(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": 1,
            "category": "bug",
            "severity": 5.0,
            "description": "issue",
            "line_end": "10",
        }
        result = validate_finding(data)
        assert result is not None
        assert result["line_end"] == 10

    def test_unconvertible_line_start_returns_none(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": "abc",
            "category": "bug",
            "severity": 5.0,
            "description": "issue",
        }
        assert validate_finding(data) is None

    def test_unconvertible_severity_returns_none(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": 1,
            "category": "bug",
            "severity": "high",
            "description": "issue",
        }
        assert validate_finding(data) is None

    def test_negative_line_start_returns_none(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": -1,
            "category": "bug",
            "severity": 5.0,
            "description": "issue",
        }
        assert validate_finding(data) is None

    def test_nan_severity_returns_none(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": 1,
            "category": "bug",
            "severity": float("nan"),
            "description": "issue",
        }
        assert validate_finding(data) is None

    def test_inf_severity_returns_none(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": 1,
            "category": "bug",
            "severity": float("inf"),
            "description": "issue",
        }
        assert validate_finding(data) is None

    def test_nan_confidence_returns_none(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": 1,
            "category": "bug",
            "severity": 5.0,
            "description": "issue",
            "confidence": float("nan"),
        }
        assert validate_finding(data) is None

    def test_non_string_file_returns_none(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": 123,
            "line_start": 1,
            "category": "bug",
            "severity": 5.0,
            "description": "issue",
        }
        assert validate_finding(data) is None

    def test_non_string_category_returns_none(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": 1,
            "category": 42,
            "severity": 5.0,
            "description": "issue",
        }
        assert validate_finding(data) is None

    def test_line_end_none_excluded_from_output(self) -> None:
        """When line_end is not provided, it should not appear in output."""
        from wfc.scripts.schemas.finding import validate_finding

        data = {
            "file": "main.py",
            "line_start": 1,
            "category": "bug",
            "severity": 5.0,
            "description": "issue",
        }
        result = validate_finding(data)
        assert result is not None
        assert "line_end" not in result

    def test_never_raises(self) -> None:
        from wfc.scripts.schemas.finding import validate_finding

        assert validate_finding(None) is None  # type: ignore[arg-type]
        assert validate_finding("not a dict") is None  # type: ignore[arg-type]
        assert validate_finding(42) is None  # type: ignore[arg-type]


class TestValidateReviewerResponse:
    """Tests for validate_reviewer_response()."""

    def test_valid_response(self) -> None:
        from wfc.scripts.schemas.reviewer_response import validate_reviewer_response

        data = {"reviewer_id": "security", "response": "Found 3 issues"}
        result = validate_reviewer_response(data)
        assert result is not None
        assert result["reviewer_id"] == "security"
        assert result["response"] == "Found 3 issues"

    def test_missing_reviewer_id_returns_none(self) -> None:
        from wfc.scripts.schemas.reviewer_response import validate_reviewer_response

        assert validate_reviewer_response({"response": "text"}) is None

    def test_empty_reviewer_id_returns_none(self) -> None:
        from wfc.scripts.schemas.reviewer_response import validate_reviewer_response

        assert validate_reviewer_response({"reviewer_id": "", "response": "text"}) is None

    def test_whitespace_reviewer_id_returns_none(self) -> None:
        from wfc.scripts.schemas.reviewer_response import validate_reviewer_response

        assert validate_reviewer_response({"reviewer_id": "   ", "response": "text"}) is None

    def test_missing_response_defaults_empty(self) -> None:
        from wfc.scripts.schemas.reviewer_response import validate_reviewer_response

        result = validate_reviewer_response({"reviewer_id": "security"})
        assert result is not None
        assert result["response"] == ""

    def test_non_dict_returns_none(self) -> None:
        from wfc.scripts.schemas.reviewer_response import validate_reviewer_response

        assert validate_reviewer_response("not a dict") is None  # type: ignore[arg-type]
        assert validate_reviewer_response(None) is None  # type: ignore[arg-type]

    def test_never_raises(self) -> None:
        from wfc.scripts.schemas.reviewer_response import validate_reviewer_response

        assert validate_reviewer_response(42) is None  # type: ignore[arg-type]


class TestRequiredFindingKeys:
    """Tests for the shared REQUIRED_FINDING_KEYS constant."""

    def test_keys_match_expected(self) -> None:
        from wfc.scripts.schemas.finding import REQUIRED_FINDING_KEYS

        assert REQUIRED_FINDING_KEYS == frozenset(
            {"file", "line_start", "category", "severity", "description"}
        )

    def test_is_frozenset(self) -> None:
        from wfc.scripts.schemas.finding import REQUIRED_FINDING_KEYS

        assert isinstance(REQUIRED_FINDING_KEYS, frozenset)


class TestHasPydantic:
    """Test backend detection."""

    def test_has_pydantic_returns_bool(self) -> None:
        from wfc.scripts.schemas.finding import has_pydantic

        assert isinstance(has_pydantic(), bool)


class TestStdlibFallback:
    """Directly test the stdlib validation path."""

    def test_valid_data(self) -> None:
        from wfc.scripts.schemas.finding import _validate_finding_stdlib

        data = {
            "file": "x.py",
            "line_start": 1,
            "category": "bug",
            "severity": 5.0,
            "description": "test",
        }
        result = _validate_finding_stdlib(data)
        assert result is not None
        assert result["severity"] == 5.0

    def test_clamps_severity_high(self) -> None:
        from wfc.scripts.schemas.finding import _validate_finding_stdlib

        data = {
            "file": "x.py",
            "line_start": 1,
            "category": "bug",
            "severity": 99.0,
            "description": "test",
        }
        result = _validate_finding_stdlib(data)
        assert result is not None
        assert result["severity"] == 10.0

    def test_clamps_severity_low(self) -> None:
        from wfc.scripts.schemas.finding import _validate_finding_stdlib

        data = {
            "file": "x.py",
            "line_start": 1,
            "category": "bug",
            "severity": -5.0,
            "description": "test",
        }
        result = _validate_finding_stdlib(data)
        assert result is not None
        assert result["severity"] == 0.0

    def test_does_not_mutate_input(self) -> None:
        from wfc.scripts.schemas.finding import _validate_finding_stdlib

        data = {
            "file": "x.py",
            "line_start": "3",
            "category": "bug",
            "severity": "5.0",
            "description": "test",
        }
        original_line_start = data["line_start"]
        _validate_finding_stdlib(data)
        assert data["line_start"] == original_line_start

    def test_nan_severity_returns_none(self) -> None:
        from wfc.scripts.schemas.finding import _validate_finding_stdlib

        data = {
            "file": "x.py",
            "line_start": 1,
            "category": "bug",
            "severity": float("nan"),
            "description": "test",
        }
        assert _validate_finding_stdlib(data) is None

    def test_inf_confidence_returns_none(self) -> None:
        from wfc.scripts.schemas.finding import _validate_finding_stdlib

        data = {
            "file": "x.py",
            "line_start": 1,
            "category": "bug",
            "severity": 5.0,
            "description": "test",
            "confidence": float("inf"),
        }
        assert _validate_finding_stdlib(data) is None

    def test_non_string_file_returns_none(self) -> None:
        from wfc.scripts.schemas.finding import _validate_finding_stdlib

        data = {
            "file": 999,
            "line_start": 1,
            "category": "bug",
            "severity": 5.0,
            "description": "test",
        }
        assert _validate_finding_stdlib(data) is None
