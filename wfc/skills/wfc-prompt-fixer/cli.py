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

    if wfc_mode and no_wfc:
        print("❌ Error: --wfc and --no-wfc are mutually exclusive")
        return 1

    path_str = path_args[0]

    if not path_str.strip():
        print("❌ Error: Path argument is empty")
        return 1

    MAX_PATH_LENGTH = 4096
    if len(path_str) > MAX_PATH_LENGTH:
        print(f"❌ Error: Path exceeds maximum length ({MAX_PATH_LENGTH} characters)")
        return 1

    try:
        prompt_path = Path(path_str).resolve()
    except (ValueError, OSError) as e:
        print(f"❌ Error: Invalid path '{path_str}': {e}")
        return 1

    if not batch_mode and not prompt_path.exists():
        print(f"❌ Error: File does not exist: {prompt_path}")
        return 1

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
