"""Shared utilities for WFC PostToolUse hooks.

Provides color codes, session path helpers, file-length checks,
and stdin parsing used across file_checker, tdd_enforcer, and
context_monitor.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

RED = "\033[0;31m"
YELLOW = "\033[0;33m"
GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
BLUE = "\033[0;34m"
MAGENTA = "\033[0;35m"
NC = "\033[0m"

FILE_LENGTH_WARN = 300
FILE_LENGTH_CRITICAL = 500


def _sessions_base() -> Path:
    """Get base sessions directory for WFC state."""
    return Path.home() / ".wfc" / "sessions"


def get_session_id() -> str:
    """Get a session identifier from environment or default."""
    return os.environ.get("WFC_SESSION_ID", "").strip() or "default"


def get_session_cache_path() -> Path:
    """Get session-scoped context cache path."""
    sid = get_session_id()
    cache_dir = _sessions_base() / sid
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "context-cache.json"


def find_git_root() -> Path | None:
    """Find git repository root from cwd."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:
        pass
    return None


def read_hook_stdin() -> dict:
    """Read and parse JSON from stdin (Claude Code hook protocol)."""
    try:
        content = sys.stdin.read()
        if not content:
            return {}
        return json.loads(content)
    except (json.JSONDecodeError, OSError):
        return {}


def get_edited_file_from_stdin() -> Path | None:
    """Extract the edited file path from PostToolUse hook stdin."""
    try:
        import select

        if select.select([sys.stdin], [], [], 0)[0]:
            data = json.load(sys.stdin)
            tool_input = data.get("tool_input", {})
            file_path = tool_input.get("file_path")
            if file_path:
                return Path(file_path)
    except Exception:
        pass
    return None


def check_file_length(file_path: Path) -> bool:
    """Warn if file exceeds length thresholds.

    Returns True if warning was emitted, False otherwise.
    """
    try:
        line_count = len(file_path.read_text().splitlines())
    except Exception:
        return False

    if line_count > FILE_LENGTH_CRITICAL:
        print("", file=sys.stderr)
        print(
            f"{RED}FILE TOO LONG: {file_path.name} has {line_count} lines "
            f"(limit: {FILE_LENGTH_CRITICAL}){NC}",
            file=sys.stderr,
        )
        print(
            f"   Split into smaller, focused modules "
            f"(<{FILE_LENGTH_WARN} lines each).",
            file=sys.stderr,
        )
        return True
    elif line_count > FILE_LENGTH_WARN:
        print("", file=sys.stderr)
        print(
            f"{YELLOW}FILE GROWING LONG: {file_path.name} has {line_count} lines "
            f"(warn: {FILE_LENGTH_WARN}){NC}",
            file=sys.stderr,
        )
        print("   Consider splitting before it grows further.", file=sys.stderr)
        return True
    return False
