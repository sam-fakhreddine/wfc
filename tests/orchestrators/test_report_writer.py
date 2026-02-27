"""Tests for report_writer — validation report persistence to ~/.wfc layout."""

from __future__ import annotations

import stat
from pathlib import Path
from unittest import mock

import pytest


from wfc.scripts.orchestrators.skill_validator_llm.report_writer import (
    find_latest_stage_report,
    get_branch,
    write_report,
    write_stage_report,
    write_summary_report,
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
    assert path.name == "logic.md"
    assert path.parent.parent.name == "wfc-test"


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


def test_write_stage_report_all_valid_stages_now_includes_refinement(
    tmp_path: Path, monkeypatch
) -> None:
    """_VALID_STAGES must include 'refinement' so write_stage_report accepts it."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    for stage in ("discovery", "logic", "edge_case", "refinement"):
        path = write_stage_report("wfc-skill", stage, f"{stage} content", "wfc", "main")
        assert path.exists()
        assert stage in path.name


def test_write_stage_report_accepts_refinement(tmp_path: Path, monkeypatch) -> None:
    """write_stage_report with stage='refinement' must not raise ValueError."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    path = write_stage_report("wfc-review", "refinement", "refinement content", "wfc", "main")
    assert path.exists()
    assert path.name == "refinement.md"
    assert path.parent.parent.name == "wfc-review"


def test_find_latest_stage_report_returns_most_recent(tmp_path: Path, monkeypatch) -> None:
    """Returns the file with the highest mtime among all run subdirs for the skill."""
    import os

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    skill_base = (
        tmp_path
        / ".wfc"
        / "projects"
        / "wfc"
        / "branches"
        / "main"
        / "docs"
        / "skill-validation"
        / "wfc-review"
    )
    skill_base.mkdir(parents=True)

    older_dir = skill_base / "20240101_120000"
    older_dir.mkdir()
    older_file = older_dir / "discovery.md"
    older_file.write_text("older report", encoding="utf-8")
    os.utime(older_file, (1_000_000, 1_000_000))

    newer_dir = skill_base / "20240102_130000"
    newer_dir.mkdir()
    newer_file = newer_dir / "discovery.md"
    newer_file.write_text("newer report", encoding="utf-8")
    os.utime(newer_file, (2_000_000, 2_000_000))

    result = find_latest_stage_report("wfc-review", "discovery", "wfc", "main")
    assert result == newer_file
    assert result.read_text(encoding="utf-8") == "newer report"


def test_find_latest_stage_report_raises_when_absent(tmp_path: Path, monkeypatch) -> None:
    """Raises FileNotFoundError when no matching report file exists."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    skill_base = (
        tmp_path
        / ".wfc"
        / "projects"
        / "wfc"
        / "branches"
        / "main"
        / "docs"
        / "skill-validation"
        / "wfc-review"
    )
    skill_base.mkdir(parents=True)

    with pytest.raises(FileNotFoundError, match="discovery"):
        find_latest_stage_report("wfc-review", "discovery", "wfc", "main")


def test_find_latest_stage_report_raises_when_dir_missing(tmp_path: Path, monkeypatch) -> None:
    """Raises FileNotFoundError when skill-validation dir does not exist at all."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    with pytest.raises(FileNotFoundError):
        find_latest_stage_report("wfc-review", "discovery", "wfc", "main")


def test_find_latest_stage_report_rejects_invalid_skill_name(tmp_path: Path, monkeypatch) -> None:
    """Invalid skill_name raises ValueError before any filesystem access."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    with pytest.raises(ValueError, match="skill_name"):
        find_latest_stage_report("../evil", "discovery", "wfc", "main")


def test_find_latest_stage_report_rejects_invalid_stage(tmp_path: Path, monkeypatch) -> None:
    """Invalid stage raises ValueError."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    with pytest.raises(ValueError, match="stage"):
        find_latest_stage_report("wfc-review", "not-a-stage", "wfc", "main")


def test_find_latest_stage_report_rejects_invalid_repo(tmp_path: Path, monkeypatch) -> None:
    """Invalid repo raises ValueError."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    with pytest.raises(ValueError, match="repo"):
        find_latest_stage_report("wfc-review", "discovery", "../evil", "main")


def test_find_latest_stage_report_rejects_dotdot_branch(tmp_path: Path, monkeypatch) -> None:
    """Branch with '..' raises ValueError."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    with pytest.raises(ValueError, match="branch"):
        find_latest_stage_report("wfc-review", "discovery", "wfc", "../evil")


def test_write_summary_report_creates_file(tmp_path: Path, monkeypatch) -> None:
    """write_summary_report creates a summary-{timestamp}.md file."""
    import re

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    entries = [
        {"skill": "wfc-foo", "score": 7.8},
        {"skill": "wfc-bar", "score": 3.2},
    ]
    result = write_summary_report(entries, "wfc", "main")
    assert result.exists()
    assert re.fullmatch(
        r"summary-\d{8}_\d{6}\.md", result.name
    ), f"Unexpected filename: {result.name!r}"


def test_write_summary_report_sorted_ascending(tmp_path: Path, monkeypatch) -> None:
    """Lower score (most broken) appears before higher score in the file."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    entries = [
        {"skill": "wfc-high", "score": 9.0},
        {"skill": "wfc-low", "score": 1.5},
        {"skill": "wfc-mid", "score": 5.0},
    ]
    result = write_summary_report(entries, "wfc", "main")
    content = result.read_text(encoding="utf-8")
    low_pos = content.index("wfc-low")
    mid_pos = content.index("wfc-mid")
    high_pos = content.index("wfc-high")
    assert low_pos < mid_pos < high_pos, "Skills must be sorted ascending by score (lowest first)"


def test_write_summary_report_file_permissions(tmp_path: Path, monkeypatch) -> None:
    """Summary file must be mode 0o600."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    result = write_summary_report([{"skill": "wfc-foo", "score": 5.0}], "wfc", "main")
    assert stat.S_IMODE(result.stat().st_mode) == 0o600


def test_write_summary_report_dir_permissions(tmp_path: Path, monkeypatch) -> None:
    """skill-validation directory must be mode 0o700."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    result = write_summary_report([{"skill": "wfc-foo", "score": 5.0}], "wfc", "main")
    assert stat.S_IMODE(result.parent.stat().st_mode) == 0o700


def test_write_summary_report_path_structure(tmp_path: Path, monkeypatch) -> None:
    """Summary file lives under .wfc/projects/{repo}/branches/{branch}/docs/skill-validation/."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    result = write_summary_report([{"skill": "wfc-foo", "score": 5.0}], "wfc", "main")
    parts = result.parts
    assert ".wfc" in parts
    assert "projects" in parts
    assert "wfc" in parts
    assert "branches" in parts
    assert "docs" in parts
    assert "skill-validation" in parts


def test_write_summary_report_markdown_table(tmp_path: Path, monkeypatch) -> None:
    """Summary file must contain a Markdown table with # / Skill / Health Score columns."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    entries = [
        {"skill": "wfc-foo", "score": 3.2},
        {"skill": "wfc-bar", "score": 7.8},
    ]
    result = write_summary_report(entries, "wfc", "main")
    content = result.read_text(encoding="utf-8")
    assert "# Skill Validation Summary" in content
    assert "| # |" in content
    assert "Skill" in content
    assert "Health Score" in content
    assert "wfc-foo" in content
    assert "wfc-bar" in content
    assert "3.2" in content
    assert "7.8" in content


def test_write_summary_report_rejects_invalid_repo(tmp_path: Path, monkeypatch) -> None:
    """Invalid repo raises ValueError."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    with pytest.raises(ValueError, match="repo"):
        write_summary_report([], "../evil", "main")


def test_write_summary_report_rejects_dotdot_branch(tmp_path: Path, monkeypatch) -> None:
    """Branch with '..' raises ValueError."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    with pytest.raises(ValueError, match="branch"):
        write_summary_report([], "wfc", "../evil")


def test_write_report_backward_compat(tmp_path: Path, monkeypatch) -> None:
    """Existing write_report() still works unchanged."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    path = write_report("wfc-test", "report content", "wfc", "main")
    assert path.exists()
    assert path.name == "wfc-test.md"
