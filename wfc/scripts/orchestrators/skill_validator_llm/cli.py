"""cli.py — Main orchestrator CLI for wfc-skill-validator-llm.

Usage:
    uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli <skill_path>
    uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli --all
    uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli --all --dry-run
    uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli --all --yes
"""

from __future__ import annotations

import argparse
import random
import string
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, TypeVar

from .report_writer import get_branch, write_report
from .skill_reader import parse_frontmatter, resolve_repo_name

_SKILLS_ROOT = Path(__file__).parents[3] / "skills"
_INPUT_RATE_PER_TOKEN = 0.000003
_MAX_WORKERS = 5

T = TypeVar("T")


def retry_with_backoff(
    fn: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> T:
    """Call *fn* with exponential backoff + jitter on transient errors.

    Retries on:
    - anthropic.APITimeoutError
    - anthropic.RateLimitError
    - anthropic.APIConnectionError
    - Any Exception whose type name contains "Timeout", "RateLimit", or
      "Connection" (fallback when anthropic is not installed).

    Args:
        fn: Zero-argument callable to call.
        max_retries: Maximum number of attempts (including the first).
        base_delay: Base delay in seconds for exponential backoff.

    Returns:
        Return value of *fn* on success.

    Raises:
        The last exception if all retries are exhausted.
    """
    _retryable_names = frozenset({"APITimeoutError", "RateLimitError", "APIConnectionError"})

    def _is_retryable(exc: Exception) -> bool:
        exc_type = type(exc).__name__
        if exc_type in _retryable_names:
            return True
        return any(part in exc_type for part in ("Timeout", "RateLimit", "Connection"))

    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            if not _is_retryable(exc):
                raise
            last_exc = exc
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt) + random.uniform(0, 0.5)
                time.sleep(delay)

    if last_exc is None:  # pragma: no cover — impossible but makes type-checker happy
        raise RuntimeError("retry_with_backoff: exhausted retries but no exception captured")
    raise last_exc


def _estimate_tokens(text: str) -> int:
    """Rough token count: len(text) // 4."""
    return len(text) // 4


def _estimate_cost(tokens: int) -> float:
    """Estimate USD cost from token count."""
    return tokens * _INPUT_RATE_PER_TOKEN


def _find_skill_dirs(skills_root: Path) -> list[Path]:
    """Return sorted list of wfc-* skill directories containing a SKILL.md."""
    return sorted(p for p in skills_root.iterdir() if p.is_dir() and (p / "SKILL.md").exists())


