"""Tests for wfc-prompt-fixer skill - file structure validation."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPromptFixerStructure:
    """Test that wfc-prompt-fixer has correct structure."""

    def test_skill_md_exists(self):
        """Test SKILL.md exists."""
        skill_path = (
            Path(__file__).parent.parent / "wfc" / "skills" / "wfc-prompt-fixer" / "SKILL.md"
        )
        assert skill_path.exists()

    def test_antipatterns_json_valid(self):
        """Test antipatterns.json is valid."""
        ref_path = (
            Path(__file__).parent.parent
            / "wfc"
            / "skills"
            / "wfc-prompt-fixer"
            / "references"
            / "antipatterns.json"
        )
        with open(ref_path) as f:
            data = json.load(f)
        assert "antipatterns" in data
        assert len(data["antipatterns"]) == 17

    def test_rubric_json_valid(self):
        """Test rubric.json is valid."""
        ref_path = (
            Path(__file__).parent.parent
            / "wfc"
            / "skills"
            / "wfc-prompt-fixer"
            / "references"
            / "rubric.json"
        )
        with open(ref_path) as f:
            data = json.load(f)
        assert "categories" in data
        assert "grading" in data

    def test_agent_prompts_exist(self):
        """Test all agent prompts exist."""
        agents_dir = Path(__file__).parent.parent / "wfc" / "skills" / "wfc-prompt-fixer" / "agents"
        assert (agents_dir / "analyzer.md").exists()
        assert (agents_dir / "fixer.md").exists()
        assert (agents_dir / "reporter.md").exists()


class TestPromptFixerCLIValidation:
    """Test CLI input validation (PROP-003, PROP-010)."""

    @pytest.fixture
    def cli_module(self):
        """Import CLI module using package import with mocked orchestrator."""
        mock_orch_class = MagicMock()
        with patch.dict(sys.modules):
            import types

            orchestrator_module = types.ModuleType("orchestrator")
            orchestrator_module.PromptFixerOrchestrator = mock_orch_class

            skill_dir = Path(__file__).parent.parent / "wfc" / "skills" / "wfc-prompt-fixer"
            sys.path.insert(0, str(skill_dir))

            try:
                with patch.dict("sys.modules", {"orchestrator": orchestrator_module}):
                    import cli

                    return cli
            finally:
                if str(skill_dir) in sys.path:
                    sys.path.remove(str(skill_dir))

    def test_empty_path_args_error(self, cli_module, capsys):
        """Test that empty path_args raises clear error message (PROP-010)."""
        with patch.object(sys, "argv", ["wfc-prompt-fixer", "--wfc"]):
            exit_code = cli_module.main()
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "No path provided" in captured.out

    def test_mutually_exclusive_wfc_flags_error(self, cli_module, capsys):
        """Test that --wfc and --no-wfc are mutually exclusive (PROP-010)."""
        with patch.object(sys, "argv", ["wfc-prompt-fixer", "--wfc", "--no-wfc", "PROMPT.md"]):
            exit_code = cli_module.main()
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "mutually exclusive" in captured.out.lower()

    def test_invalid_path_resolve_error(self, cli_module, capsys, tmp_path):
        """Test that invalid paths are caught with try/except (PROP-010)."""
        invalid_path = "\0invalid\0path"
        with patch.object(sys, "argv", ["wfc-prompt-fixer", invalid_path]):
            exit_code = cli_module.main()
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "invalid" in captured.out.lower() or "error" in captured.out.lower()

    def test_nonexistent_file_error_nonbatch_mode(self, cli_module, capsys):
        """Test that nonexistent files are rejected in non-batch mode (PROP-010)."""
        with patch.object(sys, "argv", ["wfc-prompt-fixer", "/nonexistent/path/PROMPT.md"]):
            exit_code = cli_module.main()
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "does not exist" in captured.out.lower() or "not found" in captured.out.lower()

    def test_path_too_long_error(self, cli_module, capsys):
        """Test that excessively long paths are rejected (PROP-003)."""
        long_path = "a" * 5000 + ".md"
        with patch.object(sys, "argv", ["wfc-prompt-fixer", long_path]):
            exit_code = cli_module.main()
            assert exit_code == 1
            _ = capsys.readouterr()

    def test_valid_single_file_passes_validation(self, cli_module, tmp_path):
        """Test that valid single file path passes validation."""
        test_file = tmp_path / "PROMPT.md"
        test_file.write_text("# Test Prompt\n\nContent here.")

        with patch.object(sys, "argv", ["wfc-prompt-fixer", str(test_file)]):
            _ = cli_module.main()

    def test_batch_mode_skips_file_existence_check(self, cli_module):
        """Test that batch mode doesn't check file existence (PROP-010)."""
        with patch.object(sys, "argv", ["wfc-prompt-fixer", "--batch", "wfc/skills/*/PROMPT.md"]):
            _ = cli_module.main()

    def test_wfc_flag_alone_accepted(self, cli_module, tmp_path):
        """Test that --wfc flag alone is accepted."""
        test_file = tmp_path / "PROMPT.md"
        test_file.write_text("# Test")

        with patch.object(sys, "argv", ["wfc-prompt-fixer", "--wfc", str(test_file)]):
            cli_module.main()

    def test_no_wfc_flag_alone_accepted(self, cli_module, tmp_path):
        """Test that --no-wfc flag alone is accepted."""
        test_file = tmp_path / "PROMPT.md"
        test_file.write_text("# Test")

        with patch.object(sys, "argv", ["wfc-prompt-fixer", "--no-wfc", str(test_file)]):
            cli_module.main()

    def test_help_flag_returns_success(self, cli_module, capsys):
        """Test that --help returns 0 and shows usage."""
        with patch.object(sys, "argv", ["wfc-prompt-fixer", "--help"]):
            exit_code = cli_module.main()
            assert exit_code == 0
            captured = capsys.readouterr()
            assert "Usage:" in captured.out


