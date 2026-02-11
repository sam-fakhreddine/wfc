"""
Rollback operations API

Atomic revert with recovery plan generation.
"""

import subprocess
from typing import Dict


def revert(merge_sha: str) -> Dict:
    """Atomic revert of merge commit"""
    try:
        subprocess.run(
            ["git", "revert", "--no-edit", merge_sha],
            check=True,
            capture_output=True
        )
        
        # Get revert SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True
        )
        
        return {
            "success": True,
            "revert_sha": result.stdout.strip(),
            "message": f"Reverted {merge_sha}"
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "message": f"Revert failed: {e.stderr.decode() if e.stderr else str(e)}"
        }


def verify() -> Dict:
    """Verify main branch is clean after rollback"""
    try:
        # Run tests or checks
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True
        )
        
        clean = len(result.stdout.strip()) == 0
        
        return {
            "success": True,
            "clean": clean,
            "message": "Main is clean" if clean else "Main has uncommitted changes"
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "message": f"Verification failed: {e.stderr.decode() if e.stderr else str(e)}"
        }


def plan(task_id: str, context: Dict) -> str:
    """Generate PLAN.md for recovery"""
    plan = f"""# Recovery Plan - {task_id}

## Failure Context

- **Task**: {task_id}
- **Merge SHA**: {context.get('merge_sha', 'N/A')}
- **Revert SHA**: {context.get('revert_sha', 'N/A')}
- **Failed Tests**: {', '.join(context.get('failed_tests', []))}

## Investigation Steps

1. Review the failed tests output
2. Check what changed between worktree creation and merge
3. Identify file conflicts or interaction issues
4. Verify property violations

## Fix Plan

1. Rebase task branch onto latest main
2. Resolve any conflicts
3. Fix failing tests
4. Re-run full test suite
5. Re-submit for review

## Next Actions

- [ ] Investigate failure root cause
- [ ] Apply fixes in preserved worktree
- [ ] Re-test locally
- [ ] Re-submit for review
"""
    return plan
