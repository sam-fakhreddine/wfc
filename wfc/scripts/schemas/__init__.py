"""Schema validation for LLM output boundaries.

Provides runtime validation at the boundary where LLM responses are parsed
into structured data. Uses Pydantic v2 when available, falls back to stdlib.
"""

from .finding import REQUIRED_FINDING_KEYS, validate_finding
from .reviewer_response import validate_reviewer_response

__all__ = ["REQUIRED_FINDING_KEYS", "validate_finding", "validate_reviewer_response"]