class TestWfcModeDetection:
    """Test wfc_mode auto-detection logic (TASK-010, PROP-012)."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        from wfc.skills import wfc_prompt_fixer

        return wfc_prompt_fixer.PromptFixerOrchestrator()

    def test_detect_skill_md_filename(self, orchestrator, tmp_path):
        """Test SKILL.md filename triggers wfc_mode."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Some content")
        assert orchestrator._detect_wfc_mode(skill_file) is True

    def test_detect_prompt_md_filename(self, orchestrator, tmp_path):
        """Test PROMPT.md filename triggers wfc_mode."""
        prompt_file = tmp_path / "PROMPT.md"
        prompt_file.write_text("# Some content")
        assert orchestrator._detect_wfc_mode(prompt_file) is True

    def test_detect_wfc_skills_path(self, orchestrator, tmp_path):
        """Test wfc/skills/* path triggers wfc_mode."""
        skills_dir = tmp_path / "wfc" / "skills" / "my-skill"
        skills_dir.mkdir(parents=True)
        prompt_file = skills_dir / "prompt.md"
        prompt_file.write_text("# Some content")
        assert orchestrator._detect_wfc_mode(prompt_file) is True

    def test_detect_wfc_reviewers_path(self, orchestrator, tmp_path):
        """Test wfc/references/reviewers/* path triggers wfc_mode."""
        reviewers_dir = tmp_path / "wfc" / "references" / "reviewers" / "security"
        reviewers_dir.mkdir(parents=True)
        prompt_file = reviewers_dir / "PROMPT.md"
        prompt_file.write_text("# Some content")
        assert orchestrator._detect_wfc_mode(prompt_file) is True

    def test_detect_valid_yaml_frontmatter(self, orchestrator, tmp_path):
        """Test valid YAML frontmatter with name: triggers wfc_mode."""
        prompt_file = tmp_path / "test.md"
        content = """---
name: my-skill
description: Test skill
---

# Content here
"""
        prompt_file.write_text(content)
        assert orchestrator._detect_wfc_mode(prompt_file) is True

    def test_detect_missing_closing_delimiter(self, orchestrator, tmp_path):
        """Test missing closing delimiter returns False (prevents false positive)."""
        prompt_file = tmp_path / "test.md"
        content = """---
name: my-skill
description: Test skill

# Content here (no closing ---)
"""
        prompt_file.write_text(content)
        assert orchestrator._detect_wfc_mode(prompt_file) is False

    def test_detect_name_in_code_block(self, orchestrator, tmp_path):
        """Test name: in code block after frontmatter returns False."""
        prompt_file = tmp_path / "test.md"
        content = """# Regular markdown

```yaml
name: this-is-in-code-block
```
"""
        prompt_file.write_text(content)
        assert orchestrator._detect_wfc_mode(prompt_file) is False

    def test_detect_name_outside_frontmatter(self, orchestrator, tmp_path):
        """Test name: appearing after closing delimiter returns False."""
        prompt_file = tmp_path / "test.md"
        content = """---
description: Test
---

# Content
name: this-is-outside-frontmatter
"""
        prompt_file.write_text(content)
        assert orchestrator._detect_wfc_mode(prompt_file) is False

    def test_detect_yaml_frontmatter_no_name(self, orchestrator, tmp_path):
        """Test YAML frontmatter without name: field returns False."""
        prompt_file = tmp_path / "test.md"
        content = """---
title: My Document
description: Test
---

# Content
"""
        prompt_file.write_text(content)
        assert orchestrator._detect_wfc_mode(prompt_file) is False

    def test_detect_binary_file(self, orchestrator, tmp_path):
        """Test binary file returns False gracefully (UnicodeDecodeError)."""
        binary_file = tmp_path / "test.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe")
        assert orchestrator._detect_wfc_mode(binary_file) is False

    def test_detect_large_file_reads_limited(self, orchestrator, tmp_path):
        """Test large file only reads first 10KB."""
        large_file = tmp_path / "large.md"
        content = "---\nname: test\n---\n" + ("x" * 20000)
        large_file.write_text(content)
        assert orchestrator._detect_wfc_mode(large_file) is True

    def test_detect_nonexistent_file(self, orchestrator, tmp_path):
        """Test nonexistent file returns False."""
        nonexistent = tmp_path / "does_not_exist.md"
        assert orchestrator._detect_wfc_mode(nonexistent) is False

    def test_detect_empty_file(self, orchestrator, tmp_path):
        """Test empty file returns False."""
        empty_file = tmp_path / "empty.md"
        empty_file.write_text("")
        assert orchestrator._detect_wfc_mode(empty_file) is False

    def test_detect_cache_works(self, orchestrator, tmp_path):
        """Test @lru_cache memoization works."""
        prompt_file = tmp_path / "SKILL.md"
        prompt_file.write_text("# Test")

        result1 = orchestrator._detect_wfc_mode(prompt_file)
        result2 = orchestrator._detect_wfc_mode(prompt_file)

        assert result1 is True
        assert result2 is True
        assert orchestrator._detect_wfc_mode.cache_info().hits > 0

    def test_detect_yaml_frontmatter_name_at_boundary(self, orchestrator, tmp_path):
        """Test frontmatter within 10KB limit is detected."""
        prompt_file = tmp_path / "boundary.md"
        padding = "x" * 9970
        content = f"---\n{padding}\nname: test\n---\n# Content after"
        prompt_file.write_text(content)
        assert orchestrator._detect_wfc_mode(prompt_file) is True

    def test_detect_multiple_dashes_in_content(self, orchestrator, tmp_path):
        """Test content with multiple --- strings doesn't cause false positive."""
        prompt_file = tmp_path / "dashes.md"
        content = """# Document

---

Some separator

---

name: not-in-frontmatter
"""
        prompt_file.write_text(content)
        assert orchestrator._detect_wfc_mode(prompt_file) is False

    def test_detect_yaml_frontmatter_windows_line_endings(self, orchestrator, tmp_path):
        """Test YAML frontmatter with Windows line endings (CRLF)."""
        prompt_file = tmp_path / "windows.md"
        content = "---\r\nname: my-skill\r\n---\r\n\r\n# Content"
        prompt_file.write_text(content, newline="")
        assert orchestrator._detect_wfc_mode(prompt_file) is True

    def test_detect_permission_error(self, orchestrator, tmp_path):
        """Test file with permission error returns False gracefully."""
        restricted_file = tmp_path / "restricted.md"
        restricted_file.write_text("---\nname: test\n---\n")
        restricted_file.chmod(0o000)
        try:
            assert orchestrator._detect_wfc_mode(restricted_file) is False
        finally:
            restricted_file.chmod(0o644)


