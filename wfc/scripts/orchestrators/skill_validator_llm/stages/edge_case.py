"""edge_case.py — Edge case stage: boundary condition and robustness stress-testing."""

from __future__ import annotations

import string
from pathlib import Path

from ..api_client import call_api
from ..skill_reader import parse_frontmatter, read_full_body

_STAGE = "edge_case"
_OFFLINE_STUB = (
    "[OFFLINE STUB — no API call made]\n\n"
    "# Edge Case: {skill_name}\n\n"
    "Offline mode — no LLM call was made.\n"
)

_HARDCODED_PROMPT = """\
Skill name: {skill_name}

Full skill definition:
{skill_body}

Stress-test this skill for boundary conditions and edge cases.

## Edge Cases

### Example edge case
**Severity**: HIGH | MEDIUM | LOW
**Trigger**: [The specific input or condition]
**What breaks**: [Routing failure / execution failure / degraded output / silent error]
**Recommendation**: [How the skill definition should handle this]
"""


def _get_template_path() -> Path:
    """Resolve template path relative to this file (validator skill's own assets)."""
    return (
        Path(__file__).parents[4]
        / "skills"
        / "wfc-skill-validator-llm"
        / "assets"
        / "templates"
        / "edge-case-prompt.txt"
    )


def run(skill_path: Path, offline: bool = False) -> str:
    """Run edge case validation for one skill.

    Args:
        skill_path: Path to the skill directory.
        offline: If True, return stub without API call.

    Returns:
        Report content string.
    """
    skill_md = skill_path / "SKILL.md"
    skill_body = read_full_body(skill_md)

    try:
        frontmatter = parse_frontmatter(skill_md)
        skill_name = frontmatter.get("name", skill_path.name)
    except ValueError:
        skill_name = skill_path.name

    if offline:
        return _OFFLINE_STUB.format(skill_name=skill_name)

    template_path = _get_template_path()
    if template_path.exists():
        raw = template_path.read_text(encoding="utf-8")
        prompt = string.Template(raw).safe_substitute(skill_name=skill_name, skill_body=skill_body)
    else:
        prompt = _HARDCODED_PROMPT.format(skill_name=skill_name, skill_body=skill_body)

    return call_api(prompt, use_thinking=False)
