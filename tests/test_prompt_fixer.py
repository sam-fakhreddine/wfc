"""Tests for wfc-prompt-fixer skill - file structure validation."""

import json
from pathlib import Path


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
