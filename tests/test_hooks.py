"""
Unit tests for WFC Git Hooks

Tests pre-commit, commit-msg, and pre-push hooks with various scenarios.
"""

import io
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Import hook modules
from wfc.wfc_tools.gitwork.hooks import commit_msg, pre_commit, pre_push
from wfc.wfc_tools.gitwork.hooks.installer import HookInstaller


class TestPreCommitHook:
    """Test pre-commit hook functionality."""

    def test_get_current_branch_success(self):
        """Test getting current branch name."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="main\n")
            branch = pre_commit.get_current_branch()
            assert branch == "main"

    def test_get_current_branch_failure(self):
        """Test handling of branch detection failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Git error")
            branch = pre_commit.get_current_branch()
            assert branch is None

    def test_get_staged_files(self):
        """Test getting staged files list."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="file1.py\nfile2.py\n")
            files = pre_commit.get_staged_files()
            assert files == ["file1.py", "file2.py"]

    def test_validate_branch_name_valid_feat(self):
        """Test valid feature branch name."""
        result = pre_commit.validate_branch_name("feat/TASK-001-add-auth")
        assert result["valid"] is True

    def test_validate_branch_name_valid_fix(self):
        """Test valid fix branch name."""
        result = pre_commit.validate_branch_name("fix/TASK-123-bug-fix")
        assert result["valid"] is True

    def test_validate_branch_name_invalid_no_slash(self):
        """Test invalid branch name without slash."""
        result = pre_commit.validate_branch_name("random-branch")
        assert result["valid"] is False
        assert "doesn't follow convention" in result["message"]

    def test_validate_branch_name_invalid_prefix(self):
        """Test invalid branch name with unknown prefix."""
        result = pre_commit.validate_branch_name("invalid/TASK-001-test")
        assert result["valid"] is False
        assert "Unknown prefix" in result["message"]

    def test_validate_branch_name_missing_task_id(self):
        """Test branch name missing TASK-XXX."""
        result = pre_commit.validate_branch_name("feat/add-feature")
        assert result["valid"] is False
        assert "Missing TASK-XXX" in result["message"]

    def test_check_sensitive_files_env(self):
        """Test detection of .env files."""
        files = [".env", "config.py", "README.md"]
        sensitive = pre_commit.check_sensitive_files(files)
        assert ".env" in sensitive
        assert len(sensitive) == 1

    def test_check_sensitive_files_credentials(self):
        """Test detection of credential files."""
        files = ["app.py", "credentials.json", "test.py"]
        sensitive = pre_commit.check_sensitive_files(files)
        assert "credentials.json" in sensitive

    def test_check_sensitive_files_multiple(self):
        """Test detection of multiple sensitive files."""
        files = [".env", "id_rsa", "normal.py", "password.txt"]
        sensitive = pre_commit.check_sensitive_files(files)
        assert len(sensitive) == 3
        assert ".env" in sensitive
        assert "id_rsa" in sensitive
        assert "password.txt" in sensitive

    def test_check_sensitive_files_none(self):
        """Test no sensitive files detected."""
        files = ["app.py", "test.py", "README.md"]
        sensitive = pre_commit.check_sensitive_files(files)
        assert len(sensitive) == 0

    @patch("wfc.wfc_tools.gitwork.hooks.pre_commit.get_current_branch")
    @patch("wfc.wfc_tools.gitwork.hooks.pre_commit.get_staged_files")
    @patch("wfc.wfc_tools.gitwork.hooks.pre_commit.log_telemetry")
    def test_pre_commit_hook_protected_branch(self, mock_log, mock_staged, mock_branch):
        """Test pre-commit hook on protected branch."""
        mock_branch.return_value = "main"
        mock_staged.return_value = ["test.py"]

        # Capture stdout
        captured_output = io.StringIO()
        with patch("sys.stdout", new=captured_output):
            exit_code = pre_commit.pre_commit_hook()

        assert exit_code == 0  # Never blocks
        output = captured_output.getvalue()
        assert "WARNING: Committing directly to 'main'" in output
        mock_log.assert_called()

    @patch("wfc.wfc_tools.gitwork.hooks.pre_commit.get_current_branch")
    @patch("wfc.wfc_tools.gitwork.hooks.pre_commit.get_staged_files")
    @patch("wfc.wfc_tools.gitwork.hooks.pre_commit.log_telemetry")
    def test_pre_commit_hook_invalid_branch_name(self, mock_log, mock_staged, mock_branch):
        """Test pre-commit hook with invalid branch name."""
        mock_branch.return_value = "random-branch"
        mock_staged.return_value = ["test.py"]

        captured_output = io.StringIO()
        with patch("sys.stdout", new=captured_output):
            exit_code = pre_commit.pre_commit_hook()

        assert exit_code == 0  # Never blocks
        output = captured_output.getvalue()
        assert "WARNING" in output

    @patch("wfc.wfc_tools.gitwork.hooks.pre_commit.get_current_branch")
    @patch("wfc.wfc_tools.gitwork.hooks.pre_commit.get_staged_files")
    @patch("wfc.wfc_tools.gitwork.hooks.pre_commit.log_telemetry")
    def test_pre_commit_hook_sensitive_files(self, mock_log, mock_staged, mock_branch):
        """Test pre-commit hook with sensitive files."""
        mock_branch.return_value = "feat/TASK-001-test"
        mock_staged.return_value = [".env", "test.py"]

        captured_output = io.StringIO()
        with patch("sys.stdout", new=captured_output):
            exit_code = pre_commit.pre_commit_hook()

        assert exit_code == 0
        output = captured_output.getvalue()
        assert "sensitive files detected" in output
        assert ".env" in output

    @patch("wfc.wfc_tools.gitwork.hooks.pre_commit.get_current_branch")
    @patch("wfc.wfc_tools.gitwork.hooks.pre_commit.get_staged_files")
    def test_pre_commit_hook_all_good(self, mock_staged, mock_branch):
        """Test pre-commit hook with valid branch and no issues."""
        mock_branch.return_value = "feat/TASK-001-add-feature"
        mock_staged.return_value = ["app.py", "test.py"]

        exit_code = pre_commit.pre_commit_hook()
        assert exit_code == 0  # Always succeeds


class TestCommitMsgHook:
    """Test commit-msg hook functionality."""

    def test_validate_commit_message_task_format(self):
        """Test valid TASK-XXX format."""
        result = commit_msg.validate_commit_message("TASK-001: Add authentication")
        assert result["valid"] is True

    def test_validate_commit_message_conventional_feat(self):
        """Test valid conventional commit (feat)."""
        result = commit_msg.validate_commit_message("feat: add user login")
        assert result["valid"] is True

    def test_validate_commit_message_conventional_fix(self):
        """Test valid conventional commit (fix)."""
        result = commit_msg.validate_commit_message("fix: resolve timeout issue")
        assert result["valid"] is True

    def test_validate_commit_message_conventional_with_scope(self):
        """Test valid conventional commit with scope."""
        result = commit_msg.validate_commit_message("feat(api): add rate limiting")
        assert result["valid"] is True

    def test_validate_commit_message_invalid(self):
        """Test invalid commit message."""
        result = commit_msg.validate_commit_message("Added some stuff")
        assert result["valid"] is False
        assert "doesn't follow convention" in result["message"]

    def test_validate_commit_message_empty(self):
        """Test empty commit message."""
        result = commit_msg.validate_commit_message("")
        assert result["valid"] is False

    def test_extract_task_id_present(self):
        """Test extracting TASK-XXX from message."""
        task_id = commit_msg.extract_task_id("TASK-123: Add feature")
        assert task_id == "TASK-123"

    def test_extract_task_id_in_middle(self):
        """Test extracting TASK-XXX from middle of message."""
        task_id = commit_msg.extract_task_id("feat: implement TASK-456 requirements")
        assert task_id == "TASK-456"

    def test_extract_task_id_absent(self):
        """Test no TASK-XXX in message."""
        task_id = commit_msg.extract_task_id("feat: add feature")
        assert task_id is None

    @patch("builtins.open", new_callable=mock_open, read_data="TASK-001: Add feature\n")
    @patch("wfc.wfc_tools.gitwork.hooks.commit_msg.log_telemetry")
    def test_commit_msg_hook_valid_task_format(self, mock_log, mock_file):
        """Test commit-msg hook with valid TASK format."""
        with patch("pathlib.Path.read_text", return_value="TASK-001: Add feature"):
            exit_code = commit_msg.commit_msg_hook("/tmp/COMMIT_EDITMSG")

        assert exit_code == 0
        mock_log.assert_called()

    @patch("builtins.open", new_callable=mock_open, read_data="feat: add feature\n")
    @patch("wfc.wfc_tools.gitwork.hooks.commit_msg.log_telemetry")
    def test_commit_msg_hook_valid_conventional(self, mock_log, mock_file):
        """Test commit-msg hook with valid conventional format."""
        with patch("pathlib.Path.read_text", return_value="feat: add feature"):
            exit_code = commit_msg.commit_msg_hook("/tmp/COMMIT_EDITMSG")

        assert exit_code == 0

    @patch("builtins.open", new_callable=mock_open, read_data="bad message\n")
    @patch("wfc.wfc_tools.gitwork.hooks.commit_msg.log_telemetry")
    def test_commit_msg_hook_invalid_format(self, mock_log, mock_file):
        """Test commit-msg hook with invalid format."""
        captured_output = io.StringIO()

        with patch("pathlib.Path.read_text", return_value="bad message"):
            with patch("sys.stdout", new=captured_output):
                exit_code = commit_msg.commit_msg_hook("/tmp/COMMIT_EDITMSG")

        assert exit_code == 0  # Never blocks
        output = captured_output.getvalue()
        assert "WARNING" in output
        mock_log.assert_called()


class TestPrePushHook:
    """Test pre-push hook functionality."""

    def test_parse_push_info_single_push(self):
        """Test parsing single push info."""
        test_input = "refs/heads/main abc123 refs/heads/main def456\n"

        with patch("sys.stdin", io.StringIO(test_input)):
            pushes = pre_push.parse_push_info()

        assert len(pushes) == 1
        assert pushes[0] == ("main", "main")

    def test_parse_push_info_multiple_pushes(self):
        """Test parsing multiple push info."""
        test_input = (
            "refs/heads/main abc123 refs/heads/main def456\n"
            "refs/heads/feat abc123 refs/heads/feat def456\n"
        )

        with patch("sys.stdin", io.StringIO(test_input)):
            pushes = pre_push.parse_push_info()

        assert len(pushes) == 2
        assert pushes[0] == ("main", "main")
        assert pushes[1] == ("feat", "feat")

    def test_parse_push_info_empty(self):
        """Test parsing empty push info."""
        with patch("sys.stdin", io.StringIO("")):
            pushes = pre_push.parse_push_info()

        assert len(pushes) == 0

    @patch("subprocess.run")
    def test_get_remote_url_success(self, mock_run):
        """Test getting remote URL."""
        mock_run.return_value = MagicMock(returncode=0, stdout="git@github.com:user/repo.git\n")
        url = pre_push.get_remote_url()
        assert url == "git@github.com:user/repo.git"

    @patch("subprocess.run")
    def test_get_remote_url_failure(self, mock_run):
        """Test handling of remote URL failure."""
        mock_run.side_effect = Exception("Git error")
        url = pre_push.get_remote_url()
        assert url is None

    def test_pre_push_hook_protected_branch(self):
        """Test pre-push hook with protected branch."""
        test_input = "refs/heads/main abc123 refs/heads/main def456\n"

        with patch("sys.stdin", io.StringIO(test_input)):
            with patch("wfc.wfc_tools.gitwork.hooks.pre_push.get_remote_url") as mock_url:
                with patch("wfc.wfc_tools.gitwork.hooks.pre_push.log_telemetry") as mock_telemetry:
                    mock_url.return_value = "git@github.com:user/repo.git"

                    captured_output = io.StringIO()
                    with patch("sys.stdout", new=captured_output):
                        exit_code = pre_push.pre_push_hook()

                    assert exit_code == 0  # Never blocks
                    output = captured_output.getvalue()
                    assert "WARNING: Pushing to protected branch" in output
                    mock_telemetry.assert_called()

    @patch("sys.stdin", io.StringIO("refs/heads/feat a b refs/heads/feat c\n"))
    @patch("wfc.wfc_tools.gitwork.hooks.pre_push.get_remote_url")
    def test_pre_push_hook_feature_branch(self, mock_url):
        """Test pre-push hook with feature branch (no warning)."""
        mock_url.return_value = "git@github.com:user/repo.git"

        captured_output = io.StringIO()
        with patch("sys.stdout", new=captured_output):
            exit_code = pre_push.pre_push_hook()

        assert exit_code == 0
        output = captured_output.getvalue()
        # Should not warn about feature branches
        assert "WARNING" not in output, "Feature branches should not produce warnings"


class TestHookInstaller:
    """Test hook installer functionality."""

    def test_installer_init(self):
        """Test installer initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            installer = HookInstaller(tmpdir)
            assert installer.project_root == Path(tmpdir)

    def test_is_git_repo_false(self):
        """Test git repo detection (not a repo)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            installer = HookInstaller(tmpdir)
            assert installer.is_git_repo() is False

    def test_is_git_repo_true(self):
        """Test git repo detection (is a repo)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .git directory
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()

            installer = HookInstaller(tmpdir)
            assert installer.is_git_repo() is True

    def test_get_hook_status_not_git_repo(self):
        """Test hook status when not a git repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            installer = HookInstaller(tmpdir)
            status = installer.get_hook_status()
            assert status == []

    def test_get_hook_status_no_hooks(self):
        """Test hook status with no hooks installed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()
            hooks_dir = git_dir / "hooks"
            hooks_dir.mkdir()

            installer = HookInstaller(tmpdir)
            status = installer.get_hook_status()

            assert len(status) == 3  # 3 hooks
            assert all(not h["installed"] for h in status)

    def test_install_hook_not_git_repo(self):
        """Test installing hook when not a git repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            installer = HookInstaller(tmpdir)
            result = installer.install_all()
            assert result["success"] is False
            assert "Not a git repository" in result["message"]

    def test_install_hook_creates_hooks_dir(self):
        """Test that install creates hooks directory if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()

            installer = HookInstaller(tmpdir)
            result = installer.install_all()

            hooks_dir = git_dir / "hooks"
            assert hooks_dir.exists()

    def test_install_hook_success(self):
        """Test successful hook installation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()

            installer = HookInstaller(tmpdir)
            result = installer.install_all()

            assert result["success"] is True
            assert len(result["installed"]) == 3

    def test_install_hook_creates_executable(self):
        """Test that installed hooks are executable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()

            installer = HookInstaller(tmpdir)
            installer.install_all()

            hook_path = git_dir / "hooks" / "pre-commit"
            assert hook_path.exists()
            assert hook_path.stat().st_mode & 0o111 != 0  # Executable

    def test_install_hook_preserves_existing(self):
        """Test that install preserves existing hooks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()
            hooks_dir = git_dir / "hooks"
            hooks_dir.mkdir()

            # Create existing hook
            existing_hook = hooks_dir / "pre-commit"
            existing_hook.write_text("#!/bin/bash\necho 'existing hook'\n")

            installer = HookInstaller(tmpdir)
            installer.install_all()

            # Check that existing hook is preserved
            hook_content = existing_hook.read_text()
            assert "existing hook" in hook_content
            assert "WFC-managed" in hook_content

    def test_uninstall_hook_not_installed(self):
        """Test uninstalling hook that's not installed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()
            hooks_dir = git_dir / "hooks"
            hooks_dir.mkdir()

            installer = HookInstaller(tmpdir)
            result = installer.uninstall_hook("pre-commit")

            assert result["success"] is True
            assert "not installed" in result["message"]

    def test_uninstall_hook_success(self):
        """Test successful hook uninstall."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()

            installer = HookInstaller(tmpdir)
            installer.install_all()

            result = installer.uninstall_all()
            assert result["success"] is True
            assert len(result["uninstalled"]) == 3

    def test_uninstall_hook_restores_original(self):
        """Test that uninstall restores original hook."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()
            hooks_dir = git_dir / "hooks"
            hooks_dir.mkdir()

            # Create existing hook
            existing_hook = hooks_dir / "pre-commit"
            original_content = "#!/bin/bash\necho 'original hook'\n"
            existing_hook.write_text(original_content)

            installer = HookInstaller(tmpdir)
            installer.install_all()

            # Verify WFC hook installed
            content = existing_hook.read_text()
            assert "WFC-managed" in content

            # Uninstall
            installer.uninstall_all()

            # Verify original restored
            content = existing_hook.read_text()
            assert "original hook" in content
            assert "WFC-managed" not in content

    def test_print_status(self):
        """Test printing hook status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()

            installer = HookInstaller(tmpdir)
            installer.install_all()

            # Should not raise exception
            captured_output = io.StringIO()
            with patch("sys.stdout", new=captured_output):
                installer.print_status()

            output = captured_output.getvalue()
            assert "WFC Git Hooks Status" in output
            assert "pre-commit" in output
            assert "commit-msg" in output
            assert "pre-push" in output


# Test telemetry integration with hooks
class TestHookTelemetryIntegration:
    """Test that hooks properly log to telemetry."""

    @patch("wfc.wfc_tools.gitwork.hooks.pre_commit.get_current_branch")
    @patch("wfc.wfc_tools.gitwork.hooks.pre_commit.get_staged_files")
    def test_pre_commit_logs_telemetry(self, mock_staged, mock_branch):
        """Test that pre-commit hook logs telemetry."""
        mock_branch.return_value = "main"
        mock_staged.return_value = ["test.py"]

        with patch("wfc.shared.telemetry_auto.log_event") as mock_log:
            pre_commit.pre_commit_hook()
            mock_log.assert_called()
            # Check that event type is correct
            call_args = mock_log.call_args
            assert call_args[0][0] == "hook_warning"

    @patch("builtins.open", new_callable=mock_open, read_data="bad message\n")
    def test_commit_msg_logs_telemetry(self, mock_file):
        """Test that commit-msg hook logs telemetry."""
        with patch("pathlib.Path.read_text", return_value="bad message"):
            with patch("wfc.shared.telemetry_auto.log_event") as mock_log:
                commit_msg.commit_msg_hook("/tmp/COMMIT_EDITMSG")
                mock_log.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
