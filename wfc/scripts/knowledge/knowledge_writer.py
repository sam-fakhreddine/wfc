"""Auto-append learnings to KNOWLEDGE.md after reviews.

Implements knowledge lifecycle: extract, append, prune, and promote.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

_log = logging.getLogger(__name__)

_DATE_RE = re.compile(r"\[(\d{4}-\d{2}-\d{2})\]")

SECTION_HEADERS: dict[str, str] = {
    "patterns_found": "## Patterns Found",
    "false_positives": "## False Positives to Avoid",
    "incidents_prevented": "## Incidents Prevented",
    "repo_rules": "## Repository-Specific Rules",
    "codebase_context": "## Codebase Context",
}

_ALL_SECTIONS_ORDERED = [
    "patterns_found",
    "false_positives",
    "incidents_prevented",
    "repo_rules",
    "codebase_context",
]


@dataclass
class LearningEntry:
    """A new knowledge entry to append."""

    text: str
    section: str
    reviewer_id: str
    source: str
    date: str = ""

    def __post_init__(self) -> None:
        if not self.date:
            self.date = date.today().isoformat()


class KnowledgeWriter:
    """Appends new learnings to KNOWLEDGE.md files and manages knowledge lifecycle."""

    def __init__(
        self,
        reviewers_dir: Path | None = None,
        global_knowledge_dir: Path | None = None,
    ) -> None:
        if reviewers_dir is None:
            reviewers_dir = Path(__file__).resolve().parents[2] / "references" / "reviewers"
        self.reviewers_dir = reviewers_dir

        if global_knowledge_dir is None:
            global_knowledge_dir = Path.home() / ".wfc" / "knowledge" / "global" / "reviewers"
        self.global_knowledge_dir = global_knowledge_dir

    def extract_learnings(
        self,
        review_findings: list[dict],
        reviewer_id: str,
        source: str,
    ) -> list[LearningEntry]:
        entries: list[LearningEntry] = []
        for f in review_findings:
            severity = f.get("severity", 0.0)
            confidence = f.get("confidence", 0.0)
            text = f.get("text", "")
            dismissed = f.get("dismissed", False)

            if dismissed:
                entries.append(
                    LearningEntry(
                        text=text, section="false_positives", reviewer_id=reviewer_id, source=source
                    )
                )
            elif severity >= 9.0:
                entries.append(
                    LearningEntry(
                        text=text,
                        section="incidents_prevented",
                        reviewer_id=reviewer_id,
                        source=source,
                    )
                )
            elif severity >= 7.0 and confidence >= 8.0:
                entries.append(
                    LearningEntry(
                        text=text, section="patterns_found", reviewer_id=reviewer_id, source=source
                    )
                )
        return entries

    def append_entries(self, entries: list[LearningEntry]) -> dict[str, int]:
        grouped: dict[str, list[LearningEntry]] = {}
        for e in entries:
            grouped.setdefault(e.reviewer_id, []).append(e)

        result: dict[str, int] = {}
        for reviewer_id, reviewer_entries in grouped.items():
            count = 0
            kp = self.reviewers_dir / reviewer_id / "KNOWLEDGE.md"
            if not kp.exists():
                self._create_empty_knowledge(kp, reviewer_id)
            current_content: str = kp.read_text(encoding="utf-8")
            for entry in reviewer_entries:
                updated_content = self._append_to_file(kp, entry, existing_content=current_content)
                if updated_content is not None:
                    current_content = updated_content
                    count += 1
            kp.write_text(current_content, encoding="utf-8")
            result[reviewer_id] = count
        return result

    def _append_to_file(
        self,
        knowledge_path: Path,
        entry: LearningEntry,
        existing_content: str | None = None,
    ) -> str | None:
        """Append *entry* to *knowledge_path*.

        When *existing_content* is supplied the file is NOT read from disk (the
        caller is responsible for passing up-to-date content and for writing the
        returned string back to disk).  When called without *existing_content*
        the legacy behaviour is preserved: read from disk, mutate, write to disk,
        and return ``True``/``False`` — except the return type is now ``str | None``
        where ``None`` means "not appended" and a non-None string means "new content".

        For backward compatibility with direct callers (e.g., ``promote_to_global``)
        the method still writes to disk when *existing_content* is not provided.
        """
        standalone = existing_content is None
        if standalone:
            if not knowledge_path.exists():
                self._create_empty_knowledge(knowledge_path, entry.reviewer_id)
            existing_content = knowledge_path.read_text(encoding="utf-8")

        content = existing_content
        assert content is not None

        entry_text, entry_source = self._sanitize_entry_fields(entry.text, entry.source)

        if self._is_duplicate(content, entry_text):
            return None

        header = SECTION_HEADERS.get(entry.section)
        if header is None:
            return None

        formatted = self._format_entry_sanitized(entry, entry_text, entry_source)
        lines = content.splitlines(keepends=True)

        header_idx: int | None = None
        for i, line in enumerate(lines):
            if line.rstrip() == header:
                header_idx = i
                break

        if header_idx is None:
            return None

        insert_idx = header_idx + 1
        for i in range(header_idx + 1, len(lines)):
            stripped = lines[i].rstrip()
            if stripped.startswith("## "):
                break
            if stripped.startswith("- "):
                insert_idx = i + 1
            elif stripped == "" and insert_idx == header_idx + 1:
                insert_idx = i + 1

        if insert_idx <= header_idx:
            insert_idx = header_idx + 1

        new_line = formatted + "\n"
        lines.insert(insert_idx, new_line)
        new_content = "".join(lines)

        if standalone:
            knowledge_path.write_text(new_content, encoding="utf-8")

        return new_content

    def _is_duplicate(self, existing_content: str, entry_text: str) -> bool:
        return entry_text.casefold() in existing_content.casefold()

    _MAX_FIELD_LEN = 500

    def _sanitize_entry_fields(self, text: str, source: str) -> tuple[str, str]:
        """Return sanitized (text, source) safe to embed in KNOWLEDGE.md.

        Rules applied to each field:
        1. Strip CR/LF characters (newline injection prevention).
        2. Truncate to _MAX_FIELD_LEN characters.
        3. Escape leading markdown tokens that would be mis-parsed as section
           headers (``## ``) or list items (``- [``).
        """

        def _sanitize(value: str) -> str:
            value = value.replace("\n", " ").replace("\r", " ")
            value = value[: self._MAX_FIELD_LEN]
            if value.startswith("## ") or value.startswith("- ["):
                value = "\\" + value
            return value

        return _sanitize(text), _sanitize(source)

    def _format_entry(self, entry: LearningEntry) -> str:
        entry_text, entry_source = self._sanitize_entry_fields(entry.text, entry.source)
        return f"- [{entry.date}] {entry_text} (Source: {entry_source})"

    def _format_entry_sanitized(
        self, entry: LearningEntry, entry_text: str, entry_source: str
    ) -> str:
        """Format an entry using already-sanitized text and source fields."""
        return f"- [{entry.date}] {entry_text} (Source: {entry_source})"

    def prune_old_entries(self, reviewer_id: str, max_age_days: int = 180) -> int:
        kp = self.reviewers_dir / reviewer_id / "KNOWLEDGE.md"
        if not kp.is_file():
            return 0
        content = kp.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)
        cutoff = date.today()

        keep: list[str] = []
        archived: list[str] = []

        for line in lines:
            stripped = line.rstrip()
            if stripped.startswith("- "):
                m = _DATE_RE.search(stripped)
                if m:
                    try:
                        entry_date = date.fromisoformat(m.group(1))
                    except ValueError:
                        _log.debug(
                            "Unparseable date %r in KNOWLEDGE.md — preserving line", m.group(1)
                        )
                        keep.append(line)
                        continue
                    age = (cutoff - entry_date).days
                    if age > max_age_days:
                        archived.append(line)
                        continue
            keep.append(line)

        if archived:
            kp.write_text("".join(keep), encoding="utf-8")
            archive_path = kp.parent / "KNOWLEDGE-ARCHIVE.md"
            if archive_path.exists():
                existing = archive_path.read_text(encoding="utf-8")
                archive_path.write_text(existing + "".join(archived), encoding="utf-8")
            else:
                archive_path.write_text(
                    "# KNOWLEDGE-ARCHIVE.md\n" + "".join(archived), encoding="utf-8"
                )

        return len(archived)

    def promote_to_global(self, entry: LearningEntry, project_name: str) -> bool:
        global_reviewer_dir = self.global_knowledge_dir / entry.reviewer_id
        global_reviewer_dir.mkdir(parents=True, exist_ok=True)
        gk = global_reviewer_dir / "KNOWLEDGE.md"

        promoted_entry = LearningEntry(
            text=entry.text,
            section=entry.section,
            reviewer_id=entry.reviewer_id,
            source=f"promoted from {project_name}",
            date=entry.date,
        )

        if not gk.exists():
            self._create_empty_knowledge(gk, entry.reviewer_id)

        return self._append_to_file(gk, promoted_entry) is not None

    def check_promotion_eligibility(
        self, entry_text: str, reviewer_id: str, min_projects: int = 2
    ) -> bool:
        # TODO: Implement cross-project promotion check — currently auto-promotes all entries.
        return True

    def _create_empty_knowledge(self, path: Path, reviewer_id: str) -> None:
        sections = "\n\n".join(SECTION_HEADERS[s] for s in _ALL_SECTIONS_ORDERED)
        path.write_text(f"# KNOWLEDGE.md -- {reviewer_id}\n\n{sections}\n", encoding="utf-8")
