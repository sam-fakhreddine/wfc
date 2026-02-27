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
from datetime import datetime
from pathlib import Path
from typing import Callable, TypeVar

from .api_client import get_accumulated_usage, reset_accumulated_usage
from .report_writer import get_branch, make_run_id, write_stage_report, write_summary_report
from .skill_reader import parse_frontmatter, resolve_repo_name
from .stages import run_discovery, run_edge_case, run_logic, run_refinement

_SKILLS_ROOT = Path(__file__).parents[3] / "skills"
_VALID_STAGES: frozenset[str] = frozenset({"discovery", "logic", "edge_case", "refinement"})
_ALL_STAGES: list[str] = ["discovery", "logic", "edge_case", "refinement"]
_INPUT_RATE_PER_TOKEN = 0.000003
_OUTPUT_RATE_PER_TOKEN = 0.000015
_EST_OUTPUT_MULTIPLIER = 0.5

_STAGE_OVERHEAD_INPUT: dict[str, int] = {
    "discovery": 8_500,
    "logic": 500,
    "edge_case": 500,
    "refinement": 3_500,
}
_STAGE_OVERHEAD_OUTPUT: dict[str, int] = {
    "discovery": 8_000,
    "logic": 1_500,
    "edge_case": 1_500,
    "refinement": 2_000,
}
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
                if "RateLimit" in type(exc).__name__:
                    delay = 60.0 + random.uniform(0, 10.0)
                else:
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


