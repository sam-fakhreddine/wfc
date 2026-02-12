#!/usr/bin/env python3
"""
WFC Metrics CLI

View telemetry data for WFC tasks.
"""

import sys
from pathlib import Path

# Add parent to path for wfc imports
wfc_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(wfc_root))

from wfc.shared.telemetry_auto import view_metrics


def main():
    """CLI entry point"""
    if len(sys.argv) == 1:
        # No arguments - show aggregate
        view_metrics()
    elif sys.argv[1] in ["-h", "--help"]:
        print("WFC Metrics Viewer")
        print("\nUsage:")
        print("  wfc metrics              # View aggregate metrics")
        print("  wfc metrics TASK-001     # View specific task metrics")
        print("  wfc metrics --all        # View aggregate metrics")
    elif sys.argv[1] == "--all":
        view_metrics()
    else:
        # Show specific task
        task_id = sys.argv[1]
        view_metrics(task_id)


if __name__ == "__main__":
    main()
