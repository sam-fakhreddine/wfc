"""Tests for skill_validator_llm cli — argument parsing, cost estimation, retry."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from wfc.scripts.orchestrators.skill_validator_llm.cli import (
    _build_parser,
    _estimate_cost,
    _estimate_tokens,
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
    assert abs(cost - 0.003) < 1e-9


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


def test_validate_skill_dry_run(tmp_path: Path, capsys) -> None:
    skill_dir = tmp_path / "wfc-test"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: wfc-test\ndescription: A test skill.\n---\n")

    result = _validate_skill(skill_dir, stage="discovery", dry_run=True)

    assert "DRY-RUN" in result
    assert "wfc-test" in result
    captured = capsys.readouterr()
    assert "Would call API" in captured.out


def test_validate_skill_uses_template_when_present(tmp_path: Path) -> None:
    skill_dir = tmp_path / "wfc-test"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: wfc-test\ndescription: Test desc.\n---\n")
    tmpl_dir = skill_dir / "assets" / "templates"
    tmpl_dir.mkdir(parents=True)
    (tmpl_dir / "discovery-prompt.txt").write_text("name: ${skill_name}\ndesc: ${description}\n")

    result = _validate_skill(skill_dir, stage="discovery", dry_run=True)

    assert "wfc-test" in result


def test_validate_skill_no_template_falls_back(tmp_path: Path) -> None:
    skill_dir = tmp_path / "wfc-test"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: wfc-test\ndescription: Fallback test.\n---\n")

    result = _validate_skill(skill_dir, stage="discovery", dry_run=True)

    assert "wfc-test" in result


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
    assert args.stage == "discovery"


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
            "wfc.scripts.orchestrators.skill_validator_llm.cli.write_report",
            return_value=tmp_path / "report.md",
        ) as mock_write,
    ):
        rc = main(["--all", "--yes"])

    assert rc == 0
    mock_write.assert_called_once()


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