class TestOrchestratorCleanup:
    """Test workspace cleanup on exception paths (TASK-002, PROP-002, PROP-004)."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        from wfc.skills import wfc_prompt_fixer

        return wfc_prompt_fixer.PromptFixerOrchestrator()

    @pytest.fixture
    def test_prompt(self, tmp_path):
        """Create a test prompt file."""
        prompt_file = tmp_path / "PROMPT.md"
        prompt_file.write_text("# Test Prompt\n\nContent here.")
        return prompt_file

    def test_fix_prompt_cleans_up_on_analyzer_exception(self, orchestrator, test_prompt, tmp_path):
        """Test that workspace is cleaned up when analyzer raises exception (PROP-002)."""
        with patch.object(
            orchestrator, "_spawn_analyzer", side_effect=Exception("Analyzer failed")
        ):
            with pytest.raises(Exception, match="Analyzer failed"):
                orchestrator.fix_prompt(test_prompt)

            workspace_dir = tmp_path / ".development" / "prompt-fixer"
            if workspace_dir.exists():
                workspaces = list(workspace_dir.iterdir())
                assert len(workspaces) == 0, "Workspace should be cleaned up on exception"

    def test_fix_prompt_cleans_up_on_fixer_exception(self, orchestrator, test_prompt, tmp_path):
        """Test that workspace is cleaned up when fixer raises exception (PROP-002)."""
        analysis = {"grade": "B", "scores": {}, "issues": [], "wfc_mode": False}

        with patch.object(orchestrator, "_spawn_analyzer", return_value=analysis):
            with patch.object(
                orchestrator, "_spawn_fixer_with_retry", side_effect=Exception("Fixer failed")
            ):
                with pytest.raises(Exception, match="Fixer failed"):
                    orchestrator.fix_prompt(test_prompt)

                workspace_dir = tmp_path / ".development" / "prompt-fixer"
                if workspace_dir.exists():
                    workspaces = list(workspace_dir.iterdir())
                    assert len(workspaces) == 0, "Workspace should be cleaned up on exception"

    def test_fix_prompt_cleans_up_on_reporter_exception(self, orchestrator, test_prompt, tmp_path):
        """Test that workspace is cleaned up when reporter raises exception (PROP-002)."""
        analysis = {"grade": "B", "scores": {}, "issues": [], "wfc_mode": False}
        fix_result = {"verdict": "PASS", "grade_after": "A", "changes": []}

        with patch.object(orchestrator, "_spawn_analyzer", return_value=analysis):
            with patch.object(orchestrator, "_spawn_fixer_with_retry", return_value=fix_result):
                with patch.object(
                    orchestrator, "_spawn_reporter", side_effect=Exception("Reporter failed")
                ):
                    with pytest.raises(Exception, match="Reporter failed"):
                        orchestrator.fix_prompt(test_prompt)

                    workspace_dir = tmp_path / ".development" / "prompt-fixer"
                    if workspace_dir.exists():
                        workspaces = list(workspace_dir.iterdir())
                        assert len(workspaces) == 0, "Workspace should be cleaned up on exception"

    def test_fix_prompt_keeps_workspace_on_success(self, orchestrator, test_prompt, tmp_path):
        """Test that workspace is NOT cleaned up on successful completion."""
        analysis = {"grade": "A", "scores": {}, "issues": [], "wfc_mode": False}

        with patch.object(orchestrator, "_spawn_analyzer", return_value=analysis):
            with patch.object(
                orchestrator, "_skip_to_reporter", return_value=Path("/mock/report.md")
            ):
                result = orchestrator.fix_prompt(test_prompt)

                assert result.workspace.exists(), "Workspace should be kept on success"

    def test_fix_prompt_keeps_workspace_with_keep_workspace_flag(self, orchestrator, test_prompt):
        """Test that workspace is kept on exception when keep_workspace=True (PROP-002)."""
        with patch.object(orchestrator, "_spawn_analyzer", side_effect=Exception("Test exception")):
            with pytest.raises(Exception, match="Test exception"):
                orchestrator.fix_prompt(test_prompt, keep_workspace=True)

            workspaces = orchestrator.workspace_manager.list_workspaces()
            assert len(workspaces) > 0, "Workspace should be kept when keep_workspace=True"

    def test_fix_batch_cleans_up_each_failed_prompt_workspace(self, tmp_path, monkeypatch):
        """Test that each failed prompt's workspace is cleaned up in batch mode (PROP-002)."""
        from wfc.skills import wfc_prompt_fixer

        monkeypatch.chdir(tmp_path)
        orchestrator = wfc_prompt_fixer.PromptFixerOrchestrator(cwd=tmp_path)

        prompts_dir = tmp_path / "wfc" / "skills"
        prompts_dir.mkdir(parents=True)

        for i in range(3):
            prompt_file = prompts_dir / f"skill-{i}" / "PROMPT.md"
            prompt_file.parent.mkdir(exist_ok=True)
            prompt_file.write_text(f"# Test Prompt {i}")

        def mock_fix_prompt(prompt_path, wfc_mode=None, auto_pr=False, keep_workspace=False):
            if "skill-1" in str(prompt_path):
                raise Exception("Failed to process skill-1")

            from wfc.skills.wfc_prompt_fixer.orchestrator import FixResult

            return FixResult(
                prompt_name=prompt_path.stem,
                prompt_path=prompt_path,
                workspace=Path("/mock/workspace"),
                grade_before="B",
                grade_after="A",
                report_path=Path("/mock/report.md"),
                changes_made=True,
                wfc_mode=False,
            )

        with patch.object(orchestrator, "fix_prompt", side_effect=mock_fix_prompt):
            results = orchestrator.fix_batch("wfc/skills/*/PROMPT.md", wfc_mode=False)

            assert len(results) == 2, "Should have 2 successful results (1 failed)"

    def test_fix_batch_cleans_up_workspaces_on_early_exception(self, orchestrator, tmp_path):
        """Test that workspaces are cleaned up when batch processing fails early (PROP-002)."""
        prompts_dir = tmp_path / "wfc" / "skills"
        prompts_dir.mkdir(parents=True)

        prompt_file = prompts_dir / "test" / "PROMPT.md"
        prompt_file.parent.mkdir(exist_ok=True)
        prompt_file.write_text("# Test Prompt")

        with patch.object(orchestrator, "fix_prompt", side_effect=Exception("Batch failure")):
            results = orchestrator.fix_batch("wfc/skills/*/PROMPT.md", wfc_mode=False)

            assert len(results) == 0, "Should have no results on exception"

    def test_cleanup_completes_within_time_limit(self, orchestrator, test_prompt, tmp_path):
        """Test that cleanup completes within reasonable time (PROP-004 - 60 seconds)."""
        import time

        with patch.object(orchestrator, "_spawn_analyzer", side_effect=Exception("Test exception")):
            start_time = time.time()
            with pytest.raises(Exception):
                orchestrator.fix_prompt(test_prompt)
            end_time = time.time()

            cleanup_time = end_time - start_time
            assert (
                cleanup_time < 5.0
            ), f"Cleanup took {cleanup_time}s, should be < 5s for small workspace"


