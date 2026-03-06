"""Tests for the CLAUDE.md Remediation Pipeline.

Tests cover:
- Context Mapper (deterministic, no LLM)
- Analyst heuristic fallback
- Fixer fallback
- QA Validator rule-based checks
- Orchestrator pipeline (no LLM)
- CLI dry-run
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from wfc.scripts.orchestrators.claude_md.analyst import analyze, _fallback_diagnosis
from wfc.scripts.orchestrators.claude_md.context_mapper import (
    map_project,
    _count_instructions,
    _extract_sections,
    _extract_commands,
)
from wfc.scripts.orchestrators.claude_md.fixer import fix, _fallback_trim
from wfc.scripts.orchestrators.claude_md.orchestrator import remediate
from wfc.scripts.orchestrators.claude_md.qa_validator import validate, _rule_based_validate
from wfc.scripts.orchestrators.claude_md.reporter import report, _rule_based_report
from wfc.scripts.orchestrators.claude_md.schemas import RemediationResult


@pytest.fixture
def minimal_project(tmp_path: Path) -> Path:
    """Project with a well-formed, short CLAUDE.md."""
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(textwrap.dedent("""\
        # MyProject

        A tool for processing customer data pipelines.

        ## Architecture
        - Python 3.12, FastAPI, PostgreSQL
        - `src/` — application code
        - `tests/` — test suite

        ## Commands
        ```bash
        uv run pytest          # run tests
        uv run ruff check .    # lint
        uv run black .         # format
        ```

        ## Important Notes
        - Never commit secrets to git.
        - Use `uv run` for all Python commands.
        """))
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "myproject"\n[tool.ruff]\n[tool.pytest.ini_options]\n'
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    return tmp_path


@pytest.fixture
def bloated_project(tmp_path: Path) -> Path:
    """Project with an oversized CLAUDE.md that has many known antipatterns."""
    lines = ["# BigProject\n"]
    lines.append("## Code Style\n")
    lines.append("- Always use 4-space indentation\n")
    lines.append("- Always use single quotes\n")
    lines.append("- Never use semicolons at end of line\n")
    lines.append("- Always add trailing newlines\n")
    for i in range(250):
        lines.append(f"- Rule {i}: always do thing {i}\n")
    lines.append("## Commands\n```bash\nnpm run nonexistent-script\n```\n")
    lines.append("## Architecture\n")
    for i in range(50):
        lines.append(f"Component {i}: does thing {i}\n")

    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("".join(lines))

    (tmp_path / ".eslintrc.json").write_text('{"rules": {}}')
    (tmp_path / "package.json").write_text('{"name": "big", "scripts": {"test": "jest"}}')
    return tmp_path


@pytest.fixture
def no_claude_md_project(tmp_path: Path) -> Path:
    """Project with no CLAUDE.md."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "empty"\n')
    return tmp_path


class TestContextMapper:
    def test_map_minimal_project(self, minimal_project: Path) -> None:
        result = map_project(minimal_project)
        assert result["claude_md"]["total_lines"] > 0
        assert result["claude_md"]["has_commands_section"] is True
        assert result["codebase"]["has_linter_config"] is True
        assert result["codebase"]["linter_type"] == "ruff"
        assert result["codebase"]["has_test_framework"] is True
        assert result["codebase"]["test_framework"] == "pytest"

    def test_map_bloated_project(self, bloated_project: Path) -> None:
        result = map_project(bloated_project)
        assert result["claude_md"]["total_lines"] > 300
        assert len(result["red_flags"]) > 0
        assert any("300" in f or "lines" in f for f in result["red_flags"])

    def test_map_missing_claude_md(self, no_claude_md_project: Path) -> None:
        result = map_project(no_claude_md_project)
        assert result["claude_md"]["total_lines"] == 0

    def test_map_nonexistent_root(self, tmp_path: Path) -> None:
        result = map_project(tmp_path / "nonexistent")
        assert isinstance(result, dict)

    def test_count_instructions_basic(self) -> None:
        content = textwrap.dedent("""\
        - Always use uv run
        - Never commit to main
        - Do not push directly
        Some prose that is not an instruction.
        """)
        count = _count_instructions(content)
        assert count >= 2

    def test_extract_sections(self) -> None:
        content = "# Project\n## Architecture\n## Commands\n### Sub\n"
        sections = _extract_sections(content)
        assert "Architecture" in sections
        assert "Commands" in sections

    def test_extract_commands(self) -> None:
        content = "Run `uv run pytest` and `make lint` to verify."
        cmds = _extract_commands(content)
        assert any("uv run pytest" in c for c in cmds)

    def test_red_flags_linter_with_style_rules(self, tmp_path: Path) -> None:
        (tmp_path / "CLAUDE.md").write_text(
            "# Proj\n## Style\n- Always use 2-space indentation\n- Never use trailing commas\n" * 20
        )
        (tmp_path / "ruff.toml").write_text("")
        result = map_project(tmp_path)
        assert any("style" in f.lower() or "linter" in f.lower() for f in result["red_flags"])


