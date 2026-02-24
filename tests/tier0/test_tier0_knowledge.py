"""
Tier 0 MVP - TASK-005 Tests
Test knowledge_writer developer attribution and file locking.
"""

import threading
from wfc.scripts.knowledge.knowledge_writer import LearningEntry, KnowledgeWriter


class TestKnowledgeWriterDeveloperAttribution:
    """Test developer_id field in knowledge entries."""

    def test_learning_entry_accepts_developer_id(self):
        """LearningEntry should accept developer_id parameter."""
        entry = LearningEntry(
            text="Test finding",
            section="patterns_found",
            reviewer_id="security",
            source="test.py:42",
            developer_id="alice",
        )
        assert entry.developer_id == "alice"

    def test_learning_entry_defaults_to_empty_developer_id(self):
        """LearningEntry should default developer_id to empty string."""
        entry = LearningEntry(
            text="Test finding",
            section="patterns_found",
            reviewer_id="security",
            source="test.py:42",
        )
        assert entry.developer_id == ""

    def test_format_entry_includes_developer_id(self, tmp_path):
        """_format_entry should include developer_id when set."""
        writer = KnowledgeWriter(reviewers_dir=tmp_path)
        entry = LearningEntry(
            text="SQL injection risk",
            section="patterns_found",
            reviewer_id="security",
            source="auth.py:15",
            developer_id="bob",
            date="2026-02-21",
        )

        formatted = writer._format_entry(entry)

        assert "bob" in formatted
        assert "SQL injection risk" in formatted
        assert "auth.py:15" in formatted

    def test_format_entry_without_developer_id(self, tmp_path):
        """_format_entry should work when developer_id is empty."""
        writer = KnowledgeWriter(reviewers_dir=tmp_path)
        entry = LearningEntry(
            text="Buffer overflow",
            section="patterns_found",
            reviewer_id="security",
            source="main.c:100",
            date="2026-02-21",
        )

        formatted = writer._format_entry(entry)

        assert "Buffer overflow" in formatted
        assert "main.c:100" in formatted

    def test_append_entries_uses_file_locking(self, tmp_path):
        """append_entries should use file locking for concurrent safety."""
        security_dir = tmp_path / "security"
        security_dir.mkdir()
        knowledge_file = security_dir / "KNOWLEDGE.md"

        knowledge_file.write_text(
            "# Security Reviewer Knowledge\n\n"
            "## Patterns Found\n\n"
            "## False Positives to Avoid\n\n"
            "## Incidents Prevented\n\n"
        )

        writer = KnowledgeWriter(reviewers_dir=tmp_path)

        entries = [
            LearningEntry(
                text=f"Finding {i}",
                section="patterns_found",
                reviewer_id="security",
                source="test.py",
                developer_id="alice",
            )
            for i in range(5)
        ]

        result = writer.append_entries(entries)

        assert result["security"] == 5

        content = knowledge_file.read_text()
        for i in range(5):
            assert f"Finding {i}" in content

    def test_concurrent_append_entries_no_corruption(self, tmp_path):
        """Concurrent append_entries calls should not corrupt knowledge file."""
        security_dir = tmp_path / "security"
        security_dir.mkdir()
        knowledge_file = security_dir / "KNOWLEDGE.md"

        knowledge_file.write_text(
            "# Security Reviewer Knowledge\n\n"
            "## Patterns Found\n\n"
            "## False Positives to Avoid\n\n"
            "## Incidents Prevented\n\n"
        )

        writer = KnowledgeWriter(reviewers_dir=tmp_path)

        def write_entries(thread_id):
            entries = [
                LearningEntry(
                    text=f"Thread-{thread_id}-Finding-{i}",
                    section="patterns_found",
                    reviewer_id="security",
                    source="test.py",
                    developer_id=f"dev{thread_id}",
                )
                for i in range(3)
            ]
            writer.append_entries(entries)

        threads = []
        for t in range(3):
            thread = threading.Thread(target=write_entries, args=(t,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        content = knowledge_file.read_text()
        for t in range(3):
            for i in range(3):
                assert f"Thread-{t}-Finding-{i}" in content

    def test_extract_learnings_preserves_developer_id(self, tmp_path):
        """extract_learnings should preserve developer_id when creating entries."""
        writer = KnowledgeWriter(reviewers_dir=tmp_path)

        review_findings = [
            {
                "text": "SQL injection in login",
                "severity": 9.5,
                "confidence": 9.0,
            }
        ]

        entries = writer.extract_learnings(review_findings, "security", "auth.py:10")

        assert len(entries) == 1
        entry = entries[0]

        entry.developer_id = "charlie"
        assert entry.developer_id == "charlie"
