"""logic.py — Logic stage: hallucination risk and ambiguous step detection."""

from __future__ import annotations

import string
from pathlib import Path

from ..api_client import call_api
from ..skill_reader import read_full_body

_STAGE = "logic"
_OFFLINE_STUB = (
    "[OFFLINE STUB — no API call made]\n\n"
    "# Logic: ${skill_name}\n\n"
    "Offline mode — no LLM call was made.\n"
)

_HARDCODED_PROMPT = """\
Skill name: ${skill_name}

Full skill definition:
${skill_body}

Simulate executing this skill and identify faults.

## Hallucination Risks
## Ambiguous Steps
## Missing Context
"""


def _get_template_path() -> Path:
    """Resolve template path relative to this file (validator skill's own assets)."""
    return (
        Path(__file__).parents[4]
        / "skills"
        / "wfc-skill-validator-llm"
        / "assets"
        / "templates"
        / "logic-prompt.txt"
    )


def run(skill_path: Path, offline: bool = False) -> str:
    """Run logic validation for one skill.

    Args:
        skill_path: Path to the skill directory.
        offline: If True, return stub without API call.

    Returns:
        Report content string.
    """
    skill_md = skill_path / "SKILL.md"
    skill_body = read_full_body(skill_md)

    from ..skill_reader import parse_frontmatter

    try:
        frontmatter = parse_frontmatter(skill_md)
        skill_name = frontmatter.get("name", skill_path.name)
    except ValueError:
        skill_name = skill_path.name

    if offline:
        return string.Template(_OFFLINE_STUB).safe_substitute(skill_name=skill_name)

    template_path = _get_template_path()
    if template_path.exists():
        raw = template_path.read_text(encoding="utf-8")
        prompt = string.Template(raw).safe_substitute(skill_name=skill_name, skill_body=skill_body)
    else:
        prompt = string.Template(_HARDCODED_PROMPT).safe_substitute(
            skill_name=skill_name, skill_body=skill_body
        )

    return call_api(prompt, use_thinking=False)
