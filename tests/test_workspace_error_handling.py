"""Tests for workspace.py error handling - TASK-001.

This module tests comprehensive error handling for all file I/O operations
in workspace.py, ensuring PROP-001 (file safety), PROP-002 (cleanup on failure),
and PROP-003 (input validation) are satisfied.
"""

import shutil
from pathlib import Path

import pytest


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace for testing."""
    base_dir = tmp_path / ".development" / "prompt-fixer"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


@pytest.fixture
def workspace_manager(temp_workspace):
    """Create a WorkspaceManager instance with temp directory."""
    from wfc.skills import wfc_prompt_fixer

    return wfc_prompt_fixer.workspace.WorkspaceManager(base_dir=temp_workspace)


@pytest.fixture
def sample_prompt(tmp_path):
    """Create a sample prompt file for testing."""
    prompt_file = tmp_path / "test_prompt.md"
    prompt_file.write_text("# Test Prompt\n\nThis is a test prompt.")
    return prompt_file


class TestWorkspaceError:
    """Test custom WorkspaceError exception class."""

    def test_workspace_error_exists(self):
        """Test that WorkspaceError exception class exists."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        assert issubclass(WorkspaceError, Exception)

    def test_workspace_error_can_be_raised(self):
        """Test that WorkspaceError can be raised with message."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        with pytest.raises(WorkspaceError) as exc_info:
            raise WorkspaceError("Test error message")
        assert "Test error message" in str(exc_info.value)


class TestCreateWorkspaceErrorHandling:
    """Test error handling in WorkspaceManager.create() method."""

    def test_create_with_nonexistent_prompt_path(self, workspace_manager, tmp_path):
        """Test create() handles nonexistent prompt path gracefully."""
        nonexistent = tmp_path / "nonexistent_prompt.md"
        workspace = workspace_manager.create(nonexistent, wfc_mode=False)
        assert workspace.exists()
        assert not (workspace / "input" / "prompt.md").exists()

    def test_create_with_permission_error_on_copy(
        self, workspace_manager, sample_prompt, monkeypatch
    ):
        """Test create() handles PermissionError during shutil.copy()."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        def mock_copy(*args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr(shutil, "copy", mock_copy)

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.create(sample_prompt, wfc_mode=False)
        assert "permission" in str(exc_info.value).lower()
        assert "check file permissions" in str(exc_info.value).lower()

    def test_create_with_oserror_on_copy(self, workspace_manager, sample_prompt, monkeypatch):
        """Test create() handles OSError during shutil.copy()."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        def mock_copy(*args, **kwargs):
            raise OSError("Disk full")

        monkeypatch.setattr(shutil, "copy", mock_copy)

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.create(sample_prompt, wfc_mode=False)
        assert "failed to copy" in str(exc_info.value).lower()


class TestWriteMetadataErrorHandling:
    """Test error handling in WorkspaceManager.write_metadata() method."""

    def test_write_metadata_with_permission_error(
        self, workspace_manager, sample_prompt, tmp_path, monkeypatch
    ):
        """Test write_metadata() handles PermissionError."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)

        def mock_open(*args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr("builtins.open", mock_open)

        from wfc.skills import wfc_prompt_fixer

        WorkspaceMetadata = wfc_prompt_fixer.workspace.WorkspaceMetadata

        metadata = WorkspaceMetadata(
            run_id="test", timestamp="20260220", prompt_path=str(sample_prompt), wfc_mode=False
        )

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.write_metadata(workspace, metadata)
        assert "permission" in str(exc_info.value).lower()

    def test_write_metadata_with_oserror(self, workspace_manager, sample_prompt, monkeypatch):
        """Test write_metadata() handles OSError."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)

        def mock_open(*args, **kwargs):
            raise OSError("Disk full")

        monkeypatch.setattr("builtins.open", mock_open)

        from wfc.skills import wfc_prompt_fixer

        WorkspaceMetadata = wfc_prompt_fixer.workspace.WorkspaceMetadata

        metadata = WorkspaceMetadata(
            run_id="test", timestamp="20260220", prompt_path=str(sample_prompt), wfc_mode=False
        )

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.write_metadata(workspace, metadata)
        assert "metadata" in str(exc_info.value).lower()


class TestReadMetadataErrorHandling:
    """Test error handling in WorkspaceManager.read_metadata() method."""

    def test_read_metadata_with_missing_file(self, workspace_manager, tmp_path):
        """Test read_metadata() handles FileNotFoundError."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        nonexistent_workspace = tmp_path / "nonexistent"
        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.read_metadata(nonexistent_workspace)
        assert "not found" in str(exc_info.value).lower()

    def test_read_metadata_with_invalid_json(self, workspace_manager, sample_prompt, tmp_path):
        """Test read_metadata() handles invalid JSON."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)
        (workspace / "metadata.json").write_text("invalid json {{{")

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.read_metadata(workspace)
        assert "invalid" in str(exc_info.value).lower() or "parse" in str(exc_info.value).lower()

    def test_read_metadata_with_permission_error(
        self, workspace_manager, sample_prompt, monkeypatch
    ):
        """Test read_metadata() handles PermissionError."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)

        def mock_open(*args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr("builtins.open", mock_open)

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.read_metadata(workspace)
        assert "permission" in str(exc_info.value).lower()


class TestWriteFixErrorHandling:
    """Test error handling in WorkspaceManager.write_fix() method."""

    def test_write_fix_with_permission_error(
        self, workspace_manager, sample_prompt, tmp_path, monkeypatch
    ):
        """Test write_fix() handles PermissionError on write_text()."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)

        original_write_text = Path.write_text

        def mock_write_text(self, *args, **kwargs):
            if "fixed_prompt.md" in str(self):
                raise PermissionError("Permission denied")
            return original_write_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", mock_write_text)

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.write_fix(
                workspace,
                fixed_prompt="Fixed content",
                changelog=["Change 1", "Change 2"],
                unresolved=["Issue 1"],
            )
        assert "permission" in str(exc_info.value).lower()

    def test_write_fix_with_oserror(self, workspace_manager, sample_prompt, monkeypatch):
        """Test write_fix() handles OSError on write_text()."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)

        original_write_text = Path.write_text

        def mock_write_text(self, *args, **kwargs):
            if "changelog.md" in str(self):
                raise OSError("Disk full")
            return original_write_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", mock_write_text)

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.write_fix(
                workspace,
                fixed_prompt="Fixed content",
                changelog=["Change 1"],
                unresolved=[],
            )
        assert "failed to write" in str(exc_info.value).lower()


class TestReadFixErrorHandling:
    """Test error handling in WorkspaceManager.read_fix() method."""

    def test_read_fix_with_missing_files(self, workspace_manager, tmp_path):
        """Test read_fix() handles FileNotFoundError for missing files."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = tmp_path / "test-workspace"
        workspace.mkdir()
        (workspace / "02-fixer").mkdir()

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.read_fix(workspace)
        assert "not found" in str(exc_info.value).lower()

    def test_read_fix_with_permission_error(self, workspace_manager, sample_prompt, monkeypatch):
        """Test read_fix() handles PermissionError on read_text()."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)
        workspace_manager.write_fix(workspace, fixed_prompt="test", changelog=["c1"], unresolved=[])

        original_read_text = Path.read_text

        def mock_read_text(self, *args, **kwargs):
            if "fixed_prompt.md" in str(self):
                raise PermissionError("Permission denied")
            return original_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", mock_read_text)

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.read_fix(workspace)
        assert "permission" in str(exc_info.value).lower()


class TestWriteReportErrorHandling:
    """Test error handling in WorkspaceManager.write_report() method."""

    def test_write_report_with_permission_error(
        self, workspace_manager, sample_prompt, monkeypatch
    ):
        """Test write_report() handles PermissionError."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)

        original_write_text = Path.write_text

        def mock_write_text(self, *args, **kwargs):
            if "report.md" in str(self):
                raise PermissionError("Permission denied")
            return original_write_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", mock_write_text)

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.write_report(workspace, "Test report")
        assert "permission" in str(exc_info.value).lower()

    def test_write_report_with_oserror(self, workspace_manager, sample_prompt, monkeypatch):
        """Test write_report() handles OSError."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)

        original_write_text = Path.write_text

        def mock_write_text(self, *args, **kwargs):
            if "report.md" in str(self):
                raise OSError("Disk full")
            return original_write_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", mock_write_text)

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.write_report(workspace, "Test report")
        assert "failed to write" in str(exc_info.value).lower()


class TestCleanupErrorHandling:
    """Test error handling in WorkspaceManager.cleanup() method."""

    def test_cleanup_with_nonexistent_workspace(self, workspace_manager, tmp_path):
        """Test cleanup() handles nonexistent workspace gracefully."""
        nonexistent = tmp_path / "nonexistent"
        workspace_manager.cleanup(nonexistent)

    def test_cleanup_uses_ignore_errors(self, workspace_manager, sample_prompt, monkeypatch):
        """Test cleanup() uses shutil.rmtree with ignore_errors=True."""
        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)

        rmtree_calls = []

        def mock_rmtree(path, ignore_errors=False):
            rmtree_calls.append({"path": path, "ignore_errors": ignore_errors})

        monkeypatch.setattr(shutil, "rmtree", mock_rmtree)

        workspace_manager.cleanup(workspace)

        assert len(rmtree_calls) == 1
        assert rmtree_calls[0]["ignore_errors"] is True

    def test_cleanup_with_permission_error_does_not_propagate(
        self, workspace_manager, sample_prompt, monkeypatch
    ):
        """Test cleanup() catches OSError and does not propagate exception."""
        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)

        def mock_rmtree(path, ignore_errors=False):
            if not ignore_errors:
                raise OSError("Permission denied")

        monkeypatch.setattr(shutil, "rmtree", mock_rmtree)

        workspace_manager.cleanup(workspace)


