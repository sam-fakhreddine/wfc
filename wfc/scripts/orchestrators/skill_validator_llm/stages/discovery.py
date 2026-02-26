"""discovery.py — Discovery stage: adversarial routing gap detection."""

from __future__ import annotations

import string
from pathlib import Path

from ..api_client import call_api
from ..skill_reader import parse_frontmatter

_STAGE = "discovery"
_OFFLINE_STUB = (
    "[OFFLINE STUB — no API call made]\n\n"
    "# Discovery: ${skill_name}\n\n"
    "Offline mode — no LLM call was made.\n"
)

_HARDCODED_PROMPT = """\
name: ${skill_name}
description: ${description}

Find routing gaps and ambiguity in the above skill description.

## Positive Triggers
## Negative Triggers
## Critique
## Suggested Rewrite
"""


def _get_template_path() -> Path:
    """Resolve template path relative to this file (validator skill's own assets)."""
    return (
        Path(__file__).parents[4]
        / "skills"
        / "wfc-skill-validator-llm"
        / "assets"
        / "templates"
        / "discovery-prompt.txt"
    )


def run(skill_path: Path, offline: bool = False) -> str:
    """Run discovery validation for one skill.

    Args:
        skill_path: Path to the skill directory.
        offline: If True, return stub without API call.

    Returns:
        Report content string.
    """
    frontmatter = parse_frontmatter(skill_path / "SKILL.md")
    skill_name = frontmatter.get("name", skill_path.name)
    description = frontmatter.get("description", "")

    if offline:
        return string.Template(_OFFLINE_STUB).safe_substitute(skill_name=skill_name)

    template_path = _get_template_path()
    if template_path.exists():
        raw = template_path.read_text(encoding="utf-8")
        prompt = string.Template(raw).safe_substitute(
            skill_name=skill_name, description=description
        )
    else:
        prompt = string.Template(_HARDCODED_PROMPT).safe_substitute(
            skill_name=skill_name, description=description
        )

    return call_api(prompt, use_thinking=True)