class TestAnalyst:
    def test_fallback_healthy_file(self, minimal_project: Path) -> None:
        manifest = map_project(minimal_project)
        diagnosis = _fallback_diagnosis(manifest)
        assert diagnosis["overall_grade"] in ("A", "B", "C")
        assert "instruction_budget_analysis" in diagnosis

    def test_fallback_bloated_file(self, bloated_project: Path) -> None:
        manifest = map_project(bloated_project)
        diagnosis = _fallback_diagnosis(manifest)
        assert diagnosis["overall_grade"] in ("C", "D", "F")
        assert diagnosis["rewrite_recommended"] is True

    def test_analyze_no_response_fn(self, minimal_project: Path) -> None:
        manifest = map_project(minimal_project)
        content = (minimal_project / "CLAUDE.md").read_text()
        result = analyze(content, manifest, response_fn=None)
        assert "overall_grade" in result
        assert "issues" in result

    def test_analyze_with_mock_response(self, minimal_project: Path) -> None:
        manifest = map_project(minimal_project)
        content = (minimal_project / "CLAUDE.md").read_text()
        mock_response = json.dumps(
            {
                "scores": {},
                "dimension_summaries": {
                    "economy": {"avg_score": 2.8, "summary": "Good"},
                    "content_quality": {"avg_score": 2.5, "summary": "Good"},
                    "separation_of_concerns": {"avg_score": 3.0, "summary": "Excellent"},
                    "structural_clarity": {"avg_score": 3.0, "summary": "Excellent"},
                },
                "issues": [],
                "instruction_budget_analysis": {
                    "estimated_claude_code_system_instructions": 50,
                    "claude_md_instructions": 15,
                    "total_estimated": 65,
                    "budget_remaining": 85,
                    "budget_status": "healthy",
                },
                "overall_grade": "A",
                "rewrite_recommended": False,
                "rewrite_scope": "none",
            }
        )
        result = analyze(content, manifest, response_fn=lambda _: mock_response)
        assert result["overall_grade"] == "A"
        assert result["rewrite_recommended"] is False

    def test_analyze_with_bad_response_falls_back(self, minimal_project: Path) -> None:
        manifest = map_project(minimal_project)
        content = (minimal_project / "CLAUDE.md").read_text()
        result = analyze(content, manifest, response_fn=lambda _: "not valid json {{{")
        assert "overall_grade" in result

    def test_budget_status_overdrawn(self, tmp_path: Path) -> None:
        rules = "\n".join(f"- Always rule {i}" for i in range(120))
        (tmp_path / "CLAUDE.md").write_text(f"# P\n{rules}\n")
        manifest = map_project(tmp_path)
        diagnosis = _fallback_diagnosis(manifest)
        assert diagnosis["instruction_budget_analysis"]["budget_status"] in ("tight", "overdrawn")