def _estimate_cost_per_skill(skill_tokens: int, stages: list[str]) -> float:
    """Better cost estimate that accounts for per-stage overhead.

    Includes thinking budget tokens (discovery), prompt template sizes,
    prior-report inputs (refinement), and expected output volumes.
    Calibrated against observed ~$7 for 31 skills / 4 stages.
    """
    total = 0.0
    for stage in stages:
        in_tok = skill_tokens + _STAGE_OVERHEAD_INPUT.get(stage, 0)
        out_tok = int(skill_tokens * _EST_OUTPUT_MULTIPLIER) + _STAGE_OVERHEAD_OUTPUT.get(stage, 0)
        total += in_tok * _INPUT_RATE_PER_TOKEN + out_tok * _OUTPUT_RATE_PER_TOKEN
    return total


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
    after_stage: Callable[[str, str], None] | None = None,
) -> dict[str, str]:
    """Run LLM validation for one skill across the given stages.

    Each stage is run in order. If ``after_stage`` is provided it is called
    immediately after each stage completes with ``(stage_name, report_content)``,
    allowing callers to flush reports to disk before the next stage reads them.

    Args:
        skill_path: Path to the skill directory.
        stages: List of stage names to run in order.
        offline: If True, use offline stubs (no API calls).
        after_stage: Optional callback invoked after each stage with
            ``(stage_name, report_content)``.

    Returns:
        Dict mapping stage name to report content string.
        On stage failure, remaining stages are skipped; the error is re-raised.
    """
    _stage_runners: dict[str, Callable] = {
        "discovery": run_discovery,
        "logic": run_logic,
        "edge_case": run_edge_case,
        "refinement": run_refinement,
    }
    results: dict[str, str] = {}
    for stage in stages:
        runner = _stage_runners[stage]
        if offline:
            print(f"[OFFLINE] {stage}: {skill_path.name}")
        report = runner(skill_path, offline=offline)
        results[stage] = report
        if after_stage is not None:
            after_stage(stage, report)
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

        reset_accumulated_usage()
        written_single: list[Path] = []
        single_run_id = make_run_id()

        def _flush_single(stage: str, report_content: str) -> None:
            path = write_stage_report(
                skill_name=skill_path.name,
                stage=stage,
                report_content=report_content,
                repo=repo,
                branch=branch,
                run_id=single_run_id,
            )
            written_single.append(path)
            print(f"Report written: {path}")

        def _run() -> dict[str, str]:
            return _validate_skill(
                skill_path, stages_to_run, offline=args.offline, after_stage=_flush_single
            )

        try:
            stage_reports = retry_with_backoff(_run)
        except Exception as exc:  # noqa: BLE001
            print(f"Error validating {skill_path.name}: {exc}", file=sys.stderr)
            return 1

        if "refinement" in stage_reports:
            health_score = _extract_health_score(stage_reports["refinement"])
            if health_score is not None:
                summary_path = write_summary_report(
                    [{"skill": skill_path.name, "score": health_score}],
                    repo=repo,
                    branch=branch,
                )
                print(f"Summary written: {summary_path}")

        usage = get_accumulated_usage()
        in_tok = usage.get("input_tokens", 0)
        out_tok = usage.get("output_tokens", 0)
        cost = in_tok * _INPUT_RATE_PER_TOKEN + out_tok * _OUTPUT_RATE_PER_TOKEN
        print(f"Tokens — input: {in_tok:,}  output: {out_tok:,}  (~${cost:.4f})")
        return 0

    skill_dirs = _find_skill_dirs(_SKILLS_ROOT)

    if not skill_dirs:
        print("No skills found.", file=sys.stderr)
        return 1

    total_tokens = 0
    total_cost = 0.0
    for sd in skill_dirs:
        try:
            fm = parse_frontmatter(sd / "SKILL.md")
            skill_tokens = _estimate_tokens(fm.get("name", "") + fm.get("description", ""))
            total_tokens += skill_tokens
            total_cost += _estimate_cost_per_skill(skill_tokens, stages_to_run)
        except Exception:  # noqa: BLE001
            pass

    if args.dry_run:
        print(f"[DRY-RUN] Skills found: {len(skill_dirs)}")
        print(f"[DRY-RUN] Stages: {stages_to_run}")
        print(f"[DRY-RUN] Estimated cost: ${total_cost:.2f}  (±2× — extended thinking variance)")
        print("[DRY-RUN] No API calls will be made.")
        return 0

    if not args.yes:
        print(f"Estimated cost for {len(skill_dirs)} skills: ~${total_cost:.2f} (±2× variance)")
        answer = input("Proceed? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Aborted.")
            return 0

    errors: list[tuple[str, Exception]] = []
    reports: list[Path] = []
    summary_entries: list[dict] = []
    total_input = 0
    total_output = 0
    run_id = make_run_id()

    n_skills = len(skill_dirs)
    completed_count = 0

    def _log(msg: str) -> None:
        """Thread-safe timestamped print."""
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}", flush=True)

    def _run_one(sd: Path) -> tuple[str, list[Path], float | None, dict[str, int]]:
        reset_accumulated_usage()
        written: list[Path] = []
        stage_results: dict[str, str] = {}

        _stage_runners_local: dict[str, Callable] = {
            "discovery": run_discovery,
            "logic": run_logic,
            "edge_case": run_edge_case,
            "refinement": run_refinement,
        }

        _log(f"START  {sd.name}  ({len(stages_to_run)} stage(s): {', '.join(stages_to_run)})")

        for i, stage in enumerate(stages_to_run, 1):
            _log(f"  {sd.name}  stage {i}/{len(stages_to_run)}: {stage} …")
            runner = _stage_runners_local[stage]
            t0 = time.monotonic()
            report = retry_with_backoff(lambda r=runner: r(sd, offline=args.offline))
            elapsed = time.monotonic() - t0
            stage_results[stage] = report
            path = write_stage_report(
                skill_name=sd.name,
                stage=stage,
                report_content=report,
                repo=repo,
                branch=branch,
                run_id=run_id,
            )
            written.append(path)
            _log(
                f"  {sd.name}  stage {i}/{len(stages_to_run)}: {stage} done ({elapsed:.1f}s) → {path.name}"
            )

        health_score = None
        if "refinement" in stage_results:
            health_score = _extract_health_score(stage_results["refinement"])
        usage = get_accumulated_usage()
        return sd.name, written, health_score, usage

    _log(f"Queuing {n_skills} skill(s) across {_MAX_WORKERS} workers  [run_id={run_id}]")

    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
        future_to_skill = {executor.submit(_run_one, sd): sd for sd in skill_dirs}
        for future in as_completed(future_to_skill):
            sd = future_to_skill[future]
            completed_count += 1
            try:
                skill_name, written, health_score, usage = future.result()
                reports.extend(written)
                in_tok = usage.get("input_tokens", 0)
                out_tok = usage.get("output_tokens", 0)
                total_input += in_tok
                total_output += out_tok
                score_str = f"  score={health_score:.1f}" if health_score is not None else ""
                if health_score is not None:
                    summary_entries.append({"skill": skill_name, "score": health_score})
                _log(
                    f"OK  [{completed_count}/{n_skills}] {skill_name}"
                    f"  [in={in_tok:,} out={out_tok:,}]{score_str}"
                )
            except Exception as exc:  # noqa: BLE001
                errors.append((sd.name, exc))
                _log(f"ERR [{completed_count}/{n_skills}] {sd.name}: {exc}")

    if errors:
        print(f"\n{len(errors)} skill(s) failed:", file=sys.stderr)
        for skill_name, exc in errors:
            print(f"  - {skill_name}: {exc}", file=sys.stderr)
        return 1

    if summary_entries:
        summary_path = write_summary_report(summary_entries, repo=repo, branch=branch)
        print(f"Summary written: {summary_path}")

    actual_cost = total_input * _INPUT_RATE_PER_TOKEN + total_output * _OUTPUT_RATE_PER_TOKEN
    print(
        f"\nTotal tokens — input: {total_input:,}  output: {total_output:,}  (~${actual_cost:.4f})"
    )
    print(f"{len(reports)} report(s) written for {len(skill_dirs)} skill(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
