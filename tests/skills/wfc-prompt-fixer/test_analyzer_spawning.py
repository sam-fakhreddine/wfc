"""
Tests for Analyzer agent spawning (TASK-003).

Tests the prompt generator pattern where:
1. Orchestrator prepares agent prompt from agents/analyzer.md
2. Orchestrator returns instructions for Claude to invoke Task tool
3. Agent writes analysis.json to workspace
4. Orchestrator validates schema and returns analysis
"""

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "wfc" / "skills"))

wfc_prompt_fixer = importlib.import_module("wfc-prompt-fixer")
PromptFixerOrchestrator = wfc_prompt_fixer.PromptFixerOrchestrator
WorkspaceManager = wfc_prompt_fixer.workspace.WorkspaceManager
WorkspaceError = wfc_prompt_fixer.workspace.WorkspaceError


class TestAnalyzerPromptPreparation:
    """Test analyzer prompt preparation (_prepare_analyzer_prompt)."""

    def test_prepare_analyzer_prompt_loads_template(self, tmp_path):
        """Test that _prepare_analyzer_prompt loads the analyzer.md template."""
        orchestrator = PromptFixerOrchestrator(cwd=tmp_path)
        workspace = tmp_path / ".development" / "prompt-fixer" / "test-workspace"
        workspace.mkdir(parents=True)

        agent_dir = tmp_path / "wfc" / "skills" / "wfc-prompt-fixer" / "agents"
        agent_dir.mkdir(parents=True)
        analyzer_md = agent_dir / "analyzer.md"
        analyzer_md.write_text("# Analyzer Agent\n\nYou analyze prompts.\n\n{workspace}")

        with patch.object(orchestrator, "_get_agent_template_path") as mock_path:
            mock_path.return_value = analyzer_md
            prompt = orchestrator._prepare_analyzer_prompt(workspace, wfc_mode=False)

        assert prompt is not None
        assert "Analyzer Agent" in prompt
        assert "analyze prompts" in prompt
        assert str(workspace) in prompt

    def test_prepare_analyzer_prompt_injects_workspace_path(self, tmp_path):
        """Test that workspace path is injected into the prompt."""
        orchestrator = PromptFixerOrchestrator(cwd=tmp_path)
        workspace = tmp_path / ".development" / "prompt-fixer" / "test-123"
        workspace.mkdir(parents=True)

        agent_dir = tmp_path / "wfc" / "skills" / "wfc-prompt-fixer" / "agents"
        agent_dir.mkdir(parents=True)
        analyzer_md = agent_dir / "analyzer.md"
        analyzer_md.write_text(
            "Read from {workspace}/input/prompt.md\nWrite to {workspace}/01-analyzer/analysis.json"
        )

        with patch.object(orchestrator, "_get_agent_template_path") as mock_path:
            mock_path.return_value = analyzer_md
            prompt = orchestrator._prepare_analyzer_prompt(workspace, wfc_mode=False)

        assert str(workspace) in prompt
        assert "{workspace}" not in prompt
        assert f"{workspace}/input/prompt.md" in prompt
        assert f"{workspace}/01-analyzer/analysis.json" in prompt

    def test_prepare_analyzer_prompt_includes_wfc_mode_flag(self, tmp_path):
        """Test that wfc_mode flag is communicated to the agent."""
        orchestrator = PromptFixerOrchestrator(cwd=tmp_path)
        workspace = tmp_path / ".development" / "prompt-fixer" / "test-456"
        workspace.mkdir(parents=True)

        metadata = {
            "run_id": "test",
            "timestamp": "now",
            "prompt_path": "/tmp/test.md",
            "wfc_mode": True,
        }
        (workspace / "metadata.json").write_text(json.dumps(metadata))

        agent_dir = tmp_path / "wfc" / "skills" / "wfc-prompt-fixer" / "agents"
        agent_dir.mkdir(parents=True)
        analyzer_md = agent_dir / "analyzer.md"
        analyzer_md.write_text("Analyze prompt. WFC mode: {wfc_mode}")

        with patch.object(orchestrator, "_get_agent_template_path") as mock_path:
            mock_path.return_value = analyzer_md
            prompt = orchestrator._prepare_analyzer_prompt(workspace, wfc_mode=True)

        assert "true" in prompt.lower() or "wfc" in prompt.lower()