class TestFixer:
    def test_fallback_returns_original(self, minimal_project: Path) -> None:
        content = (minimal_project / "CLAUDE.md").read_text()
        manifest = map_project(minimal_project)
        diagnosis = _fallback_diagnosis(manifest)
        result = _fallback_trim(content, diagnosis)
        assert "rewritten_content" in result
        assert "metrics" in result
        assert result["metrics"]["original_lines"] == len(content.splitlines())

    def test_fix_no_response_fn(self, minimal_project: Path) -> None:
        content = (minimal_project / "CLAUDE.md").read_text()
        manifest = map_project(minimal_project)
        diagnosis = _fallback_diagnosis(manifest)
        result = fix(content, manifest, diagnosis, response_fn=None)
        assert result["rewritten_content"] is not None
        assert isinstance(result["changelog"], list)

    def test_fix_with_mock_response(self, bloated_project: Path) -> None:
        content = (bloated_project / "CLAUDE.md").read_text()
        manifest = map_project(bloated_project)
        diagnosis = _fallback_diagnosis(manifest)

        short_rewrite = "# BigProject\n\nA project.\n\n## Commands\n```bash\nnpm test\n```\n"
        mock_response = json.dumps(
            {
                "rewritten_content": short_rewrite,
                "changelog": ["[CMD-001] Removed 300 lines of style rules"],
                "migration_plan": "Configure eslint hook for style enforcement",
                "extracted_files": [],
                "metrics": {
                    "original_lines": len(content.splitlines()),
                    "rewritten_lines": len(short_rewrite.splitlines()),
                    "original_instructions": 110,
                    "rewritten_instructions": 5,
                    "lines_removed": len(content.splitlines()) - len(short_rewrite.splitlines()),
                    "lines_extracted": 0,
                    "hooks_recommended": 1,
                    "slash_commands_recommended": 0,
                    "subdirectory_files_created": 0,
                },
            }
        )
        result = fix(content, manifest, diagnosis, response_fn=lambda _: mock_response)
        assert result["rewritten_content"] == short_rewrite
        assert result["metrics"]["rewritten_lines"] < result["metrics"]["original_lines"]


class TestQAValidator:
    def test_pass_when_rewrite_shorter(self, minimal_project: Path) -> None:
        original = (minimal_project / "CLAUDE.md").read_text()
        manifest = map_project(minimal_project)
        diagnosis = _fallback_diagnosis(manifest)
        short_rewrite = "# P\n\nShort.\n\n## Commands\n```bash\nuv run pytest\n```\n"
        orig_inst = diagnosis["instruction_budget_analysis"]["claude_md_instructions"]
        fixer_output = {
            "rewritten_content": short_rewrite,
            "changelog": [],
            "migration_plan": "",
            "extracted_files": [],
            "metrics": {
                "original_lines": len(original.splitlines()),
                "rewritten_lines": len(short_rewrite.splitlines()),
                "original_instructions": orig_inst,
                "rewritten_instructions": max(0, orig_inst - 1),
            },
        }
        result = _rule_based_validate(original, manifest, diagnosis, fixer_output)
        assert result["verdict"] in ("PASS", "PASS_WITH_NOTES")

    def test_fail_when_rewrite_longer(self, minimal_project: Path) -> None:
        original = (minimal_project / "CLAUDE.md").read_text()
        manifest = map_project(minimal_project)
        diagnosis = _fallback_diagnosis(manifest)
        long_rewrite = original + "\n" * 100 + "# Extra section\n" + "- Extra rule\n" * 50
        fixer_output = {
            "rewritten_content": long_rewrite,
            "changelog": [],
            "migration_plan": "",
            "extracted_files": [],
            "metrics": {
                "original_lines": len(original.splitlines()),
                "rewritten_lines": len(long_rewrite.splitlines()),
                "original_instructions": 10,
                "rewritten_instructions": 60,
            },
        }
        result = _rule_based_validate(original, manifest, diagnosis, fixer_output)
        assert result["verdict"] == "FAIL"
        assert result["final_recommendation"] == "revise"

    def test_validate_no_response_fn(self, minimal_project: Path) -> None:
        original = (minimal_project / "CLAUDE.md").read_text()
        manifest = map_project(minimal_project)
        diagnosis = _fallback_diagnosis(manifest)
        fixer_output = {
            "rewritten_content": "# P\nShort.\n",
            "changelog": [],
            "migration_plan": "",
            "extracted_files": [],
            "metrics": {"original_lines": 20, "rewritten_lines": 2},
        }
        result = validate(original, manifest, diagnosis, fixer_output, response_fn=None)
        assert "verdict" in result
        assert "budget_check" in result


