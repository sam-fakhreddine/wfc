#!/usr/bin/env python3
"""Run REAL consensus review with actual Claude subagents."""

import json
import subprocess
import sys
from pathlib import Path

from wfc.scripts.orchestrators.review.orchestrator import (
    ReviewOrchestrator,
    ReviewRequest,
)


def main():
    result = subprocess.run(
        [
            "git",
            "diff",
            "develop..claude/add-prompt-fixer-and-doctor",
            "--",
            "wfc/scripts/orchestrators/review/",
            "tests/orchestrators/review/",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    diff_content = result.stdout

    files_result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "develop..claude/add-prompt-fixer-and-doctor",
            "--",
            "wfc/scripts/orchestrators/review/",
            "tests/orchestrators/review/",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    files = [f.strip() for f in files_result.stdout.splitlines() if f.strip()]

    print("=" * 70)
    print("REAL CONSENSUS REVIEW - DIFF MANIFEST IMPLEMENTATION")
    print("=" * 70)
    print(f"\n🔍 Files: {len(files)}")
    print(f"📊 Diff size: {len(diff_content):,} characters")
    print("\nThis will invoke 5 real Claude subagents. This takes time.\n")

    orchestrator = ReviewOrchestrator(use_diff_manifest=True)

    request = ReviewRequest(
        task_id="diff-manifest-impl-review",
        files=files,
        diff_content=diff_content,
        properties=[
            {
                "type": "SAFETY",
                "statement": "When use_diff_manifest=False, behavior must be identical to current implementation",
            },
            {
                "type": "PERFORMANCE",
                "statement": "When use_diff_manifest=True, token usage must be reduced by ≥70%",
            },
            {
                "type": "INVARIANT",
                "statement": "Finding counts with manifests must be within ±15% of full diff findings",
            },
            {
                "type": "LIVENESS",
                "statement": "All 5 reviewers must successfully process manifests",
            },
            {
                "type": "SAFETY",
                "statement": "If manifest builder fails, system must fall back to full diff without crashing",
            },
        ],
    )

    print("📋 Phase 1: Preparing review tasks...")
    tasks = orchestrator.prepare_review(request)

    print(f"\n✅ Prepared {len(tasks)} reviewer tasks:")
    for task in tasks:
        relevant = "✓" if task["relevant"] else "✗"
        tokens = task.get("token_count", 0)
        metrics = task.get("token_metrics")
        if metrics:
            reduction = metrics.get("reduction_pct", 0)
            print(
                f"  [{relevant}] {task['reviewer_name']}: ~{tokens:,} tokens "
                f"({reduction:.1f}% reduction via manifest)"
            )
        else:
            print(f"  [{relevant}] {task['reviewer_name']}: ~{tokens:,} tokens")

    tasks_file = Path(".development/review_tasks.json")
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    with open(tasks_file, "w") as f:
        json.dump(tasks, f, indent=2, default=str)
    print(f"\n💾 Tasks saved to: {tasks_file}")

    print("\n" + "=" * 70)
    print("NEXT STEPS - MANUAL REVIEW INVOCATION")
    print("=" * 70)
    print("\nTo complete this review, invoke each reviewer as a Task:")
    print()

    for i, task in enumerate(tasks, 1):
        if not task["relevant"]:
            print(f"{i}. {task['reviewer_name']}: SKIPPED (not relevant)")
            continue

        print(f"{i}. {task['reviewer_name']}:")
        print(f"   Task tool with prompt from tasks_file[{i - 1}]['prompt']")
        print(f"   Temperature: {task['temperature']}")
        print()

    print("\nOnce you have all responses, run:")
    print("  python finalize_review.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
