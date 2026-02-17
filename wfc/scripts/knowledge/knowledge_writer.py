"""Auto-append learnings to KNOWLEDGE.md after reviews.

Implements knowledge lifecycle: extract, append, prune, and promote.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

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
            reviewers_dir = Path(__file__).resolve().parents[2] / "reviewers"
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
            for entry in reviewer_entries:
                if self._append_to_file(kp, entry):
                    count += 1
            result[reviewer_id] = count
        return result

    def _append_to_file(self, knowledge_path: Path, entry: LearningEntry) -> bool:
        if not knowledge_path.exists():
            self._create_empty_knowledge(knowledge_path, entry.reviewer_id)
        content = knowledge_path.read_text(encoding="utf-8")
        if self._is_duplicate(content, entry.text):
            return False

        header = SECTION_HEADERS.get(entry.section)
        if header is None:
            return False

        formatted = self._format_entry(entry)
        lines = content.splitlines(keepends=True)

        header_idx: int | None = None
        for i, line in enumerate(lines):
            if line.rstrip() == header:
                header_idx = i
                break

        if header_idx is None:
            return False

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
        knowledge_path.write_text("".join(lines), encoding="utf-8")
        return True

    def _is_duplicate(self, existing_content: str, entry_text: str) -> bool:
        return entry_text.casefold() in existing_content.casefold()

    def _format_entry(self, entry: LearningEntry) -> str:
        return f"- [{entry.date}] {entry.text} (Source: {entry.source})"

    def prune_old_entries(self, reviewer_id: str, max_age_days: int = 180) -> int:
        kp = self.reviewers_dir / reviewer_id / "KNOWLEDGE.md"
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
                    entry_date = date.fromisoformat(m.group(1))
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

        return self._append_to_file(gk, promoted_entry)

    def check_promotion_eligibility(
        self, entry_text: str, reviewer_id: str, min_projects: int = 2
    ) -> bool:
        # TODO: Implement cross-project promotion check — currently auto-promotes all entries.
        return True

    def _create_empty_knowledge(self, path: Path, reviewer_id: str) -> None:
        sections = "\n\n".join(SECTION_HEADERS[s] for s in _ALL_SECTIONS_ORDERED)
        path.write_text(f"# KNOWLEDGE.md -- {reviewer_id}\n\n{sections}\n", encoding="utf-8")
