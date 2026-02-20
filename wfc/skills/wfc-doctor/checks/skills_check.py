"""Agent Skills compliance checker."""

from pathlib import Path

from ..types import CheckResult


class SkillsChecker:
    """Check Agent Skills compliance for all WFC skills."""

    def check(self, auto_fix: bool = False) -> CheckResult:
        """
        Check Agent Skills compliance.

        - Counts skills in ~/.claude/skills/wfc-*
        - Validates YAML frontmatter
        - Checks for deprecated fields
        """

        issues = []
        fixes_applied = []

        skills_dir = Path.home() / ".claude" / "skills"
        if skills_dir.exists():
            wfc_skills = list(skills_dir.glob("wfc-*"))
            skill_count = len(wfc_skills)

            if skill_count != 30:
                issues.append(f"Expected 30 WFC skills, found {skill_count}")
        else:
            issues.append("~/.claude/skills/ directory not found")

        # TODO: Validate frontmatter format
        # TODO: Check for deprecated fields
        # TODO: Run skills-ref validate if available

        status = "FAIL" if issues else "PASS"

        return CheckResult(name="skills", status=status, issues=issues, fixes_applied=fixes_applied)
