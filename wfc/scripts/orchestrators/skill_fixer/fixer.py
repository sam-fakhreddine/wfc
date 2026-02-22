"""Fixer agent - LLM rewriting with fallback.

NEVER modifies scripts - only flags issues for human review.
"""

import re
from typing import Callable, Dict, List, Optional

from .prompts import prepare_fixer_prompt
from .schemas import FixerOutput, SkillDiagnosis, SkillManifest


class SkillFixer:
    """
    Rewrites skills to fix diagnosed issues.

    CRITICAL: NEVER modifies scripts - only SKILL.md and references/.
    """

    def fix(
        self,
        skill_content: str,
        manifest: SkillManifest,
        diagnosis: SkillDiagnosis,
        revision_notes: Optional[str] = None,
        response_fn: Optional[Callable[[str], str]] = None,
    ) -> FixerOutput:
        """
        Fix skill based on diagnosis.

        Args:
            skill_content: Original SKILL.md content
            manifest: Cataloger manifest
            diagnosis: Analyst diagnosis
            revision_notes: Optional revision notes from failed QA
            response_fn: Optional LLM response function

        Returns:
            FixerOutput with rewritten files
        """
        if response_fn:
            return self._fix_with_llm(
                skill_content, manifest, diagnosis, revision_notes, response_fn
            )
        else:
            return self._fix_fallback(skill_content, manifest, diagnosis)

    def _fix_with_llm(
        self,
        skill_content: str,
        manifest: SkillManifest,
        diagnosis: SkillDiagnosis,
        revision_notes: Optional[str],
        response_fn: Callable[[str], str],
    ) -> FixerOutput:
        """Fix with LLM."""
        prompt = prepare_fixer_prompt(str(manifest.skill_path), revision_notes or "")

        response = response_fn(prompt)

        rewritten_files = self._extract_files_from_response(response)

        changelog = self._extract_changelog_from_response(response)

        script_issues = []
        for issue in diagnosis.issues:
            if "SCRIPT" in issue.dimension.upper() or any(
                "script" in str(e).lower() for e in issue.evidence
            ):
                script_issues.append(f"{issue.id}: {issue.description} - {issue.fix_directive}")

        unresolved = []
        if not rewritten_files:
            unresolved.append("LLM did not generate any rewritten files")

        return FixerOutput(
            rewritten_files=rewritten_files,
            changelog=changelog if changelog else ["LLM rewrite completed"],
            script_issues=script_issues,
            unresolved=unresolved,
        )

    def _fix_fallback(
        self, skill_content: str, manifest: SkillManifest, diagnosis: SkillDiagnosis
    ) -> FixerOutput:
        """Fallback minimal fixes."""
        rewritten_files: Dict[str, str] = {}
        changelog: List[str] = []
        script_issues: List[str] = []
        unresolved: List[str] = []

        desc = manifest.frontmatter.description
        if manifest.frontmatter.description_length < 50:
            expanded_desc = (
                f"{desc}. Comprehensive skill for handling {manifest.frontmatter.name} operations."
            )
            skill_content = skill_content.replace(
                f"description: {desc}", f"description: {expanded_desc}"
            )
            changelog.append("Expanded description to meet minimum length")

        elif manifest.frontmatter.description_length > 1024:
            truncated_desc = desc[:1020] + "..."
            skill_content = skill_content.replace(
                f"description: {desc}", f"description: {truncated_desc}"
            )
            changelog.append("Truncated description to fit 1024 char limit")

        for phantom in manifest.cross_references.referenced_but_missing:
            if phantom in skill_content:
                skill_content = skill_content.replace(phantom, "[removed: file not found]")
                changelog.append(f"Removed phantom reference: {phantom}")

        if manifest.filesystem.scripts_non_executable:
            for script in manifest.filesystem.scripts_non_executable:
                script_issues.append(f"{script}: Add execute permission (chmod +x)")

        if manifest.filesystem.scripts_missing_shebang:
            for script in manifest.filesystem.scripts_missing_shebang:
                if script not in [s.split(":")[0] for s in script_issues]:
                    script_issues.append(
                        f"{script}: Add shebang line (#!/bin/bash or #!/usr/bin/env python3)"
                    )

        # Note unresolved complex issues
        for issue in diagnosis.issues:
            if issue.severity == "critical" and issue.id not in [
                "SK-01",
                "SK-02",
                "SK-03",
                "SK-08",
            ]:
                unresolved.append(f"{issue.id}: {issue.description} - requires manual review")

        rewritten_files["SKILL.md"] = skill_content

        if not changelog:
            changelog.append("No automated fixes applied (fallback mode)")

        return FixerOutput(
            rewritten_files=rewritten_files,
            changelog=changelog,
            script_issues=script_issues,
            unresolved=unresolved,
        )

    def _extract_files_from_response(self, response: str) -> Dict[str, str]:
        """Extract rewritten files from LLM response."""
        files = {}

        pattern = r"```(\S+\.md)\n(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)

        for filename, content in matches:
            files[filename] = content.strip()

        return files

    def _extract_changelog_from_response(self, response: str) -> List[str]:
        """Extract changelog from LLM response."""
        lines = response.split("\n")
        changelog = []

        in_changelog = False
        for line in lines:
            if "changelog" in line.lower() or "changes" in line.lower():
                in_changelog = True
                continue

            if in_changelog:
                match = re.match(r"^\d+\.\s+(.+)$", line.strip())
                if match:
                    changelog.append(match.group(1))
                elif line.strip() and not line.strip().startswith("#"):
                    if line.startswith("##"):
                        break

        return changelog
