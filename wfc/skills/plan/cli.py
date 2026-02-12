"""
CLI Presentation Tier for wfc-plan

Handles user interaction and output formatting.
"""

import sys
from pathlib import Path
from typing import Optional

from .orchestrator import PlanOrchestrator

# Import from shared (two levels up from skills/plan)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.telemetry import get_telemetry
from shared.config import get_config


class PlanCLI:
    """
    CLI interface for wfc-plan.

    MULTI-TIER: Presentation layer only.
    """

    def __init__(self):
        self.config = get_config()
        self.telemetry = get_telemetry()

    def run(self, output_dir: Optional[str] = None) -> int:
        """
        Run planning process.

        Returns exit code (0 = success).
        """

        try:
            # Parse output directory
            if output_dir:
                out_path = Path(output_dir)
            else:
                out_path = Path(self.config.get("plan.output_dir", "./plan"))

            # Display header
            self._print_header()

            # Run orchestrator
            orchestrator = PlanOrchestrator(out_path)
            result = orchestrator.run()

            # Display results
            self._print_results(result)

            # Record telemetry
            self.telemetry.record("plan", {
                "status": "success",
                "output_dir": str(result.output_dir),
                "tasks_count": len(open(result.tasks_file).read().split("## TASK-")) - 1,
                "properties_count": len(open(result.properties_file).read().split("## PROP-")) - 1,
            })

            return 0

        except Exception as e:
            self._print_error(f"Planning failed: {e}")
            self.telemetry.record("plan", {
                "status": "error",
                "error": str(e)
            })
            return 1

    def _print_header(self) -> None:
        """Print CLI header"""
        print("=" * 80)
        print("WFC:PLAN - Adaptive Planning with Formal Properties")
        print("=" * 80)
        print()

    def _print_results(self, result) -> None:
        """Print planning results"""
        print()
        print("=" * 80)
        print("✨ PLANNING COMPLETE")
        print("=" * 80)
        print()
        print(f"📁 Output Directory: {result.output_dir}")
        print()
        print(f"✅ TASKS.md:      {result.tasks_file}")
        print(f"✅ PROPERTIES.md: {result.properties_file}")
        print(f"✅ TEST-PLAN.md:  {result.test_plan_file}")
        print()
        print(f"🎯 Goal: {result.interview_result.goal}")
        print()
        print("Next step: Run `/wfc-implement {result.tasks_file}` to start implementation")
        print("=" * 80)

    def _print_error(self, message: str) -> None:
        """Print error message"""
        print(f"❌ ERROR: {message}", file=sys.stderr)


def main():
    """Entry point for CLI"""
    cli = PlanCLI()
    output_dir = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(cli.run(output_dir))


if __name__ == "__main__":
    main()