class TestWriteAnalysisErrorHandling:
    """Test error handling in WorkspaceManager.write_analysis() method."""

    def test_write_analysis_with_permission_error(
        self, workspace_manager, sample_prompt, monkeypatch
    ):
        """Test write_analysis() handles PermissionError."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)

        def mock_open(*args, **kwargs):
            if "analysis.json" in str(args[0]):
                raise PermissionError("Permission denied")
            return open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.write_analysis(workspace, {"grade": "A"})
        assert "permission" in str(exc_info.value).lower()

    def test_write_analysis_with_oserror(self, workspace_manager, sample_prompt, monkeypatch):
        """Test write_analysis() handles OSError."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)

        def mock_open(*args, **kwargs):
            if "analysis.json" in str(args[0]):
                raise OSError("Disk full")
            return open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.write_analysis(workspace, {"grade": "A"})
        assert "failed to write" in str(exc_info.value).lower()


class TestReadAnalysisErrorHandling:
    """Test error handling in WorkspaceManager.read_analysis() method."""

    def test_read_analysis_with_missing_file(self, workspace_manager, tmp_path):
        """Test read_analysis() handles FileNotFoundError."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = tmp_path / "test-workspace"
        workspace.mkdir()
        (workspace / "01-analyzer").mkdir()

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.read_analysis(workspace)
        assert "not found" in str(exc_info.value).lower()

    def test_read_analysis_with_invalid_json(self, workspace_manager, sample_prompt):
        """Test read_analysis() handles invalid JSON."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)
        (workspace / "01-analyzer" / "analysis.json").write_text("invalid {{{")

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.read_analysis(workspace)
        assert "invalid" in str(exc_info.value).lower() or "parse" in str(exc_info.value).lower()

    def test_read_analysis_with_permission_error(
        self, workspace_manager, sample_prompt, monkeypatch
    ):
        """Test read_analysis() handles PermissionError."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)
        workspace_manager.write_analysis(workspace, {"grade": "A"})

        def mock_open(*args, **kwargs):
            if "analysis.json" in str(args[0]):
                raise PermissionError("Permission denied")
            return open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.read_analysis(workspace)
        assert "permission" in str(exc_info.value).lower()


class TestActionableErrorMessages:
    """Test that error messages include actionable feedback."""

    def test_permission_error_includes_actionable_advice(
        self, workspace_manager, sample_prompt, monkeypatch
    ):
        """Test PermissionError messages include advice to check permissions."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)

        def mock_write_text(self, *args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr(Path, "write_text", mock_write_text)

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.write_report(workspace, "test")

        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in ["check", "permission", "access", "verify"])

    def test_file_not_found_includes_path_information(self, workspace_manager, tmp_path):
        """Test FileNotFoundError messages include path information."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.read_metadata(nonexistent)

        error_msg = str(exc_info.value).lower()
        assert "metadata" in error_msg or "not found" in error_msg

    def test_disk_full_error_includes_helpful_message(
        self, workspace_manager, sample_prompt, monkeypatch
    ):
        """Test OSError (disk full) messages are helpful."""
        from wfc.skills import wfc_prompt_fixer

        WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError

        workspace = workspace_manager.create(sample_prompt, wfc_mode=False)

        def mock_write_text(self, *args, **kwargs):
            raise OSError("No space left on device")

        monkeypatch.setattr(Path, "write_text", mock_write_text)

        with pytest.raises(WorkspaceError) as exc_info:
            workspace_manager.write_report(workspace, "test")

        error_msg = str(exc_info.value).lower()
        assert any(
            keyword in error_msg for keyword in ["failed", "write", "space", "disk", "error"]
        )
