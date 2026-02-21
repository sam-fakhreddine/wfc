"""
Tier 0 MVP - TASK-002 Tests
Test WorktreeOperations project namespacing.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock
from wfc.gitwork.api.worktree import WorktreeOperations


class TestWorktreeOperationsNamespacing:
    """Test WorktreeOperations project_id namespacing."""

    def test_worktree_operations_accepts_project_id(self):
        """WorktreeOperations should accept project_id parameter."""
        ops = WorktreeOperations(project_id="proj1")
        assert ops.project_id == "proj1"

    def test_worktree_operations_defaults_to_none(self):
        """WorktreeOperations should default project_id to None."""
        ops = WorktreeOperations()
        assert ops.project_id is None

    @patch("wfc.gitwork.api.worktree._repo_root")
    def test_worktree_path_with_project_id(self, mock_repo_root):
        """Worktree path should include project_id when set."""
        mock_repo_root.return_value = "/repo"
        ops = WorktreeOperations(project_id="proj1")

        path = ops._worktree_path("test-task")

        assert path == Path("/repo/.worktrees/proj1/wfc-test-task")

    @patch("wfc.gitwork.api.worktree._repo_root")
    def test_worktree_path_without_project_id(self, mock_repo_root):
        """Worktree path should use legacy format when project_id is None."""
        mock_repo_root.return_value = "/repo"
        ops = WorktreeOperations()

        path = ops._worktree_path("test-task")

        assert path == Path("/repo/.worktrees/wfc-test-task")

    @patch("wfc.gitwork.api.worktree._repo_root")
    def test_worktree_path_fallback_with_project_id(self, mock_repo_root):
        """Worktree path should namespace relative path when git fails."""
        mock_repo_root.return_value = None
        ops = WorktreeOperations(project_id="proj1")

        path = ops._worktree_path("test-task")

        assert path == Path(".worktrees/proj1/wfc-test-task")

    @patch("wfc.gitwork.api.worktree._repo_root")
    def test_worktree_path_fallback_without_project_id(self, mock_repo_root):
        """Worktree path should use legacy relative path when git fails."""
        mock_repo_root.return_value = None
        ops = WorktreeOperations()

        path = ops._worktree_path("test-task")

        assert path == Path(".worktrees/wfc-test-task")

    @patch("wfc.gitwork.api.worktree._run_manager")
    @patch("wfc.gitwork.api.worktree._MANAGER_SCRIPT")
    @patch("wfc.gitwork.api.worktree._repo_root")
    def test_create_branch_name_with_project_id(
        self, mock_repo_root, mock_script, mock_run_manager
    ):
        """Create should namespace branch name when project_id is set."""
        mock_repo_root.return_value = "/repo"
        mock_script.exists.return_value = True
        mock_run_manager.return_value = MagicMock(returncode=0, stdout="", stderr="")

        ops = WorktreeOperations(project_id="proj1")
        result = ops.create("test-task")

        assert result["success"] is True
        assert result["branch_name"] == "wfc/proj1/test-task"

    @patch("wfc.gitwork.api.worktree._run_manager")
    @patch("wfc.gitwork.api.worktree._MANAGER_SCRIPT")
    @patch("wfc.gitwork.api.worktree._repo_root")
    def test_create_branch_name_without_project_id(
        self, mock_repo_root, mock_script, mock_run_manager
    ):
        """Create should use legacy branch name when project_id is None."""
        mock_repo_root.return_value = "/repo"
        mock_script.exists.return_value = True
        mock_run_manager.return_value = MagicMock(returncode=0, stdout="", stderr="")

        ops = WorktreeOperations()
        result = ops.create("test-task")

        assert result["success"] is True
        assert result["branch_name"] == "wfc/test-task"

    @patch("wfc.gitwork.api.worktree._repo_root")
    def test_two_projects_same_task_different_paths(self, mock_repo_root):
        """Two projects with same task_id should get different paths."""
        mock_repo_root.return_value = "/repo"

        ops1 = WorktreeOperations(project_id="proj1")
        ops2 = WorktreeOperations(project_id="proj2")

        path1 = ops1._worktree_path("same-task")
        path2 = ops2._worktree_path("same-task")

        assert path1 != path2
        assert path1 == Path("/repo/.worktrees/proj1/wfc-same-task")
        assert path2 == Path("/repo/.worktrees/proj2/wfc-same-task")

    @patch("wfc.gitwork.api.worktree._run_manager")
    @patch("wfc.gitwork.api.worktree._MANAGER_SCRIPT")
    @patch("wfc.gitwork.api.worktree._repo_root")
    def test_two_projects_same_task_different_branches(
        self, mock_repo_root, mock_script, mock_run_manager
    ):
        """Two projects with same task_id should get different branch names."""
        mock_repo_root.return_value = "/repo"
        mock_script.exists.return_value = True
        mock_run_manager.return_value = MagicMock(returncode=0, stdout="", stderr="")

        ops1 = WorktreeOperations(project_id="proj1")
        ops2 = WorktreeOperations(project_id="proj2")

        result1 = ops1.create("same-task")
        result2 = ops2.create("same-task")

        assert result1["branch_name"] != result2["branch_name"]
        assert result1["branch_name"] == "wfc/proj1/same-task"
        assert result2["branch_name"] == "wfc/proj2/same-task"