def _validate_skill(
    skill_path: Path,
    stage: str,
    dry_run: bool,
) -> str:
    """Run LLM discovery validation for one skill.

    Loads the discovery prompt template from the skill's
    ``assets/templates/discovery-prompt.txt``, formats it with the skill
    name and description, then calls the API (stubbed in this PR).

    Args:
        skill_path: Path to the skill directory.
        stage: Validation stage identifier (e.g. "discovery").
        dry_run: If True, print stub message and return mock response.

    Returns:
        Report content string.
    """
    skill_md = skill_path / "SKILL.md"
    frontmatter = parse_frontmatter(skill_md)
    skill_name: str = frontmatter.get("name", skill_path.name)
    description: str = frontmatter.get("description", "")

    template_path = skill_path / "assets" / "templates" / "discovery-prompt.txt"
    if template_path.exists():
        raw_template = template_path.read_text(encoding="utf-8")
        prompt = string.Template(raw_template).safe_substitute(
            skill_name=skill_name, description=description
        )
    else:
        prompt = f"name: {skill_name}\ndescription: {description}\n\nStage: {stage}\n"

    if dry_run:
        print(f"[DRY-RUN] Would call API for {skill_name}")
        return f"# DRY-RUN: {skill_name}\n\nPrompt length: {len(prompt)} chars\n"

    print(f"[STUB] Would call API for {skill_name}")
    return f"# STUB: {skill_name}\n\nPrompt length: {len(prompt)} chars\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wfc-skill-validator-llm",
        description="LLM-based discovery validation for WFC skills.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "skill_path",
        nargs="?",
        type=Path,
        help="Path to a single skill directory to validate.",
    )
    mode.add_argument(
        "--all",
        action="store_true",
        dest="all_skills",
        help="Validate all installed skills.",
    )
    parser.add_argument(
        "--stage",
        default="discovery",
        help="Validation stage to run (default: discovery).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Print plan with cost estimates, no API calls or file writes.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip cost confirmation prompt when using --all.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI.

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.all_skills and args.skill_path is None:
        parser.print_help()
        return 1

    repo = resolve_repo_name()
    branch = get_branch()

    if args.skill_path is not None:
        skill_path: Path = args.skill_path.resolve()

        if not (skill_path / "SKILL.md").exists():
            print(
                f"Error: no SKILL.md found in {skill_path}",
                file=sys.stderr,
            )
            return 1

        if args.dry_run:
            fm = parse_frontmatter(skill_path / "SKILL.md")
            name = fm.get("name", skill_path.name)
            desc = fm.get("description", "")
            tokens = _estimate_tokens(name + desc)
            cost = _estimate_cost(tokens)
            print(f"[DRY-RUN] Skill: {name}")
            print(f"[DRY-RUN] Estimated tokens: {tokens}")
            print(f"[DRY-RUN] Estimated cost:   ${cost:.6f}")
            print(f"[DRY-RUN] Stage: {args.stage}")
            print("[DRY-RUN] No API calls will be made.")
            return 0

        def _run() -> str:
            return _validate_skill(skill_path, args.stage, dry_run=False)

        try:
            report_content = retry_with_backoff(_run)
        except Exception as exc:  # noqa: BLE001
            print(f"Error validating {skill_path.name}: {exc}", file=sys.stderr)
            return 1

        report_path = write_report(
            skill_name=skill_path.name,
            report_content=report_content,
            repo=repo,
            branch=branch,
        )
        print(f"Report written: {report_path}")
        return 0

    skill_dirs = _find_skill_dirs(_SKILLS_ROOT)

    if not skill_dirs:
        print("No skills found.", file=sys.stderr)
        return 1

    total_tokens = 0
    for sd in skill_dirs:
        try:
            fm = parse_frontmatter(sd / "SKILL.md")
            total_tokens += _estimate_tokens(fm.get("name", "") + fm.get("description", ""))
        except Exception:  # noqa: BLE001
            pass

    total_cost = _estimate_cost(total_tokens)

    if args.dry_run:
        print(f"[DRY-RUN] Skills found: {len(skill_dirs)}")
        print(f"[DRY-RUN] Estimated total tokens: {total_tokens}")
        print(f"[DRY-RUN] Estimated total cost:   ${total_cost:.6f}")
        print(f"[DRY-RUN] Stage: {args.stage}")
        print("[DRY-RUN] No API calls will be made.")
        return 0

    if not args.yes:
        print(f"Estimated cost for {len(skill_dirs)} skills: ${total_cost:.6f}")
        answer = input("Proceed? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Aborted.")
            return 0

    errors: list[tuple[str, Exception]] = []
    reports: list[Path] = []

    def _run_one(sd: Path) -> tuple[str, str]:
        content = retry_with_backoff(lambda: _validate_skill(sd, args.stage, dry_run=False))
        return sd.name, content

    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
        future_to_skill = {executor.submit(_run_one, sd): sd for sd in skill_dirs}
        for future in as_completed(future_to_skill):
            sd = future_to_skill[future]
            try:
                skill_name, report_content = future.result()
                report_path = write_report(
                    skill_name=skill_name,
                    report_content=report_content,
                    repo=repo,
                    branch=branch,
                )
                reports.append(report_path)
                print(f"OK  {skill_name}: {report_path}")
            except Exception as exc:  # noqa: BLE001
                errors.append((sd.name, exc))
                print(f"ERR {sd.name}: {exc}", file=sys.stderr)

    if errors:
        print(f"\n{len(errors)} skill(s) failed:", file=sys.stderr)
        for skill_name, exc in errors:
            print(f"  - {skill_name}: {exc}", file=sys.stderr)
        return 1

    print(f"\n{len(reports)} skill(s) validated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
