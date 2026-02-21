"""Diff manifest builder for token-efficient reviewer prompts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ChangeType(str, Enum):
    """Type of change in a file."""

    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"
    RENAMED = "renamed"


class HunkType(str, Enum):
    """Type of change within a hunk."""

    ADDITION = "addition"
    DELETION = "deletion"
    MODIFICATION = "modification"


@dataclass
class ChangeHunk:
    """
    A contiguous block of changes within a file.

    Represents a single logical change (e.g., one function modification).
    """

    line_start: int
    line_end: int
    added_lines: int
    removed_lines: int
    context_before: str
    change_summary: str
    change_type: HunkType
    raw_diff_lines: list[str] = field(default_factory=list)


@dataclass
class FileChange:
    """
    Per-file change summary.

    Groups all hunks for a single file with metadata.
    """

    path: str
    change_type: ChangeType
    hunks: list[ChangeHunk] = field(default_factory=list)
    domain_tags: list[str] = field(default_factory=list)
    total_added: int = 0
    total_removed: int = 0


@dataclass
class DiffManifest:
    """
    Complete structured representation of a diff.

    Replaces embedded diff content in reviewer prompts.
    """

    files_changed: int
    lines_added: int
    lines_removed: int
    lines_modified: int
    file_changes: list[FileChange] = field(default_factory=list)
    domain_hints: dict[str, list[str]] = field(default_factory=dict)

    def get_files_for_domain(self, domain: str) -> list[str]:
        """Get list of files relevant to a specific reviewer domain."""
        return self.domain_hints.get(domain, [])

    def get_token_estimate(self) -> int:
        """Estimate token count for this manifest (~chars/4)."""
        total_chars = 100

        for file_change in self.file_changes:
            total_chars += 50

            for hunk in file_change.hunks:
                total_chars += len(hunk.context_before)
                total_chars += len(hunk.change_summary)
                total_chars += 30

        return total_chars // 4


def build_diff_manifest(
    diff_content: str,
    reviewer_id: str | None = None,
    files: list[str] | None = None,
) -> DiffManifest:
    """
    Build a structured diff manifest from raw diff content.

    Args:
        diff_content: Raw git diff output (unified format)
        reviewer_id: Optional reviewer ID for domain filtering
        files: Optional list of files being reviewed

    Returns:
        DiffManifest with structured change information
    """
    from .diff_parser import parse_diff
    from .domain_tagger import tag_file_domains

    file_changes = parse_diff(diff_content)

    for file_change in file_changes:
        file_change.domain_tags = tag_file_domains(file_change.path, file_change.hunks)

    files_changed = len(file_changes)
    lines_added = sum(fc.total_added for fc in file_changes)
    lines_removed = sum(fc.total_removed for fc in file_changes)
    lines_modified = lines_added + lines_removed

    domain_hints: dict[str, list[str]] = {}
    for file_change in file_changes:
        for domain in file_change.domain_tags:
            if domain not in domain_hints:
                domain_hints[domain] = []
            domain_hints[domain].append(file_change.path)

    return DiffManifest(
        files_changed=files_changed,
        lines_added=lines_added,
        lines_removed=lines_removed,
        lines_modified=lines_modified,
        file_changes=file_changes,
        domain_hints=domain_hints,
    )


def format_manifest_for_reviewer(manifest: DiffManifest, reviewer_id: str) -> str:
    """
    Format manifest as markdown for reviewer consumption.

    Args:
        manifest: Diff manifest to format
        reviewer_id: Reviewer ID (for domain filtering)

    Returns:
        Markdown-formatted manifest
    """
    lines = []

    lines.append("# Diff Summary")
    lines.append("")
    lines.append(
        f"**Files Changed:** {manifest.files_changed} | "
        f"**Lines Added:** {manifest.lines_added} | "
        f"**Lines Removed:** {manifest.lines_removed}"
    )
    lines.append("")

    relevant_files = manifest.get_files_for_domain(reviewer_id)
    if relevant_files:
        lines.append(f"**Relevant to {reviewer_id}:** {len(relevant_files)} files")
        lines.append("")

    for file_change in manifest.file_changes:
        relevance = ""
        if file_change.path in relevant_files:
            relevance = f" ({', '.join(file_change.domain_tags)})"

        lines.append(f"## {file_change.path}{relevance}")
        lines.append(
            f"**Change:** {file_change.change_type.value} | "
            f"+{file_change.total_added} -{file_change.total_removed}"
        )
        lines.append("")

        for hunk in file_change.hunks:
            lines.append(f"**Lines {hunk.line_start}-{hunk.line_end}:** {hunk.change_summary}")
            if hunk.context_before:
                lines.append(f"```\n{hunk.context_before}\n```")
            lines.append("")

    return "\n".join(lines)
