"""Reporter — Agent 5 of the CLAUDE.md remediation pipeline.

Synthesizes manifest, diagnosis, fixer output, and validation result into a
human-readable markdown report.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def _build_prompt(
    manifest: dict[str, Any],
    diagnosis: dict[str, Any],
    fixer_output: dict[str, Any],
    validation: dict[str, Any],
) -> str:
    return (
        f"<manifest>\n{json.dumps(manifest, indent=2)}\n</manifest>\n\n"
        f"<diagnosis>\n{json.dumps(diagnosis, indent=2)}\n</diagnosis>\n\n"
        f"<fixer_output>\n{json.dumps(fixer_output, indent=2)}\n</fixer_output>\n\n"
        f"<validation>\n{json.dumps(validation, indent=2)}\n</validation>\n\n"
        "Write the remediation report in the specified markdown format."
    )


def _rule_based_report(
    manifest: dict[str, Any],
    diagnosis: dict[str, Any],
    fixer_output: dict[str, Any],
    validation: dict[str, Any],
) -> str:
    """Generate a minimal report without an LLM."""
    grade = diagnosis.get("overall_grade", "?")
    verdict = validation.get("verdict", "UNKNOWN")
    bc = validation.get("budget_check", {})
    orig_lines = bc.get("original_lines", manifest.get("claude_md", {}).get("total_lines", "?"))
    new_lines = bc.get("rewritten_lines", "?")
    orig_inst = bc.get("original_instructions", "?")
    new_inst = bc.get("rewritten_instructions", "?")

    pct = ""
    if isinstance(orig_lines, int) and isinstance(new_lines, int) and orig_lines > 0:
        pct = f" ({round((orig_lines - new_lines) / orig_lines * 100)}% reduction)"

    changelog = fixer_output.get("changelog", [])
    migration = fixer_output.get("migration_plan", "")
    rewritten = fixer_output.get("rewritten_content", "")
    extracted = fixer_output.get("extracted_files", [])

    grade_after = "B" if verdict != "FAIL" else grade

    lines = [
        "## Summary",
        f"- Original: {orig_lines} lines, ~{orig_inst} instructions",
        f"- Rewritten: {new_lines} lines, ~{new_inst} instructions{pct}",
        f"- Budget status: {bc.get('budget_status', '?')}",
        f"- Grade: {grade} → {grade_after}",
        f"- Verdict: {verdict}",
        "",
        "## What Was Cut",
    ]
    cut_items = [c for c in changelog if "Removed" in c or "removed" in c][:5]
    for item in cut_items:
        lines.append(f"- {item}")
    if not cut_items:
        lines.append("- See changelog for details")

    lines += ["", "## What Was Extracted"]
    extracted_items = [c for c in changelog if "Extracted" in c or "extracted" in c][:5]
    for item in extracted_items:
        lines.append(f"- {item}")
    if not extracted_items:
        lines.append("- Nothing extracted (inline content removed or kept)")

    lines += ["", "## Migration Actions (Human Required)"]
    if migration:
        lines.append(migration)
    elif extracted:
        for i, f in enumerate(extracted, 1):
            lines.append(f"{i}. Create `{f['path']}` with extracted content (see below)")
    else:
        lines.append("No migration actions required.")

    if verdict == "FAIL":
        lines += ["", "---", "Rewrite failed validation. Original file preserved."]
    elif rewritten:
        lines += ["", "## Rewritten CLAUDE.md", "```markdown", rewritten, "```"]
        if extracted:
            lines += ["", "## Extracted Files"]
            for f in extracted:
                lines += [f"### `{f['path']}`", "```markdown", f["content"], "```"]

    return "\n".join(lines)


def report(
    manifest: dict[str, Any],
    diagnosis: dict[str, Any],
    fixer_output: dict[str, Any],
    validation: dict[str, Any],
    response_fn: Callable[[str], str] | None = None,
) -> str:
    """Run the Reporter agent. Returns a markdown string."""
    if response_fn is None:
        return _rule_based_report(manifest, diagnosis, fixer_output, validation)

    prompt = _build_prompt(manifest, diagnosis, fixer_output, validation)
    try:
        return response_fn(prompt)
    except Exception:
        logger.exception("Reporter LLM call failed; using rule-based report")
        return _rule_based_report(manifest, diagnosis, fixer_output, validation)
