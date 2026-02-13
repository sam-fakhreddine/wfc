"""
Pre-push hook - Warns about pushing to protected branches

Soft enforcement: Warns but NEVER blocks pushes.
"""

import subprocess
import sys
from typing import Dict, Any, List, Tuple, Optional


def parse_push_info() -> List[Tuple[str, str]]:
    """
    Parse push information from stdin.

    Git passes push info via stdin in format:
    <local ref> <local sha> <remote ref> <remote sha>

    Returns:
        List of (local_ref, remote_ref) tuples
    """
    pushes = []
    for line in sys.stdin:
        parts = line.strip().split()
        if len(parts) >= 3:
            local_ref = parts[0]  # e.g., refs/heads/main
            remote_ref = parts[2]  # e.g., refs/heads/main

            # Extract branch names
            local_branch = local_ref.replace("refs/heads/", "")
            remote_branch = remote_ref.replace("refs/heads/", "")

            pushes.append((local_branch, remote_branch))

    return pushes


def get_remote_url() -> Optional[str]:
    """Get remote URL for current repo."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def is_force_push() -> bool:
    """Check if this is a force push."""
    try:
        # Check git command line for force flags
        # This is a simplified check - in practice, git doesn't pass this info directly
        # We rely on git's own force-push prevention
        return False
    except Exception:
        return False


def log_telemetry(event: str, data: Dict[str, Any]) -> None:
    """Log hook event to telemetry (if available)."""
    try:
        from wfc.shared.telemetry_auto import log_event

        log_event(event, data)
    except Exception:
        # Telemetry not available or failed - continue
        pass


def pre_push_hook() -> int:
    """
    Pre-push hook - soft enforcement.

    Checks:
    1. Warn if pushing to protected branches (main/master/develop/production)
    2. Warn about force pushes
    3. Log violations to telemetry

    Returns:
        0 (always - never blocks)
    """
    protected_branches = ["main", "master", "develop", "production"]
    pushes = parse_push_info()

    if not pushes:
        # No push info available - allow
        return 0

    violations = []
    remote_url = get_remote_url()

    for local_branch, remote_branch in pushes:
        # Check 1: Protected branch warning
        if remote_branch in protected_branches:
            print(f"\n⚠️  WARNING: Pushing to protected branch '{remote_branch}'")
            print(f"   Local branch: {local_branch}")
            if remote_url:
                print(f"   Remote: {remote_url}")
            print("\n   Consider:")
            print("     1. Create a PR instead")
            print("     2. Use WFC PR workflow (default)")
            print(f"     3. Ensure you have permission to push to {remote_branch}")
            print()

            violations.append(
                {
                    "type": "push_to_protected",
                    "local_branch": local_branch,
                    "remote_branch": remote_branch,
                    "severity": "warning",
                }
            )

            # Log telemetry
            log_telemetry(
                "hook_warning",
                {
                    "hook": "pre-push",
                    "violation": "push_to_protected",
                    "local_branch": local_branch,
                    "remote_branch": remote_branch,
                    "remote_url": remote_url,
                },
            )

    # Check 2: Force push warning (if detectable)
    if is_force_push():
        print("\n⚠️  WARNING: Force push detected")
        print("   Force pushes can overwrite remote history")
        print("   Consider using --force-with-lease for safety")
        print()

        violations.append({"type": "force_push", "severity": "warning"})

        # Log telemetry
        log_telemetry(
            "hook_warning",
            {"hook": "pre-push", "violation": "force_push", "branches": pushes},
        )

    # Always succeed (soft enforcement)
    if violations:
        print(f"✅ Push allowed (soft enforcement - {len(violations)} warnings)\n")

    return 0


def main():
    """Entry point for git hook."""
    sys.exit(pre_push_hook())


if __name__ == "__main__":
    main()