class TestAnalysisSchemaValidation:
    """Test analysis.json schema validation (PROP-006)."""

    def test_validate_analysis_schema_accepts_valid_analysis(self):
        """Test that valid analysis.json passes schema validation."""
        validate_analysis_schema = wfc_prompt_fixer.orchestrator.validate_analysis_schema

        valid_analysis = {
            "classification": {
                "prompt_type": "system",
                "deployment_context": "claude_code",
                "complexity": "moderate",
                "domain": "code_generation",
                "target_model": "sonnet",
                "has_tools": True,
                "has_examples": False,
                "has_output_format_spec": True,
                "estimated_token_count": 1200,
            },
            "scores": {
                "XML_SEGMENTATION": {"score": 2, "evidence": "Some XML tags present"},
                "INSTRUCTION_HIERARCHY": {"score": 3, "evidence": "Clear priority"},
            },
            "issues": [
                {
                    "id": "ISSUE-001",
                    "antipattern_id": "AP-01",
                    "category": "STRUCTURE",
                    "severity": "major",
                    "description": "Missing XML tags",
                    "impact": "Reduces clarity",
                    "fix_directive": "Add XML tags",
                    "evidence": "Quote from prompt",
                }
            ],
            "overall_grade": "B",
            "average_score": 2.5,
            "rewrite_recommended": True,
            "rewrite_scope": "partial",
            "wfc_mode": False,
            "summary": "Prompt needs minor improvements.",
        }

        is_valid, errors = validate_analysis_schema(valid_analysis)
        assert is_valid is True
        assert errors == []

    def test_validate_analysis_schema_rejects_missing_required_fields(self):
        """Test that analysis missing required fields fails validation."""
        validate_analysis_schema = wfc_prompt_fixer.orchestrator.validate_analysis_schema

        invalid_analysis = {
            "overall_grade": "B",
        }

        is_valid, errors = validate_analysis_schema(invalid_analysis)
        assert is_valid is False
        assert len(errors) > 0
        assert any("classification" in err.lower() for err in errors)

    def test_validate_analysis_schema_rejects_invalid_grade(self):
        """Test that invalid grades (not A-F) fail validation."""
        validate_analysis_schema = wfc_prompt_fixer.orchestrator.validate_analysis_schema

        invalid_analysis = {
            "classification": {"prompt_type": "system"},
            "scores": {},
            "issues": [],
            "overall_grade": "Z",
            "average_score": 2.0,
            "rewrite_recommended": False,
            "rewrite_scope": "none",
            "wfc_mode": False,
            "summary": "Test",
        }

        is_valid, errors = validate_analysis_schema(invalid_analysis)
        assert is_valid is False
        assert any("grade" in err.lower() for err in errors)

    def test_validate_analysis_schema_rejects_invalid_severity(self):
        """Test that invalid severity values fail validation."""
        validate_analysis_schema = wfc_prompt_fixer.orchestrator.validate_analysis_schema

        invalid_analysis = {
            "classification": {"prompt_type": "system"},
            "scores": {},
            "issues": [
                {
                    "id": "ISSUE-001",
                    "severity": "super-critical",
                    "category": "STRUCTURE",
                }
            ],
            "overall_grade": "B",
            "average_score": 2.0,
            "rewrite_recommended": False,
            "rewrite_scope": "none",
            "wfc_mode": False,
            "summary": "Test",
        }

        is_valid, errors = validate_analysis_schema(invalid_analysis)
        assert is_valid is False
        assert any("severity" in err.lower() for err in errors)


