"""
Commit-msg hook - Validates commit message format

Soft enforcement: Warns but NEVER blocks commits.
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def validate_commit_message(message: str) -> Dict[str, Any]:
    """
    Validate commit message against conventional commits format.

    Expected format:
    - <type>: <description>
    - <type>(scope): <description>
    - TASK-XXX: <description>

    Valid types: feat, fix, chore, refactor, test, docs, security, perf, ci
    """
    lines = message.strip().split("\n")
    if not lines:
        return {"valid": False, "message": "Empty commit message"}

    first_line = lines[0].strip()

    # Check for TASK-XXX prefix (preferred)
    task_pattern = r"^TASK-\d+:"
    if re.match(task_pattern, first_line):
        return {"valid": True, "message": "Task-based commit message"}

    # Check for conventional commit format
    conventional_pattern = (
        r"^(feat|fix|chore|refactor|test|docs|security|perf|ci|build|style)(\(.+\))?: .+"
    )
    if re.match(conventional_pattern, first_line):
        return {"valid": True, "message": "Conventional commit format"}

    # Invalid format
    return {
        "valid": False,
        "message": "Commit message doesn't follow convention",
        "suggestion": "Use: TASK-XXX: description OR feat/fix/chore: description",
        "examples": [
            "TASK-001: Add rate limiting to API",
            "feat: add user authentication",
            "fix(api): resolve timeout issue",
            "chore: update dependencies",
        ],
    }


def extract_task_id(message: str) -> Optional[str]:
    """Extract TASK-XXX from commit message if present."""
    match = re.search(r"TASK-(\d+)", message)
    if match:
        return f"TASK-{match.group(1)}"
    return None


def log_telemetry(event: str, data: Dict[str, Any]) -> None:
    """Log hook event to telemetry (if available)."""
    try:
        from wfc.shared.telemetry_auto import log_event

        log_event(event, data)
    except Exception:
        # Telemetry not available or failed - continue
        pass


def commit_msg_hook(commit_msg_file: str) -> int:
    """
    Commit-msg hook - soft enforcement.

    Checks:
    1. Validate commit message format
    2. Suggest improvements
    3. Log violations to telemetry

    Args:
        commit_msg_file: Path to .git/COMMIT_EDITMSG

    Returns:
        0 (always - never blocks)
    """
    try:
        message = Path(commit_msg_file).read_text()
    except Exception as e:
        print(f"⚠️  Could not read commit message: {e}")
        return 0

    validation = validate_commit_message(message)

    if not validation["valid"]:
        print(f"\n⚠️  WARNING: {validation['message']}")
        print(f"   Suggestion: {validation.get('suggestion', 'N/A')}")

        if "examples" in validation:
            print("\n   Examples:")
            for example in validation["examples"]:
                print(f"     - {example}")

        print()

        # Log telemetry
        log_telemetry(
            "hook_warning",
            {
                "hook": "commit-msg",
                "violation": "non_conventional_commit",
                "message": message.split("\n")[0],
                "validation_message": validation["message"],
            },
        )

        print("✅ Commit allowed (soft enforcement - message format warning)\n")

    # Extract and log task ID if present
    task_id = extract_task_id(message)
    if task_id:
        log_telemetry(
            "commit_with_task",
            {"hook": "commit-msg", "task_id": task_id, "message": message.split("\n")[0]},
        )

    return 0


def main():
    """Entry point for git hook."""
    if len(sys.argv) < 2:
        print("Error: commit message file not provided")
        sys.exit(1)

    sys.exit(commit_msg_hook(sys.argv[1]))


if __name__ == "__main__":
    main()
