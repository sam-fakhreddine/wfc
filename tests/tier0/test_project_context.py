"""
Tier 0 MVP - TASK-001 Tests
Test ProjectContext dataclass and factory method.
"""

import pytest
from pathlib import Path

from wfc.shared.config.wfc_config import WFCConfig, ProjectContext


class TestProjectContext:
    """Test ProjectContext dataclass and creation."""

    def test_project_context_dataclass_exists(self):
        """ProjectContext should be importable."""

    def test_project_context_has_required_fields(self):
        """ProjectContext should have all 6 required fields."""
        ctx = ProjectContext(
            project_id="test-proj",
            developer_id="alice",
            repo_path=Path("/tmp/repo"),
            worktree_dir=Path("/tmp/repo/.worktrees/test-proj"),
            metrics_dir=Path.home() / ".wfc/metrics/test-proj",
            output_dir=Path("/tmp/repo/.wfc/output/test-proj"),
        )

        assert ctx.project_id == "test-proj"
        assert ctx.developer_id == "alice"
        assert ctx.repo_path == Path("/tmp/repo").resolve()
        assert ctx.worktree_dir == Path("/tmp/repo/.worktrees/test-proj").resolve()
        assert ctx.metrics_dir == (Path.home() / ".wfc/metrics/test-proj").resolve()
        assert ctx.output_dir == Path("/tmp/repo/.wfc/output/test-proj").resolve()

    def test_project_context_converts_paths_to_absolute(self):
        """__post_init__ should convert all paths to absolute."""
        ctx = ProjectContext(
            project_id="test",
            developer_id="bob",
            repo_path=Path("relative/path"),
            worktree_dir=Path("worktrees"),
            metrics_dir=Path("metrics"),
            output_dir=Path("output"),
        )

        assert ctx.repo_path.is_absolute()
        assert ctx.worktree_dir.is_absolute()
        assert ctx.metrics_dir.is_absolute()
        assert ctx.output_dir.is_absolute()

    def test_wfc_config_has_create_project_context_method(self):
        """WFCConfig should have create_project_context factory method."""
        config = WFCConfig()
        assert hasattr(config, "create_project_context")
        assert callable(config.create_project_context)

    def test_create_project_context_basic(self, tmp_path):
        """create_project_context should create valid ProjectContext."""
        config = WFCConfig(project_root=tmp_path)

        ctx = config.create_project_context(project_id="proj1", developer_id="alice")

        assert ctx.project_id == "proj1"
        assert ctx.developer_id == "alice"
        assert ctx.repo_path == tmp_path
        assert "proj1" in str(ctx.worktree_dir)
        assert "proj1" in str(ctx.metrics_dir)
        assert "proj1" in str(ctx.output_dir)

    def test_create_project_context_namespaced_paths(self, tmp_path):
        """Paths should be namespaced by project_id."""
        config = WFCConfig(project_root=tmp_path)

        ctx = config.create_project_context(project_id="my-project", developer_id="bob")

        assert ctx.worktree_dir == tmp_path / ".worktrees" / "my-project"

        expected_metrics = Path.home() / ".claude" / "metrics" / "my-project"
        assert ctx.metrics_dir == expected_metrics

        assert ctx.output_dir == tmp_path / ".wfc" / "output" / "my-project"

    def test_create_project_context_validates_project_id(self):
        """Should reject invalid project_id (not matching ^[a-zA-Z0-9_-]{1,64}$)."""
        config = WFCConfig()

        config.create_project_context("valid-id_123", "dev")
        config.create_project_context("project", "dev")
        config.create_project_context("proj-123_test", "dev")

        with pytest.raises(ValueError, match="Invalid project_id"):
            config.create_project_context("invalid/id", "dev")

        with pytest.raises(ValueError, match="Invalid project_id"):
            config.create_project_context("../../etc/passwd", "dev")

        with pytest.raises(ValueError, match="Invalid project_id"):
            config.create_project_context("", "dev")

        with pytest.raises(ValueError, match="Invalid project_id"):
            config.create_project_context("a" * 65, "dev")

        with pytest.raises(ValueError, match="Invalid project_id"):
            config.create_project_context("invalid id", "dev")

    def test_create_project_context_validates_developer_id(self):
        """Should reject invalid developer_id (not matching ^[a-zA-Z0-9_-]{1,64}$)."""
        config = WFCConfig()

        config.create_project_context("proj", "alice")
        config.create_project_context("proj", "dev-123_test")

        with pytest.raises(ValueError, match="Invalid developer_id"):
            config.create_project_context("proj", "invalid/dev")

        with pytest.raises(ValueError, match="Invalid developer_id"):
            config.create_project_context("proj", "")

        with pytest.raises(ValueError, match="Invalid developer_id"):
            config.create_project_context("proj", "a" * 65)

        with pytest.raises(ValueError, match="Invalid developer_id"):
            config.create_project_context("proj", "dev name")

    def test_create_project_context_custom_repo_path(self, tmp_path):
        """Should accept custom repo_path parameter."""
        config = WFCConfig()
        custom_repo = tmp_path / "custom"
        custom_repo.mkdir()

        ctx = config.create_project_context(
            project_id="proj", developer_id="alice", repo_path=custom_repo
        )

        assert ctx.repo_path == custom_repo
        assert ctx.worktree_dir == custom_repo / ".worktrees" / "proj"

    def test_create_project_context_all_paths_absolute(self, tmp_path):
        """All paths in returned ProjectContext should be absolute."""
        config = WFCConfig(project_root=tmp_path)

        ctx = config.create_project_context(project_id="proj", developer_id="dev")

        assert ctx.repo_path.is_absolute()
        assert ctx.worktree_dir.is_absolute()
        assert ctx.metrics_dir.is_absolute()
        assert ctx.output_dir.is_absolute()
