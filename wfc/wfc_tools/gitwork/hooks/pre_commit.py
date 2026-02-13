"""
Pre-commit hook - Warns about direct commits to protected branches

Soft enforcement: Warns but NEVER blocks commits.
"""

import subprocess
import sys
from typing import Dict, Any, List, Optional


def get_current_branch() -> Optional[str]:
    """Get current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_staged_files() -> List[str]:
    """Get list of staged files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return [f for f in result.stdout.strip().split("\n") if f]
    except Exception:
        pass
    return []


def validate_branch_name(branch: str) -> Dict[str, Any]:
    """
    Validate branch name against WFC conventions.

    Expected formats:
    - feat/TASK-XXX-description
    - fix/TASK-XXX-description
    - chore/TASK-XXX-description
    - refactor/TASK-XXX-description
    - test/TASK-XXX-description
    - security/TASK-XXX-description
    """
    valid_prefixes = ["feat", "fix", "chore", "refactor", "test", "security", "docs"]

    # Check if branch follows convention
    parts = branch.split("/")
    if len(parts) < 2:
        return {
            "valid": False,
            "message": f"Branch '{branch}' doesn't follow convention",
            "suggestion": "Expected: feat/TASK-XXX-description",
        }

    prefix = parts[0]
    if prefix not in valid_prefixes:
        return {
            "valid": False,
            "message": f"Unknown prefix '{prefix}'",
            "suggestion": f"Expected one of: {', '.join(valid_prefixes)}",
        }

    # Check for TASK-XXX in branch name
    if len(parts) >= 2 and not parts[1].startswith("TASK-"):
        return {
            "valid": False,
            "message": "Missing TASK-XXX identifier",
            "suggestion": f"Expected: {prefix}/TASK-XXX-description",
        }

    return {"valid": True, "message": "Branch name follows convention"}


def check_sensitive_files(files: List[str]) -> List[str]:
    """Check for sensitive files in staged changes."""
    sensitive_patterns = [
        ".env",
        "credentials.json",
        "secrets.json",
        ".pem",
        ".key",
        "id_rsa",
        "password",
        "token",
    ]

    sensitive_files = []
    for f in files:
        lower_f = f.lower()
        for pattern in sensitive_patterns:
            if pattern in lower_f:
                sensitive_files.append(f)
                break

    return sensitive_files


def log_telemetry(event: str, data: Dict[str, Any]) -> None:
    """Log hook event to telemetry (if available)."""
    try:
        from wfc.shared.telemetry_auto import log_event

        log_event(event, data)
    except Exception:
        # Telemetry not available or failed - continue
        pass


def pre_commit_hook() -> int:
    """
    Pre-commit hook - soft enforcement.

    Checks:
    1. Warn if committing to protected branch (main/master)
    2. Validate branch name convention
    3. Warn about sensitive files
    4. Log violations to telemetry

    Returns:
        0 (always - never blocks)
    """
    current_branch = get_current_branch()
    if not current_branch:
        print("⚠️  Could not determine current branch")
        return 0

    staged_files = get_staged_files()
    violations = []

    # Check 1: Protected branch warning
    protected_branches = ["main", "master", "develop", "production"]
    if current_branch in protected_branches:
        print(f"\n⚠️  WARNING: Committing directly to '{current_branch}'")
        print("   Consider: git checkout -b feat/TASK-XXX-description")
        print()

        violations.append(
            {
                "type": "direct_commit_to_protected",
                "branch": current_branch,
                "severity": "warning",
            }
        )

        # Log telemetry
        log_telemetry(
            "hook_warning",
            {
                "hook": "pre-commit",
                "violation": "direct_commit_to_protected",
                "branch": current_branch,
                "user_bypassed": False,
            },
        )

    # Check 2: Branch name validation (only for non-protected branches)
    if current_branch not in protected_branches:
        validation = validate_branch_name(current_branch)
        if not validation["valid"]:
            print(f"\n⚠️  WARNING: {validation['message']}")
            print(f"   Suggestion: {validation['suggestion']}")
            print()

            violations.append(
                {
                    "type": "non_conventional_branch",
                    "branch": current_branch,
                    "severity": "warning",
                }
            )

            # Log telemetry
            log_telemetry(
                "hook_warning",
                {
                    "hook": "pre-commit",
                    "violation": "non_conventional_branch",
                    "branch": current_branch,
                    "message": validation["message"],
                },
            )

    # Check 3: Sensitive files warning
    sensitive_files = check_sensitive_files(staged_files)
    if sensitive_files:
        print("\n⚠️  WARNING: Potentially sensitive files detected:")
        for f in sensitive_files:
            print(f"   - {f}")
        print("   Ensure these files don't contain secrets/credentials")
        print()

        violations.append(
            {
                "type": "sensitive_files_staged",
                "files": sensitive_files,
                "severity": "warning",
            }
        )

        # Log telemetry
        log_telemetry(
            "hook_warning",
            {
                "hook": "pre-commit",
                "violation": "sensitive_files_staged",
                "files": sensitive_files,
                "count": len(sensitive_files),
            },
        )

    # Always succeed (soft enforcement)
    if violations:
        print(f"✅ Commit allowed (soft enforcement - {len(violations)} warnings)\n")

    return 0


def main():
    """Entry point for git hook."""
    sys.exit(pre_commit_hook())


if __name__ == "__main__":
    main()
