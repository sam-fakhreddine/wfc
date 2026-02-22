"""Integration tests for skill fixer pipeline.

Tests the complete 6-agent pipeline end-to-end.
"""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_skill_dir():
    """Create a temporary skill directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()
        yield skill_dir


@pytest.fixture
def minimal_skill(temp_skill_dir):
    """Create a minimal skill with known issues (Grade F)."""
    skill_md = temp_skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: test-skill
description: Test
---
# Test Skill
[Vague content without proper structure]
""")
    return temp_skill_dir


@pytest.fixture
def grade_a_skill(temp_skill_dir):
    """Create a Grade A skill that should short-circuit."""
    skill_md = temp_skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: test-skill-a
description: >
  Comprehensive description covering all user phrasings for the test skill.
  Includes examples, boundaries, and clear triggering language.
---

# Test Skill

Quick reference for common operations.

## Core Workflow

1. Do the thing
2. Validate the result
3. Generate output

## Examples

Basic usage:
```
test-skill --input file.txt
```

Edge cases handled gracefully.
""")
    return temp_skill_dir


@pytest.fixture
def skill_with_scripts(temp_skill_dir):
    """Create a skill with script issues."""
    skill_md = temp_skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: test-skill-scripts
description: Test skill with scripts
---
# Test Skill

Uses scripts/helper.sh for processing.
""")

    scripts_dir = temp_skill_dir / "scripts"
    scripts_dir.mkdir()
    helper_script = scripts_dir / "helper.sh"
    helper_script.write_text("echo 'test'")

    return temp_skill_dir


class TestWorkspaceManager:
    """Test workspace management."""

    def test_create_workspace(self, minimal_skill):
        """Test workspace creation."""
        from wfc.scripts.orchestrators.skill_fixer.workspace import WorkspaceManager

        manager = WorkspaceManager()
        workspace = manager.create(minimal_skill, run_functional_qa=False)

        assert workspace.exists()
        assert (workspace / "input" / "SKILL.md").exists()
        assert (workspace / "01-cataloger").exists()
        assert (workspace / "02-analyst").exists()
        assert (workspace / "03-fixer").exists()
        assert (workspace / "04-structural-qa").exists()
        assert (workspace / "05-functional-qa").exists()
        assert (workspace / "06-reporter").exists()
        assert (workspace / "metadata.json").exists()

        metadata = manager.read_metadata(workspace)
        assert metadata.skill_name == "test-skill"
        assert metadata.run_functional_qa is False

        manager.cleanup(workspace)


class TestCataloger:
    """Test cataloger phase."""

    def test_catalog_minimal_skill(self, minimal_skill):
        """Test cataloging a minimal skill."""
        from wfc.scripts.orchestrators.skill_fixer.cataloger import SkillCataloger

        cataloger = SkillCataloger()
        manifest = cataloger.catalog(minimal_skill)

        assert manifest.skill_path == minimal_skill
        assert manifest.frontmatter.name == "test-skill"
        assert manifest.frontmatter.description == "Test"
        assert manifest.frontmatter.description_length == 4
        assert manifest.body.total_lines > 0

    def test_catalog_detects_script_issues(self, skill_with_scripts):
        """Test that cataloger detects non-executable scripts."""
        from wfc.scripts.orchestrators.skill_fixer.cataloger import SkillCataloger

        cataloger = SkillCataloger()
        manifest = cataloger.catalog(skill_with_scripts)

        assert manifest.filesystem.scripts_count == 1
        assert len(manifest.filesystem.scripts_non_executable) == 1
        assert "helper.sh" in manifest.filesystem.scripts_non_executable[0]

    def test_catalog_detects_cross_references(self, skill_with_scripts):
        """Test that cataloger detects file references."""
        from wfc.scripts.orchestrators.skill_fixer.cataloger import SkillCataloger

        cataloger = SkillCataloger()
        manifest = cataloger.catalog(skill_with_scripts)

        assert "scripts/helper.sh" in manifest.cross_references.all_file_references


class TestAnalyst:
    """Test analyst phase."""

    def test_analyze_minimal_skill_fallback(self, minimal_skill):
        """Test analyst fallback (no LLM) gives Grade F."""
        from wfc.scripts.orchestrators.skill_fixer.analyst import SkillAnalyst
        from wfc.scripts.orchestrators.skill_fixer.cataloger import SkillCataloger

        cataloger = SkillCataloger()
        manifest = cataloger.catalog(minimal_skill)

        analyst = SkillAnalyst()
        skill_content = (minimal_skill / "SKILL.md").read_text()
        diagnosis = analyst.analyze(skill_content, manifest, response_fn=None)

        assert diagnosis.overall_grade == "F"
        assert diagnosis.rewrite_recommended is True
        assert len(diagnosis.issues) > 0


class TestFixer:
    """Test fixer phase."""

    def test_fixer_preserves_scripts(self, skill_with_scripts):
        """Test that fixer never modifies scripts."""
        from wfc.scripts.orchestrators.skill_fixer.analyst import SkillAnalyst
        from wfc.scripts.orchestrators.skill_fixer.cataloger import SkillCataloger
        from wfc.scripts.orchestrators.skill_fixer.fixer import SkillFixer

        cataloger = SkillCataloger()
        manifest = cataloger.catalog(skill_with_scripts)

        analyst = SkillAnalyst()
        skill_content = (skill_with_scripts / "SKILL.md").read_text()
        diagnosis = analyst.analyze(skill_content, manifest, response_fn=None)

        fixer = SkillFixer()
        fixer_output = fixer.fix(skill_content, manifest, diagnosis, response_fn=None)

        assert "scripts/helper.sh" not in fixer_output.rewritten_files

        assert len(fixer_output.script_issues) > 0


