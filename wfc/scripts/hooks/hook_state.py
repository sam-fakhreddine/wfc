"""
Session-scoped state manager for WFC hooks.

Tracks which warnings have been shown to avoid duplicate noise.
State is scoped to the current session (parent PID) and persisted as
JSON in a temp directory.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Optional


def _session_key() -> str:
    """Generate a stable session key from parent PID and process start time."""
    ppid = os.getppid()
    # Use parent PID as the session identifier - all hook invocations
    # within the same Claude Code session share the same parent.
    return f"wfc-hooks-{ppid}"


def _state_path(session_key: Optional[str] = None) -> Path:
    """Return path to the session state file in the system temp directory."""
    key = session_key or _session_key()
    return Path(tempfile.gettempdir()) / f"{key}.json"


class HookState:
    """
    Session-scoped state for deduplicating hook warnings.

    Backed by a JSON file in /tmp keyed by the parent process ID.
    This ensures all hook invocations within the same Claude Code session
    share state, while different sessions get independent state.
    """

    def __init__(self, session_key: Optional[str] = None) -> None:
        self._path = _state_path(session_key)
        self._warned: dict[str, list[str]] = {}
        self._load()

    def _load(self) -> None:
        """Load existing state from disk, if any."""
        try:
            if self._path.exists():
                data = json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._warned = data.get("warned", {})
                    # Expire stale sessions (older than 24 hours)
                    created = data.get("created", 0)
                    if time.time() - created > 86400:
                        self._warned = {}
        except (json.JSONDecodeError, OSError, KeyError):
            self._warned = {}

    def _save(self) -> None:
        """Persist state to disk."""
        try:
            data = {
                "warned": self._warned,
                "created": time.time(),
            }
            self._path.write_text(json.dumps(data), encoding="utf-8")
        except OSError:
            pass  # Non-critical - worst case we re-warn

    def has_warned(self, file_path: str, pattern_id: str) -> bool:
        """Check if a warning has already been shown for this file + pattern combo."""
        patterns = self._warned.get(file_path, [])
        return pattern_id in patterns

    def mark_warned(self, file_path: str, pattern_id: str) -> None:
        """Record that a warning was shown for this file + pattern combo."""
        if file_path not in self._warned:
            self._warned[file_path] = []
        if pattern_id not in self._warned[file_path]:
            self._warned[file_path].append(pattern_id)
        self._save()

    def clear(self) -> None:
        """Clear all state (useful for testing)."""
        self._warned = {}
        try:
            if self._path.exists():
                self._path.unlink()
        except OSError:
            pass  # Fail-open: hook bugs should never block the user
