"""Tests for stages.refinement — architecture refinement and health score stage."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from wfc.scripts.orchestrators.skill_validator_llm.stages.refinement import (
    _get_template_path,
    run,
)

VALID_SKILL_MD = """\
---
name: wfc-test-skill
description: A test skill for refinement validation.
triggers:
  - test refinement
version: "1.0"
---

## Workflow
Step 1. Do something.
"""

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"


def _make_skill_dir(tmp_path: Path) -> Path:
    skill_dir = tmp_path / "wfc-test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(VALID_SKILL_MD, encoding="utf-8")
    return skill_dir


def _make_prior_report(tmp_path: Path) -> Path:
    prior = tmp_path / "prior.md"
    prior.write_text("prior report content", encoding="utf-8")
    return prior


def test_run_offline_returns_stub(tmp_path: Path) -> None:
    skill_dir = _make_skill_dir(tmp_path)
    result = run(skill_dir, offline=True)
    assert result.startswith("[OFFLINE STUB] refinement")


def test_run_offline_no_find_latest_call(tmp_path: Path) -> None:
    skill_dir = _make_skill_dir(tmp_path)
    with mock.patch(
        "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.find_latest_stage_report"
    ) as mock_find:
        run(skill_dir, offline=True)
        mock_find.assert_not_called()


def test_run_returns_health_score_header(tmp_path: Path) -> None:
    skill_dir = _make_skill_dir(tmp_path)
    prior_report_file = _make_prior_report(tmp_path)
    fixture_content = (FIXTURES_DIR / "refinement-response.txt").read_text(encoding="utf-8")

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.find_latest_stage_report",
            return_value=prior_report_file,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.call_api",
            return_value=fixture_content,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.get_branch",
            return_value="test-branch",
        ),
    ):
        result = run(skill_dir)
    assert result.startswith("Health Score:")


def test_run_health_formula(tmp_path: Path) -> None:
    skill_dir = _make_skill_dir(tmp_path)
    prior_report_file = _make_prior_report(tmp_path)
    response = "Trigger Clarity: 5/10\nScope Accuracy: 6/10\nStep Clarity: 7/10\n"

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.find_latest_stage_report",
            return_value=prior_report_file,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.call_api",
            return_value=response,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.get_branch",
            return_value="test-branch",
        ),
    ):
        result = run(skill_dir)
    assert "Health Score: 5.8 / 10" in result


def test_run_sub_score_clamping(tmp_path: Path) -> None:
    skill_dir = _make_skill_dir(tmp_path)
    prior_report_file = _make_prior_report(tmp_path)
    response = "Trigger Clarity: 15/10\nScope Accuracy: 15/10\nStep Clarity: 15/10\n"

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.find_latest_stage_report",
            return_value=prior_report_file,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.call_api",
            return_value=response,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.get_branch",
            return_value="test-branch",
        ),
    ):
        result = run(skill_dir)
    assert "Health Score: 10.0 / 10" in result


def test_run_sub_score_absent_defaults_to_5(tmp_path: Path) -> None:
    skill_dir = _make_skill_dir(tmp_path)
    prior_report_file = _make_prior_report(tmp_path)
    response = "No scores here — just some text.\n"

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.find_latest_stage_report",
            return_value=prior_report_file,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.call_api",
            return_value=response,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.get_branch",
            return_value="test-branch",
        ),
    ):
        result = run(skill_dir)
    assert "Health Score: 5.0 / 10" in result
    assert "Warning: sub-score" in result


def test_run_propagates_file_not_found(tmp_path: Path) -> None:
    skill_dir = _make_skill_dir(tmp_path)

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.find_latest_stage_report",
            side_effect=FileNotFoundError("No discovery report"),
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.call_api"
        ) as mock_api,
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.get_branch",
            return_value="test-branch",
        ),
    ):
        with pytest.raises(FileNotFoundError):
            run(skill_dir)
        mock_api.assert_not_called()


def test_run_name_mismatch_warning(tmp_path: Path) -> None:
    skill_dir = _make_skill_dir(tmp_path)
    prior_report_file = _make_prior_report(tmp_path)
    response = (
        "Trigger Clarity: 7/10\nScope Accuracy: 7/10\nStep Clarity: 7/10\n\n"
        "```yaml\n---\nname: wfc-different-name\ndescription: Changed.\n---\n```\n"
    )

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.find_latest_stage_report",
            return_value=prior_report_file,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.call_api",
            return_value=response,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.get_branch",
            return_value="test-branch",
        ),
    ):
        result = run(skill_dir)
    assert "Warning: proposed rewrite changes name field" in result


def test_run_no_name_mismatch_no_warning(tmp_path: Path) -> None:
    skill_dir = _make_skill_dir(tmp_path)
    prior_report_file = _make_prior_report(tmp_path)
    response = (
        "Trigger Clarity: 7/10\nScope Accuracy: 7/10\nStep Clarity: 7/10\n\n"
        "```yaml\n---\nname: wfc-test-skill\ndescription: Same name.\n---\n```\n"
    )

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.find_latest_stage_report",
            return_value=prior_report_file,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.call_api",
            return_value=response,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.stages.refinement.get_branch",
            return_value="test-branch",
        ),
    ):
        result = run(skill_dir)
    first_three_lines = "\n".join(result.splitlines()[:3])
    assert "Warning" not in first_three_lines


def test_run_real_template_loads() -> None:
    template_path = _get_template_path()
    assert template_path.exists(), f"Template not found at: {template_path}"
    content = template_path.read_text(encoding="utf-8")
    assert "${skill_name}" in content


def test_stages_init_exports_run_refinement() -> None:
    from wfc.scripts.orchestrators.skill_validator_llm.stages import run_refinement

    assert callable(run_refinement)
