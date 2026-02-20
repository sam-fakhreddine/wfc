"""CLI entry point for wfc-prompt-fixer skill."""

import sys
from pathlib import Path

from .orchestrator import PromptFixerOrchestrator


def main() -> int:
    """Entry point for /wfc-prompt-fixer slash command."""
    args = sys.argv[1:]

    if not args or args[0] in ["-h", "--help"]:
        print(__doc__)
        print("\nUsage:")
        print("  /wfc-prompt-fixer <path>              # Fix single prompt")
        print("  /wfc-prompt-fixer --batch <pattern>   # Fix multiple prompts")
        print("  /wfc-prompt-fixer --wfc <path>        # Force WFC mode")
        print("  /wfc-prompt-fixer --no-wfc <path>     # Disable WFC checks")
        print("  /wfc-prompt-fixer --auto-pr <path>    # Auto-create PR")
        return 0

    batch_mode = "--batch" in args
    wfc_mode = "--wfc" in args
    no_wfc = "--no-wfc" in args
    auto_pr = "--auto-pr" in args

    path_args = [arg for arg in args if not arg.startswith("--")]

    if not path_args:
        print("❌ Error: No path provided")
        return 1

    prompt_path = Path(path_args[0])

    orchestrator = PromptFixerOrchestrator(cwd=Path.cwd())

    try:
        if batch_mode:
            print(f"🔧 Batch mode: {prompt_path}")
            results = orchestrator.fix_batch(
                pattern=str(prompt_path),
                wfc_mode=wfc_mode if wfc_mode else (not no_wfc),
                auto_pr=auto_pr,
            )
            print(f"\n✅ Fixed {len(results)} prompts")
            for result in results:
                print(f"  - {result.prompt_name}: {result.grade_before} → {result.grade_after}")
        else:
            print(f"🔧 Fixing prompt: {prompt_path}")
            result = orchestrator.fix_prompt(
                prompt_path=prompt_path,
                wfc_mode=wfc_mode if wfc_mode else (not no_wfc),
                auto_pr=auto_pr,
            )
            print(f"\n✅ Grade: {result.grade_before} → {result.grade_after}")
            print(f"📄 Report: {result.report_path}")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
