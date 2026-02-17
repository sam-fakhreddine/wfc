"""Detect drift in KNOWLEDGE.md files — staleness, bloat, contradictions, orphans.

Signals when knowledge files need pruning, updating, or review.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

_DATE_RE = re.compile(r"\[(\d{4}-\d{2}-\d{2})\]")

_FILE_PATH_RE = re.compile(r"`([a-zA-Z0-9_./-]+\.\w+)(?::\d+)?`")

_ENTRY_RE = re.compile(r"^\s*-\s+")

_PATTERNS_FOUND = "## Patterns Found"
_FALSE_POSITIVES = "## False Positives to Avoid"


@dataclass
class DriftSignal:
    """A detected drift issue in a knowledge file."""

    reviewer_id: str
    signal_type: str
    severity: str
    description: str
    file_path: str
    line_range: tuple[int, int] | None = None


@dataclass
class DriftReport:
    """Summary of drift analysis across all knowledge files."""

    signals: list[DriftSignal] = field(default_factory=list)
    total_entries: int = 0
    stale_count: int = 0
    bloated_count: int = 0
    healthy_count: int = 0
    recommendation: str = "healthy"


class DriftDetector:
    """Detect knowledge drift across reviewer KNOWLEDGE.md files."""

    STALE_THRESHOLD_DAYS: int = 90
    BLOAT_THRESHOLD_ENTRIES: int = 50

    def __init__(
        self,
        reviewers_dir: Path | None = None,
        global_knowledge_dir: Path | None = None,
        project_root: Path | None = None,
    ) -> None:
        """Initialize with paths to reviewer and global knowledge directories."""
        self.reviewers_dir = reviewers_dir or Path("wfc/reviewers")
        self.global_knowledge_dir = global_knowledge_dir
        self.project_root = project_root or Path(".")

    def analyze(self) -> DriftReport:
        """Run full drift analysis across all knowledge files."""
        report = DriftReport()
        knowledge_files = self._find_knowledge_files()

        for km_path, reviewer_id in knowledge_files:
            entries = self._count_entries(km_path)
            report.total_entries += entries

            stale = self.check_staleness(km_path, reviewer_id)
            bloat = self.check_bloat(km_path, reviewer_id)
            contradictions = self.check_contradictions(km_path, reviewer_id)
            orphaned = self.check_orphaned(km_path, reviewer_id)

            all_signals = stale + bloat + contradictions + orphaned
            report.signals.extend(all_signals)
            report.stale_count += len(stale)
            report.bloated_count += len(bloat)

            if not all_signals:
                report.healthy_count += 1

        report.recommendation = self._compute_recommendation(report)
        return report

    def check_staleness(self, knowledge_path: Path, reviewer_id: str) -> list[DriftSignal]:
        """Check for entries older than STALE_THRESHOLD_DAYS."""
        signals: list[DriftSignal] = []
        cutoff = date.today() - timedelta(days=self.STALE_THRESHOLD_DAYS)
        content = knowledge_path.read_text()
        lines = content.splitlines()

        for i, line in enumerate(lines, start=1):
            if not _ENTRY_RE.match(line):
                continue
            match = _DATE_RE.search(line)
            if not match:
                continue
            try:
                entry_date = date.fromisoformat(match.group(1))
            except ValueError:
                continue
            if entry_date < cutoff:
                age_days = (date.today() - entry_date).days
                signals.append(
                    DriftSignal(
                        reviewer_id=reviewer_id,
                        signal_type="stale",
                        severity="medium",
                        description=f"Entry is {age_days} days old (threshold: {self.STALE_THRESHOLD_DAYS})",
                        file_path=str(knowledge_path),
                        line_range=(i, i),
                    )
                )
        return signals

    def check_bloat(self, knowledge_path: Path, reviewer_id: str) -> list[DriftSignal]:
        """Check if a knowledge file exceeds BLOAT_THRESHOLD_ENTRIES."""
        entry_count = self._count_entries(knowledge_path)
        if entry_count > self.BLOAT_THRESHOLD_ENTRIES:
            return [
                DriftSignal(
                    reviewer_id=reviewer_id,
                    signal_type="bloated",
                    severity="high",
                    description=(
                        f"File has {entry_count} entries "
                        f"(threshold: {self.BLOAT_THRESHOLD_ENTRIES})"
                    ),
                    file_path=str(knowledge_path),
                )
            ]
        return []

    def check_contradictions(self, knowledge_path: Path, reviewer_id: str) -> list[DriftSignal]:
        """Check for entries in both Patterns Found and False Positives with similar file paths."""
        content = knowledge_path.read_text()
        sections = self._parse_sections(content)

        patterns_paths = self._extract_file_paths_from_section(sections.get(_PATTERNS_FOUND, ""))
        false_pos_paths = self._extract_file_paths_from_section(sections.get(_FALSE_POSITIVES, ""))

        patterns_stems = {self._stem(p) for p in patterns_paths}
        false_pos_stems = {self._stem(p) for p in false_pos_paths}
        overlapping = patterns_stems & false_pos_stems

        signals: list[DriftSignal] = []
        for stem in sorted(overlapping):
            signals.append(
                DriftSignal(
                    reviewer_id=reviewer_id,
                    signal_type="contradictory",
                    severity="high",
                    description=(
                        f"'{stem}' appears in both Patterns Found and "
                        f"False Positives — may be contradictory"
                    ),
                    file_path=str(knowledge_path),
                )
            )
        return signals

    def check_orphaned(self, knowledge_path: Path, reviewer_id: str) -> list[DriftSignal]:
        """Check for entries referencing files that no longer exist in the project."""
        content = knowledge_path.read_text()
        file_paths = self._extract_file_paths_from_section(content)
        seen: set[str] = set()
        signals: list[DriftSignal] = []

        for fp in file_paths:
            stem = self._stem(fp)
            if stem in seen:
                continue
            seen.add(stem)
            resolved = self.project_root / stem
            if not resolved.exists():
                signals.append(
                    DriftSignal(
                        reviewer_id=reviewer_id,
                        signal_type="orphaned",
                        severity="low",
                        description=f"Referenced file '{stem}' no longer exists",
                        file_path=str(knowledge_path),
                    )
                )
        return signals

    def _find_knowledge_files(self) -> list[tuple[Path, str]]:
        """Find all KNOWLEDGE.md files under reviewers_dir."""
        results: list[tuple[Path, str]] = []
        if not self.reviewers_dir.exists():
            return results
        for km in sorted(self.reviewers_dir.rglob("KNOWLEDGE.md")):
            reviewer_id = km.parent.name
            results.append((km, reviewer_id))
        return results

    def _count_entries(self, knowledge_path: Path) -> int:
        """Count entry lines (lines starting with '- ') in a knowledge file."""
        content = knowledge_path.read_text()
        return sum(1 for line in content.splitlines() if _ENTRY_RE.match(line))

    def _parse_sections(self, content: str) -> dict[str, str]:
        """Parse KNOWLEDGE.md into sections keyed by header."""
        sections: dict[str, str] = {}
        current_header: str | None = None
        current_lines: list[str] = []

        for line in content.splitlines():
            if line.startswith("## "):
                if current_header is not None:
                    sections[current_header] = "\n".join(current_lines)
                current_header = line.strip()
                current_lines = []
            else:
                current_lines.append(line)

        if current_header is not None:
            sections[current_header] = "\n".join(current_lines)

        return sections

    def _extract_file_paths_from_section(self, section_text: str) -> list[str]:
        """Extract file paths from backtick-wrapped references."""
        return _FILE_PATH_RE.findall(section_text)

    @staticmethod
    def _stem(file_ref: str) -> str:
        """Strip line numbers from a file reference: 'app/db.py:42' → 'app/db.py'."""
        return file_ref.split(":")[0]

    @staticmethod
    def _compute_recommendation(report: DriftReport) -> str:
        """Determine overall recommendation from signals."""
        has_contradictions = any(s.signal_type == "contradictory" for s in report.signals)
        has_bloat = any(s.signal_type == "bloated" for s in report.signals)
        has_stale = any(s.signal_type == "stale" for s in report.signals)

        if has_contradictions:
            return "needs_review"
        if has_bloat or has_stale:
            return "needs_pruning"
        return "healthy"
