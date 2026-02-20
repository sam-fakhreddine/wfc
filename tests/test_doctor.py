"""Tests for wfc-doctor skill - file structure validation."""

from pathlib import Path


class TestDoctorStructure:
    """Test that wfc-doctor has correct structure."""

    def test_skill_md_exists(self):
        """Test SKILL.md exists."""
        skill_path = Path(__file__).parent.parent / "wfc" / "skills" / "wfc-doctor" / "SKILL.md"
        assert skill_path.exists()

    def test_check_modules_exist(self):
        """Test all check modules exist."""
        checks_dir = Path(__file__).parent.parent / "wfc" / "skills" / "wfc-doctor" / "checks"
        assert (checks_dir / "skills_check.py").exists()
        assert (checks_dir / "prompts_check.py").exists()
        assert (checks_dir / "settings_check.py").exists()
        assert (checks_dir / "hooks_check.py").exists()
        assert (checks_dir / "precommit_check.py").exists()