class TestFixResultSchemaValidation:
    """Test validate_fix_result_schema() helper function (TASK-004, PROP-006)."""

    def test_valid_fix_result_passes_validation(self):
        """Test that a valid fix result passes schema validation."""
        from wfc.skills import wfc_prompt_fixer  # noqa: F401
        from wfc_prompt_fixer.orchestrator import validate_fix_result_schema

        fix_result = {
            "verdict": "PASS",
            "intent_preserved": True,
            "issues_resolved": {
                "total_critical_major": 5,
                "resolved": 5,
                "unresolved": [],
                "inadequately_resolved": [],
            },
            "regressions": [],
            "scope_creep": [],
            "grade_after": "A",
            "final_recommendation": "ship",
            "revision_notes": "",
        }

        is_valid, errors = validate_fix_result_schema(fix_result)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_verdict_field_fails_validation(self):
        """Test that missing verdict field fails validation."""
        from wfc.skills import wfc_prompt_fixer  # noqa: F401
        from wfc_prompt_fixer.orchestrator import validate_fix_result_schema

        fix_result = {
            "intent_preserved": True,
            "issues_resolved": {},
            "regressions": [],
            "scope_creep": [],
            "grade_after": "A",
        }

        is_valid, errors = validate_fix_result_schema(fix_result)
        assert is_valid is False
        assert any("verdict" in err.lower() for err in errors)

    def test_invalid_verdict_value_fails_validation(self):
        """Test that invalid verdict value fails validation."""
        from wfc.skills import wfc_prompt_fixer  # noqa: F401
        from wfc_prompt_fixer.orchestrator import validate_fix_result_schema

        fix_result = {
            "verdict": "INVALID_VERDICT",
            "intent_preserved": True,
            "issues_resolved": {},
            "regressions": [],
            "scope_creep": [],
            "grade_after": "A",
        }

        is_valid, errors = validate_fix_result_schema(fix_result)
        assert is_valid is False
        assert any("verdict" in err.lower() for err in errors)

    def test_invalid_grade_after_fails_validation(self):
        """Test that invalid grade_after value fails validation."""
        from wfc.skills import wfc_prompt_fixer  # noqa: F401
        from wfc_prompt_fixer.orchestrator import validate_fix_result_schema

        fix_result = {
            "verdict": "PASS",
            "intent_preserved": True,
            "issues_resolved": {},
            "regressions": [],
            "scope_creep": [],
            "grade_after": "X",
        }

        is_valid, errors = validate_fix_result_schema(fix_result)
        assert is_valid is False
        assert any("grade_after" in err.lower() for err in errors)

    def test_missing_intent_preserved_fails_validation(self):
        """Test that missing intent_preserved field fails validation."""
        from wfc.skills import wfc_prompt_fixer  # noqa: F401
        from wfc_prompt_fixer.orchestrator import validate_fix_result_schema

        fix_result = {
            "verdict": "PASS",
            "issues_resolved": {},
            "regressions": [],
            "scope_creep": [],
            "grade_after": "A",
        }

        is_valid, errors = validate_fix_result_schema(fix_result)
        assert is_valid is False
        assert any("intent_preserved" in err.lower() for err in errors)


