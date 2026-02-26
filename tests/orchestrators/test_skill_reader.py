"""Tests for skill_reader — SKILL.md frontmatter parser and dir tree builder."""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from wfc.scripts.orchestrators.skill_validator_llm.skill_reader import (
    build_dir_tree,
    parse_frontmatter,
    resolve_repo_name,
)

VALID_FRONTMATTER = """\
---
name: wfc-test
description: A test skill for unit tests.
triggers:
  - test something
version: "1.0"
---

# Body content here
"""

MISSING_CLOSE_DELIMITER = """\
---
name: wfc-test
description: No closing delimiter.
"""

NO_FRONTMATTER = """\
# Just a plain markdown file
No frontmatter at all.
"""


def test_parse_frontmatter_valid(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(VALID_FRONTMATTER, encoding="utf-8")

    result = parse_frontmatter(skill_md)

    assert result["name"] == "wfc-test"
    assert result["description"] == "A test skill for unit tests."
    assert result["version"] == "1.0"


def test_parse_frontmatter_unclosed_raises(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(MISSING_CLOSE_DELIMITER, encoding="utf-8")

    with pytest.raises(ValueError, match="Unclosed frontmatter"):
        parse_frontmatter(skill_md)


def test_parse_frontmatter_no_frontmatter_raises(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(NO_FRONTMATTER, encoding="utf-8")

    with pytest.raises(ValueError, match="Unclosed frontmatter"):
        parse_frontmatter(skill_md)


def test_parse_frontmatter_empty_body(tmp_path: Path) -> None:
    """Frontmatter with no body after closing delimiter should still parse."""
    content = "---\nname: minimal\ndescription: short\n---\n"
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(content, encoding="utf-8")

    result = parse_frontmatter(skill_md)
    assert result["name"] == "minimal"


def test_parse_frontmatter_uses_safe_load(tmp_path: Path) -> None:
    """Ensure yaml.safe_load is used (not yaml.load) — no arbitrary objects."""
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(VALID_FRONTMATTER, encoding="utf-8")
    result = parse_frontmatter(skill_md)
    assert isinstance(result, dict)


def test_build_dir_tree_flat(tmp_path: Path) -> None:
    (tmp_path / "SKILL.md").write_text("", encoding="utf-8")
    (tmp_path / "README.md").write_text("", encoding="utf-8")

    result = build_dir_tree(tmp_path)

    assert "SKILL.md" in result
    assert "README.md" in result
    assert result == sorted(result)


def test_build_dir_tree_two_levels(tmp_path: Path) -> None:
    (tmp_path / "SKILL.md").write_text("", encoding="utf-8")
    sub = tmp_path / "assets" / "templates"
    sub.mkdir(parents=True)
    (sub / "prompt.txt").write_text("", encoding="utf-8")
    assets_dir = tmp_path / "assets"
    (assets_dir / "config.json").write_text("{}", encoding="utf-8")

    result = build_dir_tree(tmp_path)

    assert "SKILL.md" in result
    assert "assets/config.json" in result
    assert "assets/templates/prompt.txt" not in result


def test_build_dir_tree_sorted(tmp_path: Path) -> None:
    for name in ["zebra.txt", "alpha.py", "middle.md"]:
        (tmp_path / name).write_text("", encoding="utf-8")

    result = build_dir_tree(tmp_path)

    assert result == sorted(result)


def test_build_dir_tree_no_symlinks(tmp_path: Path) -> None:
    real_file = tmp_path / "real.txt"
    real_file.write_text("real", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(real_file)
    except OSError:
        pytest.skip("Symlinks not supported on this platform")

    result = build_dir_tree(tmp_path)

    assert isinstance(result, list)


def test_resolve_repo_name_from_env() -> None:
    with mock.patch.dict(os.environ, {"WFC_CORPUS_REPO": "my-project"}):
        name = resolve_repo_name()
    assert name == "my-project"


def test_resolve_repo_name_env_takes_priority_over_git() -> None:
    with mock.patch.dict(os.environ, {"WFC_CORPUS_REPO": "env-wins"}):
        with mock.patch(
            "wfc.scripts.orchestrators.skill_validator_llm.skill_reader.subprocess.run"
        ) as mock_run:
            name = resolve_repo_name()
            mock_run.assert_not_called()
    assert name == "env-wins"


def test_resolve_repo_name_from_git(tmp_path: Path) -> None:
    with mock.patch.dict(os.environ, {}, clear=False):
        env = {k: v for k, v in os.environ.items() if k != "WFC_CORPUS_REPO"}
        with mock.patch.dict(os.environ, env, clear=True):
            mock_result = mock.MagicMock()
            mock_result.stdout = f"{tmp_path}/my-repo\n"
            with mock.patch(
                "wfc.scripts.orchestrators.skill_validator_llm.skill_reader.subprocess.run",
                return_value=mock_result,
            ):
                name = resolve_repo_name()
    assert name == "my-repo"


def test_resolve_repo_name_invalid_raises() -> None:
    with mock.patch.dict(os.environ, {"WFC_CORPUS_REPO": "../evil"}):
        with pytest.raises(ValueError):
            resolve_repo_name()


def test_resolve_repo_name_slash_raises() -> None:
    with mock.patch.dict(os.environ, {"WFC_CORPUS_REPO": "a/b"}):
        with pytest.raises(ValueError):
            resolve_repo_name()


def test_resolve_repo_name_leading_dash_raises() -> None:
    with mock.patch.dict(os.environ, {"WFC_CORPUS_REPO": "-bad"}):
        with pytest.raises(ValueError):
            resolve_repo_name()


def test_resolve_repo_name_special_chars_raises() -> None:
    with mock.patch.dict(os.environ, {"WFC_CORPUS_REPO": "name with spaces"}):
        with pytest.raises(ValueError):
            resolve_repo_name()
