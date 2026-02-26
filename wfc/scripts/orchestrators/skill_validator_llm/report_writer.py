"""report_writer.py — Write LLM validation reports to ~/.wfc project layout."""

from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path


def get_branch() -> str:
    """Return the current git branch name.

    Falls back to "unknown" if git is unavailable or not in a repo.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        branch = result.stdout.strip()
        return branch if branch else "unknown"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def write_report(
    skill_name: str,
    report_content: str,
    repo: str,
    branch: str,
) -> Path:
    """Write an LLM validation report to the ~/.wfc project layout.

    Output path:
        ~/.wfc/projects/{repo}/branches/{branch}/docs/skill-validation/{timestamp}/

    The timestamp is formatted as YYYYMMDD_HHMMSS.
    The directory is created with mode 0o700 (owner-only).
    The report file is written with mode 0o600 (owner read/write).

    Args:
        skill_name: The skill identifier (used as the filename base).
        report_content: The full text content of the report.
        repo: Repository name (e.g. "wfc").
        branch: Branch name (e.g. "claude/fix-skill-conformance").

    Returns:
        Path to the written report file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = (
        Path.home()
        / ".wfc"
        / "projects"
        / repo
        / "branches"
        / branch
        / "docs"
        / "skill-validation"
        / timestamp
    )
    report_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

    report_file = report_dir / f"{skill_name}.md"
    report_file.write_text(report_content, encoding="utf-8")
    report_file.chmod(0o600)

    return report_file


_SAFE_SKILL_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
_VALID_STAGES: frozenset[str] = frozenset({"discovery", "logic", "edge_case"})


def write_stage_report(
    skill_name: str,
    stage: str,
    report_content: str,
    repo: str,
    branch: str,
) -> Path:
    """Write a per-stage LLM validation report to the ~/.wfc project layout.

    Output path:
        ~/.wfc/projects/{repo}/branches/{branch}/docs/skill-validation/{timestamp}/

    The report file is named {skill_name}-{stage}.md.

    Args:
        skill_name: The skill identifier. Must match r'^[a-zA-Z0-9_-]+$'.
        stage: Validation stage. Must be one of: discovery, logic, edge_case.
        report_content: The full text content of the report.
        repo: Repository name (e.g. "wfc").
        branch: Branch name (e.g. "claude/wfc-skill-validator-llm-phase2").

    Returns:
        Path to the written report file.

    Raises:
        ValueError: If skill_name or stage fails validation.
    """
    if not _SAFE_SKILL_NAME_RE.match(skill_name):
        raise ValueError(f"Invalid skill_name {skill_name!r}: must match r'^[a-zA-Z0-9_-]+$'.")
    if stage not in _VALID_STAGES:
        raise ValueError(f"Invalid stage {stage!r}: must be one of {sorted(_VALID_STAGES)}.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = (
        Path.home()
        / ".wfc"
        / "projects"
        / repo
        / "branches"
        / branch
        / "docs"
        / "skill-validation"
        / timestamp
    )
    report_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

    report_file = report_dir / f"{skill_name}-{stage}.md"
    report_file.write_text(report_content, encoding="utf-8")
    report_file.chmod(0o600)

    return report_file
