"""skill_reader.py — Parse SKILL.md frontmatter and directory structure."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import yaml


def parse_frontmatter(path: Path) -> dict:
    """Read YAML frontmatter from a SKILL.md file.

    Algorithm:
    1. Open file and read lines.
    2. Find first line matching exactly "---".
    3. Find next line matching exactly "---".
    4. If second delimiter not found, raise ValueError.
    5. Parse content between delimiters with yaml.safe_load().

    Args:
        path: Path to a SKILL.md file.

    Returns:
        dict with at least "name" and "description" keys.

    Raises:
        ValueError: If the frontmatter is unclosed (missing second ---).
    """
    lines = path.read_text(encoding="utf-8").splitlines()

    start: int | None = None
    end: int | None = None

    for i, line in enumerate(lines):
        if line.strip() == "---":
            if start is None:
                start = i
            else:
                end = i
                break

    if start is None or end is None:
        raise ValueError(f"Unclosed frontmatter in {path}")

    frontmatter_text = "\n".join(lines[start + 1 : end])
    data: dict = yaml.safe_load(frontmatter_text) or {}
    return data


def build_dir_tree(path: Path) -> list[str]:
    """Return a sorted list of files up to 2 levels deep under path.

    Args:
        path: Root directory to enumerate.

    Returns:
        Sorted list of relative file path strings (max 2 levels deep),
        following no symlinks.
    """
    results: list[str] = []

    for entry in os.scandir(path):
        rel = entry.name
        if entry.is_file(follow_symlinks=False):
            results.append(rel)
        elif entry.is_dir(follow_symlinks=False):
            try:
                for sub_entry in os.scandir(entry.path):
                    if sub_entry.is_file(follow_symlinks=False):
                        results.append(f"{rel}/{sub_entry.name}")
            except PermissionError:
                pass

    return sorted(results)


_SAFE_REPO_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def resolve_repo_name() -> str:
    """Resolve the current repository name for corpus path construction.

    Priority:
    1. WFC_CORPUS_REPO environment variable.
    2. Basename of `git rev-parse --show-toplevel` output.
    3. Fallback literal "wfc".

    Validation:
    - Must match r"^[a-zA-Z0-9_-]+$"
    - Must not contain ".." or "/"
    - Must not start with "-"

    Returns:
        Validated repository name string.

    Raises:
        ValueError: If the resolved name fails validation.
    """
    env_val = os.environ.get("WFC_CORPUS_REPO")

    if env_val is not None:
        name = env_val
    else:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            name = Path(result.stdout.strip()).name
        except (subprocess.CalledProcessError, FileNotFoundError):
            name = "wfc"

        print(
            f"WFC_CORPUS_REPO not set; using repo name '{name}' from git. "
            "Set WFC_CORPUS_REPO to override.",
            file=sys.stderr,
        )

    if ".." in name or "/" in name or name.startswith("-"):
        raise ValueError(
            f"Resolved repo name {name!r} contains illegal characters ('..', '/', or leading '-')."
        )
    if not _SAFE_REPO_NAME_RE.match(name):
        raise ValueError(f"Resolved repo name {name!r} does not match r'^[a-zA-Z0-9_-]+$'.")

    return name
