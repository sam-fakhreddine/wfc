"""refinement.py — Refinement stage: synthesise findings and propose SKILL.md rewrite."""

from __future__ import annotations

import re
import string
from pathlib import Path

from ..api_client import call_api
from ..report_writer import find_latest_stage_report, get_branch
from ..skill_reader import parse_frontmatter, read_full_body, resolve_repo_name

_STAGE = "refinement"

_HARDCODED_PROMPT = """\
Skill name: ${skill_name}

Full skill definition:
${skill_body}

Discovery findings:
${discovery_report}

Logic findings:
${logic_report}

Edge case findings:
${edge_case_report}

Diagnose: vague trigger descriptions, missing Not for: exclusions, overclaimed capabilities.

Trigger Clarity: N/10
Scope Accuracy: N/10
Step Clarity: N/10

Proposed rewrite:
```yaml
${skill_body}
```
"""


def _get_template_path() -> Path:
    """Resolve template path relative to this file (validator skill's own assets)."""
    return (
        Path(__file__).parents[4]
        / "skills"
        / "wfc-skill-validator-llm"
        / "assets"
        / "templates"
        / "refinement-prompt.txt"
    )


def _parse_sub_score(pattern: str, text: str) -> tuple[int, bool]:
    """Parse a sub-score from LLM response text.

    Returns:
        Tuple of (score clamped to [1, 10], found) where found is False if not present.
    """
    m = re.search(pattern, text)
    if m is None:
        return 5, False
    value = max(1, min(10, int(m.group(1))))
    return value, True


def run(skill_path: Path, offline: bool = False) -> str:
    """Run refinement validation for one skill.

    Args:
        skill_path: Path to the skill directory.
        offline: If True, return stub without API call or filesystem reads.

    Returns:
        Report content string with health score prepended.

    Raises:
        FileNotFoundError: If a prior stage report is not found on disk.
    """
    skill_md = skill_path / "SKILL.md"

    try:
        frontmatter = parse_frontmatter(skill_md)
        skill_name = frontmatter.get("name", skill_path.name)
    except ValueError:
        skill_name = skill_path.name

    if offline:
        return f"[OFFLINE STUB] refinement — {skill_name}"

    skill_body = read_full_body(skill_md)

    repo = resolve_repo_name()
    branch = get_branch()

    report_skill_name = skill_path.name
    prior_stages = ["discovery", "logic", "edge_case"]
    prior_texts: dict[str, str] = {}
    for stage in prior_stages:
        report_path = find_latest_stage_report(report_skill_name, stage, repo, branch)
        prior_texts[stage] = report_path.read_text(encoding="utf-8")

    template_path = _get_template_path()
    if template_path.exists():
        raw = template_path.read_text(encoding="utf-8")
    else:
        raw = _HARDCODED_PROMPT

    prompt = string.Template(raw).safe_substitute(
        skill_name=skill_name,
        skill_body=skill_body,
        discovery_report=prior_texts["discovery"],
        logic_report=prior_texts["logic"],
        edge_case_report=prior_texts["edge_case"],
    )

    response = call_api(prompt, use_thinking=False)

    warnings: list[str] = []

    trigger_clarity, tc_found = _parse_sub_score(r"Trigger Clarity:\s*(\d+)/10", response)
    if not tc_found:
        warnings.append("# Warning: sub-score Trigger Clarity not found, defaulting to 5\n")

    scope_accuracy, sa_found = _parse_sub_score(r"Scope Accuracy:\s*(\d+)/10", response)
    if not sa_found:
        warnings.append("# Warning: sub-score Scope Accuracy not found, defaulting to 5\n")

    step_clarity, sc_found = _parse_sub_score(r"Step Clarity:\s*(\d+)/10", response)
    if not sc_found:
        warnings.append("# Warning: sub-score Step Clarity not found, defaulting to 5\n")

    health_score = round(
        (0.4 * trigger_clarity) + (0.35 * scope_accuracy) + (0.25 * step_clarity), 1
    )

    fenced_block_match = re.search(r"```(?:yaml)?\s*\n(.*?)```", response, re.DOTALL)
    if fenced_block_match:
        block = fenced_block_match.group(1)
        name_match = re.search(r"^name:\s*(.+)$", block, re.MULTILINE)
        if name_match:
            proposed_name = name_match.group(1).strip()
            if proposed_name != skill_name:
                warnings.append(
                    "# Warning: proposed rewrite changes name field — review carefully\n"
                )

    warning_text = "".join(warnings)
    report = f"Health Score: {health_score:.1f} / 10\n\n{warning_text}{response}"
    return report
