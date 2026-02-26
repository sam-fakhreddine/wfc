"""Tests for stages.edge_case — boundary condition and robustness stress-testing stage."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from wfc.scripts.orchestrators.skill_validator_llm.stages.edge_case import (
    _get_template_path,
    run,
)

VALID_SKILL_MD = """\
---
name: wfc-edge-test
description: A skill for testing edge case validation.
triggers:
  - test edge cases
version: "1.0"
---

## Workflow
Step 1. Accept user input.
Step 2. Process and return output.
"""

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"


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
        "wfc.scripts.orchestrators.skill_validator_llm.stages.edge_case.call_api"
    ) as mock_api:
        run(skill_dir, offline=True)
        mock_api.assert_not_called()


def test_run_calls_api_without_thinking(skill_dir: Path) -> None:
    with mock.patch(
        "wfc.scripts.orchestrators.skill_validator_llm.stages.edge_case.call_api"
    ) as mock_api:
        mock_api.return_value = "mocked response"
        run(skill_dir, offline=False)
        assert mock_api.called
        call_kwargs = mock_api.call_args.kwargs
        assert call_kwargs.get("use_thinking", False) is False


def test_run_reads_full_body(skill_dir: Path) -> None:
    """Prompt passed to call_api must contain the full SKILL.md content."""
    with mock.patch(
        "wfc.scripts.orchestrators.skill_validator_llm.stages.edge_case.call_api"
    ) as mock_api:
        mock_api.return_value = "mocked response"
        run(skill_dir, offline=False)
        assert mock_api.called
        prompt_arg = mock_api.call_args.args[0]
        assert "Step 1. Accept user input." in prompt_arg
        assert "Step 2. Process and return output." in prompt_arg


def test_template_path_resolves_to_real_file() -> None:
    """Template file must exist on disk — catches path calculation regressions."""
    template_path = _get_template_path()
    assert template_path.exists(), f"Template not found at: {template_path}"


def test_fixture_has_required_sections() -> None:
    """edge-case-response.txt fixture must contain the expected section headers."""
    fixture = FIXTURES_DIR / "edge-case-response.txt"
    content = fixture.read_text(encoding="utf-8")
    assert "## Edge Cases" in content


def test_run_offline_stub_contains_skill_name(skill_dir: Path) -> None:
    result = run(skill_dir, offline=True)
    assert "wfc-edge-test" in result


def test_run_returns_api_response(skill_dir: Path) -> None:
    with mock.patch(
        "wfc.scripts.orchestrators.skill_validator_llm.stages.edge_case.call_api"
    ) as mock_api:
        mock_api.return_value = "## Edge Cases\n\n### Empty input\n**Severity**: HIGH"
        result = run(skill_dir, offline=False)
        assert result == "## Edge Cases\n\n### Empty input\n**Severity**: HIGH"
