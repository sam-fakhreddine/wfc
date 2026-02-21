"""Tests for wfc-prompt-fixer CLI validation (PROP-003, PROP-010)."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock


def _load_cli_module():
    """Load the CLI module using importlib to handle hyphenated directory name."""
    cli_path = Path(__file__).parent.parent / "wfc" / "skills" / "wfc-prompt-fixer" / "cli.py"

    with open(cli_path) as f:
        cli_code = f.read()

    cli_code = cli_code.replace(
        "from .orchestrator import PromptFixerOrchestrator",
        "PromptFixerOrchestrator = lambda *args, **kwargs: type('MockOrchestrator', (), {})()",
    )

    cli_module = type(sys)("wfc_prompt_fixer_cli")
    exec(cli_code, cli_module.__dict__)

    return cli_module


CLI_MODULE = _load_cli_module()


class TestCLIValidation:
    """Test CLI input validation for TASK-007."""

    def test_empty_path_args_error(self, capsys):
        """Test that empty path_args raises clear error message (PROP-010)."""
        with patch.object(sys, "argv", ["wfc-prompt-fixer", "--wfc"]):
            exit_code = CLI_MODULE.main()
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "No path provided" in captured.out

    def test_mutually_exclusive_wfc_flags_error(self, capsys):
        """Test that --wfc and --no-wfc are mutually exclusive (PROP-010)."""
        with patch.object(sys, "argv", ["wfc-prompt-fixer", "--wfc", "--no-wfc", "PROMPT.md"]):
            exit_code = CLI_MODULE.main()
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "mutually exclusive" in captured.out.lower()

    def test_invalid_path_resolve_error(self, capsys):
        """Test that invalid paths are caught with try/except (PROP-010)."""
        invalid_path = "\0invalid\0path"
        with patch.object(sys, "argv", ["wfc-prompt-fixer", invalid_path]):
            exit_code = CLI_MODULE.main()
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "invalid" in captured.out.lower() or "error" in captured.out.lower()

    def test_nonexistent_file_error_nonbatch_mode(self, capsys):
        """Test that nonexistent files are rejected in non-batch mode (PROP-010)."""
        with patch.object(sys, "argv", ["wfc-prompt-fixer", "/nonexistent/path/PROMPT.md"]):
            exit_code = CLI_MODULE.main()
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "does not exist" in captured.out.lower()

    def test_path_too_long_error(self, capsys):
        """Test that excessively long paths are rejected (PROP-003)."""
        long_path = "a" * 5000 + ".md"
        with patch.object(sys, "argv", ["wfc-prompt-fixer", long_path]):
            exit_code = CLI_MODULE.main()
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "exceeds maximum length" in captured.out

    def test_empty_string_path_error(self, capsys):
        """Test that empty string path is rejected (PROP-003)."""
        with patch.object(sys, "argv", ["wfc-prompt-fixer", "   "]):
            exit_code = CLI_MODULE.main()
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "empty" in captured.out.lower()

    def test_valid_file_passes_validation(self, tmp_path):
        """Test that valid single file path passes validation."""
        test_file = tmp_path / "PROMPT.md"
        test_file.write_text("# Test Prompt\n\nContent here.")

        mock_orch_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.grade_before = "C"
        mock_result.grade_after = "A"
        mock_result.report_path = "/tmp/report.md"
        mock_orch_instance.fix_prompt.return_value = mock_result

        with patch.object(CLI_MODULE, "PromptFixerOrchestrator", return_value=mock_orch_instance):
            with patch.object(sys, "argv", ["wfc-prompt-fixer", str(test_file)]):
                exit_code = CLI_MODULE.main()
                assert exit_code == 0

    def test_batch_mode_skips_file_existence_check(self):
        """Test that batch mode doesn't check file existence (PROP-010)."""
        mock_orch_instance = MagicMock()
        mock_orch_instance.fix_batch.return_value = []

        with patch.object(CLI_MODULE, "PromptFixerOrchestrator", return_value=mock_orch_instance):
            with patch.object(
                sys, "argv", ["wfc-prompt-fixer", "--batch", "wfc/skills/*/PROMPT.md"]
            ):
                exit_code = CLI_MODULE.main()
                assert exit_code == 0

    def test_wfc_flag_alone_accepted(self, tmp_path):
        """Test that --wfc flag alone is accepted."""
        test_file = tmp_path / "PROMPT.md"
        test_file.write_text("# Test")

        mock_orch_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.grade_before = "C"
        mock_result.grade_after = "A"
        mock_result.report_path = "/tmp/report.md"
        mock_orch_instance.fix_prompt.return_value = mock_result

        with patch.object(CLI_MODULE, "PromptFixerOrchestrator", return_value=mock_orch_instance):
            with patch.object(sys, "argv", ["wfc-prompt-fixer", "--wfc", str(test_file)]):
                exit_code = CLI_MODULE.main()
                assert exit_code == 0

    def test_no_wfc_flag_alone_accepted(self, tmp_path):
        """Test that --no-wfc flag alone is accepted."""
        test_file = tmp_path / "PROMPT.md"
        test_file.write_text("# Test")

        mock_orch_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.grade_before = "C"
        mock_result.grade_after = "A"
        mock_result.report_path = "/tmp/report.md"
        mock_orch_instance.fix_prompt.return_value = mock_result

        with patch.object(CLI_MODULE, "PromptFixerOrchestrator", return_value=mock_orch_instance):
            with patch.object(sys, "argv", ["wfc-prompt-fixer", "--no-wfc", str(test_file)]):
                exit_code = CLI_MODULE.main()
                assert exit_code == 0

    def test_help_flag_returns_success(self, capsys):
        """Test that --help returns 0 and shows usage."""
        with patch.object(sys, "argv", ["wfc-prompt-fixer", "--help"]):
            exit_code = CLI_MODULE.main()
            assert exit_code == 0
            captured = capsys.readouterr()
            assert "Usage:" in captured.out
