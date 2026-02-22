"""CLI entry point for skill fixer orchestrator."""

import argparse
import sys
from pathlib import Path

from .orchestrator import SkillFixerOrchestrator


def main():
    """CLI main entry point."""
    parser = argparse.ArgumentParser(
        description="Fix Claude Skills using 6-agent pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fix a single skill
  python -m wfc.scripts.orchestrators.skill_fixer.cli ~/.claude/skills/wfc-build

  # Fix with functional QA
  python -m wfc.scripts.orchestrators.skill_fixer.cli --functional-qa ~/.claude/skills/wfc-build

  # Batch fix multiple skills
  python -m wfc.scripts.orchestrators.skill_fixer.cli ~/.claude/skills/wfc-*
""",
    )

    parser.add_argument(
        "skill_path",
        type=str,
        help="Path to skill directory (or glob pattern for batch)",
    )

    parser.add_argument(
        "--functional-qa",
        action="store_true",
        help="Run functional QA (optional, slow)",
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Maximum retry attempts (default: 2)",
    )

    args = parser.parse_args()

    skill_path = Path(args.skill_path).expanduser()

    if not skill_path.exists():
        print(f"Error: Skill path not found: {skill_path}", file=sys.stderr)
        sys.exit(1)

    orchestrator = SkillFixerOrchestrator()

    try:
        report = orchestrator.fix_skill(
            skill_path,
            run_functional_qa=args.functional_qa,
            max_retries=args.max_retries,
        )

        print("\n" + "=" * 60)
        print(report.report_text)
        print("=" * 60)

        if report.summary.structural_verdict == "FAIL":
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
