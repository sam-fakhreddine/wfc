#!/usr/bin/env python3
"""Upsert WFC PostToolUse hooks into .claude/settings.json.

Never clobbers existing settings. Merges WFC hooks alongside whatever
the user already has configured. Idempotent — safe to run repeatedly.

Usage:
    python register_hooks.py [settings_path]

If settings_path is omitted, defaults to ~/.claude/settings.json.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

WFC_HOOKS = {
    "UserPromptSubmit": [
        {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": "python ~/.wfc/scripts/security/semantic_firewall.py",
                },
            ],
        },
    ],
    "PostToolUse": [
        {
            "matcher": "Write|Edit",
            "hooks": [
                {
                    "type": "command",
                    "command": "python ~/.wfc/scripts/hooks/file_checker.py",
                },
                {
                    "type": "command",
                    "command": "python ~/.wfc/scripts/hooks/tdd_enforcer.py",
                },
            ],
        },
        {
            "matcher": "Read|Write|Edit|Bash|Task|Skill|Grep|Glob",
            "hooks": [
                {
                    "type": "command",
                    "command": "python ~/.wfc/scripts/hooks/context_monitor.py",
                },
            ],
        },
    ],
}

WFC_MARKERS = ("~/.wfc/scripts/hooks/", "wfc/scripts/security/", "~/.wfc/scripts/security/")


def is_wfc_hook_entry(entry: dict) -> bool:
    """Check if a hook entry belongs to WFC."""
    for hook in entry.get("hooks", []):
        cmd = hook.get("command", "")
        if any(marker in cmd for marker in WFC_MARKERS):
            return True
    return False


def upsert_hooks(settings_path: Path) -> bool:
    """Upsert WFC hooks into settings.json. Returns True if file was modified."""
    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text())
        except (json.JSONDecodeError, OSError):
            data = {}
    else:
        data = {}

    if not isinstance(data, dict):
        data = {}

    if "hooks" not in data:
        data["hooks"] = {}

    hooks = data["hooks"]
    modified = False

    for hook_type, wfc_entries in WFC_HOOKS.items():
        if hook_type not in hooks:
            hooks[hook_type] = []
            modified = True

        existing = hooks[hook_type]

        cleaned = [entry for entry in existing if not is_wfc_hook_entry(entry)]

        if len(cleaned) != len(existing):
            modified = True

        new_entries = cleaned + wfc_entries
        if new_entries != hooks[hook_type]:
            modified = True
        hooks[hook_type] = new_entries

    if modified:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(data, indent=2) + "\n"
        # Atomic write: temp file in same dir + os.replace
        fd, tmp_path = tempfile.mkstemp(dir=str(settings_path.parent))
        try:
            os.write(fd, content.encode())
        finally:
            os.close(fd)
        os.replace(tmp_path, str(settings_path))

    return modified


def main() -> int:
    if len(sys.argv) > 1:
        settings_path = Path(sys.argv[1])
    else:
        settings_path = Path.home() / ".claude" / "settings.json"

    try:
        changed = upsert_hooks(settings_path)
        if changed:
            print(f"WFC hooks registered in {settings_path}")
        else:
            print(f"WFC hooks already current in {settings_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
