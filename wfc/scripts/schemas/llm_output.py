"""LLM output boundary validation for WFC review findings.

Uses Pydantic v2 when available for schema validation with coercion.
Falls back to pure-Python validation with identical semantics when Pydantic
is not installed. All functions are fail-open: they never raise exceptions,
returning None or safe defaults on invalid input.

Exported API:
    - HAS_PYDANTIC: bool -- whether pydantic is available
    - validate_finding(raw) -> dict | None
    - validate_findings(raw) -> list[dict]
    - validate_reviewer_output(raw) -> dict
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


HAS_PYDANTIC: bool = False

try:
    from pydantic import BaseModel, ValidationError, field_validator

    HAS_PYDANTIC = True
except ImportError:
    pass


def _to_float(value: Any, default: float = 0.0) -> float | None:
    """Coerce a value to float. Returns None if not convertible."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any, default: int = 0) -> int | None:
    """Coerce a value to int. Returns None if not convertible."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, lo: float = 0.0, hi: float = 10.0) -> float:
    """Clamp a float between lo and hi."""
    return max(lo, min(hi, value))


if HAS_PYDANTIC:

    class FindingModel(BaseModel):
        """Schema for a single review finding from LLM output."""

        model_config = {"extra": "ignore", "coerce_numbers_to_str": False}

        file: str
        description: str
        line_start: int = 0
        line_end: int | None = None
        category: str = "general"
        severity: float = 0.0
        confidence: float = 5.0
        remediation: str | None = None

        @field_validator("severity", mode="before")
        @classmethod
        def coerce_severity(cls, v: Any) -> float:
            result = _to_float(v)
            if result is None:
                raise ValueError(f"Cannot convert severity to float: {v!r}")
            return _clamp(result)

        @field_validator("confidence", mode="before")
        @classmethod
        def coerce_confidence(cls, v: Any) -> float:
            result = _to_float(v, default=5.0)
            if result is None:
                raise ValueError(f"Cannot convert confidence to float: {v!r}")
            return _clamp(result)

        @field_validator("line_start", mode="before")
        @classmethod
        def coerce_line_start(cls, v: Any) -> int:
            result = _to_int(v, default=0)
            if result is None:
                raise ValueError(f"Cannot convert line_start to int: {v!r}")
            return result

        @field_validator("line_end", mode="before")
        @classmethod
        def coerce_line_end(cls, v: Any) -> int | None:
            if v is None:
                return None
            result = _to_int(v)
            if result is None:
                raise ValueError(f"Cannot convert line_end to int: {v!r}")
            return result

        def to_dict(self) -> dict:
            """Convert to plain dict, omitting None optional fields."""
            d: dict[str, Any] = {
                "file": self.file,
                "description": self.description,
                "line_start": self.line_start,
                "category": self.category,
                "severity": self.severity,
                "confidence": self.confidence,
            }
            if self.line_end is not None:
                d["line_end"] = self.line_end
            if self.remediation is not None:
                d["remediation"] = self.remediation
            return d


def _validate_finding_pure(raw: Any) -> dict | None:
    """Validate a single finding using pure Python. Returns dict or None."""
    if not isinstance(raw, dict):
        return None

    file_val = raw.get("file")
    desc_val = raw.get("description")
    if not file_val or not isinstance(file_val, str):
        return None
    if not desc_val or not isinstance(desc_val, str):
        return None

    severity_raw = raw.get("severity", 0.0)
    severity = _to_float(severity_raw)
    if severity is None:
        return None
    severity = _clamp(severity)

    line_start_raw = raw.get("line_start", 0)
    line_start = _to_int(line_start_raw)
    if line_start is None:
        return None

    category = raw.get("category", "general")
    if not isinstance(category, str):
        category = "general"

    confidence_raw = raw.get("confidence", 5.0)
    confidence = _to_float(confidence_raw, default=5.0)
    if confidence is None:
        confidence = 5.0
    confidence = _clamp(confidence)

    result: dict[str, Any] = {
        "file": file_val,
        "description": desc_val,
        "line_start": line_start,
        "category": category,
        "severity": severity,
        "confidence": confidence,
    }

    line_end_raw = raw.get("line_end")
    if line_end_raw is not None:
        line_end = _to_int(line_end_raw)
        if line_end is not None:
            result["line_end"] = line_end

    remediation = raw.get("remediation")
    if remediation is not None and isinstance(remediation, str):
        result["remediation"] = remediation

    return result


def validate_finding(raw: Any) -> dict | None:
    """Validate and coerce a single LLM finding dict.

    Returns a validated dict with proper types and clamped values,
    or None if the input is invalid or missing required fields.

    Uses Pydantic when available, pure-Python otherwise.
    Both paths produce identical output.

    This function is fail-open: it never raises.
    """
    try:
        if not isinstance(raw, dict):
            return None

        if HAS_PYDANTIC:
            try:
                model = FindingModel(**raw)
                return model.to_dict()
            except (ValidationError, Exception):
                return None
        else:
            return _validate_finding_pure(raw)
    except Exception:
        logger.debug("Unexpected error validating finding", exc_info=True)
        return None


def validate_findings(raw: Any) -> list[dict]:
    """Validate a list of findings, filtering out invalid ones.

    Returns a list of validated finding dicts. Invalid entries are silently
    dropped. Non-list input returns an empty list.

    This function is fail-open: it never raises.
    """
    try:
        if not isinstance(raw, list):
            return []

        results: list[dict] = []
        for item in raw:
            validated = validate_finding(item)
            if validated is not None:
                results.append(validated)
        return results
    except Exception:
        logger.debug("Unexpected error validating findings list", exc_info=True)
        return []


def validate_reviewer_output(raw: Any) -> dict:
    """Validate a full reviewer output (score + summary + findings).

    Always returns a dict with at least {score, summary, findings}.
    Invalid or missing fields get safe defaults.

    This function is fail-open: it never raises.
    """
    default: dict[str, Any] = {
        "score": 0.0,
        "summary": "",
        "findings": [],
    }

    try:
        if not isinstance(raw, dict):
            return default

        score_raw = raw.get("score", 0.0)
        score = _to_float(score_raw, default=0.0)
        if score is None:
            score = 0.0
        score = _clamp(score)

        summary = raw.get("summary", "")
        if not isinstance(summary, str):
            summary = ""

        findings_raw = raw.get("findings", [])
        findings = validate_findings(findings_raw)

        return {
            "score": score,
            "summary": summary,
            "findings": findings,
        }
    except Exception:
        logger.debug("Unexpected error validating reviewer output", exc_info=True)
        return default
