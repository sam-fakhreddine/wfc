"""Tests for skill_validator_llm cli — argument parsing, cost estimation, retry."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from wfc.scripts.orchestrators.skill_validator_llm.cli import (
    _ALL_STAGES,
    _build_parser,
    _estimate_cost,
    _estimate_tokens,
    _extract_health_score,
    _find_skill_dirs,
    _validate_skill,
    main,
    retry_with_backoff,
)


def test_estimate_tokens_empty() -> None:
    assert _estimate_tokens("") == 0


def test_estimate_tokens_basic() -> None:
    text = "a" * 100
    assert _estimate_tokens(text) == 25


def test_estimate_cost_zero() -> None:
    assert _estimate_cost(0) == 0.0


def test_estimate_cost_positive() -> None:
    cost = _estimate_cost(1000)
    assert abs(cost - 0.0105) < 1e-9


def test_find_skill_dirs_returns_only_dirs_with_skill_md(tmp_path: Path) -> None:
    (tmp_path / "wfc-foo").mkdir()
    (tmp_path / "wfc-foo" / "SKILL.md").write_text("---\nname: wfc-foo\n---\n")
    (tmp_path / "wfc-bar").mkdir()

    result = _find_skill_dirs(tmp_path)

    assert len(result) == 1
    assert result[0].name == "wfc-foo"


def test_find_skill_dirs_sorted(tmp_path: Path) -> None:
    for name in ["wfc-zzz", "wfc-aaa", "wfc-mmm"]:
        d = tmp_path / name
        d.mkdir()
        (d / "SKILL.md").write_text(f"---\nname: {name}\n---\n")

    result = _find_skill_dirs(tmp_path)

    assert [r.name for r in result] == sorted(r.name for r in result)


def test_validate_skill_returns_dict_of_stage_results(tmp_path: Path) -> None:
    skill_dir = tmp_path / "wfc-test"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: wfc-test\ndescription: A test skill.\n---\n")

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.run_discovery",
            return_value="discovery report",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.run_logic",
            return_value="logic report",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.run_edge_case",
            return_value="edge report",
        ),
    ):
        result = _validate_skill(
            skill_dir, stages=["discovery", "logic", "edge_case"], offline=False
        )

    assert result == {
        "discovery": "discovery report",
        "logic": "logic report",
        "edge_case": "edge report",
    }


def test_validate_skill_offline_returns_stub_content(tmp_path: Path) -> None:
    skill_dir = tmp_path / "wfc-test"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: wfc-test\ndescription: Test desc.\n---\n")

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.run_discovery",
            return_value="[OFFLINE STUB — no API call made] discovery",
        ),
    ):
        result = _validate_skill(skill_dir, stages=["discovery"], offline=True)

    assert "OFFLINE STUB" in result["discovery"]


def test_validate_skill_single_stage(tmp_path: Path) -> None:
    skill_dir = tmp_path / "wfc-test"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: wfc-test\ndescription: Fallback test.\n---\n")

    with mock.patch(
        "wfc.scripts.orchestrators.skill_validator_llm.cli.run_logic",
        return_value="logic only",
    ):
        result = _validate_skill(skill_dir, stages=["logic"], offline=False)

    assert list(result.keys()) == ["logic"]
    assert result["logic"] == "logic only"


def test_retry_with_backoff_success_first_try() -> None:
    call_count = 0

    def fn() -> str:
        nonlocal call_count
        call_count += 1
        return "ok"

    result = retry_with_backoff(fn, max_retries=3, base_delay=0.0)

    assert result == "ok"
    assert call_count == 1


def test_retry_with_backoff_retries_on_timeout() -> None:
    call_count = 0

    class FakeTimeoutError(Exception):
        pass

    FakeTimeoutError.__name__ = "APITimeoutError"

    def fn() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise FakeTimeoutError("timeout")
        return "ok"

    with mock.patch("time.sleep"):
        result = retry_with_backoff(fn, max_retries=3, base_delay=0.0)

    assert result == "ok"
    assert call_count == 3


def test_retry_with_backoff_raises_non_retryable_immediately() -> None:
    call_count = 0

    def fn() -> None:
        nonlocal call_count
        call_count += 1
        raise ValueError("not retryable")

    with pytest.raises(ValueError, match="not retryable"):
        retry_with_backoff(fn, max_retries=3, base_delay=0.0)

    assert call_count == 1


def test_retry_with_backoff_exhausts_retries_and_raises() -> None:
    class FakeRateLimitError(Exception):
        pass

    FakeRateLimitError.__name__ = "RateLimitError"

    def fn() -> None:
        raise FakeRateLimitError("rate limit")

    with mock.patch("time.sleep"):
        with pytest.raises(FakeRateLimitError):
            retry_with_backoff(fn, max_retries=3, base_delay=0.0)


def test_retry_with_backoff_connection_error_retried() -> None:
    call_count = 0

    class FakeConnectionError(Exception):
        pass

    FakeConnectionError.__name__ = "APIConnectionError"

    def fn() -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise FakeConnectionError("conn")
        return "recovered"

    with mock.patch("time.sleep"):
        result = retry_with_backoff(fn, max_retries=3, base_delay=0.0)

    assert result == "recovered"
    assert call_count == 2


def test_parser_skill_path_positional() -> None:
    parser = _build_parser()
    args = parser.parse_args(["/some/path"])
    assert args.skill_path == Path("/some/path")
    assert not args.all_skills


def test_parser_all_flag() -> None:
    parser = _build_parser()
    args = parser.parse_args(["--all"])
    assert args.all_skills
    assert args.skill_path is None


def test_parser_dry_run_flag() -> None:
    parser = _build_parser()
    args = parser.parse_args(["--all", "--dry-run"])
    assert args.dry_run
    assert args.all_skills


def test_parser_yes_flag() -> None:
    parser = _build_parser()
    args = parser.parse_args(["--all", "--yes"])
    assert args.yes


def test_parser_stage_default() -> None:
    parser = _build_parser()
    args = parser.parse_args(["--all"])
    assert args.stage is None


def test_parser_stage_custom() -> None:
    parser = _build_parser()
    args = parser.parse_args(["--all", "--stage", "logic"])
    assert args.stage == "logic"


def test_parser_mutually_exclusive_skill_path_and_all(capsys) -> None:
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["/some/path", "--all"])


def _make_skill(root: Path, name: str) -> Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: A skill called {name}.\n---\n")
    return d


def test_main_no_args_returns_1(capsys) -> None:
    rc = main([])
    assert rc == 1


def test_main_single_skill_missing_skill_md(tmp_path: Path) -> None:
    skill_dir = tmp_path / "wfc-empty"
    skill_dir.mkdir()

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
    ):
        rc = main([str(skill_dir)])

    assert rc == 1


def test_main_single_skill_dry_run(tmp_path: Path, capsys) -> None:
    skill_dir = _make_skill(tmp_path, "wfc-test")

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
    ):
        rc = main([str(skill_dir), "--dry-run"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "DRY-RUN" in out
    assert "wfc-test" in out


def test_main_all_dry_run(tmp_path: Path, capsys) -> None:
    skills_root = tmp_path / "skills"
    _make_skill(skills_root, "wfc-alpha")
    _make_skill(skills_root, "wfc-beta")

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli._SKILLS_ROOT",
            skills_root,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
    ):
        rc = main(["--all", "--dry-run"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "DRY-RUN" in out
    assert "2" in out


def test_main_all_yes_writes_reports(tmp_path: Path, capsys) -> None:
    skills_root = tmp_path / "skills"
    _make_skill(skills_root, "wfc-alpha")

    stage_results = {
        "discovery": "disc report",
        "logic": "logic report",
        "edge_case": "edge report",
    }

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli._SKILLS_ROOT",
            skills_root,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.write_stage_report",
            return_value=tmp_path / "report.md",
        ) as mock_write,
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli._validate_skill",
            return_value=stage_results,
        ),
    ):
        rc = main(["--all", "--yes"])

    assert rc == 0
    assert mock_write.call_count == 3


def test_main_all_no_skills_returns_1(tmp_path: Path) -> None:
    skills_root = tmp_path / "empty_skills"
    skills_root.mkdir()

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli._SKILLS_ROOT",
            skills_root,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
    ):
        rc = main(["--all", "--yes"])

    assert rc == 1


def test_main_all_without_yes_aborts_on_no(tmp_path: Path, capsys) -> None:
    skills_root = tmp_path / "skills"
    _make_skill(skills_root, "wfc-alpha")

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli._SKILLS_ROOT",
            skills_root,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
        mock.patch("builtins.input", return_value="n"),
    ):
        rc = main(["--all"])

    assert rc == 0
    assert "Aborted" in capsys.readouterr().out


def test_stage_flag_invalid_exits_1(capsys) -> None:
    """--stage with invalid value returns exit code 1 without making git calls."""
    rc = main(["--all", "--stage", "invalid_stage"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "invalid" in err.lower() or "valid" in err.lower()


def test_stage_flag_discovery_only(tmp_path: Path, capsys) -> None:
    """--stage discovery runs only the discovery stage."""
    skill_dir = _make_skill(tmp_path, "wfc-solo")

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.write_stage_report",
            return_value=tmp_path / "report.md",
        ) as mock_write,
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli._validate_skill",
            return_value={"discovery": "disc report"},
        ),
    ):
        rc = main([str(skill_dir), "--stage", "discovery"])

    assert rc == 0
    mock_write.assert_called_once()


def test_offline_flag_no_api_calls(tmp_path: Path, capsys) -> None:
    """--offline flag prints [OFFLINE] messages and does not call the API."""
    skill_dir = _make_skill(tmp_path, "wfc-offline")

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.write_stage_report",
            return_value=tmp_path / "report.md",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.run_discovery",
            return_value="[OFFLINE STUB — no API call made] discovery",
        ) as mock_disc,
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.run_logic",
            return_value="[OFFLINE STUB — no API call made] logic",
        ) as mock_logic,
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.run_edge_case",
            return_value="[OFFLINE STUB — no API call made] edge",
        ) as mock_edge,
    ):
        rc = main([str(skill_dir), "--offline"])

    assert rc == 0
    mock_disc.assert_called_once_with(skill_dir.resolve(), offline=True)
    mock_logic.assert_called_once_with(skill_dir.resolve(), offline=True)
    mock_edge.assert_called_once_with(skill_dir.resolve(), offline=True)


def test_dry_run_shows_per_stage_cost(tmp_path: Path, capsys) -> None:
    """--dry-run for a single skill shows per-stage cost breakdown."""
    skill_dir = _make_skill(tmp_path, "wfc-cost")

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
    ):
        rc = main([str(skill_dir), "--dry-run"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "DRY-RUN" in out
    assert "discovery" in out
    assert "logic" in out
    assert "edge_case" in out


def test_full_pipeline_writes_three_reports(tmp_path: Path, capsys) -> None:
    """Running all 3 stages for one skill writes exactly 3 reports."""
    skill_dir = _make_skill(tmp_path, "wfc-full")

    stage_results = {
        "discovery": "disc report",
        "logic": "logic report",
        "edge_case": "edge report",
    }

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.write_stage_report",
            return_value=tmp_path / "report.md",
        ) as mock_write,
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli._validate_skill",
            return_value=stage_results,
        ),
    ):
        rc = main([str(skill_dir)])

    assert rc == 0
    assert mock_write.call_count == 3


def test_all_stages_includes_refinement() -> None:
    """_ALL_STAGES must list all 4 stages with refinement last."""
    assert _ALL_STAGES == ["discovery", "logic", "edge_case", "refinement"]


def test_extract_health_score_valid() -> None:
    """Parses a well-formed Health Score header and returns the float."""
    report = "## Analysis\n\nHealth Score: 7.3 / 10\n\nSome more text."
    assert _extract_health_score(report) == 7.3


def test_extract_health_score_integer_value() -> None:
    """Health Score header with an integer value (e.g. 8 / 10) returns float."""
    report = "Health Score: 8 / 10"
    assert _extract_health_score(report) == 8.0


def test_extract_health_score_missing() -> None:
    """Returns None when the Health Score header is absent."""
    assert _extract_health_score("no header here") is None


def test_extract_health_score_empty_string() -> None:
    """Returns None for an empty string."""
    assert _extract_health_score("") is None


def test_extract_health_score_with_whitespace_variants() -> None:
    """Handles varied whitespace around the score and slash."""
    report = "Health Score:  9.5  /  10"
    assert _extract_health_score(report) == 9.5


def test_stage_flag_refinement_valid(tmp_path: Path) -> None:
    """--stage refinement is accepted and runs only refinement."""
    skill_dir = _make_skill(tmp_path, "wfc-refine")

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.write_stage_report",
            return_value=tmp_path / "report.md",
        ) as mock_write,
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.write_summary_report",
            return_value=tmp_path / "summary.md",
        ) as mock_summary,
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli._validate_skill",
            return_value={"refinement": "Health Score: 6.0 / 10\ndetails"},
        ),
    ):
        rc = main([str(skill_dir), "--stage", "refinement"])

    assert rc == 0
    mock_write.assert_called_once()
    mock_summary.assert_called_once()


def test_stage_flag_invalid_value_exits_1(capsys) -> None:
    """--stage with unknown value returns exit code 1 with error on stderr."""
    rc = main(["--all", "--stage", "invalid_val"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "invalid_val" in err or "invalid" in err.lower()


def test_single_skill_refinement_writes_summary(tmp_path: Path, capsys) -> None:
    """After refinement on a single skill, write_summary_report is called once."""
    skill_dir = _make_skill(tmp_path, "wfc-refine2")

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.write_stage_report",
            return_value=tmp_path / "report.md",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.write_summary_report",
            return_value=tmp_path / "summary.md",
        ) as mock_summary,
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli._validate_skill",
            return_value={"refinement": "Health Score: 7.3 / 10\ndetails"},
        ),
    ):
        rc = main([str(skill_dir), "--stage", "refinement"])

    assert rc == 0
    mock_summary.assert_called_once_with(
        [{"skill": "wfc-refine2", "score": 7.3}],
        repo="wfc",
        branch="main",
    )
    out = capsys.readouterr().out
    assert "Summary written:" in out


def test_single_skill_no_refinement_no_summary(tmp_path: Path) -> None:
    """When refinement is not in stage_reports, write_summary_report is NOT called."""
    skill_dir = _make_skill(tmp_path, "wfc-norefine")

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.write_stage_report",
            return_value=tmp_path / "report.md",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.write_summary_report",
        ) as mock_summary,
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli._validate_skill",
            return_value={"discovery": "disc report"},
        ),
    ):
        rc = main([str(skill_dir), "--stage", "discovery"])

    assert rc == 0
    mock_summary.assert_not_called()


def test_main_all_yes_with_refinement_writes_summary(tmp_path: Path, capsys) -> None:
    """--all --yes running refinement calls write_summary_report once with all skills."""
    skills_root = tmp_path / "skills"
    _make_skill(skills_root, "wfc-alpha")
    _make_skill(skills_root, "wfc-beta")

    stage_results = {"refinement": "Health Score: 8.0 / 10\ndetails"}

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli._SKILLS_ROOT",
            skills_root,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.write_stage_report",
            return_value=tmp_path / "report.md",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.write_summary_report",
            return_value=tmp_path / "summary.md",
        ) as mock_summary,
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli._validate_skill",
            return_value=stage_results,
        ),
    ):
        rc = main(["--all", "--yes", "--stage", "refinement"])

    assert rc == 0
    mock_summary.assert_called_once()
    call_args = mock_summary.call_args
    entries = call_args[0][0] if call_args[0] else call_args[1]["entries"]
    assert len(entries) == 2
    out = capsys.readouterr().out
    assert "Summary written:" in out


def test_main_all_yes_discovery_only_no_summary(tmp_path: Path) -> None:
    """--all --yes --stage discovery does NOT call write_summary_report."""
    skills_root = tmp_path / "skills"
    _make_skill(skills_root, "wfc-alpha")

    stage_results = {"discovery": "disc report"}

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli._SKILLS_ROOT",
            skills_root,
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.write_stage_report",
            return_value=tmp_path / "report.md",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.write_summary_report",
        ) as mock_summary,
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli._validate_skill",
            return_value=stage_results,
        ),
    ):
        rc = main(["--all", "--yes", "--stage", "discovery"])

    assert rc == 0
    mock_summary.assert_not_called()


def test_dry_run_shows_four_stage_cost_lines(tmp_path: Path, capsys) -> None:
    """--dry-run for a single skill shows cost lines for all 4 stages."""
    skill_dir = _make_skill(tmp_path, "wfc-drycost")

    with (
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.resolve_repo_name",
            return_value="wfc",
        ),
        mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.cli.get_branch",
            return_value="main",
        ),
    ):
        rc = main([str(skill_dir), "--dry-run"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "discovery" in out
    assert "logic" in out
    assert "edge_case" in out
    assert "refinement" in out