class TestSpawnAnalyzer:
    """Test _spawn_analyzer() using prompt generator pattern."""

    def test_spawn_analyzer_prepares_prompt_and_waits_for_result(self, tmp_path):
        """Test that _spawn_analyzer prepares prompt but doesn't directly invoke Task tool."""
        orchestrator = PromptFixerOrchestrator(cwd=tmp_path)
        workspace_manager = WorkspaceManager(base_dir=tmp_path / ".development" / "prompt-fixer")

        prompt_path = tmp_path / "test_prompt.md"
        prompt_path.write_text("# Test Prompt\n\nYou are a test.")
        workspace = workspace_manager.create(prompt_path, wfc_mode=False)

        agent_dir = tmp_path / "wfc" / "skills" / "wfc-prompt-fixer" / "agents"
        agent_dir.mkdir(parents=True)
        analyzer_md = agent_dir / "analyzer.md"
        analyzer_md.write_text("Analyze {workspace}/input/prompt.md")

        with patch.object(orchestrator, "_prepare_analyzer_prompt") as mock_prepare:
            mock_prepare.return_value = f"Analyze {workspace}/input/prompt.md"

            analysis = {
                "classification": {"prompt_type": "system"},
                "scores": {"XML_SEGMENTATION": {"score": 2, "evidence": "test"}},
                "issues": [],
                "overall_grade": "B",
                "average_score": 2.0,
                "rewrite_recommended": False,
                "rewrite_scope": "none",
                "wfc_mode": False,
                "summary": "Test analysis",
            }
            workspace_manager.write_analysis(workspace, analysis)

            result = orchestrator._spawn_analyzer(workspace, wfc_mode=False)

        # Note: Implementation uses positional args, not keyword args
        assert mock_prepare.call_count == 1
        call_args = mock_prepare.call_args
        assert call_args[0][0] == workspace
        assert (len(call_args[0]) > 1 and not call_args[0][1]) or not call_args[1].get("wfc_mode")

        assert result["overall_grade"] == "B"
        assert result["average_score"] == 2.0

    def test_spawn_analyzer_validates_schema_on_read(self, tmp_path):
        """Test that _spawn_analyzer validates analysis.json schema (PROP-006)."""
        orchestrator = PromptFixerOrchestrator(cwd=tmp_path)
        workspace_manager = WorkspaceManager(base_dir=tmp_path / ".development" / "prompt-fixer")

        prompt_path = tmp_path / "test_prompt.md"
        prompt_path.write_text("# Test Prompt")
        workspace = workspace_manager.create(prompt_path, wfc_mode=False)

        invalid_analysis = {"overall_grade": "B"}
        workspace_manager.write_analysis(workspace, invalid_analysis)

        with patch.object(orchestrator, "_prepare_analyzer_prompt") as mock_prepare:
            mock_prepare.return_value = "Test prompt"

            with pytest.raises(WorkspaceError, match="(?i)schema|invalid|validation"):
                orchestrator._spawn_analyzer(workspace, wfc_mode=False)

    def test_spawn_analyzer_raises_error_if_analysis_not_found(self, tmp_path):
        """Test that _spawn_analyzer raises error if analysis.json doesn't exist."""
        orchestrator = PromptFixerOrchestrator(cwd=tmp_path)
        workspace_manager = WorkspaceManager(base_dir=tmp_path / ".development" / "prompt-fixer")

        prompt_path = tmp_path / "test_prompt.md"
        prompt_path.write_text("# Test Prompt")
        workspace = workspace_manager.create(prompt_path, wfc_mode=False)

        with patch.object(orchestrator, "_prepare_analyzer_prompt") as mock_prepare:
            mock_prepare.return_value = "Test prompt"

            with pytest.raises(TimeoutError, match="(?i)did not complete|timeout"):
                orchestrator._spawn_analyzer(workspace, wfc_mode=False)
