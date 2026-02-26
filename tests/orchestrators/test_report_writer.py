"""Tests for report_writer — validation report persistence to ~/.wfc layout."""

from __future__ import annotations

import stat
from pathlib import Path
from unittest import mock

import pytest


from wfc.scripts.orchestrators.skill_validator_llm.report_writer import (
    get_branch,
    write_report,
    write_stage_report,
)


def test_get_branch_returns_string() -> None:
    branch = get_branch()
    assert isinstance(branch, str)
    assert len(branch) > 0


def test_get_branch_fallback_on_failure() -> None:
    with mock.patch(
        "wfc.scripts.orchestrators.skill_validator_llm.report_writer.subprocess.run",
        side_effect=FileNotFoundError("git not found"),
    ):
        branch = get_branch()
    assert branch == "unknown"


def test_get_branch_fallback_on_called_process_error() -> None:
    import subprocess

    with mock.patch(
        "wfc.scripts.orchestrators.skill_validator_llm.report_writer.subprocess.run",
        side_effect=subprocess.CalledProcessError(128, "git"),
    ):
        branch = get_branch()
    assert branch == "unknown"


def test_get_branch_returns_stripped_value() -> None:
    mock_result = mock.MagicMock()
    mock_result.stdout = "  main  \n"
    with mock.patch(
        "wfc.scripts.orchestrators.skill_validator_llm.report_writer.subprocess.run",
        return_value=mock_result,
    ):
        branch = get_branch()
    assert branch == "main"


def test_get_branch_empty_stdout_returns_unknown() -> None:
    mock_result = mock.MagicMock()
    mock_result.stdout = ""
    with mock.patch(
        "wfc.scripts.orchestrators.skill_validator_llm.report_writer.subprocess.run",
        return_value=mock_result,
    ):
        branch = get_branch()
    assert branch == "unknown"


def test_write_report_creates_file(tmp_path: Path) -> None:
    with mock.patch("pathlib.Path.home", return_value=tmp_path):
        report_path = write_report(
            skill_name="wfc-test",
            report_content="# Test Report\n\nSome content.",
            repo="wfc",
            branch="main",
        )

    assert report_path.exists()
    assert report_path.read_text(encoding="utf-8") == "# Test Report\n\nSome content."


def test_write_report_path_structure(tmp_path: Path) -> None:
    with mock.patch("pathlib.Path.home", return_value=tmp_path):
        report_path = write_report(
            skill_name="wfc-review",
            report_content="content",
            repo="myrepo",
            branch="claude/fix-something",
        )

    parts = report_path.parts
    assert ".wfc" in parts
    assert "projects" in parts
    assert "myrepo" in parts
    assert "branches" in parts
    assert "docs" in parts
    assert "skill-validation" in parts
    assert report_path.name == "wfc-review.md"


def test_write_report_timestamp_in_path(tmp_path: Path) -> None:
    import re

    with mock.patch("pathlib.Path.home", return_value=tmp_path):
        report_path = write_report(
            skill_name="wfc-test",
            report_content="content",
            repo="wfc",
            branch="main",
        )

    timestamp_dir = report_path.parent.name
    assert re.fullmatch(
        r"\d{8}_\d{6}", timestamp_dir
    ), f"Expected YYYYMMDD_HHMMSS format, got: {timestamp_dir!r}"


def test_write_report_file_permissions(tmp_path: Path) -> None:
    with mock.patch("pathlib.Path.home", return_value=tmp_path):
        report_path = write_report(
            skill_name="wfc-test",
            report_content="content",
            repo="wfc",
            branch="main",
        )

    file_mode = stat.S_IMODE(report_path.stat().st_mode)
    assert file_mode == 0o600, f"Expected 0o600, got 0o{file_mode:o}"


def test_write_report_dir_permissions(tmp_path: Path) -> None:
    with mock.patch("pathlib.Path.home", return_value=tmp_path):
        report_path = write_report(
            skill_name="wfc-test",
            report_content="content",
            repo="wfc",
            branch="main",
        )

    dir_mode = stat.S_IMODE(report_path.parent.stat().st_mode)
    assert dir_mode == 0o700, f"Expected 0o700, got 0o{dir_mode:o}"


def test_write_report_returns_path_object(tmp_path: Path) -> None:
    with mock.patch("pathlib.Path.home", return_value=tmp_path):
        result = write_report(
            skill_name="wfc-test",
            report_content="content",
            repo="wfc",
            branch="main",
        )

    assert isinstance(result, Path)


def test_write_report_branch_with_slash(tmp_path: Path) -> None:
    """Branch names with slashes (e.g. claude/fix-x) must be preserved in path."""
    with mock.patch("pathlib.Path.home", return_value=tmp_path):
        report_path = write_report(
            skill_name="wfc-test",
            report_content="content",
            repo="wfc",
            branch="claude/fix-something",
        )

    assert report_path.exists()
    assert (tmp_path / ".wfc" / "projects" / "wfc" / "branches" / "claude").is_dir()


def test_write_stage_report_creates_correct_filename(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    path = write_stage_report("wfc-test", "logic", "content", "wfc", "main")
    assert path.name == "wfc-test-logic.md"


def test_write_stage_report_file_permissions(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    path = write_stage_report("wfc-test", "discovery", "content", "wfc", "main")
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_write_stage_report_dir_permissions(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    path = write_stage_report("wfc-test", "edge_case", "content", "wfc", "main")
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700


def test_write_stage_report_invalid_skill_name_raises(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    with pytest.raises(ValueError, match="skill_name"):
        write_stage_report("../evil", "discovery", "content", "wfc", "main")
    assert not list(tmp_path.glob("**/*.md"))


def test_write_stage_report_invalid_stage_raises(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    with pytest.raises(ValueError, match="stage"):
        write_stage_report("wfc-test", "invalid_stage", "content", "wfc", "main")


def test_write_stage_report_all_valid_stages(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    for stage in ("discovery", "logic", "edge_case"):
        path = write_stage_report("wfc-skill", stage, f"{stage} content", "wfc", "main")
        assert path.exists()
        assert stage in path.name


def test_write_report_backward_compat(tmp_path: Path, monkeypatch) -> None:
    """Existing write_report() still works unchanged."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    path = write_report("wfc-test", "report content", "wfc", "main")
    assert path.exists()
    assert path.name == "wfc-test.md"
