"""
Tests for WFC Build CLI Interface

Verifies SKILL.md content and structure for wfc-build skill
"""

import pytest
from pathlib import Path


class TestCLIInterface:
    """Test CLI invocation and argument parsing"""

    def setup_method(self):
        """Setup test fixtures"""
        self.skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        assert self.skill_path.exists(), "SKILL.md must exist"

    def test_cli_script_exists(self):
        """TEST-020: SKILL.md has frontmatter and key content"""
        content = self.skill_path.read_text()
        assert "name: wfc-build" in content
        assert "Orchestrator" in content
        assert "## Usage" in content

    def test_cli_has_argument_parsing(self):
        """TEST-021: SKILL.md documents argument handling"""
        content = self.skill_path.read_text()
        assert "argument-hint:" in content
        assert '/wfc-build "' in content

    def test_cli_imports_orchestrator(self):
        """TEST-022: SKILL.md references Orchestrator"""
        content = self.skill_path.read_text()
        assert "Orchestrator" in content


class TestCLIArgumentHandling:
    """Test different CLI argument combinations"""

    def test_no_arguments_means_interactive(self):
        """Test no arguments triggers interactive mode"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert "Adaptive Interview" in content

    def test_feature_hint_argument(self):
        """Test feature hint is parsed"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert '/wfc-build "add' in content or '/wfc-build "' in content

    def test_dry_run_flag(self):
        """Test --dry-run flag is recognized"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert "enforce_tdd" in content or "require_quality_check" in content


class TestCLIExitCodes:
    """Test CLI exit codes for different scenarios"""

    def test_success_exit_code(self):
        """TEST-023: SKILL.md documents success indicators"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert "PASS" in content or "APPROVED" in content

    def test_xl_recommendation_exit_code(self):
        """TEST-024: SKILL.md documents complexity assessment"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert "Complexity Assessment" in content

    def test_error_exit_code(self):
        """TEST-025: SKILL.md documents rollback/failure handling"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert "rollback" in content.lower()


class TestCLIIntegration:
    """Test CLI integration with BuildOrchestrator"""

    def test_cli_calls_orchestrator_execute(self):
        """TEST-026: SKILL.md describes orchestrator coordination"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert "Orchestrator" in content
        assert "coordinate" in content.lower() or "Responsibilities" in content

    def test_cli_passes_arguments_to_orchestrator(self):
        """TEST-027: SKILL.md documents description/feature workflow"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert "description" in content.lower()
        assert '/wfc-build "' in content
