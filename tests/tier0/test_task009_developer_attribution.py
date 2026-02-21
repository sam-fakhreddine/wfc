"""
Phase 1 - TASK-009 Integration Tests
Test that developer_id flows from ProjectContext to KnowledgeWriter.
"""

from wfc.scripts.knowledge.knowledge_writer import LearningEntry, KnowledgeWriter


class TestDeveloperAttributionFlow:
    """Test developer_id attribution flow."""

    def test_learning_entry_accepts_developer_id_from_context(self, tmp_path):
        """LearningEntry should accept developer_id parameter."""
        entry = LearningEntry(
            text="Test finding",
            section="patterns_found",
            reviewer_id="security",
            source="test.py",
            developer_id="alice",
        )

        assert entry.developer_id == "alice"

    def test_knowledge_writer_preserves_developer_id(self, tmp_path):
        """KnowledgeWriter should preserve developer_id in formatted entries."""
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

        entry = LearningEntry(
            text="SQL injection vulnerability",
            section="patterns_found",
            reviewer_id="security",
            source="auth.py:42",
            developer_id="bob",
        )

        writer.append_entries([entry])

        content = knowledge_file.read_text()

        assert "bob" in content.lower()
        assert "SQL injection vulnerability" in content

    def test_orchestrator_can_provide_developer_id_to_learnings(self, tmp_path):
        """
        Integration test: ProjectContext developer_id flows to knowledge entries.

        This test simulates the flow:
        1. ProjectContext created with developer_id
        2. Review findings generated
        3. Learnings extracted with developer attribution
        4. Knowledge base updated with developer_id
        """
        from wfc.shared.config.wfc_config import WFCConfig

        config = WFCConfig(project_root=tmp_path)
        project_context = config.create_project_context("proj1", "charlie", tmp_path)

        reviewers_dir = tmp_path / "reviewers"
        security_dir = reviewers_dir / "security"
        security_dir.mkdir(parents=True)
        knowledge_file = security_dir / "KNOWLEDGE.md"

        knowledge_file.write_text(
            "# Security Reviewer Knowledge\n\n"
            "## Patterns Found\n\n"
            "## False Positives to Avoid\n\n"
            "## Incidents Prevented\n\n"
        )

        writer = KnowledgeWriter(reviewers_dir=reviewers_dir)

        entry = LearningEntry(
            text="XSS vulnerability in user input",
            section="patterns_found",
            reviewer_id="security",
            source="views.py:123",
            developer_id=project_context.developer_id,
        )

        writer.append_entries([entry])

        content = knowledge_file.read_text()

        assert project_context.developer_id in content
        assert "charlie" in content
        assert "XSS vulnerability" in content