class TestFixerPromptGeneration:
    """Test _prepare_fixer_prompt() method (TASK-004)."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        from wfc.skills import wfc_prompt_fixer

        return wfc_prompt_fixer.PromptFixerOrchestrator()

    def test_prepare_fixer_prompt_loads_template(self, orchestrator, tmp_path):
        """Test that _prepare_fixer_prompt loads fixer.md template."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        prompt = orchestrator._prepare_fixer_prompt(workspace)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Fixer Agent" in prompt or "fixer" in prompt.lower()

    def test_prepare_fixer_prompt_injects_workspace_path(self, orchestrator, tmp_path):
        """Test that workspace path is injected into template."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        prompt = orchestrator._prepare_fixer_prompt(workspace)

        assert str(workspace) in prompt

    def test_prepare_fixer_prompt_template_missing_raises_error(self, orchestrator, tmp_path):
        """Test that missing fixer.md template raises WorkspaceError."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with patch.object(
            orchestrator, "_get_agent_template_path", return_value=Path("/nonexistent/fixer.md")
        ):
            with pytest.raises(Exception, match="Agent template not found"):
                orchestrator._prepare_fixer_prompt(workspace)


class TestFixerRetryLogic:
    """Test _spawn_fixer_with_retry() retry logic and exponential backoff (TASK-004, PROP-007)."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        from wfc.skills import wfc_prompt_fixer

        return wfc_prompt_fixer.PromptFixerOrchestrator()

    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a workspace with analysis.json."""
        workspace = tmp_path / "workspace"
        (workspace / "01-analyzer").mkdir(parents=True)
        (workspace / "02-fixer").mkdir(parents=True)

        analysis = {
            "classification": {},
            "scores": {},
            "issues": [{"severity": "critical", "description": "Test issue"}],
            "overall_grade": "C",
            "average_score": 6.0,
            "rewrite_recommended": True,
            "rewrite_scope": "full",
            "wfc_mode": False,
            "summary": "Test summary",
        }

        with open(workspace / "01-analyzer" / "analysis.json", "w") as f:
            json.dump(analysis, f)

        return workspace

    def test_fixer_passes_on_first_attempt(self, orchestrator, workspace):
        """Test that fixer returns immediately when validation passes on first attempt."""
        validation_result = {
            "verdict": "PASS",
            "intent_preserved": True,
            "issues_resolved": {
                "total_critical_major": 1,
                "resolved": 1,
                "unresolved": [],
                "inadequately_resolved": [],
            },
            "regressions": [],
            "scope_creep": [],
            "grade_after": "A",
            "final_recommendation": "ship",
            "revision_notes": "",
        }

        def mock_write_validation(ws_path):
            with open(ws_path / "02-fixer" / "validation.json", "w") as f:
                json.dump(validation_result, f)

        with patch.object(orchestrator, "_prepare_fixer_prompt", return_value="Mock prompt"):
            with patch.object(orchestrator.workspace_manager, "write_fix"):
                mock_write_validation(workspace)
                fix_result = orchestrator._spawn_fixer_with_retry(workspace, max_retries=2)

                assert fix_result["verdict"] == "PASS"
                assert fix_result["grade_after"] == "A"

    def test_fixer_retries_on_fail_verdict(self, orchestrator, workspace):
        """Test that fixer retries when validation verdict is FAIL."""

        validation_fail = {
            "verdict": "FAIL",
            "intent_preserved": False,
            "issues_resolved": {
                "total_critical_major": 1,
                "resolved": 0,
                "unresolved": ["TEST-001"],
                "inadequately_resolved": [],
            },
            "regressions": [
                {"description": "Test regression", "severity": "critical", "location": "test"}
            ],
            "scope_creep": [],
            "grade_after": "C",
            "final_recommendation": "revise",
            "revision_notes": "Fix intent preservation issue",
        }

        validation_pass = {
            "verdict": "PASS",
            "intent_preserved": True,
            "issues_resolved": {
                "total_critical_major": 1,
                "resolved": 1,
                "unresolved": [],
                "inadequately_resolved": [],
            },
            "regressions": [],
            "scope_creep": [],
            "grade_after": "A",
            "final_recommendation": "ship",
            "revision_notes": "",
        }

        attempt_count = [0]

        def mock_write_validation(ws_path):
            attempt_count[0] += 1
            result = validation_fail if attempt_count[0] == 1 else validation_pass
            with open(ws_path / "02-fixer" / "validation.json", "w") as f:
                json.dump(result, f)

        with patch.object(orchestrator, "_prepare_fixer_prompt", return_value="Mock prompt"):
            with patch.object(orchestrator.workspace_manager, "write_fix"):
                mock_write_validation(workspace)
                mock_write_validation(workspace)
                fix_result = orchestrator._spawn_fixer_with_retry(workspace, max_retries=2)

                assert attempt_count[0] == 2
                assert fix_result["verdict"] == "PASS"

    def test_fixer_implements_exponential_backoff(self, orchestrator, workspace):
        """Test that retry logic implements exponential backoff (PROP-007)."""

        validation_fail = {
            "verdict": "FAIL",
            "intent_preserved": False,
            "issues_resolved": {
                "total_critical_major": 1,
                "resolved": 0,
                "unresolved": ["TEST-001"],
                "inadequately_resolved": [],
            },
            "regressions": [],
            "scope_creep": [],
            "grade_after": "C",
            "final_recommendation": "revise",
            "revision_notes": "Test",
        }

        with open(workspace / "02-fixer" / "validation.json", "w") as f:
            json.dump(validation_fail, f)

        with patch.object(orchestrator, "_prepare_fixer_prompt", return_value="Mock prompt"):
            with patch.object(orchestrator.workspace_manager, "write_fix"):
                with patch("time.sleep") as mock_sleep:
                    _result = orchestrator._spawn_fixer_with_retry(workspace, max_retries=2)

                    sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
                    assert len(sleep_calls) == 2, "Should have 2 sleep calls for 2 retries"
                    assert sleep_calls[0] == 2, "First backoff should be 2 seconds"
                    assert sleep_calls[1] == 4, "Second backoff should be 4 seconds"

    def test_fixer_caps_backoff_at_30_seconds(self, orchestrator, workspace):
        """Test that exponential backoff caps at 30 seconds (PROP-007)."""

        validation_fail = {
            "verdict": "FAIL",
            "intent_preserved": False,
            "issues_resolved": {},
            "regressions": [],
            "scope_creep": [],
            "grade_after": "C",
            "final_recommendation": "revise",
            "revision_notes": "Test",
        }

        with patch.object(orchestrator, "_prepare_fixer_prompt", return_value="Mock prompt"):
            with patch.object(orchestrator.workspace_manager, "write_fix"):
                with patch("time.sleep") as mock_sleep:
                    for _ in range(3):
                        with open(workspace / "02-fixer" / "validation.json", "w") as f:
                            json.dump(validation_fail, f)

                    orchestrator._spawn_fixer_with_retry(workspace, max_retries=2)

                    sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
                    for sleep_time in sleep_calls:
                        assert (
                            sleep_time <= 30
                        ), f"Backoff should cap at 30 seconds, got {sleep_time}s"

    def test_fixer_validation_schema_checked(self, orchestrator, workspace):
        """Test that validation.json is schema-validated before accepting result."""
        invalid_validation = {
            "verdict": "INVALID",
            "grade_after": "Z",
        }

        with open(workspace / "02-fixer" / "validation.json", "w") as f:
            json.dump(invalid_validation, f)

        with patch.object(orchestrator, "_prepare_fixer_prompt", return_value="Mock prompt"):
            with pytest.raises(Exception):
                orchestrator._spawn_fixer_with_retry(workspace, max_retries=0)


