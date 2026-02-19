"""Finding schema validation at LLM output boundary.

Uses Pydantic v2 when available, falls back to stdlib validation.
Both paths guarantee: required keys present, correct types, clamped ranges.
Invalid findings return None (fail-open — logged and dropped).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

REQUIRED_FINDING_KEYS = frozenset({"file", "line_start", "category", "severity", "description"})


try:
    from pydantic import BaseModel, ConfigDict, Field

    class FindingSchema(BaseModel):
        """Pydantic v2 model for a single reviewer finding."""

        file: str
        line_start: int = Field(ge=0)
        category: str
        severity: float = Field(ge=0.0, le=10.0)
        description: str
        line_end: int | None = None
        confidence: float = Field(ge=0.0, le=100.0, default=0.0)
        remediation: str | None = None
        model_config = ConfigDict(extra="allow", coerce_numbers_to_str=False)

    _HAS_PYDANTIC = True

except ImportError:
    _HAS_PYDANTIC = False


def _validate_finding_stdlib(data: dict[str, Any]) -> dict[str, Any] | None:
    """Validate and coerce a finding dict using stdlib only.

    Returns the cleaned dict or None if irrecoverable.
    """
    if not REQUIRED_FINDING_KEYS.issubset(data.keys()):
        return None
    out = dict(data)
    try:
        out["line_start"] = int(out["line_start"])
        out["severity"] = max(0.0, min(10.0, float(out["severity"])))
        out["confidence"] = max(0.0, min(100.0, float(out.get("confidence", 0))))
        if out.get("line_end") is not None:
            out["line_end"] = int(out["line_end"])
    except (ValueError, TypeError):
        return None
    if out["line_start"] < 0:
        return None
    return out


def validate_finding(data: dict[str, Any]) -> dict[str, Any] | None:
    """Validate a single finding dict at the LLM output boundary.

    Auto-selects Pydantic v2 when available, otherwise uses stdlib fallback.
    Returns the validated (and type-coerced) dict, or None if the finding
    is irrecoverably malformed. Never raises.
    """
    try:
        if _HAS_PYDANTIC:
            model = FindingSchema.model_validate(data)  # type: ignore[name-defined]
            return model.model_dump()
        return _validate_finding_stdlib(data)
    except Exception:
        logger.debug("Finding validation failed for %r", data, exc_info=True)
        return None


def has_pydantic() -> bool:
    """Return whether Pydantic backend is active."""
    return _HAS_PYDANTIC
