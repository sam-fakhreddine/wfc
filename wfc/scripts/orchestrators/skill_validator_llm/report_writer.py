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
_SAFE_REPO_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
_SAFE_BRANCH_RE = re.compile(r"^[a-zA-Z0-9_./-]+$")
_VALID_STAGES: frozenset[str] = frozenset({"discovery", "logic", "edge_case", "refinement"})


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
        repo: Repository name (e.g. "wfc"). Must match r'^[a-zA-Z0-9_-]+$'.
        branch: Branch name (e.g. "claude/wfc-skill-validator-llm-phase2").
            Must match r'^[a-zA-Z0-9_./-]+$' and must not contain "..".

    Returns:
        Path to the written report file.

    Raises:
        ValueError: If skill_name, stage, repo, or branch fails validation.
    """
    if not _SAFE_SKILL_NAME_RE.match(skill_name):
        raise ValueError(f"Invalid skill_name {skill_name!r}: must match r'^[a-zA-Z0-9_-]+$'.")
    if stage not in _VALID_STAGES:
        raise ValueError(f"Invalid stage {stage!r}: must be one of {sorted(_VALID_STAGES)}.")
    if not _SAFE_REPO_NAME_RE.match(repo):
        raise ValueError(f"Invalid repo {repo!r}: must match r'^[a-zA-Z0-9_-]+$'.")
    if not _SAFE_BRANCH_RE.match(branch) or ".." in branch:
        raise ValueError(
            f"Invalid branch {branch!r}: must match r'^[a-zA-Z0-9_./-]+$' and must not contain '..'."
        )

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


def find_latest_stage_report(
    skill_name: str,
    stage: str,
    repo: str,
    branch: str,
) -> Path:
    """Return the most-recently written stage report for a given skill.

    Scans all timestamped subdirectories under:
        ~/.wfc/projects/{repo}/branches/{branch}/docs/skill-validation/
    and returns the path with the highest mtime for the file named
    ``{skill_name}-{stage}.md``.

    Args:
        skill_name: The skill identifier. Must match r'^[a-zA-Z0-9_-]+$'.
        stage: Validation stage. Must be one of: discovery, logic, edge_case, refinement.
        repo: Repository name (e.g. "wfc"). Must match r'^[a-zA-Z0-9_-]+$'.
        branch: Branch name. Must match r'^[a-zA-Z0-9_./-]+$' and must not contain "..".

    Returns:
        Path to the most recent matching report file.

    Raises:
        ValueError: If skill_name, stage, repo, or branch fails validation.
        FileNotFoundError: If no matching report file is found.
    """
    if not _SAFE_SKILL_NAME_RE.match(skill_name):
        raise ValueError(f"Invalid skill_name {skill_name!r}: must match r'^[a-zA-Z0-9_-]+$'.")
    if stage not in _VALID_STAGES:
        raise ValueError(f"Invalid stage {stage!r}: must be one of {sorted(_VALID_STAGES)}.")
    if not _SAFE_REPO_NAME_RE.match(repo):
        raise ValueError(f"Invalid repo {repo!r}: must match r'^[a-zA-Z0-9_-]+$'.")
    if not _SAFE_BRANCH_RE.match(branch) or ".." in branch:
        raise ValueError(
            f"Invalid branch {branch!r}: must match r'^[a-zA-Z0-9_./-]+$' and must not contain '..'."
        )

    base = (
        Path.home() / ".wfc" / "projects" / repo / "branches" / branch / "docs" / "skill-validation"
    )

    target_filename = f"{skill_name}-{stage}.md"
    best: Path | None = None
    best_mtime: float = -1.0

    if base.is_dir():
        for subdir in base.iterdir():
            if not subdir.is_dir():
                continue
            candidate = subdir / target_filename
            if candidate.is_file():
                mtime = candidate.stat().st_mtime
                if mtime > best_mtime:
                    best_mtime = mtime
                    best = candidate

    if best is None:
        raise FileNotFoundError(
            f"No {stage} report found for {skill_name} in ~/.wfc/.../docs/skill-validation/"
        )
    return best


def write_summary_report(
    entries: list[dict],
    repo: str,
    branch: str,
) -> Path:
    """Write a Markdown summary table of all skill health scores.

    Entries are sorted ascending by score (lowest = most broken first).

    Output path:
        ~/.wfc/projects/{repo}/branches/{branch}/docs/skill-validation/summary-{timestamp}.md

    Args:
        entries: List of ``{"skill": str, "score": float}`` dicts.
        repo: Repository name (e.g. "wfc"). Must match r'^[a-zA-Z0-9_-]+$'.
        branch: Branch name. Must match r'^[a-zA-Z0-9_./-]+$' and must not contain "..".

    Returns:
        Path to the written summary file.

    Raises:
        ValueError: If repo or branch fails validation.
    """
    if not _SAFE_REPO_NAME_RE.match(repo):
        raise ValueError(f"Invalid repo {repo!r}: must match r'^[a-zA-Z0-9_-]+$'.")
    if not _SAFE_BRANCH_RE.match(branch) or ".." in branch:
        raise ValueError(
            f"Invalid branch {branch!r}: must match r'^[a-zA-Z0-9_./-]+$' and must not contain '..'."
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = (
        Path.home() / ".wfc" / "projects" / repo / "branches" / branch / "docs" / "skill-validation"
    )
    report_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

    sorted_entries = sorted(entries, key=lambda e: e["score"])

    rows = "\n".join(
        f"| {i + 1} | {e['skill']} | {e['score']} |" for i, e in enumerate(sorted_entries)
    )
    content = (
        f"# Skill Validation Summary\n\n"
        f"Generated: {timestamp}\n\n"
        f"| # | Skill | Health Score |\n"
        f"|---|-------|--------------|\n"
        f"{rows}\n"
    )

    summary_file = report_dir / f"summary-{timestamp}.md"
    summary_file.write_text(content, encoding="utf-8")
    summary_file.chmod(0o600)

    return summary_file
