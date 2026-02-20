"""CLI entry point for wfc-doctor skill."""

import sys
from pathlib import Path

from .orchestrator import DoctorOrchestrator


def main() -> int:
    """Entry point for /wfc-doctor slash command."""
    args = sys.argv[1:]

    if args and args[0] in ["-h", "--help"]:
        print(__doc__)
        print("\nUsage:")
        print("  /wfc-doctor              # Run all checks")
        print("  /wfc-doctor --fix        # Run checks + auto-fix")
        print("  /wfc-doctor --check-only # Report only, no fixes")
        return 0

    fix_mode = "--fix" in args
    check_only = "--check-only" in args

    orchestrator = DoctorOrchestrator(cwd=Path.cwd())

    try:
        result = orchestrator.run_health_check(auto_fix=fix_mode and not check_only)

        print(f"\n📊 WFC Health Check: {result.status}")
        print(f"📄 Report: {result.report_path}")

        if result.status == "PASS":
            return 0
        elif result.status == "WARN":
            return 1
        else:
            return 2

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
