"""
Refusal Agent - Structured block responses for WFC hook system.

Fail-open: If the refusal agent itself fails, the caller falls back to
the original plain-text behavior.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from typing import Any

logger = logging.getLogger("wfc.security.refusal")


_SUGGESTION_MAP: dict[str, str] = {
    "eval-injection": (
        "Use ast.literal_eval() for safe evaluation, or restructure to avoid eval entirely."
    ),
    "os-system": ("Use subprocess.run() with a list of arguments (no shell=True) instead."),
    "subprocess-shell": (
        "Pass command as a list and remove shell=True: subprocess.run(['cmd', 'arg'])."
    ),
    "rm-rf-root": ("Use a safer path and double-check the target directory before deletion."),
    "rm-rf-home": ("Use a safer path and double-check the target directory before deletion."),
    "new-function": ("Use a regular function definition instead of new Function()."),
    "hardcoded-secret": ("Move secrets to environment variables or a .env file (gitignored)."),
}


def _generate_suggestion(reason: str, pattern_id: str, tool_name: str = "") -> str:
    """Return a remediation suggestion for *pattern_id*, falling back to a
    generic hint derived from *reason*."""
    if pattern_id and pattern_id in _SUGGESTION_MAP:
        return _SUGGESTION_MAP[pattern_id]
    if "security" in reason.lower():
        return "Review the flagged code for security implications. Consider safer alternatives."
    return "Review the blocked action and consider an alternative approach."


def format_block_response(
    reason: str,
    pattern_id: str = "",
    tool_name: str = "",
    suggestion: str = "",
) -> str:
    """Build a structured JSON block-response string.

    Returns a JSON string with keys: blocked, reason, suggestion, event_id,
    pattern_id.
    """
    event_id = str(uuid.uuid4())
    if not suggestion:
        suggestion = _generate_suggestion(reason, pattern_id, tool_name)
    return json.dumps(
        {
            "blocked": True,
            "reason": reason,
            "suggestion": suggestion,
            "event_id": event_id,
            "pattern_id": pattern_id,
        }
    )


def emit_and_exit(
    reason: str,
    pattern_id: str = "",
    tool_name: str = "",
    suggestion: str = "",
    extra_payload: dict[str, Any] | None = None,
) -> None:
    """Format, emit observability event, print to stderr, and ``sys.exit(2)``.

    Falls back to plain-text output on any internal error (fail-open).
    """
    try:
        response_json = format_block_response(
            reason=reason,
            pattern_id=pattern_id,
            tool_name=tool_name,
            suggestion=suggestion,
        )
        response_dict: dict[str, Any] = json.loads(response_json)

        try:
            from wfc.observability.instrument import (  # type: ignore[import-untyped]
                emit_event,
                incr,
            )

            payload: dict[str, Any] = {
                "reason": reason,
                "pattern_id": pattern_id,
                "tool_name": tool_name,
                "event_id": response_dict.get("event_id", ""),
                "suggestion": response_dict.get("suggestion", ""),
            }
            if extra_payload:
                payload.update(extra_payload)
            emit_event(
                "security.block",
                source="refusal_agent",
                payload=payload,
                level="warning",
            )
            incr("security.blocks", labels={"pattern_id": pattern_id or "unknown"})
        except Exception:
            pass

        print(response_json, file=sys.stderr)
    except Exception:
        logger.warning("Refusal agent failed, falling back to plain text")
        print(reason, file=sys.stderr)

    sys.exit(2)
