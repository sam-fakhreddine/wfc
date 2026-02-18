"""Tests for worktree operations API and worktree-manager.sh integration."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wfc.wfc_tools.gitwork.api.worktree import (
    WorktreeOperations,
    _MANAGER_SCRIPT,
    validate_worktree_input,
)




class TestValidateWorktreeInput:
    def test_empty_task_id(self):
        assert validate_worktree_input("") == "task_id is required"

    def test_valid_task_id(self):
        assert validate_worktree_input("TASK-001") is None

    def test_valid_task_id_with_base(self):
        assert validate_worktree_input("TASK-001", "develop") is None

    def test_path_traversal_in_task_id(self):
        result = validate_worktree_input("../evil")
        assert result is not None
        assert "path traversal" in result

    def test_slash_in_task_id(self):
        result = validate_worktree_input("foo/bar")
        assert result is not None
        assert "path traversal" in result

    def test_flag_injection_in_task_id(self):
        result = validate_worktree_input("--exec=evil")
        assert result is not None
        assert "flag injection" in result

    def test_flag_injection_in_base_ref(self):
        result = validate_worktree_input("TASK-001", "--exec=evil")
        assert result is not None
        assert "flag injection" in result

    def test_path_traversal_in_base_ref(self):
        result = validate_worktree_input("TASK-001", "../../etc")
        assert result is not None
        assert "path traversal" in result




class TestManagerScript:
    def test_script_path_exists(self):
        assert _MANAGER_SCRIPT.name == "worktree-manager.sh"
        assert "scripts" in str(_MANAGER_SCRIPT)

    def test_script_is_under_gitwork(self):
        assert "gitwork" in str(_MANAGER_SCRIPT)




class TestWorktreeOperationsCreate:
    def test_create_validates_input(self):
        ops = WorktreeOperations()
        result = ops.create("")
        assert result["success"] is False
        assert "Validation failed" in result["message"]

    def test_create_rejects_path_traversal(self):
        ops = WorktreeOperations()
        result = ops.create("../evil")
        assert result["success"] is False

    @patch("wfc.wfc_tools.gitwork.api.worktree._MANAGER_SCRIPT")
    @patch("wfc.wfc_tools.gitwork.api.worktree._run_manager")
    def test_create_uses_manager_script(self, mock_run, mock_script):
        mock_script.exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="created", stderr="")

        ops = WorktreeOperations()
        result = ops.create("TASK-001", "develop")

        assert result["success"] is True
        assert result["env_synced"] is True
        assert result["branch_name"] == "wfc/TASK-001"
        assert result["worktree_path"] == ".worktrees/wfc-TASK-001"
        mock_run.assert_called_once_with(["create", "TASK-001", "develop"])

    @patch("wfc.wfc_tools.gitwork.api.worktree._MANAGER_SCRIPT")
    @patch("wfc.wfc_tools.gitwork.api.worktree._run_manager")
    def test_create_reports_manager_failure(self, mock_run, mock_script):
        mock_script.exists.return_value = True
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="branch already exists"
        )

        ops = WorktreeOperations()
        result = ops.create("TASK-001")

        assert result["success"] is False
        assert "worktree-manager.sh failed" in result["message"]

    @patch("wfc.wfc_tools.gitwork.api.worktree._MANAGER_SCRIPT")
    @patch("subprocess.run")
    def test_create_falls_back_to_raw_git(self, mock_run, mock_script):
        mock_script.exists.return_value = False
        mock_run.return_value = MagicMock(returncode=0)

        ops = WorktreeOperations()
        result = ops.create("TASK-001", "main")

        assert result["success"] is True
        assert result["env_synced"] is False

    def test_create_defaults_to_develop(self):
        ops = WorktreeOperations()
        with patch(
            "wfc.wfc_tools.gitwork.api.worktree._MANAGER_SCRIPT"
        ) as mock_script:
            mock_script.exists.return_value = True
            with patch(
                "wfc.wfc_tools.gitwork.api.worktree._run_manager"
            ) as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
                ops.create("TASK-002")
                mock_run.assert_called_once_with(["create", "TASK-002", "develop"])


class TestWorktreeOperationsDelete:
    def test_delete_validates_input(self):
        ops = WorktreeOperations()
        result = ops.delete("")
        assert result["success"] is False

    @patch("subprocess.run")
    def test_delete_prunes_after_remove(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        ops = WorktreeOperations()
        result = ops.delete("TASK-001")

        assert result["success"] is True
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_delete_with_force(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        ops = WorktreeOperations()
        ops.delete("TASK-001", force=True)

        first_call = mock_run.call_args_list[0]
        assert "--force" in first_call[0][0]


class TestWorktreeOperationsList:
    @patch("subprocess.run")
    def test_list_parses_porcelain(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="worktree /repo\nbranch refs/heads/main\n\nworktree /repo/.worktrees/wfc-TASK-001\nbranch refs/heads/wfc/TASK-001\n",
        )

        ops = WorktreeOperations()
        result = ops.list()

        assert len(result) == 2
        assert result[0]["path"] == "/repo"
        assert result[1]["branch"] == "refs/heads/wfc/TASK-001"

    @patch("subprocess.run")
    def test_list_handles_error(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        ops = WorktreeOperations()
        result = ops.list()
        assert result == []


class TestWorktreeOperationsCleanup:
    @patch("wfc.wfc_tools.gitwork.api.worktree._MANAGER_SCRIPT")
    @patch("wfc.wfc_tools.gitwork.api.worktree._run_manager")
    def test_cleanup_uses_manager(self, mock_run, mock_script):
        mock_script.exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="cleaned")

        ops = WorktreeOperations()
        result = ops.cleanup()

        assert result["success"] is True
        mock_run.assert_called_once_with(["cleanup"])

    @patch("wfc.wfc_tools.gitwork.api.worktree._MANAGER_SCRIPT")
    def test_cleanup_fails_without_script(self, mock_script):
        mock_script.exists.return_value = False

        ops = WorktreeOperations()
        result = ops.cleanup()
        assert result["success"] is False


class TestWorktreeOperationsSyncEnv:
    @patch("wfc.wfc_tools.gitwork.api.worktree._MANAGER_SCRIPT")
    @patch("wfc.wfc_tools.gitwork.api.worktree._run_manager")
    def test_sync_env_uses_manager(self, mock_run, mock_script):
        mock_script.exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="synced")

        ops = WorktreeOperations()
        result = ops.sync_env("TASK-001")

        assert result["success"] is True
        mock_run.assert_called_once_with(["copy-env", "TASK-001"])

    def test_sync_env_validates_input(self):
        ops = WorktreeOperations()
        result = ops.sync_env("")
        assert result["success"] is False


class TestWorktreeOperationsStatus:
    @patch("subprocess.run")
    def test_status_clean(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="")

        ops = WorktreeOperations()
        result = ops.status("TASK-001")

        assert result["success"] is True
        assert result["clean"] is True

    @patch("subprocess.run")
    def test_status_dirty(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=" M file.py\n")

        ops = WorktreeOperations()
        result = ops.status("TASK-001")

        assert result["success"] is True
        assert result["clean"] is False




class TestWorktreeManagerScript:
    """Tests that verify the worktree-manager.sh script exists and is valid."""

    def test_script_exists(self):
        script = Path(__file__).parent.parent / "wfc" / "wfc-tools" / "gitwork" / "scripts" / "worktree-manager.sh"
        assert script.exists(), f"worktree-manager.sh not found at {script}"

    def test_script_is_executable(self):
        script = Path(__file__).parent.parent / "wfc" / "wfc-tools" / "gitwork" / "scripts" / "worktree-manager.sh"
        if script.exists():
            import os
            assert os.access(script, os.X_OK), "worktree-manager.sh is not executable"

    def test_script_help_runs(self):
        script = Path(__file__).parent.parent / "wfc" / "wfc-tools" / "gitwork" / "scripts" / "worktree-manager.sh"
        if script.exists():
            result = subprocess.run(
                ["bash", str(script), "help"],
                capture_output=True, text=True
            )
            assert "WFC Worktree Manager" in result.stdout
            assert "create" in result.stdout
            assert "cleanup" in result.stdout




class TestModuleFunctions:
    """Test the module-level convenience functions."""

    @patch("wfc.wfc_tools.gitwork.api.worktree._instance")
    def test_create_delegates(self, mock_instance):
        from wfc.wfc_tools.gitwork.api import worktree
        worktree.create("TASK-001", "develop")
        mock_instance.create.assert_called_once_with("TASK-001", "develop")

    @patch("wfc.wfc_tools.gitwork.api.worktree._instance")
    def test_delete_delegates(self, mock_instance):
        from wfc.wfc_tools.gitwork.api import worktree
        worktree.delete("TASK-001", True)
        mock_instance.delete.assert_called_once_with("TASK-001", True)

    @patch("wfc.wfc_tools.gitwork.api.worktree._instance")
    def test_cleanup_delegates(self, mock_instance):
        from wfc.wfc_tools.gitwork.api import worktree
        worktree.cleanup()
        mock_instance.cleanup.assert_called_once()

    @patch("wfc.wfc_tools.gitwork.api.worktree._instance")
    def test_sync_env_delegates(self, mock_instance):
        from wfc.wfc_tools.gitwork.api import worktree
        worktree.sync_env("TASK-001")
        mock_instance.sync_env.assert_called_once_with("TASK-001")
