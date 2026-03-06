"""QA Validator — Agent 4 of the CLAUDE.md remediation pipeline.

Validates the Fixer's rewrite against budget, content integrity, and intent
preservation constraints. Adversarial: bias toward finding problems.
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


def _rule_based_validate(
    original: str,
    manifest: dict[str, Any],
    diagnosis: dict[str, Any],
    fixer_output: dict[str, Any],
) -> dict[str, Any]:
    """Rule-based validation (no LLM required)."""
    rewritten = fixer_output.get("rewritten_content") or original
    orig_lines = len(original.splitlines())
    new_lines = len(rewritten.splitlines())
    orig_instructions = diagnosis.get("instruction_budget_analysis", {}).get(
        "claude_md_instructions", 0
    )
    new_instructions = fixer_output.get("metrics", {}).get(
        "rewritten_instructions", orig_instructions
    )

    regressions = []
    if new_lines > orig_lines:
        regressions.append(
            {
                "description": f"Rewritten file is longer ({new_lines} vs {orig_lines} lines)",
                "severity": "major",
            }
        )
    if new_lines > 300:
        regressions.append(
            {
                "description": f"Rewritten file still exceeds 300 lines ({new_lines})",
                "severity": "critical",
            }
        )
    if new_instructions > orig_instructions:
        regressions.append(
            {
                "description": "Rewritten file has more instructions than original",
                "severity": "critical",
            }
        )

    valid_cmds = {
        c["command"]
        for c in manifest.get("cross_reference", {}).get("commands_valid", [])
        if c.get("exists")
    }
    stale = []
    for match in re.finditer(r"`([a-z][a-z0-9 _\-./]+)`", rewritten):
        cmd = match.group(1)
        if len(cmd.split()) > 1 and cmd not in valid_cmds:
            stale.append(cmd)

    budget_improved = new_lines < orig_lines or new_instructions < orig_instructions
    budget_status = "improved" if budget_improved else "unchanged"

    total_issues = len(
        [i for i in diagnosis.get("issues", []) if i.get("severity") in ("critical", "major")]
    )
    changelog = fixer_output.get("changelog", [])
    resolved = sum(1 for i in diagnosis.get("issues", []) if any(i["id"] in c for c in changelog))

    verdict = "PASS"
    recommendation = "ship"
    revision_notes = ""

    if regressions:
        critical_regs = [r for r in regressions if r["severity"] == "critical"]
        if critical_regs:
            verdict = "FAIL"
            recommendation = "revise"
            revision_notes = "; ".join(r["description"] for r in critical_regs)
        else:
            verdict = "PASS_WITH_NOTES"

    return {
        "verdict": verdict,
        "budget_check": {
            "original_lines": orig_lines,
            "rewritten_lines": new_lines,
            "original_instructions": orig_instructions,
            "rewritten_instructions": new_instructions,
            "budget_status": budget_status,
        },
        "content_integrity": {
            "stale_commands": stale[:5],
            "stale_paths": [],
            "contradictions": [],
        },
        "intent_preserved": True,
        "lost_content_without_destination": [],
        "issues_resolved": {
            "total_critical_major": total_issues,
            "resolved": resolved,
            "unresolved": [
                i["id"]
                for i in diagnosis.get("issues", [])
                if i.get("severity") in ("critical", "major")
                and not any(i["id"] in c for c in changelog)
            ],
        },
        "separation_violations": [],
        "migration_plan_issues": [],
        "regressions": regressions,
        "final_recommendation": recommendation,
        "revision_notes": revision_notes,
    }


def _build_prompt(
    original: str,
    manifest: dict[str, Any],
    diagnosis: dict[str, Any],
    fixer_output: dict[str, Any],
) -> str:
    return (
        f"<original>\n{original}\n</original>\n\n"
        f"<manifest>\n{json.dumps(manifest, indent=2)}\n</manifest>\n\n"
        f"<diagnosis>\n{json.dumps(diagnosis, indent=2)}\n</diagnosis>\n\n"
        f"<rewrite>\n{json.dumps(fixer_output, indent=2)}\n</rewrite>\n\n"
        "Validate this rewrite. Be adversarial. Respond with JSON."
    )


def validate(
    original_content: str,
    manifest: dict[str, Any],
    diagnosis: dict[str, Any],
    fixer_output: dict[str, Any],
    response_fn: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    """Run the QA Validator agent."""
    rule_result = _rule_based_validate(original_content, manifest, diagnosis, fixer_output)

    if response_fn is None:
        return rule_result

    prompt = _build_prompt(original_content, manifest, diagnosis, fixer_output)
    try:
        response = response_fn(prompt)
        llm_result = _extract_json(response)
        if llm_result and "verdict" in llm_result:
            verdict_rank = {"PASS": 0, "PASS_WITH_NOTES": 1, "FAIL": 2}
            llm_rank = verdict_rank.get(llm_result.get("verdict", "PASS"), 0)
            rule_rank = verdict_rank.get(rule_result["verdict"], 0)
            if rule_rank > llm_rank:
                llm_result["verdict"] = rule_result["verdict"]
                llm_result["final_recommendation"] = rule_result["final_recommendation"]
                llm_result["revision_notes"] = (
                    llm_result.get("revision_notes", "")
                    + " "
                    + rule_result.get("revision_notes", "")
                ).strip()
            return llm_result
    except Exception:
        logger.exception("QA Validator LLM call failed; using rule-based result")

    return rule_result
