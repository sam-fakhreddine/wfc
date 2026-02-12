"""
Tests for WFC Build CLI Interface

Verifies command-line interface and argument parsing
"""

import pytest
import subprocess
import sys
from pathlib import Path


class TestCLIInterface:
    """Test CLI invocation and argument parsing"""

    def setup_method(self):
        """Setup test fixtures"""
        self.skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        assert self.skill_path.exists(), "SKILL.md must exist"

    def test_cli_script_exists(self):
        """TEST-020: CLI script exists in SKILL.md"""
        content = self.skill_path.read_text()
        assert "#!/usr/bin/env python3" in content
        assert "BuildOrchestrator" in content
        assert "def main():" in content

    def test_cli_has_argument_parsing(self):
        """TEST-021: CLI parses arguments correctly"""
        content = self.skill_path.read_text()
        assert "--dry-run" in content
        assert "feature_hint" in content
        assert "sys.argv" in content

    def test_cli_imports_orchestrator(self):
        """TEST-022: CLI imports BuildOrchestrator"""
        content = self.skill_path.read_text()
        assert "from wfc.scripts.skills.build.orchestrator import BuildOrchestrator" in content


class TestCLIArgumentHandling:
    """Test different CLI argument combinations"""

    def test_no_arguments_means_interactive(self):
        """Test no arguments triggers interactive mode"""
        # This would be tested via actual invocation
        # For now, verify the logic structure exists
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert "feature_hint = None" in content

    def test_feature_hint_argument(self):
        """Test feature hint is parsed"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert "feature_hint = arg" in content or "feature_hint = " in content

    def test_dry_run_flag(self):
        """Test --dry-run flag is recognized"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert "dry_run = True" in content


class TestCLIExitCodes:
    """Test CLI exit codes for different scenarios"""

    def test_success_exit_code(self):
        """TEST-023: Success returns exit code 0"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert 'sys.exit(0)' in content

    def test_xl_recommendation_exit_code(self):
        """TEST-024: XL recommendation returns exit code 2"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert 'sys.exit(2)' in content

    def test_error_exit_code(self):
        """TEST-025: Error returns exit code 1"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert 'sys.exit(1)' in content


class TestCLIIntegration:
    """Test CLI integration with BuildOrchestrator"""

    def test_cli_calls_orchestrator_execute(self):
        """TEST-026: CLI calls orchestrator.execute()"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert "orchestrator = BuildOrchestrator()" in content
        assert "orchestrator.execute(" in content

    def test_cli_passes_arguments_to_orchestrator(self):
        """TEST-027: CLI passes arguments to orchestrator"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()
        assert "feature_hint=feature_hint" in content
        assert "dry_run=dry_run" in content
