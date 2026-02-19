"""Reviewer response schema validation at LLM output boundary.

Validates the task_response dict structure passed from the orchestrator
to ReviewerEngine.parse_results(). Uses Pydantic v2 when available,
falls back to stdlib validation.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


try:
    from pydantic import BaseModel, field_validator

    class ReviewerResponseSchema(BaseModel):
        """Pydantic v2 model for a reviewer task response."""

        reviewer_id: str
        response: str = ""

        @field_validator("reviewer_id")
        @classmethod
        def check_non_empty(cls, v: str) -> str:
            if not v.strip():
                raise ValueError("reviewer_id must be non-empty")
            return v

    _HAS_PYDANTIC = True

except ImportError:
    _HAS_PYDANTIC = False


def _validate_response_stdlib(data: dict[str, Any]) -> dict[str, Any] | None:
    """Validate a reviewer response dict using stdlib only."""
    if not isinstance(data, dict):
        return None
    if "reviewer_id" not in data:
        return None
    rid = data["reviewer_id"]
    if not isinstance(rid, str) or not rid.strip():
        return None
    return {
        "reviewer_id": rid,
        "response": str(data.get("response", "")),
    }


def validate_reviewer_response(data: dict[str, Any]) -> dict[str, Any] | None:
    """Validate a task_response dict at the LLM output boundary.

    Returns the validated dict or None if irrecoverably malformed. Never raises.
    """
    try:
        if _HAS_PYDANTIC:
            model = ReviewerResponseSchema.model_validate(data)  # type: ignore[name-defined]
            return model.model_dump()
        return _validate_response_stdlib(data)
    except Exception:
        logger.debug("Reviewer response validation failed for %r", data, exc_info=True)
        return None