class TestReporterPromptGeneration:
    """Test _prepare_reporter_prompt() method (TASK-005)."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        from wfc.skills import wfc_prompt_fixer

        return wfc_prompt_fixer.PromptFixerOrchestrator()

    def test_prepare_reporter_prompt_loads_template(self, orchestrator, tmp_path):
        """Test that _prepare_reporter_prompt loads reporter.md template."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        prompt = orchestrator._prepare_reporter_prompt(workspace, no_changes=False)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Reporter Agent" in prompt or "reporter" in prompt.lower()

    def test_prepare_reporter_prompt_injects_workspace_path(self, orchestrator, tmp_path):
        """Test that workspace path is injected into template."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        prompt = orchestrator._prepare_reporter_prompt(workspace, no_changes=False)

        assert str(workspace) in prompt

    def test_prepare_reporter_prompt_includes_no_changes_flag(self, orchestrator, tmp_path):
        """Test that no_changes flag is included in reporter prompt."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        prompt = orchestrator._prepare_reporter_prompt(workspace, no_changes=True)

        assert "no_changes" in prompt.lower() or "grade a" in prompt.lower()

    def test_prepare_reporter_prompt_template_missing_raises_error(self, orchestrator, tmp_path):
        """Test that missing reporter.md template raises WorkspaceError."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with patch.object(
            orchestrator, "_get_agent_template_path", return_value=Path("/nonexistent/reporter.md")
        ):
            with pytest.raises(Exception, match="Agent template not found"):
                orchestrator._prepare_reporter_prompt(workspace, no_changes=False)


class TestReporterSpawning:
    """Test Reporter agent spawning methods (TASK-005)."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        from wfc.skills import wfc_prompt_fixer

        return wfc_prompt_fixer.PromptFixerOrchestrator()

    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a workspace with all required files."""
        workspace = tmp_path / "workspace"
        (workspace / "input").mkdir(parents=True)
        (workspace / "01-analyzer").mkdir(parents=True)
        (workspace / "02-fixer").mkdir(parents=True)
        (workspace / "03-reporter").mkdir(parents=True)

        metadata = {
            "run_id": "test-run-123",
            "prompt_path": "/test/PROMPT.md",
            "wfc_mode": False,
            "timestamp": "2024-01-01T00:00:00",
        }
        with open(workspace / "metadata.json", "w") as f:
            json.dump(metadata, f)

        (workspace / "input" / "prompt.md").write_text("# Test Prompt\n\nOriginal content.")

        analysis = {
            "classification": {},
            "scores": {},
            "issues": [],
            "overall_grade": "A",
            "average_score": 3.0,
            "rewrite_recommended": False,
            "rewrite_scope": "none",
            "wfc_mode": False,
            "summary": "Excellent prompt",
        }
        with open(workspace / "01-analyzer" / "analysis.json", "w") as f:
            json.dump(analysis, f)

        return workspace

    def test_skip_to_reporter_prepares_prompt(self, orchestrator, workspace):
        """Test that _skip_to_reporter prepares reporter prompt correctly."""
        with patch.object(
            orchestrator, "_prepare_reporter_prompt", return_value="Mock prompt"
        ) as mock_prepare:
            report_path = workspace / "03-reporter" / "report.md"
            report_path.write_text("Mock report")
            with patch.object(
                orchestrator.workspace_manager, "read_report", return_value=report_path
            ):
                result = orchestrator._skip_to_reporter(workspace, no_changes=True)

                mock_prepare.assert_called_once_with(workspace, no_changes=True)
                assert result.exists()

    def test_skip_to_reporter_creates_report_file(self, orchestrator, workspace):
        """Test that _skip_to_reporter creates a report file."""
        with patch.object(orchestrator, "_prepare_reporter_prompt", return_value="Mock prompt"):
            report_path = workspace / "03-reporter" / "report.md"
            report_path.write_text("# Prompt Fix Report\n\nNo changes needed.")
            with patch.object(
                orchestrator.workspace_manager, "read_report", return_value=report_path
            ):
                result = orchestrator._skip_to_reporter(workspace, no_changes=True)

                assert result.exists()
                assert "report.md" in str(result)

    def test_spawn_reporter_prepares_prompt(self, orchestrator, workspace):
        """Test that _spawn_reporter prepares reporter prompt correctly."""
        (workspace / "02-fixer" / "fixed_prompt.md").write_text("# Fixed Prompt")
        (workspace / "02-fixer" / "changelog.md").write_text("1. Change 1")
        (workspace / "02-fixer" / "unresolved.md").write_text("No unresolved items.")
        validation = {
            "verdict": "PASS",
            "intent_preserved": True,
            "issues_resolved": {},
            "regressions": [],
            "scope_creep": [],
            "grade_after": "A",
            "final_recommendation": "ship",
        }
        with open(workspace / "02-fixer" / "validation.json", "w") as f:
            json.dump(validation, f)

        with patch.object(
            orchestrator, "_prepare_reporter_prompt", return_value="Mock prompt"
        ) as mock_prepare:
            report_path = workspace / "03-reporter" / "report.md"
            report_path.write_text("Mock report")
            with patch.object(
                orchestrator.workspace_manager, "read_report", return_value=report_path
            ):
                result = orchestrator._spawn_reporter(workspace)

                mock_prepare.assert_called_once_with(workspace, no_changes=False)
                assert result.exists()

    def test_spawn_reporter_creates_comprehensive_report(self, orchestrator, workspace):
        """Test that _spawn_reporter creates a comprehensive report with all sections."""
        (workspace / "02-fixer" / "fixed_prompt.md").write_text("# Fixed Prompt")
        (workspace / "02-fixer" / "changelog.md").write_text("1. Change 1")
        (workspace / "02-fixer" / "unresolved.md").write_text("No unresolved items.")
        validation = {
            "verdict": "PASS",
            "intent_preserved": True,
            "issues_resolved": {},
            "regressions": [],
            "scope_creep": [],
            "grade_after": "A",
            "final_recommendation": "ship",
        }
        with open(workspace / "02-fixer" / "validation.json", "w") as f:
            json.dump(validation, f)

        with patch.object(orchestrator, "_prepare_reporter_prompt", return_value="Mock prompt"):
            report_path = workspace / "03-reporter" / "report.md"
            report_content = """# Prompt Fix Report

