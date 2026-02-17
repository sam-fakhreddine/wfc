"""Parse KNOWLEDGE.md into atomic entries for RAG indexing.

Each KNOWLEDGE.md follows a strict schema (see docs/reference/KNOWLEDGE_SCHEMA.md):
- Sections are ## headers mapping to known categories
- Entries are lines starting with `- [YYYY-MM-DD] ... (Source: ...)`
- Each entry is an atomic, self-contained fact
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class KnowledgeChunk:
    """A single atomic entry from a KNOWLEDGE.md file."""

    text: str
    reviewer_id: str
    section: str
    date: str
    source: str
    chunk_id: str


_ENTRY_PATTERN = re.compile(r"^-\s+\[(\d{4}-\d{2}-\d{2})\]\s+(.+?)\s+\(Source:\s+(.+?)\)\s*$")

_ENTRY_NO_SOURCE_PATTERN = re.compile(r"^-\s+\[(\d{4}-\d{2}-\d{2})\]\s+(.+?)\s*$")


class KnowledgeChunker:
    """Parses KNOWLEDGE.md files into atomic KnowledgeChunk entries."""

    SECTION_MAP: dict[str, str] = {
        "Patterns Found": "patterns_found",
        "False Positives to Avoid": "false_positives",
        "Incidents Prevented": "incidents_prevented",
        "Repository-Specific Rules": "repo_rules",
        "Codebase Context": "codebase_context",
    }

    def parse(self, content: str, reviewer_id: str) -> list[KnowledgeChunk]:
        """Parse a KNOWLEDGE.md file content into chunks.

        Args:
            content: Raw markdown content of the KNOWLEDGE.md file.
            reviewer_id: Identifier for the reviewer (e.g. 'security').

        Returns:
            List of KnowledgeChunk entries parsed from the content.
        """
        chunks: list[KnowledgeChunk] = []
        current_section: str | None = None

        for line in content.splitlines():
            stripped = line.strip()

            if stripped.startswith("## "):
                header = stripped[3:].strip()
                current_section = self.SECTION_MAP.get(header)
                continue

            if current_section is None:
                continue

            if not stripped.startswith("- "):
                continue

            chunk = self._parse_entry(stripped, reviewer_id, current_section)
            if chunk is not None:
                chunks.append(chunk)

        return chunks

    def parse_file(self, path: Path, reviewer_id: str) -> list[KnowledgeChunk]:
        """Parse a KNOWLEDGE.md file from disk.

        Args:
            path: Path to the KNOWLEDGE.md file.
            reviewer_id: Identifier for the reviewer.

        Returns:
            List of KnowledgeChunk entries.
        """
        content = path.read_text(encoding="utf-8")
        return self.parse(content, reviewer_id)

    def _parse_entry(self, line: str, reviewer_id: str, section: str) -> KnowledgeChunk | None:
        """Parse a single entry line into a KnowledgeChunk."""
        match = _ENTRY_PATTERN.match(line)
        if match:
            date, text, source = match.groups()
            normalized_text = text.strip()
            normalized_source = source.strip()
            return KnowledgeChunk(
                text=normalized_text,
                reviewer_id=reviewer_id,
                section=section,
                date=date,
                source=normalized_source,
                chunk_id=self._make_chunk_id(
                    reviewer_id, section, date, normalized_source, normalized_text
                ),
            )

        match = _ENTRY_NO_SOURCE_PATTERN.match(line)
        if match:
            date, text = match.groups()
            normalized_text = text.strip()
            return KnowledgeChunk(
                text=normalized_text,
                reviewer_id=reviewer_id,
                section=section,
                date=date,
                source="unknown",
                chunk_id=self._make_chunk_id(
                    reviewer_id, section, date, "unknown", normalized_text
                ),
            )

        return None

    @staticmethod
    def _make_chunk_id(reviewer_id: str, section: str, date: str, source: str, text: str) -> str:
        """Generate a deterministic chunk ID from normalized content."""
        normalized_text = " ".join(text.split())
        raw = f"{reviewer_id}:{section}:{date}:{source}:{normalized_text}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
