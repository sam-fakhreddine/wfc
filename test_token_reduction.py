"""Test token reduction with real diffs."""

import subprocess
from wfc.scripts.orchestrators.review.diff_manifest import (
    build_diff_manifest,
    format_manifest_for_reviewer,
)


def get_commit_diff(commit_hash: str) -> str:
    """Get diff for a commit."""
    result = subprocess.run(
        ["git", "show", commit_hash, "--unified=3"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def estimate_tokens(text: str) -> int:
    """Estimate token count (chars / 4)."""
    return len(text) // 4


def test_commit(commit_hash: str, commit_desc: str, reviewer_id: str):
    """Test token reduction for a specific commit."""
    print(f"\n{'='*70}")
    print(f"Testing: {commit_desc}")
    print(f"Commit: {commit_hash}")
    print(f"Reviewer: {reviewer_id}")
    print(f"{'='*70}")

    full_diff = get_commit_diff(commit_hash)
    full_diff_tokens = estimate_tokens(full_diff)

    print("\n📊 Full Diff:")
    print(f"   Characters: {len(full_diff):,}")
    print(f"   Estimated tokens: {full_diff_tokens:,}")

    manifest = build_diff_manifest(full_diff, reviewer_id)
    manifest_markdown = format_manifest_for_reviewer(manifest, reviewer_id)
    manifest_tokens = estimate_tokens(manifest_markdown)

    print("\n📊 Manifest:")
    print(f"   Characters: {len(manifest_markdown):,}")
    print(f"   Estimated tokens: {manifest_tokens:,}")

    reduction_pct = ((full_diff_tokens - manifest_tokens) / full_diff_tokens) * 100

    print("\n✅ Token Reduction:")
    print(f"   Before: {full_diff_tokens:,} tokens")
    print(f"   After: {manifest_tokens:,} tokens")
    print(f"   Saved: {full_diff_tokens - manifest_tokens:,} tokens ({reduction_pct:.1f}%)")

    print("\n📝 Manifest Preview (first 500 chars):")
    print("-" * 70)
    print(manifest_markdown[:500])
    if len(manifest_markdown) > 500:
        print("...")
    print("-" * 70)

    return {
        "commit": commit_hash,
        "description": commit_desc,
        "reviewer": reviewer_id,
        "full_diff_tokens": full_diff_tokens,
        "manifest_tokens": manifest_tokens,
        "reduction_pct": reduction_pct,
        "files_changed": manifest.files_changed,
        "lines_added": manifest.lines_added,
        "lines_removed": manifest.lines_removed,
    }


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("DIFF MANIFEST TOKEN REDUCTION TEST")
    print("=" * 70)

    results = []

    results.append(
        test_commit(
            "3588da9",
            "feat(skills): front-load orchestration mode constraints",
            "security",
        )
    )

    results.append(
        test_commit(
            "c15bcb6",
            "refactor(prompt-fixer): extract polling helper and optimize performance",
            "performance",
        )
    )

    results.append(
        test_commit(
            "72478b6",
            "fix(tests): add missing PEP 562 import for test_batch_performance",
            "correctness",
        )
    )

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total_before = sum(r["full_diff_tokens"] for r in results)
    total_after = sum(r["manifest_tokens"] for r in results)
    total_reduction = ((total_before - total_after) / total_before) * 100

    print("\n📊 Aggregate Results:")
    print(f"   Total tokens (before): {total_before:,}")
    print(f"   Total tokens (after): {total_after:,}")
    print(f"   Total saved: {total_before - total_after:,} tokens")
    print(f"   Average reduction: {total_reduction:.1f}%")

    print("\n📈 Per-Commit Breakdown:")
    for r in results:
        print(
            f"   {r['commit'][:7]} | {r['reduction_pct']:>5.1f}% reduction | "
            f"{r['files_changed']} files | {r['description'][:40]}"
        )

    print(f"\n{'='*70}")
    print("DECISION GATE: Validate >70% token savings")
    print(f"{'='*70}")

    if total_reduction >= 70:
        print(f"✅ PASS: {total_reduction:.1f}% reduction (target: 70%)")
        print("   → Diff reference architecture is viable")
        print("   → Proceed to Phase 1: Ultra-minimal prompts")
    elif total_reduction >= 50:
        print(f"⚠️  MARGINAL: {total_reduction:.1f}% reduction (target: 70%)")
        print("   → Proceed with caution")
        print("   → Consider tuning manifest format")
    else:
        print(f"❌ FAIL: {total_reduction:.1f}% reduction (target: 70%)")
        print("   → Diff reference architecture not viable")
        print("   → Abort Option B, consider Option A (prompts only)")

    print()