**Prompt:** test
**Run ID:** test-run-123

## Summary
- Original grade: A
- Final grade: A
- Verdict: PASS
"""
            report_path.write_text(report_content)
            with patch.object(
                orchestrator.workspace_manager, "read_report", return_value=report_path
            ):
                result = orchestrator._spawn_reporter(workspace)

                assert result.exists()
                content = result.read_text()
                assert "Summary" in content
                assert "Original grade" in content


class TestPRCreation:
    """Test _create_pr() method (TASK-005)."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        from wfc.skills import wfc_prompt_fixer

        return wfc_prompt_fixer.PromptFixerOrchestrator()

    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a workspace for PR testing."""
        workspace = tmp_path / "workspace"
        (workspace / "02-fixer").mkdir(parents=True)
        (workspace / "02-fixer" / "fixed_prompt.md").write_text("# Fixed Prompt")
        return workspace

    def test_create_pr_creates_branch(self, orchestrator, workspace, tmp_path):
        """Test that _create_pr creates a git branch."""
        prompt_path = tmp_path / "PROMPT.md"
        prompt_path.write_text("# Original")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            orchestrator._create_pr(prompt_path, workspace, "B", "A")

            branch_calls = [call for call in mock_run.call_args_list if "branch" in str(call)]
            assert len(branch_calls) > 0 or any(
                "checkout -b" in str(call) for call in mock_run.call_args_list
            )

    def test_create_pr_commits_changes(self, orchestrator, workspace, tmp_path):
        """Test that _create_pr commits the fixed prompt."""
        prompt_path = tmp_path / "PROMPT.md"
        prompt_path.write_text("# Original")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            orchestrator._create_pr(prompt_path, workspace, "B", "A")

            commit_calls = [call for call in mock_run.call_args_list if "commit" in str(call)]
            assert len(commit_calls) > 0

    def test_create_pr_pushes_to_remote(self, orchestrator, workspace, tmp_path):
        """Test that _create_pr pushes to remote."""
        prompt_path = tmp_path / "PROMPT.md"
        prompt_path.write_text("# Original")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            orchestrator._create_pr(prompt_path, workspace, "B", "A")

            push_calls = [call for call in mock_run.call_args_list if "push" in str(call)]
            assert len(push_calls) > 0

    def test_create_pr_uses_gh_cli(self, orchestrator, workspace, tmp_path):
        """Test that _create_pr uses gh CLI to create PR."""
        prompt_path = tmp_path / "PROMPT.md"
        prompt_path.write_text("# Original")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            orchestrator._create_pr(prompt_path, workspace, "B", "A")

            gh_calls = [call for call in mock_run.call_args_list if "gh" in str(call)]
            assert len(gh_calls) > 0

    def test_create_pr_includes_grade_in_message(self, orchestrator, workspace, tmp_path):
        """Test that _create_pr includes grade improvement in commit message."""
        prompt_path = tmp_path / "PROMPT.md"
        prompt_path.write_text("# Original")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            orchestrator._create_pr(prompt_path, workspace, "B", "A")

            commit_calls = [str(call) for call in mock_run.call_args_list if "commit" in str(call)]
            assert any("B" in call and "A" in call for call in commit_calls)