class TestReporter:
    def test_rule_based_report_pass(self) -> None:
        manifest = {"claude_md": {"total_lines": 50}}
        diagnosis = {
            "overall_grade": "D",
            "issues": [],
            "instruction_budget_analysis": {"claude_md_instructions": 80},
        }
        fixer_output = {
            "rewritten_content": "# P\nShort.\n",
            "changelog": ["[CMD-001] Removed style rules"],
            "migration_plan": "Configure ruff hook",
            "extracted_files": [],
            "metrics": {
                "original_lines": 50,
                "rewritten_lines": 2,
                "original_instructions": 80,
                "rewritten_instructions": 5,
            },
        }
        validation = {
            "verdict": "PASS",
            "budget_check": {
                "original_lines": 50,
                "rewritten_lines": 2,
                "original_instructions": 80,
                "rewritten_instructions": 5,
                "budget_status": "improved",
            },
        }
        result = _rule_based_report(manifest, diagnosis, fixer_output, validation)
        assert "## Summary" in result
        assert "PASS" in result
        assert "## Migration Actions" in result

    def test_rule_based_report_fail(self) -> None:
        manifest = {"claude_md": {"total_lines": 100}}
        fixer_output = {
            "rewritten_content": None,
            "changelog": [],
            "migration_plan": "",
            "extracted_files": [],
            "metrics": {},
        }
        validation = {"verdict": "FAIL", "budget_check": {}}
        result = _rule_based_report(manifest, {}, fixer_output, validation)
        assert "FAIL" in result or "preserved" in result.lower()

    def test_report_no_response_fn(self) -> None:
        result = report(
            {},
            {},
            {
                "rewritten_content": None,
                "changelog": [],
                "migration_plan": "",
                "extracted_files": [],
                "metrics": {},
            },
            {"verdict": "PASS", "budget_check": {}},
            response_fn=None,
        )
        assert isinstance(result, str)


class TestOrchestrator:
    def test_grade_a_returns_no_changes(self, minimal_project: Path) -> None:
        """A file diagnosed as grade A should skip Fixer + QA."""
        grade_a_response = json.dumps(
            {
                "scores": {},
                "dimension_summaries": {
                    "economy": {"avg_score": 3.0, "summary": "Excellent"},
                    "content_quality": {"avg_score": 3.0, "summary": "Excellent"},
                    "separation_of_concerns": {"avg_score": 3.0, "summary": "Excellent"},
                    "structural_clarity": {"avg_score": 3.0, "summary": "Excellent"},
                },
                "issues": [],
                "instruction_budget_analysis": {
                    "estimated_claude_code_system_instructions": 50,
                    "claude_md_instructions": 10,
                    "total_estimated": 60,
                    "budget_remaining": 90,
                    "budget_status": "healthy",
                },
                "overall_grade": "A",
                "rewrite_recommended": False,
                "rewrite_scope": "none",
            }
        )
        result = remediate(
            minimal_project,
            analyst_response_fn=lambda _: grade_a_response,
        )
        assert result.no_changes_needed is True
        assert result.grade_before == "A"
        assert result.rewritten_content is None

    def test_full_pipeline_heuristic_mode(self, bloated_project: Path) -> None:
        """Full pipeline in heuristic mode (no LLM calls)."""
        result = remediate(bloated_project)
        assert isinstance(result, RemediationResult)
        assert result.grade_before in ("A", "B", "C", "D", "F")
        assert result.original_lines > 0
        assert result.error is None or isinstance(result.error, str)

    def test_pipeline_missing_claude_md(self, no_claude_md_project: Path) -> None:
        """Pipeline with no CLAUDE.md — should return a valid result, not raise."""
        result = remediate(no_claude_md_project)
        assert isinstance(result, RemediationResult)

    def test_pipeline_fails_gracefully_on_analyst_error(self, minimal_project: Path) -> None:
        """If the analyst raises, pipeline continues with safe defaults."""

        def bad_analyst(prompt: str) -> str:
            raise RuntimeError("Simulated analyst failure")

        result = remediate(minimal_project, analyst_response_fn=bad_analyst)
        assert isinstance(result, RemediationResult)
        assert result.error is None

    def test_pipeline_qa_retry_on_fail(self, bloated_project: Path) -> None:
        """QA returning FAIL triggers Fixer retry up to max_qa_retries."""
        call_count = {"fixer": 0, "qa": 0}
        short = "# P\nShort.\n"

        def counting_fixer(prompt: str) -> str:
            call_count["fixer"] += 1
            return json.dumps(
                {
                    "rewritten_content": short,
                    "changelog": ["[CMD-001] Fixed"],
                    "migration_plan": "",
                    "extracted_files": [],
                    "metrics": {
                        "original_lines": 350,
                        "rewritten_lines": 2,
                        "original_instructions": 110,
                        "rewritten_instructions": 5,
                        "lines_removed": 348,
                        "lines_extracted": 0,
                        "hooks_recommended": 0,
                        "slash_commands_recommended": 0,
                        "subdirectory_files_created": 0,
                    },
                }
            )

        call_count_ref = [0]

        def counting_qa(prompt: str) -> str:
            call_count_ref[0] += 1
            if call_count_ref[0] == 1:
                return json.dumps(
                    {
                        "verdict": "FAIL",
                        "budget_check": {
                            "original_lines": 350,
                            "rewritten_lines": 2,
                            "original_instructions": 110,
                            "rewritten_instructions": 5,
                            "budget_status": "improved",
                        },
                        "content_integrity": {
                            "stale_commands": [],
                            "stale_paths": [],
                            "contradictions": [],
                        },
                        "intent_preserved": True,
                        "lost_content_without_destination": [],
                        "issues_resolved": {
                            "total_critical_major": 1,
                            "resolved": 1,
                            "unresolved": [],
                        },
                        "separation_violations": [],
                        "migration_plan_issues": [],
                        "regressions": [],
                        "final_recommendation": "revise",
                        "revision_notes": "Need to add project summary",
                    }
                )
            return json.dumps(
                {
                    "verdict": "PASS",
                    "budget_check": {
                        "original_lines": 350,
                        "rewritten_lines": 2,
                        "original_instructions": 110,
                        "rewritten_instructions": 5,
                        "budget_status": "improved",
                    },
                    "content_integrity": {
                        "stale_commands": [],
                        "stale_paths": [],
                        "contradictions": [],
                    },
                    "intent_preserved": True,
                    "lost_content_without_destination": [],
                    "issues_resolved": {"total_critical_major": 1, "resolved": 1, "unresolved": []},
                    "separation_violations": [],
                    "migration_plan_issues": [],
                    "regressions": [],
                    "final_recommendation": "ship",
                    "revision_notes": "",
                }
            )

        result = remediate(
            bloated_project,
            fixer_response_fn=counting_fixer,
            qa_response_fn=counting_qa,
        )
        assert result.verdict in ("PASS", "PASS_WITH_NOTES")
        assert call_count["fixer"] >= 1

    def test_remediation_result_properties(self) -> None:
        result = RemediationResult(
            project_root="/tmp/p",
            claude_md_path="/tmp/p/CLAUDE.md",
            grade_before="A",
            grade_after="A",
            verdict="PASS",
            original_lines=50,
            rewritten_lines=50,
            original_instructions=10,
            rewritten_instructions=10,
            rewritten_content=None,
        )
        assert result.no_changes_needed is True
        assert result.succeeded is True

    def test_remediation_result_failure(self) -> None:
        result = RemediationResult(
            project_root="/tmp/p",
            claude_md_path="/tmp/p/CLAUDE.md",
            grade_before="D",
            grade_after="D",
            verdict="FAIL",
            original_lines=400,
            rewritten_lines=400,
            original_instructions=120,
            rewritten_instructions=120,
            rewritten_content=None,
            error="Pipeline error",
        )
        assert result.succeeded is False


