"""
Phase 1 - TASK-008 Integration Tests
Test ReviewOrchestrator with ProjectContext integration.
"""

from wfc.shared.config.wfc_config import WFCConfig
from wfc.scripts.orchestrators.review.orchestrator import ReviewOrchestrator


class TestReviewOrchestratorProjectContext:
    """Test ReviewOrchestrator integration with ProjectContext."""

    def test_orchestrator_accepts_project_context(self, tmp_path):
        """ReviewOrchestrator should accept optional project_context parameter."""
        config = WFCConfig(project_root=tmp_path)
        project_context = config.create_project_context("test-proj", "test-dev", tmp_path)

        orchestrator = ReviewOrchestrator(
            config=config,
            project_context=project_context,
        )

        assert orchestrator.project_context == project_context

    def test_orchestrator_backward_compatible_without_project_context(self, tmp_path):
        """ReviewOrchestrator should work without project_context (backward compat)."""
        config = WFCConfig(project_root=tmp_path)

        orchestrator = ReviewOrchestrator(config=config)

        assert orchestrator.project_context is None

    def test_orchestrator_uses_namespaced_output_dir(self, tmp_path):
        """Output directory should use project_context.output_dir when provided."""
        config = WFCConfig(project_root=tmp_path)
        project_context = config.create_project_context("test-proj", "test-dev", tmp_path)

        orchestrator = ReviewOrchestrator(
            config=config,
            project_context=project_context,
        )

        assert orchestrator.output_dir == project_context.output_dir
        assert "test-proj" in str(orchestrator.output_dir)

    def test_orchestrator_uses_legacy_output_dir_without_context(self, tmp_path):
        """Output directory should use legacy path when project_context is None."""
        config = WFCConfig(project_root=tmp_path)

        orchestrator = ReviewOrchestrator(config=config)

        assert orchestrator.output_dir == tmp_path / ".wfc" / "output"

    def test_orchestrator_creates_worktree_operations_with_project_id(self, tmp_path):
        """WorktreeOperations should be created with project_id when context provided."""
        config = WFCConfig(project_root=tmp_path)
        project_context = config.create_project_context("test-proj", "test-dev", tmp_path)

        orchestrator = ReviewOrchestrator(
            config=config,
            project_context=project_context,
        )

        worktree_ops = orchestrator._create_worktree_operations()

        assert worktree_ops.project_id == "test-proj"

    def test_orchestrator_creates_legacy_worktree_operations_without_context(self, tmp_path):
        """WorktreeOperations should be created without project_id when context is None."""
        config = WFCConfig(project_root=tmp_path)

        orchestrator = ReviewOrchestrator(config=config)

        worktree_ops = orchestrator._create_worktree_operations()

        assert worktree_ops.project_id is None

    def test_report_filename_includes_project_id(self, tmp_path):
        """Report filename should include project_id when context provided."""
        config = WFCConfig(project_root=tmp_path)
        project_context = config.create_project_context("test-proj", "test-dev", tmp_path)

        orchestrator = ReviewOrchestrator(
            config=config,
            project_context=project_context,
        )

        report_name = orchestrator._get_report_filename()

        assert "test-proj" in report_name
        assert report_name.startswith("REVIEW-test-proj")

    def test_report_filename_legacy_without_project_id(self, tmp_path):
        """Report filename should use 'global' when project_context is None."""
        config = WFCConfig(project_root=tmp_path)

        orchestrator = ReviewOrchestrator(config=config)

        report_name = orchestrator._get_report_filename()

        assert "global" in report_name or "REVIEW" in report_name

    def test_two_projects_different_output_directories(self, tmp_path):
        """Two projects should have completely separate output directories."""
        config = WFCConfig(project_root=tmp_path)

        context1 = config.create_project_context("proj1", "dev1", tmp_path)
        context2 = config.create_project_context("proj2", "dev2", tmp_path)

        orchestrator1 = ReviewOrchestrator(config=config, project_context=context1)
        orchestrator2 = ReviewOrchestrator(config=config, project_context=context2)

        assert orchestrator1.output_dir != orchestrator2.output_dir
        assert "proj1" in str(orchestrator1.output_dir)
        assert "proj2" in str(orchestrator2.output_dir)