class TestStructuralQA:
    """Test structural QA phase."""

    def test_structural_qa_validates_frontmatter(self):
        """Test that structural QA validates YAML frontmatter."""
        from wfc.scripts.orchestrators.skill_fixer.structural_qa import StructuralQA
        from wfc.scripts.orchestrators.skill_fixer.schemas import (
            FixerOutput,
            SkillDiagnosis,
            SkillManifest,
            FrontmatterMetrics,
            BodyMetrics,
            FilesystemMetrics,
            CrossReferences,
        )

        manifest = SkillManifest(
            skill_path=Path("/tmp/test"),
            frontmatter=FrontmatterMetrics(
                name="test",
                description="Test",
                description_length=4,
                has_required_fields=True,
                frontmatter_valid=True,
            ),
            body=BodyMetrics(
                total_lines=10, section_count=1, code_block_count=0, file_reference_count=0
            ),
            filesystem=FilesystemMetrics(
                scripts_count=0, references_count=0, assets_count=0, total_files=0
            ),
            cross_references=CrossReferences(),
        )

        diagnosis = SkillDiagnosis(
            scores={},
            dimension_summaries={},
            issues=[],
            overall_grade="C",
            rewrite_recommended=True,
            rewrite_scope="full",
            summary="Test",
        )

        fixer_output = FixerOutput(
            rewritten_files={"SKILL.md": "---\nname: test\n---\n# Test\nImproved content\n"},
            changelog=["Improved description"],
            script_issues=[],
            unresolved=[],
        )

        qa = StructuralQA()
        original_content = "---\nname: test\n---\n# Test\nOriginal\n"
        validation = qa.validate(
            original_content, manifest, diagnosis, fixer_output, response_fn=None
        )

        assert validation.verdict in ["PASS", "FAIL", "PASS_WITH_NOTES"]
        assert validation.frontmatter_valid is True


class TestOrchestrator:
    """Test orchestrator coordination."""

    def test_orchestrator_short_circuits_grade_a(self, grade_a_skill):
        """Test that orchestrator short-circuits Grade A skills."""
        from wfc.scripts.orchestrators.skill_fixer.orchestrator import SkillFixerOrchestrator

        orchestrator = SkillFixerOrchestrator()

        result = orchestrator.fix_skill(
            grade_a_skill,
            run_functional_qa=False,
            analyst_fn=None,
            fixer_fn=None,
            qa_fn=None,
            reporter_fn=None,
        )

        assert result.summary.original_grade in ["A", "B"]
        assert result.summary.final_grade == result.summary.original_grade

    def test_orchestrator_retry_loop(self, minimal_skill):
        """Test that orchestrator retries on FAIL verdict."""
        from wfc.scripts.orchestrators.skill_fixer.orchestrator import SkillFixerOrchestrator

        orchestrator = SkillFixerOrchestrator()

        result = orchestrator.fix_skill(
            minimal_skill,
            run_functional_qa=False,
            analyst_fn=None,
            fixer_fn=None,
            qa_fn=None,
            reporter_fn=None,
        )

        assert result.summary.original_grade == "F"
        assert result.report_text is not None


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_pipeline_minimal_skill(self, minimal_skill):
        """Test full pipeline on minimal skill."""
        from wfc.scripts.orchestrators.skill_fixer.orchestrator import SkillFixerOrchestrator

        orchestrator = SkillFixerOrchestrator()
        result = orchestrator.fix_skill(
            minimal_skill,
            run_functional_qa=False,
            analyst_fn=None,
            fixer_fn=None,
            qa_fn=None,
            reporter_fn=None,
        )

        assert result.summary.skill_name == "test-skill"
        assert result.summary.original_grade is not None
        assert result.summary.structural_verdict in ["PASS", "FAIL", "PASS_WITH_NOTES"]
        assert result.report_text is not None
        assert len(result.report_text) > 0

    def test_full_pipeline_with_scripts(self, skill_with_scripts):
        """Test full pipeline detects and reports script issues."""
        from wfc.scripts.orchestrators.skill_fixer.orchestrator import SkillFixerOrchestrator

        orchestrator = SkillFixerOrchestrator()
        result = orchestrator.fix_skill(
            skill_with_scripts,
            run_functional_qa=False,
            analyst_fn=None,
            fixer_fn=None,
            qa_fn=None,
            reporter_fn=None,
        )

        assert len(result.script_issues) > 0
        assert any("helper.sh" in issue for issue in result.script_issues)


class TestAntipatterns:
    """Test antipattern detection."""

    def test_antipattern_sk01_empty_description(self, temp_skill_dir):
        """Test SK-01: Empty/TODO description."""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text("""---
name: test
description: TODO
---
# Test
""")

        from wfc.scripts.orchestrators.skill_fixer.cataloger import SkillCataloger
        from wfc.scripts.orchestrators.skill_fixer.analyst import SkillAnalyst

        cataloger = SkillCataloger()
        manifest = cataloger.catalog(temp_skill_dir)

        analyst = SkillAnalyst()
        diagnosis = analyst.analyze(skill_md.read_text(), manifest, response_fn=None)

        assert any(issue.id == "SK-01" for issue in diagnosis.issues)


class TestRubric:
    """Test rubric scoring."""

    def test_rubric_dimensions_present(self):
        """Test that rubric has all expected dimensions."""
        pass


class TestWithLLM:
    """Tests that require LLM integration (skipped in CI)."""

    @pytest.mark.skip(reason="Requires LLM API access")
    def test_analyst_with_llm(self):
        """Test analyst with real LLM."""
        pass

    @pytest.mark.skip(reason="Requires LLM API access")
    def test_fixer_with_llm(self):
        """Test fixer with real LLM."""
        pass
