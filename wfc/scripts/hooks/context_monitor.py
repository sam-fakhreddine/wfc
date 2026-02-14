#!/usr/bin/env python3
"""PostToolUse context monitor — warns when context usage is high.

Tracks context window consumption and provides tiered warnings:
  - 80%: Prepare for handoff (finish current task, then hand off)
  - 90%: Mandatory handoff (stop new work, write continuation notes)
  - 95%: Critical (handoff NOW, no more work)

Session-scoped: each WFC session tracks its own context independently,
enabling parallel sessions without interference.

Non-blocking: returns exit code 2 to show warnings without interrupting.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import CYAN, MAGENTA, NC, RED, YELLOW, get_session_cache_path, get_session_id

THRESHOLD_WARN = 80
THRESHOLD_STOP = 90
THRESHOLD_CRITICAL = 95
CONTEXT_WINDOW_TOKENS = 200_000


def _get_context_pct_path() -> Path:
    """Get the context percentage cache path for this session."""
    sid = get_session_id()
    cache_dir = Path.home() / ".wfc" / "sessions" / sid
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "context-pct.json"


def _read_context_pct() -> float | None:
    """Read context percentage from session cache.

    Returns None if cache is missing, corrupt, or stale (>60s).
    """
    cache_file = _get_context_pct_path()
    if not cache_file.exists():
        return None
    try:
        data = json.loads(cache_file.read_text())
        ts = data.get("ts")
        if ts is None or time.time() - ts > 60:
            return None
        pct = data.get("pct")
        return float(pct) if pct is not None else None
    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        return None


def _is_throttled() -> bool:
    """Check if monitoring should be throttled.

    Skips if last check was <30s ago AND context <80%.
    Never throttles at 80%+ (always show high-context warnings).
    """
    cache_path = get_session_cache_path()
    if not cache_path.exists():
        return False

    try:
        with cache_path.open() as f:
            cache = json.load(f)

        timestamp = cache.get("timestamp")
        if timestamp is None:
            return False

        if time.time() - timestamp < 30:
            pct = cache.get("pct", 0)
            if pct < THRESHOLD_WARN:
                return True

        return False
    except (json.JSONDecodeError, OSError, KeyError):
        return False


def _save_cache(pct: float, shown_80: bool = False) -> None:
    """Save context state to session cache."""
    cache_path = get_session_cache_path()
    existing_shown_80 = False

    if cache_path.exists():
        try:
            with cache_path.open() as f:
                cache = json.load(f)
                existing_shown_80 = cache.get("shown_80_warn", False)
        except (json.JSONDecodeError, OSError):
            pass

    try:
        with cache_path.open("w") as f:
            json.dump(
                {
                    "pct": pct,
                    "timestamp": time.time(),
                    "shown_80_warn": shown_80 or existing_shown_80,
                },
                f,
            )
    except OSError:
        pass


def _get_shown_80() -> bool:
    """Check if 80% warning was already shown this session."""
    cache_path = get_session_cache_path()
    if not cache_path.exists():
        return False
    try:
        with cache_path.open() as f:
            cache = json.load(f)
            return cache.get("shown_80_warn", False)
    except (json.JSONDecodeError, OSError):
        return False


def run_context_monitor() -> int:
    """Run context monitoring and return exit code."""
    if _is_throttled():
        return 0

    pct = _read_context_pct()
    if pct is None:
        return 0

    _save_cache(pct)

    if pct >= THRESHOLD_CRITICAL:
        print("", file=sys.stderr)
        print(
            f"{RED}CONTEXT {pct:.0f}% - CRITICAL: HANDOFF NOW{NC}",
            file=sys.stderr,
        )
        print(
            f"{RED}Do NOT write code, fix errors, or run commands.{NC}",
            file=sys.stderr,
        )
        print(
            f"{RED}Write continuation notes and stop immediately.{NC}",
            file=sys.stderr,
        )
        print(f"{RED}  1. Summarize current state and next steps{NC}", file=sys.stderr)
        print(f"{RED}  2. Note any in-progress work{NC}", file=sys.stderr)
        print(f"{RED}  3. Stop - next session continues seamlessly{NC}", file=sys.stderr)
        return 2

    if pct >= THRESHOLD_STOP:
        _save_cache(pct)
        print("", file=sys.stderr)
        print(
            f"{RED}CONTEXT {pct:.0f}% - MANDATORY HANDOFF{NC}",
            file=sys.stderr,
        )
        print(
            f"{RED}Do NOT start new tasks or fix cycles.{NC}",
            file=sys.stderr,
        )
        print(
            f"{RED}Finish current task, write continuation notes, then stop.{NC}",
            file=sys.stderr,
        )
        return 2

    shown_80 = _get_shown_80()

    if pct >= THRESHOLD_WARN and not shown_80:
        _save_cache(pct, shown_80=True)
        print("", file=sys.stderr)
        print(
            f"{YELLOW}CONTEXT {pct:.0f}% - PREPARE FOR HANDOFF{NC}",
            file=sys.stderr,
        )
        print(
            f"{YELLOW}Finish current task with full quality, then hand off.{NC}",
            file=sys.stderr,
        )
        print(
            f"{YELLOW}Next session continues seamlessly - never rush!{NC}",
            file=sys.stderr,
        )
        return 2

    if pct >= THRESHOLD_WARN and shown_80:
        print(f"{YELLOW}Context: {pct:.0f}%{NC}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(run_context_monitor())
