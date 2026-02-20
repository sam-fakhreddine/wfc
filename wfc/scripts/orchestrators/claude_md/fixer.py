"""Fixer — Agent 3 of the CLAUDE.md remediation pipeline.

Takes the CLAUDE.md content, manifest, and diagnosis, then produces a rewritten
CLAUDE.md plus a migration plan. The primary operation is subtraction.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def _build_prompt(
    claude_md_content: str,
    manifest: dict[str, Any],
    diagnosis: dict[str, Any],
    revision_notes: str = "",
) -> str:
    parts = [
        f"<claude_md>\n{claude_md_content}\n</claude_md>",
        f"<manifest>\n{json.dumps(manifest, indent=2)}\n</manifest>",
        f"<diagnosis>\n{json.dumps(diagnosis, indent=2)}\n</diagnosis>",
    ]
    if revision_notes:
        parts.append(f"<revision_notes>\n{revision_notes}\n</revision_notes>")
    parts.append(
        "Rewrite this CLAUDE.md to fix the diagnosed issues. "
        "Primary goal: subtract content. Respond with JSON per the output format."
    )
    return "\n\n".join(parts)


def _fallback_trim(claude_md_content: str, diagnosis: dict[str, Any]) -> dict[str, Any]:
    """Minimal rule-based trim when LLM is unavailable."""
    original_lines = claude_md_content.splitlines()
    kept: list[str] = list(original_lines)
    rewritten = "\n".join(kept)
    total = len(original_lines)
    return {
        "rewritten_content": rewritten,
        "changelog": ["[FALLBACK] No LLM available — original content preserved unchanged"],
        "migration_plan": "Manual review required — LLM fixer was unavailable",
        "extracted_files": [],
        "metrics": {
            "original_lines": total,
            "rewritten_lines": len(kept),
            "original_instructions": diagnosis.get("instruction_budget_analysis", {}).get(
                "claude_md_instructions", 0
            ),
            "rewritten_instructions": diagnosis.get("instruction_budget_analysis", {}).get(
                "claude_md_instructions", 0
            ),
            "lines_removed": total - len(kept),
            "lines_extracted": 0,
            "hooks_recommended": 0,
            "slash_commands_recommended": 0,
            "subdirectory_files_created": 0,
        },
    }


def fix(
    claude_md_content: str,
    manifest: dict[str, Any],
    diagnosis: dict[str, Any],
    response_fn: Callable[[str], str] | None = None,
    revision_notes: str = "",
) -> dict[str, Any]:
    """Run the Fixer agent.

    Args:
        claude_md_content: Raw content of the CLAUDE.md file.
        manifest: Context Mapper output.
        diagnosis: Analyst output.
        response_fn: Callable that takes a prompt and returns a response.
        revision_notes: Optional QA feedback for retry pass.

    Returns:
        Fixer output dict with rewritten_content, changelog, migration_plan,
        extracted_files, and metrics.
    """
    if response_fn is None:
        logger.debug("No response_fn — using fallback trim")
        return _fallback_trim(claude_md_content, diagnosis)

    prompt = _build_prompt(claude_md_content, manifest, diagnosis, revision_notes)
    try:
        response = response_fn(prompt)
        result = _extract_json(response)
        if result and result.get("rewritten_content") is not None:
            return result
        logger.warning("Fixer returned unexpected response; using fallback")
    except Exception:
        logger.exception("Fixer LLM call failed; using fallback")

    return _fallback_trim(claude_md_content, diagnosis)
