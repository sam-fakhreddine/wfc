"""Parse git unified diff format into structured FileChange objects."""

from __future__ import annotations

import re

from .diff_manifest import ChangeHunk, ChangeType, FileChange, HunkType

_DIFF_GIT_PATTERN = re.compile(r"^diff --git a/(.+?) b/(.+?)$")
_HUNK_HEADER_PATTERN = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@([^\n]*)")


def parse_diff(diff_content: str) -> list[FileChange]:
    """
    Parse unified diff into structured FileChange objects.

    Args:
        diff_content: Raw git diff output

    Returns:
        List of FileChange objects
    """
    if not diff_content.strip():
        return []

    file_changes: list[FileChange] = []
    current_file: FileChange | None = None
    current_hunk: ChangeHunk | None = None
    current_hunk_lines: list[str] = []

    lines = diff_content.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith("diff --git"):
            if current_hunk and current_file:
                _finalize_hunk(current_hunk, current_hunk_lines, current_file)
                current_file.hunks.append(current_hunk)
                current_hunk = None
                current_hunk_lines = []

            if current_file:
                file_changes.append(current_file)

            match = _DIFF_GIT_PATTERN.search(line)
            if match:
                path = match.group(2)
                current_file = FileChange(path=path, change_type=ChangeType.MODIFIED)

        elif line.startswith("new file mode"):
            if current_file:
                current_file.change_type = ChangeType.ADDED

        elif line.startswith("deleted file mode"):
            if current_file:
                current_file.change_type = ChangeType.DELETED

        elif line.startswith("rename from"):
            if current_file:
                current_file.change_type = ChangeType.RENAMED

        elif line.startswith("@@"):
            if current_hunk and current_file:
                _finalize_hunk(current_hunk, current_hunk_lines, current_file)
                current_file.hunks.append(current_hunk)

            match = _HUNK_HEADER_PATTERN.search(line)
            if match:
                line_start = int(match.group(3))
                context_hint = match.group(5).strip()

                current_hunk = ChangeHunk(
                    line_start=line_start,
                    line_end=line_start,
                    added_lines=0,
                    removed_lines=0,
                    context_before=context_hint,
                    change_summary="",
                    change_type=HunkType.MODIFICATION,
                )
                current_hunk_lines = []

        elif current_hunk:
            if line.startswith("+") and not line.startswith("+++"):
                current_hunk.added_lines += 1
                current_hunk_lines.append(line)
                if current_file:
                    current_file.total_added += 1

            elif line.startswith("-") and not line.startswith("---"):
                current_hunk.removed_lines += 1
                current_hunk_lines.append(line)
                if current_file:
                    current_file.total_removed += 1

            elif line.startswith(" "):
                current_hunk_lines.append(line)

        i += 1

    if current_hunk and current_file:
        _finalize_hunk(current_hunk, current_hunk_lines, current_file)
        current_file.hunks.append(current_hunk)

    if current_file:
        file_changes.append(current_file)

    return file_changes


def _finalize_hunk(hunk: ChangeHunk, hunk_lines: list[str], file_change: FileChange) -> None:
    """
    Finalize hunk by extracting context and summary.

    Args:
        hunk: Hunk to finalize
        hunk_lines: Raw diff lines for this hunk
        file_change: Parent file change
    """
    hunk.line_end = hunk.line_start + max(hunk.added_lines, hunk.removed_lines, 1) - 1

    if hunk.added_lines > 0 and hunk.removed_lines == 0:
        hunk.change_type = HunkType.ADDITION
    elif hunk.removed_lines > 0 and hunk.added_lines == 0:
        hunk.change_type = HunkType.DELETION
    else:
        hunk.change_type = HunkType.MODIFICATION

    if not hunk.context_before:
        hunk.context_before = _extract_context(hunk_lines, file_change.path)

    hunk.change_summary = _generate_summary(hunk, hunk_lines)

    hunk.raw_diff_lines = hunk_lines[:50]


def _extract_context(hunk_lines: list[str], file_path: str) -> str:
    """
    Extract surrounding context (function/class signature).

    Args:
        hunk_lines: Raw diff lines
        file_path: File path (for language detection)

    Returns:
        Context string (e.g., "def authenticate(user):")
    """
    for line in hunk_lines[:10]:
        stripped = line.lstrip(" +-")

        if "def " in stripped or "class " in stripped:
            return stripped.strip()

        if "function " in stripped or "const " in stripped or "class " in stripped:
            return stripped.strip()

        if "func " in stripped:
            return stripped.strip()

        if "fn " in stripped or "impl " in stripped:
            return stripped.strip()

    return ""


def _generate_summary(hunk: ChangeHunk, hunk_lines: list[str]) -> str:
    """
    Generate human-readable summary of changes.

    Args:
        hunk: Hunk being summarized
        hunk_lines: Raw diff lines

    Returns:
        Summary string
    """
    if hunk.change_type == HunkType.ADDITION:
        added_content = " ".join(
            line.lstrip("+ ").strip() for line in hunk_lines[:3] if line.startswith("+")
        )
        if len(added_content) > 60:
            added_content = added_content[:57] + "..."
        return f"Added: {added_content}" if added_content else "New code added"

    elif hunk.change_type == HunkType.DELETION:
        removed_content = " ".join(
            line.lstrip("- ").strip() for line in hunk_lines[:3] if line.startswith("-")
        )
        if len(removed_content) > 60:
            removed_content = removed_content[:57] + "..."
        return f"Removed: {removed_content}" if removed_content else "Code removed"

    else:
        removed = next(
            (line.lstrip("- ").strip() for line in hunk_lines if line.startswith("-")),
            "",
        )
        added = next(
            (line.lstrip("+ ").strip() for line in hunk_lines if line.startswith("+")),
            "",
        )

        if removed and added:
            if len(removed) > 30:
                removed = removed[:27] + "..."
            if len(added) > 30:
                added = added[:27] + "..."
            return f"Modified: {removed} → {added}"

        return "Modified code"
