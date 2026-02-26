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
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, TypeVar

from .report_writer import get_branch, write_stage_report, write_summary_report
from .skill_reader import parse_frontmatter, resolve_repo_name
from .stages import run_discovery, run_edge_case, run_logic, run_refinement

_SKILLS_ROOT = Path(__file__).parents[3] / "skills"
_VALID_STAGES: frozenset[str] = frozenset({"discovery", "logic", "edge_case", "refinement"})
_ALL_STAGES: list[str] = ["discovery", "logic", "edge_case", "refinement"]
_INPUT_RATE_PER_TOKEN = 0.000003
_OUTPUT_RATE_PER_TOKEN = 0.000015
_EST_OUTPUT_MULTIPLIER = 0.5
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
    """Estimate USD cost from input token count (includes estimated output)."""
    output_tokens = int(tokens * _EST_OUTPUT_MULTIPLIER)
    return tokens * _INPUT_RATE_PER_TOKEN + output_tokens * _OUTPUT_RATE_PER_TOKEN


def _find_skill_dirs(skills_root: Path) -> list[Path]:
    """Return sorted list of wfc-* skill directories containing a SKILL.md."""
    return sorted(p for p in skills_root.iterdir() if p.is_dir() and (p / "SKILL.md").exists())


def _extract_health_score(report: str) -> float | None:
    """Extract health score from a refinement report string.

    Returns the float score (e.g. 7.3) or None if the header is absent.
    """
    m = re.search(r"Health Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", report)
    if m:
        return float(m.group(1))
    return None


def _validate_skill(
    skill_path: Path,
    stages: list[str],
    offline: bool,
) -> dict[str, str]:
    """Run LLM validation for one skill across the given stages.

    Args:
        skill_path: Path to the skill directory.
        stages: List of stage names to run in order.
        offline: If True, use offline stubs (no API calls).

    Returns:
        Dict mapping stage name to report content string.
        On stage failure, remaining stages are skipped; the error is re-raised.
    """
    _STAGE_RUNNERS = {
        "discovery": run_discovery,
        "logic": run_logic,
        "edge_case": run_edge_case,
        "refinement": run_refinement,
    }
    results: dict[str, str] = {}
    for stage in stages:
        runner = _STAGE_RUNNERS[stage]
        if offline:
            print(f"[OFFLINE] {stage}: {skill_path.name}")
        report = runner(skill_path, offline=offline)
        results[stage] = report
    return results


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
        default=None,
        help="Validation stage to run: discovery, logic, edge_case, refinement. Default: run all stages.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip API calls; write offline stub reports. Safe for CI usage.",
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

    stages_to_run: list[str]
    if args.stage is not None:
        if args.stage not in _VALID_STAGES:
            print(
                f"Error: invalid --stage {args.stage!r}. Valid stages: {sorted(_VALID_STAGES)}",
                file=sys.stderr,
            )
            return 1
        stages_to_run = [args.stage]
    else:
        stages_to_run = _ALL_STAGES

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
            tokens_per_stage = _estimate_tokens(name + desc)
            print(f"[DRY-RUN] Skill: {name}")
            for stage in stages_to_run:
                cost = _estimate_cost(tokens_per_stage)
                print(f"[DRY-RUN]   Stage {stage}: ~{tokens_per_stage} tokens, ~${cost:.6f}")
            total_cost = _estimate_cost(tokens_per_stage) * len(stages_to_run)
            print(f"[DRY-RUN] Total estimated cost: ${total_cost:.6f}")
            print("[DRY-RUN] No API calls will be made.")
            return 0

        def _run() -> dict[str, str]:
            return _validate_skill(skill_path, stages_to_run, offline=args.offline)

        try:
            stage_reports = retry_with_backoff(_run)
        except Exception as exc:  # noqa: BLE001
            print(f"Error validating {skill_path.name}: {exc}", file=sys.stderr)
            return 1

        for stage, report_content in stage_reports.items():
            report_path = write_stage_report(
                skill_name=skill_path.name,
                stage=stage,
                report_content=report_content,
                repo=repo,
                branch=branch,
            )
            print(f"Report written: {report_path}")

        if "refinement" in stage_reports:
            health_score = _extract_health_score(stage_reports["refinement"])
            if health_score is not None:
                summary_path = write_summary_report(
                    [{"skill": skill_path.name, "score": health_score}],
                    repo=repo,
                    branch=branch,
                )
                print(f"Summary written: {summary_path}")

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

    total_cost = _estimate_cost(total_tokens) * len(stages_to_run)

    if args.dry_run:
        print(f"[DRY-RUN] Skills found: {len(skill_dirs)}")
        print(f"[DRY-RUN] Estimated total tokens: {total_tokens}")
        print(f"[DRY-RUN] Estimated total cost:   ${total_cost:.6f}")
        print(f"[DRY-RUN] Stages: {stages_to_run}")
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
    summary_entries: list[dict] = []

    def _run_one(sd: Path) -> tuple[str, dict[str, str], float | None]:
        stage_results = retry_with_backoff(
            lambda: _validate_skill(sd, stages_to_run, offline=args.offline)
        )
        health_score = None
        if "refinement" in stage_results:
            health_score = _extract_health_score(stage_results["refinement"])
        return sd.name, stage_results, health_score

    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
        future_to_skill = {executor.submit(_run_one, sd): sd for sd in skill_dirs}
        for future in as_completed(future_to_skill):
            sd = future_to_skill[future]
            try:
                skill_name, stage_results, health_score = future.result()
                for stage, report_content in stage_results.items():
                    report_path = write_stage_report(
                        skill_name=skill_name,
                        stage=stage,
                        report_content=report_content,
                        repo=repo,
                        branch=branch,
                    )
                    reports.append(report_path)
                if health_score is not None:
                    summary_entries.append({"skill": skill_name, "score": health_score})
                print(f"OK  {skill_name}: {len(stage_results)} stage(s) written")
            except Exception as exc:  # noqa: BLE001
                errors.append((sd.name, exc))
                print(f"ERR {sd.name}: {exc}", file=sys.stderr)

    if errors:
        print(f"\n{len(errors)} skill(s) failed:", file=sys.stderr)
        for skill_name, exc in errors:
            print(f"  - {skill_name}: {exc}", file=sys.stderr)
        return 1

    if summary_entries:
        summary_path = write_summary_report(summary_entries, repo=repo, branch=branch)
        print(f"Summary written: {summary_path}")

    print(f"\n{len(reports)} report(s) written for {len(skill_dirs)} skill(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
