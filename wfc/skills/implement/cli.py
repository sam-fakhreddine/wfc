"""
WFC Implement - CLI (Presentation Tier)

ELEGANT: Simple argument parsing, clean output
MULTI-TIER: Calls logic tier (orchestrator), formats results
PARALLEL: Could launch dashboard in background

This is the PRESENTATION TIER - it handles user input/output
but delegates all logic to the orchestrator.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from wfc.shared.config import get_config
from wfc.skills.implement.orchestrator import run_implementation, RunResult


def cli_implement(args: Optional[list] = None) -> int:
    """
    CLI entry point for /wfc:implement

    Args:
        args: Optional command line arguments (for testing)

    Returns:
        Exit code (0 = success, 1 = error)

    PRESENTATION TIER: This function handles:
    - Argument parsing
    - Input validation
    - Calling logic tier (orchestrator)
    - Formatting output
    - Exit codes

    It does NOT contain business logic.
    """
    parser = argparse.ArgumentParser(
        description="WFC Implement - Multi-Agent Parallel Implementation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  wfc:implement                        Use TASKS.md from /plan
  wfc:implement --tasks custom.md      Use custom tasks file
  wfc:implement --agents 5             Override agent count
  wfc:implement --strategy smart       Use smart grouping strategy
  wfc:implement --dry-run              Show plan without executing

Philosophy:
  ELEGANT - Simple and effective over over-engineered
  MULTI-TIER - Any front-end on any application
  PARALLEL - Work in parallel always
        """
    )

    parser.add_argument(
        "--tasks",
        type=Path,
        default=Path("plan/TASKS.md"),
        help="Path to TASKS.md (default: plan/TASKS.md)"
    )

    parser.add_argument(
        "--agents",
        type=int,
        help="Number of concurrent agents (overrides config)"
    )

    parser.add_argument(
        "--strategy",
        choices=["one_per_task", "pool", "smart"],
        help="Agent assignment strategy (overrides config)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without executing"
    )

    parser.add_argument(
        "--project",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)"
    )

    parsed_args = parser.parse_args(args)

    # PRESENTATION: Display header
    print("🚀 WFC Implement - Multi-Agent Parallel Implementation")
    print("=" * 60)
    print()

    # PRESENTATION: Validate inputs
    if not parsed_args.tasks.exists():
        print(f"❌ Error: Tasks file not found: {parsed_args.tasks}")
        print()
        print("Create tasks file with:")
        print(f"  wfc:plan  (generates TASKS.md)")
        print()
        return 1

    if not parsed_args.project.exists():
        print(f"❌ Error: Project directory not found: {parsed_args.project}")
        return 1

    # PRESENTATION: Load config (from DATA TIER)
    config = get_config(parsed_args.project)

    # PRESENTATION: Apply CLI overrides
    if parsed_args.agents:
        print(f"⚙️  Override: max_agents = {parsed_args.agents}")

    if parsed_args.strategy:
        print(f"⚙️  Override: strategy = {parsed_args.strategy}")

    if parsed_args.dry_run:
        print("⚙️  Dry run mode: showing plan without execution")

    print()
    print(f"📁 Project: {parsed_args.project}")
    print(f"📋 Tasks: {parsed_args.tasks}")
    print(f"🤖 Strategy: {config.get('orchestration.agent_strategy', 'smart')}")
    print(f"👥 Max agents: {config.get('orchestration.max_agents', 5)}")
    print()

    if parsed_args.dry_run:
        print("✅ Dry run complete - no changes made")
        return 0

    try:
        # LOGIC TIER: Run implementation (all business logic here)
        result = run_implementation(
            tasks_file=parsed_args.tasks,
            config=config,
            project_root=parsed_args.project
        )

        # PRESENTATION: Format and display results
        print()
        print("✅ Implementation complete!")
        print()
        print(f"📊 Results:")
        print(f"   Tasks completed: {result.tasks_completed}")
        print(f"   Tasks failed: {result.tasks_failed}")
        print(f"   Tasks rolled back: {result.tasks_rolled_back}")
        print(f"   Duration: {result.duration_ms / 1000:.1f}s")
        print(f"   Total tokens: {result.total_tokens.get('total', 0):,}")
        print()

        # Exit code based on failures
        if result.tasks_failed > 0:
            print("⚠️  Some tasks failed - see logs for details")
            return 1

        return 0

    except Exception as e:
        # PRESENTATION: Format error output
        print()
        print(f"❌ Error: {str(e)}")
        print()
        return 1


def main():
    """Entry point for command line."""
    sys.exit(cli_implement())


if __name__ == "__main__":
    main()
