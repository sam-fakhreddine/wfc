#!/usr/bin/env python3
"""
WFC Build CLI

Entry point for /wfc-build skill.
Intentional Vibe: Quick interview → delegate to subagent(s) → ship it.
"""

import sys
from pathlib import Path

# Add WFC to path for imports
wfc_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(wfc_root))

from .orchestrator import BuildOrchestrator  # noqa: E402


def main():
    """
    Main entry point for wfc-build.

    Usage:
        /wfc-build
        /wfc-build "add progressive doc loader"
        /wfc-build "add OAuth2 authentication"
    """
    # Get description from args
    description = None
    if len(sys.argv) > 1:
        description = " ".join(sys.argv[1:])

    # Get project root (current directory)
    project_root = Path.cwd()

    print("\n🎯 WFC:BUILD - Intentional Vibe")
    print("   Vibe coding + WFC guardrails = Professional quality\n")

    # Run orchestrator
    orchestrator = BuildOrchestrator(project_root)

    try:
        result = orchestrator.run(description)

        # Display result
        print("\n" + "=" * 60)
        print("✅ BUILD INITIATED")
        print("=" * 60)
        print(f"Status: {result['status']}")
        print(f"Agents: {result['agents']}")
        print(f"Complexity: {result['spec'].complexity}")
        print("\n📋 Next Steps:")
        print("   1. Subagent(s) will implement in isolated worktree(s)")
        print("   2. TDD workflow: TEST → IMPLEMENT → REFACTOR")
        print("   3. Quality checks: formatters, linters, tests")
        print("   4. Consensus review: wfc-review")
        print("   5. Auto-merge to main (or rollback on failure)")
        print("\n⏳ Waiting for subagent(s) to complete...")

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Build cancelled by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
