"""Shared utilities for WFC hooks.

Provides color codes, session path helpers, file-length checks,
stdin parsing, and regex timeout helpers used across PreToolUse
and PostToolUse hooks.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import re
import subprocess
import sys
import threading
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

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


_SIGALRM_AVAILABLE = (
    platform.system() != "Windows"
    and hasattr(__import__("signal"), "SIGALRM")
    and threading.current_thread() is threading.main_thread()
)


class RegexTimeout(Exception):
    """Raised when regex compilation or matching times out."""


def _regex_timeout_handler(signum, frame):
    raise RegexTimeout("Regex operation timed out")


@contextmanager
def regex_timeout(seconds: int = 1):
    """Context manager for regex operations with timeout protection.

    On Unix main thread: uses SIGALRM for hard timeout.
    On Windows or non-main threads: no-op (degrades gracefully with warning on first use).
    """
    if not _SIGALRM_AVAILABLE:
        yield
        return

    import signal

    old_handler = signal.signal(signal.SIGALRM, _regex_timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


@lru_cache(maxsize=256)
def compile_regex(pattern: str) -> Optional[re.Pattern]:
    """Compile a regex pattern with caching and timeout protection.

    Returns None on invalid patterns or compilation timeout.
    The timeout is baked in (1 second) — not a parameter — because
    lru_cache keys must be stable.
    """
    try:
        with regex_timeout(1):
            return re.compile(pattern)
    except (re.error, RegexTimeout) as e:
        logger.debug("Regex pattern failed '%s': %s", pattern, e)
        return None


def safe_regex_search(pattern: str, text: str) -> bool:
    """Search text against a regex pattern with timeout protection.

    Returns False on timeout, invalid pattern, or no match.
    """
    compiled = compile_regex(pattern)
    if compiled is None:
        return False
    try:
        with regex_timeout(1):
            return bool(compiled.search(text))
    except RegexTimeout:
        logger.warning("Regex match timed out for pattern: %s", pattern[:50])
        return False


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
            f"   Split into smaller, focused modules (<{FILE_LENGTH_WARN} lines each).",
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
