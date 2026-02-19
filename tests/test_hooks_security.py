"""Tests for Git Hooks Security (H-04) - Path Traversal Prevention & Whitelist Validation.

Tests the VALID_HOOKS whitelist and path traversal checks in hooks.py.
The install() function hardcodes Path(".git/hooks"), so we monkeypatch for
the success case and test validation logic directly for rejection cases.

"""

import importlib.util
from pathlib import Path

import pytest

_hooks_path = Path(__file__).parent.parent / "wfc" / "gitwork" / "api" / "hooks.py"
_spec = importlib.util.spec_from_file_location("hooks", _hooks_path)
hooks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hooks)

install = hooks.install
is_hook_type_valid = hooks.is_hook_type_valid
has_path_traversal = hooks.has_path_traversal
VALID_HOOKS = hooks.VALID_HOOKS
wrap = hooks.wrap
manage = hooks.manage


class TestHookTypeValidation:
    """Test hook type whitelist validation functions."""

    def test_valid_hook_types(self):
        """All standard git hook types should be valid."""
        expected_valid = {
            "pre-commit",
            "prepare-commit-msg",
            "commit-msg",
            "post-commit",
            "pre-rebase",
            "post-rebase",
            "pre-push",
            "post-push",
            "pre-merge",
            "post-merge",
            "pre-checkout",
            "post-checkout",
            "pre-auto-gc",
            "post-auto-gc",
        }
        assert VALID_HOOKS == expected_valid

    def test_is_hook_type_valid_accepts_valid(self):
        """is_hook_type_valid returns True for valid hook types."""
        assert is_hook_type_valid("pre-commit") is True
        assert is_hook_type_valid("post-merge") is True
        assert is_hook_type_valid("pre-push") is True

    def test_is_hook_type_valid_rejects_invalid(self):
        """is_hook_type_valid returns False for unknown types."""
        assert is_hook_type_valid("malicious") is False
        assert is_hook_type_valid("pre-hack") is False
        assert is_hook_type_valid("") is False

    def test_has_path_traversal_detects_dotdot(self):
        """has_path_traversal catches '..' sequences."""
        assert has_path_traversal("../etc/passwd") is True
        assert has_path_traversal("hook/../etc") is True

    def test_has_path_traversal_detects_slash(self):
        """has_path_traversal catches '/' characters."""
        assert has_path_traversal("etc/passwd") is True
        assert has_path_traversal("/tmp/evil") is True

    def test_has_path_traversal_clean_names(self):
        """has_path_traversal returns False for clean hook names."""
        assert has_path_traversal("pre-commit") is False
        assert has_path_traversal("post-merge") is False


class TestInstallValidation:
    """Test install() validation — rejection cases don't touch the filesystem."""

    def test_install_invalid_hook_type_fails(self):
        """Invalid hook types should fail with descriptive error."""
        result = install("malicious", "#!/bin/bash\necho 'hack'")
        assert result["success"] is False
        assert "Invalid hook type" in result["message"]
        assert "malicious" in result["message"]

    def test_install_path_traversal_rejected(self):
        """Path traversal attempts should be rejected by whitelist."""
        result = install("../etc/passwd", "#!/bin/bash\necho 'traversal'")
        assert result["success"] is False
        assert "Invalid hook type" in result["message"]

    def test_install_empty_hook_type_fails(self):
        """Empty string hook type should be rejected."""
        result = install("", "#!/bin/bash\necho 'empty'")
        assert result["success"] is False

    def test_install_valid_hook_succeeds(self, tmp_path, monkeypatch):
        """Valid hook type should install when filesystem is available."""
        git_hooks = tmp_path / ".git" / "hooks"
        git_hooks.mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

        result = install("pre-commit", "#!/bin/bash\necho 'test'")
        assert result["success"] is True
        assert result["message"] == "Installed pre-commit hook"

        hook_file = git_hooks / "pre-commit"
        assert hook_file.exists()
        assert "echo 'test'" in hook_file.read_text()


class TestWrapValidation:
    """Test wrap() function behavior."""

    def test_wrap_rejects_invalid_hook_type(self):
        """wrap() should reject invalid hook types just like install()."""
        result = wrap("malicious", "echo 'hack'")
        assert result["success"] is False
        assert "Invalid hook type" in result["message"]

    def test_wrap_rejects_path_traversal(self):
        """wrap() should reject path traversal attempts."""
        result = wrap("../etc/passwd", "echo 'traversal'")
        assert result["success"] is False
        assert "Invalid hook type" in result["message"]

    def test_wrap_creates_combined_hook(self, tmp_path, monkeypatch):
        """wrap() should combine new script with existing hook."""
        git_hooks = tmp_path / ".git" / "hooks"
        git_hooks.mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

        result = wrap("pre-commit", "echo 'new'")
        assert result["success"] is True
        assert "Wrapped" in result["message"]

    def test_wrap_preserves_existing(self, tmp_path, monkeypatch):
        """wrap() should preserve existing hook content."""
        git_hooks = tmp_path / ".git" / "hooks"
        git_hooks.mkdir(parents=True)

        existing_hook = git_hooks / "pre-commit"
        existing_hook.write_text("#!/bin/bash\necho 'original'")

        monkeypatch.chdir(tmp_path)
        wrap("pre-commit", "echo 'new'")

        content = existing_hook.read_text()
        assert "echo 'new'" in content
        assert "echo 'original'" in content


class TestManage:
    """Test manage() function."""

    def test_manage_returns_list(self, tmp_path, monkeypatch):
        """manage() should return a list of hook dicts."""
        git_hooks = tmp_path / ".git" / "hooks"
        git_hooks.mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

        result = manage()
        assert isinstance(result, list)

    def test_manage_no_hooks_dir(self, tmp_path, monkeypatch):
        """manage() should return empty list if .git/hooks doesn't exist."""
        monkeypatch.chdir(tmp_path)
        result = manage()
        assert result == []

    def test_manage_lists_installed_hooks(self, tmp_path, monkeypatch):
        """manage() should list hooks that are installed."""
        git_hooks = tmp_path / ".git" / "hooks"
        git_hooks.mkdir(parents=True)

        hook = git_hooks / "pre-commit"
        hook.write_text("#!/bin/bash\necho 'test'")
        hook.chmod(0o755)

        monkeypatch.chdir(tmp_path)
        result = manage()
        assert len(result) == 1
        assert result[0]["name"] == "pre-commit"
        assert result[0]["enabled"] is True

    def test_manage_ignores_sample_files(self, tmp_path, monkeypatch):
        """manage() should ignore .sample hook files."""
        git_hooks = tmp_path / ".git" / "hooks"
        git_hooks.mkdir(parents=True)

        sample = git_hooks / "pre-commit.sample"
        sample.write_text("#!/bin/bash\necho 'sample'")

        monkeypatch.chdir(tmp_path)
        result = manage()
        assert len(result) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
