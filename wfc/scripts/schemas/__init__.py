"""Schema validation for LLM output boundaries.

Provides Pydantic-based validation when available, with pure-Python fallback.
All validation is fail-open: never raises, returns None or defaults on error.
"""

from __future__ import annotations
