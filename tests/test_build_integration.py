"""
Tests for WFC Build Integration

Verifies wfc-build integrates with WFC config, telemetry, and safety properties
"""

import pytest
from pathlib import Path
from wfc.shared.config.wfc_config import WFCConfig
from wfc.scripts.skills.build.orchestrator import BuildOrchestrator


class TestConfigIntegration:
    """Test wfc-build config integration"""

    def test_build_config_exists(self):
        """TEST-028: Build config section exists in defaults"""
        config = WFCConfig()
        config_dict = config.load()

        assert "build" in config_dict
        assert isinstance(config_dict["build"], dict)

    def test_build_config_values(self):
        """TEST-029: Build config has expected values"""
        config = WFCConfig()
        config_dict = config.load()
        build_config = config_dict["build"]

        assert build_config["max_questions"] == 5
        assert build_config["auto_assess_complexity"] is True
        assert build_config["dry_run_default"] is False
        assert build_config["xl_recommendation_threshold"] == 10

    def test_build_config_safety_properties(self):
        """TEST-030: Build config enforces safety properties"""
        config = WFCConfig()
        config_dict = config.load()
        build_config = config_dict["build"]

        # PROP-001: Quality gates enforced
        assert build_config["enforce_quality_gates"] is True

        # PROP-002: Consensus review enforced
        assert build_config["enforce_review"] is True

        # PROP-003: No auto-push to remote
        assert build_config["auto_push"] is False

        # PROP-007: TDD enforced
        assert build_config["enforce_tdd"] is True

    def test_build_config_performance_properties(self):
        """TEST-031: Build config has performance limits"""
        config = WFCConfig()
        config_dict = config.load()
        build_config = config_dict["build"]

        # PROP-008: Interview timeout <30s
        assert build_config["interview_timeout_seconds"] == 30

    def test_config_dot_notation_access(self):
        """TEST-032: Can access build config via dot notation"""
        config = WFCConfig()

        assert config.get("build.max_questions") == 5
        assert config.get("build.auto_assess_complexity") is True
        assert config.get("build.enforce_quality_gates") is True


class TestSafetyPropertyEnforcement:
    """Test safety property enforcement in orchestrator"""

    def setup_method(self):
        """Setup test fixtures"""
        self.orchestrator = BuildOrchestrator()

    def test_prop_001_never_bypass_quality(self):
        """TEST-033: PROP-001 - Never bypasses quality gates"""
        result = self.orchestrator.execute(
            feature_hint="Test feature",
            dry_run=False
        )

        if result.get("implementation"):
            impl = result["implementation"]
            assert impl.get("would_run_quality_gates") is True

    def test_prop_002_never_skip_review(self):
        """TEST-034: PROP-002 - Never skips consensus review"""
        result = self.orchestrator.execute(
            feature_hint="Test feature",
            dry_run=False
        )

        if result.get("implementation"):
            impl = result["implementation"]
            assert impl.get("would_run_consensus_review") is True

    def test_prop_003_never_auto_push(self):
        """TEST-035: PROP-003 - Never auto-pushes to remote"""
        result = self.orchestrator.execute(
            feature_hint="Test feature",
            dry_run=False
        )

        if result.get("implementation"):
            impl = result["implementation"]
            assert impl.get("would_push_to_remote") is False

    def test_prop_007_tdd_enforced(self):
        """TEST-036: PROP-007 - TDD workflow enforced"""
        result = self.orchestrator.execute(
            feature_hint="Test feature",
            dry_run=False
        )

        if result.get("implementation"):
            impl = result["implementation"]
            assert impl.get("would_enforce_tdd") is True


class TestDocumentationIntegration:
    """Test documentation reflects wfc-build integration"""

    def test_skill_in_readme(self):
        """TEST-037: wfc-build is documented in README"""
        readme_path = Path(__file__).parent.parent / "README.md"
        content = readme_path.read_text()

        assert "wfc-build" in content
        assert "Quick feature builder" in content

    def test_skill_in_claude_md(self):
        """TEST-038: wfc-build is documented in CLAUDE.md"""
        claude_md_path = Path(__file__).parent.parent / "CLAUDE.md"
        content = claude_md_path.read_text()

        assert "/wfc-build" in content
        assert "Intentional Vibe" in content or "quick" in content.lower()


class TestSkillInstallation:
    """Test skill files are properly installed"""

    def test_skill_md_exists(self):
        """TEST-039: SKILL.md exists"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        assert skill_path.exists(), "SKILL.md must be installed"

    def test_skill_has_executable_code(self):
        """TEST-040: SKILL.md has executable CLI code"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()

        assert "#!/usr/bin/env python3" in content
        assert "BuildOrchestrator" in content
        assert "def main():" in content

    def test_skill_has_usage_examples(self):
        """TEST-041: SKILL.md has usage examples"""
        skill_path = Path.home() / ".claude/skills/wfc-build/SKILL.md"
        content = skill_path.read_text()

        assert "/wfc-build" in content
        assert "Usage" in content or "usage" in content