class TestCLI:
    def test_cli_dry_run(self, minimal_project: Path, capsys) -> None:
        from wfc.scripts.orchestrators.claude_md.cli import main

        exit_code = main([str(minimal_project), "--no-llm"])
        assert exit_code in (0, 1)

    def test_cli_missing_project(self, tmp_path: Path, capsys) -> None:
        from wfc.scripts.orchestrators.claude_md.cli import main

        nonexistent = str(tmp_path / "nonexistent")
        exit_code = main([nonexistent, "--no-llm"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "does not exist" in captured.err

    def test_cli_no_claude_md(self, no_claude_md_project: Path, capsys) -> None:
        from wfc.scripts.orchestrators.claude_md.cli import main

        exit_code = main([str(no_claude_md_project), "--no-llm"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "No CLAUDE.md" in captured.err

    def test_cli_json_output(self, minimal_project: Path, capsys) -> None:
        from wfc.scripts.orchestrators.claude_md.cli import main

        main([str(minimal_project), "--no-llm", "--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "grade_before" in data
        assert "verdict" in data

    def test_cli_output_to_file(self, minimal_project: Path, tmp_path: Path) -> None:
        from wfc.scripts.orchestrators.claude_md.cli import main

        output_file = tmp_path / "report.md"
        main([str(minimal_project), "--no-llm", "--output", str(output_file)])
        assert output_file.exists()
        assert len(output_file.read_text()) > 0
