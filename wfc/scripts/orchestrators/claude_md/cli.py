"""CLI interface for the CLAUDE.md remediation pipeline.

Usage:
    uv run python -m wfc.scripts.orchestrators.claude_md.cli [OPTIONS] [PROJECT_ROOT]

Options:
    --write         Write the rewritten CLAUDE.md (after confirmation prompt)
    --write-force   Write without prompting
    --dry-run       Show report only, no writes (default)
    --no-llm        Skip LLM agents (heuristic mode only)
    --output FILE   Write report to a file instead of stdout
    --json          Output raw JSON instead of markdown report

The CLI is SAFE BY DEFAULT: it never writes files unless --write or --write-force
is explicitly passed.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .orchestrator import PipelineConfig, remediate
from .schemas import RemediationResult

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wfc claude-md",
        description="Diagnose and fix CLAUDE.md files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run analysis (safe, no writes)
  uv run python -m wfc.scripts.orchestrators.claude_md.cli .

  # Show what would change, then write if you approve
  uv run python -m wfc.scripts.orchestrators.claude_md.cli --write .

  # Heuristic mode (no API key required)
  uv run python -m wfc.scripts.orchestrators.claude_md.cli --no-llm .
        """,
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the rewritten CLAUDE.md (prompts for confirmation)",
    )
    parser.add_argument(
        "--write-force",
        action="store_true",
        help="Write the rewritten CLAUDE.md without prompting",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Show report only, no writes (default)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Use heuristic agents only (no API key required)",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write report to a file instead of stdout",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON result instead of markdown report",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )
    return parser


def _make_llm_agents() -> dict:
    """Try to build LLM response functions using the Anthropic SDK.

    Returns a dict with keys: analyst, fixer, qa, reporter.
    Returns empty dict if SDK is unavailable.
    """
    try:
        import anthropic  # type: ignore[import]

        from .prompts import (
            ANALYST_PROMPT,
            CONTEXT_MAPPER_PROMPT,  # noqa: F401 — imported for reference
            FIXER_PROMPT,
            QA_VALIDATOR_PROMPT,
            REPORTER_PROMPT,
        )

        client = anthropic.Anthropic()

        def _make_fn(system: str, model: str = "claude-sonnet-4-6") -> callable:
            def fn(user_message: str) -> str:
                msg = client.messages.create(
                    model=model,
                    max_tokens=8192,
                    system=system,
                    messages=[{"role": "user", "content": user_message}],
                )
                return msg.content[0].text

            return fn

        return {
            "analyst": _make_fn(ANALYST_PROMPT),
            "fixer": _make_fn(FIXER_PROMPT),
            "qa": _make_fn(QA_VALIDATOR_PROMPT),
            "reporter": _make_fn(REPORTER_PROMPT, model="claude-haiku-4-5-20251001"),
        }
    except ImportError:
        logger.warning("anthropic SDK not installed — running in heuristic mode")
        return {}
    except Exception as e:
        logger.warning("Failed to initialize Anthropic client (%s) — heuristic mode", e)
        return {}


def _result_to_dict(result: RemediationResult) -> dict:
    return {
        "project_root": result.project_root,
        "claude_md_path": result.claude_md_path,
        "grade_before": result.grade_before,
        "grade_after": result.grade_after,
        "verdict": result.verdict,
        "original_lines": result.original_lines,
        "rewritten_lines": result.rewritten_lines,
        "original_instructions": result.original_instructions,
        "rewritten_instructions": result.rewritten_instructions,
        "succeeded": result.succeeded,
        "no_changes_needed": result.no_changes_needed,
        "changelog": result.changelog,
        "migration_plan": result.migration_plan,
        "extracted_files": [{"path": f.path, "content": f.content} for f in result.extracted_files],
        "rewritten_content": result.rewritten_content,
        "report": result.report,
        "error": result.error,
    }


def _confirm_write() -> bool:
    try:
        answer = input("Write rewritten CLAUDE.md? [y/N] ").strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def _write_results(result: RemediationResult, project_root: Path, force: bool = False) -> None:
    """Write rewritten CLAUDE.md and extracted files to disk."""
    if result.rewritten_content is None:
        print("Nothing to write (no rewrite produced).", file=sys.stderr)
        return

    if not force and not _confirm_write():
        print("Write cancelled.", file=sys.stderr)
        return

    claude_md = project_root / "CLAUDE.md"
    backup = project_root / "CLAUDE.md.bak"
    if claude_md.exists():
        backup.write_text(claude_md.read_text(errors="replace"))
        print(f"Backup written to {backup}")

    claude_md.write_text(result.rewritten_content)
    print(f"Written: {claude_md}")

    for extracted in result.extracted_files:
        dest = project_root / extracted.path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(extracted.content)
        print(f"Created: {dest}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s %(levelname)s %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)

    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"Error: {project_root} does not exist", file=sys.stderr)
        return 1

    claude_md = project_root / "CLAUDE.md"
    if not claude_md.exists():
        print(f"Error: No CLAUDE.md found in {project_root}", file=sys.stderr)
        return 1

    llm_agents: dict = {}
    if not args.no_llm:
        llm_agents = _make_llm_agents()
        if not llm_agents:
            print(
                "Info: Running in heuristic mode (no LLM agents). "
                "Install anthropic SDK and set ANTHROPIC_API_KEY for full analysis.",
                file=sys.stderr,
            )

    try:
        result = remediate(
            project_root,
            analyst_response_fn=llm_agents.get("analyst"),
            fixer_response_fn=llm_agents.get("fixer"),
            qa_response_fn=llm_agents.get("qa"),
            reporter_response_fn=llm_agents.get("reporter"),
            config=PipelineConfig(),
        )
    except Exception as e:
        print(f"Pipeline error: {e}", file=sys.stderr)
        return 1

    if args.json:
        output = json.dumps(_result_to_dict(result), indent=2)
    else:
        output = result.report

    if args.output:
        Path(args.output).write_text(output)
        print(f"Report written to {args.output}")
    else:
        print(output)

    if args.write_force:
        _write_results(result, project_root, force=True)
    elif args.write:
        _write_results(result, project_root, force=False)

    return 0 if result.succeeded or result.no_changes_needed else 1


if __name__ == "__main__":
    sys.exit(main())
