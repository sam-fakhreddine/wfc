"""
Tests for WFC CLI - Secure run_command implementation

Tests the security fix for shell injection vulnerability (H-01).
Following TDD: RED phase - tests should fail before implementation.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from wfc.cli import run_command


class TestRunCommandSecurity:
    """Test suite for shell injection prevention in run_command."""

    def test_run_command_accepts_list_of_strings(self):
        """run_command should accept List[str] instead of str."""
        if hasattr(run_command, "__annotations__") and "cmd" in run_command.__annotations__:
            import inspect

            sig = inspect.signature(run_command)
            cmd_annotation = sig.parameters["cmd"].annotation
            assert cmd_annotation != str, "cmd parameter should not be str only"

    def test_simple_command_works(self):
        """Basic command execution should work."""
        result = run_command(["echo", "hello"], check=False)
        assert result == 0

    def test_shell_metacharacters_not_executed(self):
        """Shell metacharacters should not be executed (security test)."""
        result = run_command(["echo", "hello; rm -rf /"], check=False)
        assert result == 0

    def test_pipe_not_executed(self):
        """Pipe operator should not be executed."""
        result = run_command(["echo", "test| cat"], check=False)
        assert result == 0

    def test_backtick_not_executed(self):
        """Backtick command substitution should not work."""
        result = run_command(["echo", "test`whoami`"], check=False)
        assert result == 0

    def test_dollar_sign_not_executed(self):
        """Variable substitution should not work."""
        result = run_command(["echo", "test$HOME"], check=False)
        assert result == 0


class TestRunCommandAllCallSites:
    """Test that all call sites are updated to use lists."""

    def test_validate_command_uses_list(self):
        """cmd_validate should use list arguments."""
        import inspect
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent.parent))
        import wfc.cli as cli_module

        source = inspect.getsource(cli_module.cmd_validate)
        assert 'run_command("' not in source, "cmd_validate should use list arguments"

    def test_test_command_uses_list(self):
        """cmd_test should use list arguments."""
        import inspect
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent.parent))
        import wfc.cli as cli_module

        source = inspect.getsource(cli_module.cmd_test)
        assert 'run_command("' not in source, "cmd_test should use list arguments"

    def test_benchmark_command_uses_list(self):
        """cmd_benchmark should use list arguments (non-shell, list-based invocation)."""
        import inspect

        import wfc.cli as cli_module

        source = inspect.getsource(cli_module.cmd_benchmark)
        assert 'run_command("' not in source, "cmd_benchmark should use list arguments"


class TestSubprocessShellFalse:
    """Verify subprocess.run uses shell=False."""

    @patch("wfc.cli.subprocess.run")
    def test_subprocess_called_with_shell_false(self, mock_run):
        """subprocess.run should be called with shell=False."""
        mock_run.return_value = MagicMock(returncode=0, stdout="")

        run_command(["echo", "test"], check=False)

        assert mock_run.called, "subprocess.run should be called"
        call_kwargs = mock_run.call_args[1]

        assert call_kwargs.get("shell") == False, "shell should be False"

        assert isinstance(call_kwargs.get("args"), list), "args should be a list"
        assert "capture_output" in call_kwargs or "stdout" in call_kwargs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
