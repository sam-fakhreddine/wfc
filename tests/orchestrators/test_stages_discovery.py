"""Tests for stages.discovery — adversarial routing gap detection stage."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from wfc.scripts.orchestrators.skill_validator_llm.stages.discovery import (
    _get_template_path,
    run,
)

VALID_SKILL_MD = """\
---
name: wfc-test-skill
description: A skill for testing routing gap detection.
triggers:
  - test routing
version: "1.0"
---

## Workflow
Step 1. Do something.
Step 2. Do something else.
"""


@pytest.fixture()
def skill_dir(tmp_path: Path) -> Path:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(VALID_SKILL_MD, encoding="utf-8")
    return tmp_path


def test_run_offline_returns_stub(skill_dir: Path) -> None:
    result = run(skill_dir, offline=True)
    assert result.startswith("[OFFLINE STUB")


def test_run_offline_no_api_call(skill_dir: Path) -> None:
    with mock.patch(
        "wfc.scripts.orchestrators.skill_validator_llm.stages.discovery.call_api"
    ) as mock_api:
        run(skill_dir, offline=True)
        mock_api.assert_not_called()


def test_run_calls_api_with_thinking(skill_dir: Path) -> None:
    with mock.patch(
        "wfc.scripts.orchestrators.skill_validator_llm.stages.discovery.call_api"
    ) as mock_api:
        mock_api.return_value = "mocked response"
        run(skill_dir, offline=False)
        assert mock_api.called
        assert mock_api.call_args.kwargs.get("use_thinking") is True


def test_run_reads_frontmatter_only(skill_dir: Path) -> None:
    """Discovery reads frontmatter (name + description), not the full body text."""
    with mock.patch(
        "wfc.scripts.orchestrators.skill_validator_llm.stages.discovery.call_api"
    ) as mock_api:
        mock_api.return_value = "mocked response"
        with mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.discovery.parse_frontmatter",
            wraps=__import__(
                "wfc.scripts.orchestrators.skill_validator_llm.skill_reader",
                fromlist=["parse_frontmatter"],
            ).parse_frontmatter,
        ) as mock_parse:
            run(skill_dir, offline=False)
            mock_parse.assert_called_once()


def test_template_path_resolves_to_real_file() -> None:
    """Template file must exist on disk — catches path calculation regressions."""
    template_path = _get_template_path()
    assert template_path.exists(), f"Template not found at: {template_path}"


def test_run_uses_template_when_present(skill_dir: Path) -> None:
    """Prompt passed to call_api must contain the skill name from frontmatter."""
    with mock.patch(
        "wfc.scripts.orchestrators.skill_validator_llm.stages.discovery.call_api"
    ) as mock_api:
        mock_api.return_value = "mocked response"
        run(skill_dir, offline=False)
        assert mock_api.called
        prompt_arg = mock_api.call_args.args[0]
        assert "wfc-test-skill" in prompt_arg


def test_run_offline_stub_contains_skill_name(skill_dir: Path) -> None:
    result = run(skill_dir, offline=True)
    assert "wfc-test-skill" in result


def test_run_returns_api_response(skill_dir: Path) -> None:
    with mock.patch(
        "wfc.scripts.orchestrators.skill_validator_llm.stages.discovery.call_api"
    ) as mock_api:
        mock_api.return_value = "## Positive Triggers\n- example"
        result = run(skill_dir, offline=False)
        assert result == "## Positive Triggers\n- example"
