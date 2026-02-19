"""Shared input validators for git operations.

Centralizes flag-injection and path-traversal guards used across
branch, commit, and worktree APIs.
"""

from __future__ import annotations

import re

FLAG_PATTERN = re.compile(r"^-")
VALID_REF_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._/\-]*$")


def is_flag_injection(value: str) -> bool:
    """Return True if value starts with '-' (flag injection attempt)."""
    return bool(FLAG_PATTERN.match(value))


def has_path_traversal(value: str) -> bool:
    """Return True if value contains path traversal sequences."""
    return ".." in value or "\\" in value


def validate_ref_name(name: str) -> bool:
    """Validate a git ref name against safe naming rules.

    Rejects: empty, >255 chars, '..', '.lock' suffix, '.' suffix,
    special chars (~^:\\), whitespace, flag injection, invalid ref chars.
    """
    if not name or len(name) > 255:
        return False
    if ".." in name or name.endswith(".lock") or name.endswith("."):
        return False
    if "~" in name or "^" in name or ":" in name or "\\" in name:
        return False
    if " " in name or "\t" in name:
        return False
    if is_flag_injection(name):
        return False
    return bool(VALID_REF_PATTERN.match(name))


def validate_task_id(task_id: str) -> bool:
    """Validate task ID — no traversal, no injection, must match TASK-NNN format."""
    if not task_id:
        return False
    if has_path_traversal(task_id) or "/" in task_id:
        return False
    if is_flag_injection(task_id):
        return False
    return bool(re.match(r"^[A-Z]+-\d+$", task_id))


def validate_file_path(path: str) -> bool:
    """Validate file path — no traversal, no injection, no null bytes."""
    if not path:
        return False
    if ".." in path:
        return False
    if is_flag_injection(path):
        return False
    if "\x00" in path:
        return False
    return True
