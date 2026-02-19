"""Tests for KnowledgeWriter — auto-append learnings after reviews."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from wfc.scripts.knowledge.knowledge_writer import (
    KnowledgeWriter,
    LearningEntry,
)

SAMPLE_KNOWLEDGE_MD = """\
# KNOWLEDGE.md -- security

## Patterns Found
- [2026-01-10] SQL injection patterns in ORM queries (Source: review-2026-01-10-PR10)

## False Positives to Avoid
- [2026-01-12] eval() in test fixtures is safe (Source: review-2026-01-12-PR12)

## Incidents Prevented

## Repository-Specific Rules
- [2026-01-15] All database queries must use parameterized statements (Source: initial-seed)

## Codebase Context
- [2026-02-01] Database layer uses SQLAlchemy ORM exclusively (Source: initial-seed)
"""


@pytest.fixture()
def reviewers_dir(tmp_path: Path) -> Path:
    """Create a minimal reviewers directory with a security reviewer."""
    sec_dir = tmp_path / "reviewers" / "security"
    sec_dir.mkdir(parents=True)
    (sec_dir / "KNOWLEDGE.md").write_text(SAMPLE_KNOWLEDGE_MD, encoding="utf-8")
    return tmp_path / "reviewers"


@pytest.fixture()
def global_dir(tmp_path: Path) -> Path:
    """Create a global knowledge directory."""
    g = tmp_path / "global" / "reviewers"
    g.mkdir(parents=True)
    return tmp_path / "global" / "reviewers"


@pytest.fixture()
def writer(reviewers_dir: Path, global_dir: Path) -> KnowledgeWriter:
    return KnowledgeWriter(reviewers_dir=reviewers_dir, global_knowledge_dir=global_dir)


class TestExtractLearnings:
    def test_critical_finding_produces_incidents_prevented(self, writer: KnowledgeWriter) -> None:
        findings = [
            {"text": "Command injection via unsanitized input", "severity": 9.5, "confidence": 9.0}
        ]
        entries = writer.extract_learnings(findings, "security", "review-2026-02-16-PR42")
        assert len(entries) == 1
        assert entries[0].section == "incidents_prevented"
        assert "Command injection" in entries[0].text

    def test_high_severity_produces_patterns_found(self, writer: KnowledgeWriter) -> None:
        findings = [
            {
                "text": "Repeated N+1 query pattern in list endpoints",
                "severity": 8.0,
                "confidence": 8.5,
            }
        ]
        entries = writer.extract_learnings(findings, "performance", "review-2026-02-16-PR42")
        assert len(entries) == 1
        assert entries[0].section == "patterns_found"

    def test_low_severity_produces_no_entry(self, writer: KnowledgeWriter) -> None:
        findings = [{"text": "Minor style issue", "severity": 3.0, "confidence": 5.0}]
        entries = writer.extract_learnings(findings, "security", "review-2026-02-16-PR42")
        assert len(entries) == 0

    def test_dismissed_finding_produces_false_positives(self, writer: KnowledgeWriter) -> None:
        findings = [
            {
                "text": "eval() in test fixture",
                "severity": 7.0,
                "confidence": 8.0,
                "dismissed": True,
            }
        ]
        entries = writer.extract_learnings(findings, "security", "review-2026-02-16-PR42")
        assert len(entries) == 1
        assert entries[0].section == "false_positives"

    def test_multiple_findings_correct_types(self, writer: KnowledgeWriter) -> None:
        findings = [
            {"text": "Critical RCE", "severity": 9.5, "confidence": 9.0},
            {"text": "Pattern X recurs", "severity": 7.5, "confidence": 8.0},
            {"text": "Noise", "severity": 2.0, "confidence": 2.0},
            {"text": "Not a bug", "severity": 8.0, "confidence": 9.0, "dismissed": True},
        ]
        entries = writer.extract_learnings(findings, "security", "src")
        sections = [e.section for e in entries]
        assert "incidents_prevented" in sections
        assert "patterns_found" in sections
        assert "false_positives" in sections
        assert len(entries) == 3

    def test_empty_findings(self, writer: KnowledgeWriter) -> None:
        entries = writer.extract_learnings([], "security", "src")
        assert entries == []


class TestAppendEntries:
    def test_appends_entry_to_correct_section(
        self, writer: KnowledgeWriter, reviewers_dir: Path
    ) -> None:
        entry = LearningEntry(
            text="New pattern detected",
            section="patterns_found",
            reviewer_id="security",
            source="review-2026-02-16-PR99",
            date="2026-02-16",
        )
        result = writer.append_entries([entry])
        assert result == {"security": 1}

        content = (reviewers_dir / "security" / "KNOWLEDGE.md").read_text(encoding="utf-8")
        assert "- [2026-02-16] New pattern detected (Source: review-2026-02-16-PR99)" in content

    def test_entry_format(self, writer: KnowledgeWriter, reviewers_dir: Path) -> None:
        entry = LearningEntry(
            text="Format check",
            section="incidents_prevented",
            reviewer_id="security",
            source="PR-100",
            date="2026-02-16",
        )
        writer.append_entries([entry])
        content = (reviewers_dir / "security" / "KNOWLEDGE.md").read_text(encoding="utf-8")
        assert "- [2026-02-16] Format check (Source: PR-100)" in content

    def test_multiple_entries_same_section(
        self, writer: KnowledgeWriter, reviewers_dir: Path
    ) -> None:
        entries = [
            LearningEntry(
                text="First",
                section="patterns_found",
                reviewer_id="security",
                source="s1",
                date="2026-02-16",
            ),
            LearningEntry(
                text="Second",
                section="patterns_found",
                reviewer_id="security",
                source="s2",
                date="2026-02-16",
            ),
        ]
        result = writer.append_entries(entries)
        assert result == {"security": 2}
        content = (reviewers_dir / "security" / "KNOWLEDGE.md").read_text(encoding="utf-8")
        assert "First" in content
        assert "Second" in content

    def test_duplicate_not_appended(self, writer: KnowledgeWriter) -> None:
        entry = LearningEntry(
            text="SQL injection patterns in ORM queries",
            section="patterns_found",
            reviewer_id="security",
            source="new-src",
            date="2026-02-16",
        )
        result = writer.append_entries([entry])
        assert result == {"security": 0}


class TestFileAppend:
    def test_entry_after_existing_in_section(
        self, writer: KnowledgeWriter, reviewers_dir: Path
    ) -> None:
        entry = LearningEntry(
            text="Added after existing",
            section="patterns_found",
            reviewer_id="security",
            source="test",
            date="2026-02-16",
        )
        kp = reviewers_dir / "security" / "KNOWLEDGE.md"
        writer._append_to_file(kp, entry)
        lines = kp.read_text(encoding="utf-8").splitlines()
        idx_header = next(i for i, ln in enumerate(lines) if ln.startswith("## Patterns Found"))
        idx_next = next(i for i, ln in enumerate(lines) if ln.startswith("## ") and i > idx_header)
        section_lines = lines[idx_header + 1 : idx_next]
        entry_lines = [ln for ln in section_lines if ln.startswith("- ")]
        assert len(entry_lines) == 2
        assert "Added after existing" in entry_lines[-1]

    def test_well_formatted_after_append(
        self, writer: KnowledgeWriter, reviewers_dir: Path
    ) -> None:
        entry = LearningEntry(
            text="Fmt test",
            section="repo_rules",
            reviewer_id="security",
            source="s",
            date="2026-02-16",
        )
        kp = reviewers_dir / "security" / "KNOWLEDGE.md"
        writer._append_to_file(kp, entry)
        content = kp.read_text(encoding="utf-8")
        assert "\n\n\n" not in content

    def test_empty_section(self, writer: KnowledgeWriter, reviewers_dir: Path) -> None:
        entry = LearningEntry(
            text="First incident entry",
            section="incidents_prevented",
            reviewer_id="security",
            source="test",
            date="2026-02-16",
        )
        kp = reviewers_dir / "security" / "KNOWLEDGE.md"
        writer._append_to_file(kp, entry)
        content = kp.read_text(encoding="utf-8")
        assert "- [2026-02-16] First incident entry (Source: test)" in content

    def test_section_at_end_of_file(self, writer: KnowledgeWriter, reviewers_dir: Path) -> None:
        entry = LearningEntry(
            text="End of file entry",
            section="codebase_context",
            reviewer_id="security",
            source="test",
            date="2026-02-16",
        )
        kp = reviewers_dir / "security" / "KNOWLEDGE.md"
        writer._append_to_file(kp, entry)
        content = kp.read_text(encoding="utf-8")
        assert "- [2026-02-16] End of file entry (Source: test)" in content


class TestDuplicateDetection:
    def test_exact_match(self, writer: KnowledgeWriter) -> None:
        assert writer._is_duplicate("hello world", "hello world") is True

    def test_substring_match(self, writer: KnowledgeWriter) -> None:
        existing = "This has SQL injection patterns in ORM queries inside."
        assert writer._is_duplicate(existing, "SQL injection patterns in ORM queries") is True

    def test_different_text(self, writer: KnowledgeWriter) -> None:
        assert writer._is_duplicate("apples and oranges", "bananas and pears") is False

    def test_case_insensitive(self, writer: KnowledgeWriter) -> None:
        assert writer._is_duplicate("SQL Injection Detected", "sql injection detected") is True


class TestPruning:
    def test_old_entries_archived(self, writer: KnowledgeWriter, reviewers_dir: Path) -> None:
        old_date = (date.today() - timedelta(days=200)).isoformat()
        recent_date = date.today().isoformat()
        km = reviewers_dir / "security" / "KNOWLEDGE.md"
        km.write_text(
            f"# KNOWLEDGE.md -- security\n\n"
            f"## Patterns Found\n"
            f"- [{old_date}] Old pattern (Source: old)\n"
            f"- [{recent_date}] New pattern (Source: new)\n\n"
            f"## False Positives to Avoid\n\n"
            f"## Incidents Prevented\n\n"
            f"## Repository-Specific Rules\n\n"
            f"## Codebase Context\n",
            encoding="utf-8",
        )
        count = writer.prune_old_entries("security", max_age_days=180)
        assert count == 1
        content = km.read_text(encoding="utf-8")
        assert "Old pattern" not in content
        assert "New pattern" in content

    def test_recent_entries_stay(self, writer: KnowledgeWriter, reviewers_dir: Path) -> None:
        recent_date = date.today().isoformat()
        km = reviewers_dir / "security" / "KNOWLEDGE.md"
        km.write_text(
            f"# KNOWLEDGE.md -- security\n\n"
            f"## Patterns Found\n"
            f"- [{recent_date}] Recent (Source: r)\n\n"
            f"## False Positives to Avoid\n\n"
            f"## Incidents Prevented\n\n"
            f"## Repository-Specific Rules\n\n"
            f"## Codebase Context\n",
            encoding="utf-8",
        )
        count = writer.prune_old_entries("security", max_age_days=180)
        assert count == 0

    def test_archive_created(self, writer: KnowledgeWriter, reviewers_dir: Path) -> None:
        old_date = (date.today() - timedelta(days=200)).isoformat()
        km = reviewers_dir / "security" / "KNOWLEDGE.md"
        km.write_text(
            f"# KNOWLEDGE.md -- security\n\n"
            f"## Patterns Found\n"
            f"- [{old_date}] Archived entry (Source: old)\n\n"
            f"## False Positives to Avoid\n\n"
            f"## Incidents Prevented\n\n"
            f"## Repository-Specific Rules\n\n"
            f"## Codebase Context\n",
            encoding="utf-8",
        )
        writer.prune_old_entries("security", max_age_days=180)
        archive = reviewers_dir / "security" / "KNOWLEDGE-ARCHIVE.md"
        assert archive.exists()
        assert "Archived entry" in archive.read_text(encoding="utf-8")

    def test_archive_appended(self, writer: KnowledgeWriter, reviewers_dir: Path) -> None:
        old_date = (date.today() - timedelta(days=200)).isoformat()
        km = reviewers_dir / "security" / "KNOWLEDGE.md"
        archive = reviewers_dir / "security" / "KNOWLEDGE-ARCHIVE.md"
        archive.write_text("# Archive\n- [2025-01-01] Previous (Source: prev)\n", encoding="utf-8")
        km.write_text(
            f"# KNOWLEDGE.md -- security\n\n"
            f"## Patterns Found\n"
            f"- [{old_date}] Another old (Source: old)\n\n"
            f"## False Positives to Avoid\n\n"
            f"## Incidents Prevented\n\n"
            f"## Repository-Specific Rules\n\n"
            f"## Codebase Context\n",
            encoding="utf-8",
        )
        writer.prune_old_entries("security", max_age_days=180)
        content = archive.read_text(encoding="utf-8")
        assert "Previous" in content
        assert "Another old" in content

    def test_returns_count(self, writer: KnowledgeWriter, reviewers_dir: Path) -> None:
        old_date = (date.today() - timedelta(days=200)).isoformat()
        km = reviewers_dir / "security" / "KNOWLEDGE.md"
        km.write_text(
            f"# KNOWLEDGE.md -- security\n\n"
            f"## Patterns Found\n"
            f"- [{old_date}] One (Source: o)\n"
            f"- [{old_date}] Two (Source: o)\n\n"
            f"## False Positives to Avoid\n\n"
            f"## Incidents Prevented\n\n"
            f"## Repository-Specific Rules\n\n"
            f"## Codebase Context\n",
            encoding="utf-8",
        )
        assert writer.prune_old_entries("security", max_age_days=180) == 2


class TestPromoteToGlobal:
    def test_creates_global_directory(self, writer: KnowledgeWriter, global_dir: Path) -> None:
        entry = LearningEntry(
            text="Globally useful pattern",
            section="patterns_found",
            reviewer_id="security",
            source="review-2026-02-16-PR42",
            date="2026-02-16",
        )
        result = writer.promote_to_global(entry, "myproject")
        assert result is True
        gk = global_dir / "security" / "KNOWLEDGE.md"
        assert gk.exists()
        content = gk.read_text(encoding="utf-8")
        assert "Globally useful pattern" in content
        assert "promoted from myproject" in content

    def test_appends_with_promoted_source(self, writer: KnowledgeWriter, global_dir: Path) -> None:
        entry = LearningEntry(
            text="Source tag test",
            section="patterns_found",
            reviewer_id="security",
            source="review-2026-02-16-PR42",
            date="2026-02-16",
        )
        writer.promote_to_global(entry, "proj-a")
        gk = global_dir / "security" / "KNOWLEDGE.md"
        content = gk.read_text(encoding="utf-8")
        assert "(Source: promoted from proj-a)" in content

    def test_duplicate_returns_false(self, writer: KnowledgeWriter, global_dir: Path) -> None:
        entry = LearningEntry(
            text="Dup global",
            section="patterns_found",
            reviewer_id="security",
            source="s",
            date="2026-02-16",
        )
        assert writer.promote_to_global(entry, "proj") is True
        assert writer.promote_to_global(entry, "proj") is False

    def test_entry_format_includes_original_source(
        self, writer: KnowledgeWriter, global_dir: Path
    ) -> None:
        entry = LearningEntry(
            text="Check format",
            section="incidents_prevented",
            reviewer_id="security",
            source="review-2026-02-16-PR42",
            date="2026-02-16",
        )
        writer.promote_to_global(entry, "myproject")
        gk = global_dir / "security" / "KNOWLEDGE.md"
        content = gk.read_text(encoding="utf-8")
        assert "- [2026-02-16] Check format (Source: promoted from myproject)" in content
