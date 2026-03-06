"""Analyst — Agent 2 of the CLAUDE.md remediation pipeline.

Takes the CLAUDE.md content and the Context Mapper manifest, then produces a
structured Diagnosis. In production this calls a Claude LLM; in test mode it
accepts injected responses via the `response_fn` parameter.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable

logger = logging.getLogger(__name__)

_SCORE_KEYS = [
    "LINE_COUNT",
    "INSTRUCTION_COUNT",
    "UNIVERSAL_APPLICABILITY",
    "TOKEN_DENSITY",
    "WHY_COVERAGE",
    "WHAT_COVERAGE",
    "HOW_COVERAGE",
    "COMMAND_ACCURACY",
    "PROGRESSIVE_DISCLOSURE",
    "LINTER_DUPLICATION",
    "HOOK_CANDIDATES",
    "SLASH_COMMAND_CANDIDATES",
    "SUBDIRECTORY_CANDIDATES",
    "SECTION_ORGANIZATION",
    "SCANNABILITY",
    "CONSISTENCY",
]


def _extract_json(text: str) -> dict[str, Any]:
    """Extract first JSON object from a text response. Never raises."""
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def _build_prompt(claude_md_content: str, manifest: dict[str, Any]) -> str:
    return (
        f"<claude_md>\n{claude_md_content}\n</claude_md>\n\n"
        f"<manifest>\n{json.dumps(manifest, indent=2)}\n</manifest>\n\n"
        "Analyze this CLAUDE.md against the diagnostic rubric and respond with JSON."
    )


def _fallback_diagnosis(manifest: dict[str, Any]) -> dict[str, Any]:
    """Rule-based fallback when LLM is unavailable."""
    total_lines = manifest.get("claude_md", {}).get("total_lines", 0)
    instruction_count = manifest.get("claude_md", {}).get("instruction_count", 0)
    red_flags = manifest.get("red_flags", [])

    if total_lines > 300 or instruction_count > 100:
        grade = "D"
    elif total_lines > 200 or instruction_count > 80:
        grade = "C"
    elif red_flags:
        grade = "C"
    else:
        grade = "B"

    issues = []
    if total_lines > 300:
        issues.append(
            {
                "id": "CMD-001",
                "dimension": "economy",
                "category": "LINE_COUNT",
                "severity": "critical",
                "description": f"CLAUDE.md is {total_lines} lines — exceeds 300-line threshold",
                "impact": "Relevance filter likely suppressing critical content",
                "fix_directive": "Remove inline reference material; extract to docs/",
                "migration_target": "extract_to_doc",
            }
        )
    if instruction_count > 80:
        issues.append(
            {
                "id": "CMD-002",
                "dimension": "economy",
                "category": "INSTRUCTION_COUNT",
                "severity": "major" if instruction_count <= 100 else "critical",
                "description": f"~{instruction_count} instructions — approaching/exceeding budget",
                "impact": "Claude ignores instructions when budget is exhausted",
                "fix_directive": "Remove non-universal instructions; move to slash commands",
                "migration_target": "convert_to_slash_command",
            }
        )

    budget_status = (
        "overdrawn" if instruction_count > 100 else "tight" if instruction_count > 80 else "healthy"
    )

    scores = {k: {"score": 2, "evidence": "Estimated from heuristics"} for k in _SCORE_KEYS}
    if total_lines > 300:
        scores["LINE_COUNT"] = {"score": 1, "evidence": f"{total_lines} lines exceeds threshold"}
    if instruction_count > 80:
        scores["INSTRUCTION_COUNT"] = {"score": 1, "evidence": f"~{instruction_count} instructions"}

    return {
        "scores": scores,
        "dimension_summaries": {
            "economy": {
                "avg_score": 1.5 if total_lines > 300 else 2.0,
                "summary": "Heuristic estimate",
            },
            "content_quality": {"avg_score": 2.0, "summary": "Heuristic estimate"},
            "separation_of_concerns": {"avg_score": 2.0, "summary": "Heuristic estimate"},
            "structural_clarity": {"avg_score": 2.0, "summary": "Heuristic estimate"},
        },
        "issues": issues,
        "instruction_budget_analysis": {
            "estimated_claude_code_system_instructions": 50,
            "claude_md_instructions": instruction_count,
            "total_estimated": 50 + instruction_count,
            "budget_remaining": max(0, 150 - 50 - instruction_count),
            "budget_status": budget_status,
        },
        "overall_grade": grade,
        "rewrite_recommended": grade in ("C", "D", "F"),
        "rewrite_scope": "full" if grade in ("D", "F") else "trim_only",
    }


def analyze(
    claude_md_content: str,
    manifest: dict[str, Any],
    response_fn: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    """Run the Analyst agent.

    Args:
        claude_md_content: Raw content of the CLAUDE.md file.
        manifest: Output from context_mapper.map_project().
        response_fn: Callable that takes a prompt string and returns a response string.
                     If None, falls back to heuristic analysis.

    Returns:
        Diagnosis dict matching the Analyst output schema.
    """
    if response_fn is None:
        logger.debug("No response_fn provided — using heuristic fallback")
        return _fallback_diagnosis(manifest)

    prompt = _build_prompt(claude_md_content, manifest)
    try:
        response = response_fn(prompt)
        diagnosis = _extract_json(response)
        if diagnosis:
            return diagnosis
        logger.warning("Analyst returned non-JSON response; using heuristic fallback")
    except Exception:
        logger.exception("Analyst LLM call failed; using heuristic fallback")

    return _fallback_diagnosis(manifest)
