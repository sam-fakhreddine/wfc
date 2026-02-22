"""Structural QA - adversarial validation with retry support."""

from typing import Callable, Optional

import yaml

from .schemas import (
    FixerOutput,
    IssueResolution,
    Regression,
    SkillDiagnosis,
    SkillManifest,
    StructuralIssue,
    ValidationResult,
)


class StructuralQA:
    """
    Validates fixes against structural requirements.

    Uses rule-based checks + optional LLM validation.
    """

    def validate(
        self,
        original_content: str,
        manifest: SkillManifest,
        diagnosis: SkillDiagnosis,
        fixer_output: FixerOutput,
        response_fn: Optional[Callable[[str], str]] = None,
    ) -> ValidationResult:
        """
        Validate fixer output.

        Args:
            original_content: Original SKILL.md
            manifest: Cataloger manifest
            diagnosis: Analyst diagnosis
            fixer_output: Fixer output
            response_fn: Optional LLM for deeper validation

        Returns:
            ValidationResult with verdict
        """
        rewritten_content = fixer_output.rewritten_files.get("SKILL.md", "")

        frontmatter_valid = self._validate_frontmatter(rewritten_content)

        intent_preserved = self._check_intent_preserved(original_content, rewritten_content)

        issues_resolved = self._check_issue_resolution(diagnosis, fixer_output)

        regressions = self._check_regressions(manifest, rewritten_content)

        structural_issues = self._check_structural_issues(rewritten_content)

        original_lines = len(original_content.split("\n"))
        rewritten_lines = (
            len(rewritten_content.split("\n")) if rewritten_content else original_lines
        )

        original_desc_len = manifest.frontmatter.description_length
        rewritten_desc_len = self._extract_description_length(rewritten_content)

        verdict = "PASS"
        revision_notes = None

        if not frontmatter_valid:
            verdict = "FAIL"
            revision_notes = "Frontmatter is invalid - fix YAML syntax and required fields"

        elif not intent_preserved:
            verdict = "FAIL"
            revision_notes = "Original intent not preserved - rewrite maintains core purpose"

        elif any(r.severity == "critical" for r in regressions):
            verdict = "FAIL"
            revision_notes = f"Critical regression: {regressions[0].description}"

        elif issues_resolved.resolution_rate < 0.5 and issues_resolved.critical_total > 0:
            verdict = "FAIL"
            revision_notes = "Less than 50% of critical/major issues resolved"

        elif rewritten_lines > 700:
            verdict = "FAIL"
            revision_notes = "SKILL.md exceeds 700 lines - extract content to references/"

        elif rewritten_desc_len > 1024:
            verdict = "FAIL"
            revision_notes = "Description exceeds 1024 characters"

        elif regressions or structural_issues:
            verdict = "PASS_WITH_NOTES"

        if verdict == "FAIL":
            final_recommendation = "revise"
        elif any(r.severity == "major" for r in regressions):
            final_recommendation = "escalate_to_human"
        else:
            final_recommendation = "ship"

        return ValidationResult(
            verdict=verdict,
            frontmatter_valid=frontmatter_valid,
            intent_preserved=intent_preserved,
            issues_resolved=issues_resolved,
            regressions=regressions,
            structural_issues=structural_issues,
            line_count={"original": original_lines, "rewritten": rewritten_lines},
            description_length={"original": original_desc_len, "rewritten": rewritten_desc_len},
            final_recommendation=final_recommendation,
            revision_notes=revision_notes,
        )

    def _validate_frontmatter(self, content: str) -> bool:
        """Validate YAML frontmatter."""
        try:
            if not content.startswith("---\n"):
                return False

            end_pos = content.find("\n---\n", 4)
            if end_pos == -1:
                return False

            frontmatter_text = content[4:end_pos]
            data = yaml.safe_load(frontmatter_text)

            if not isinstance(data, dict):
                return False

            if "name" not in data or "description" not in data:
                return False

            return True
        except Exception:
            return False

    def _check_intent_preserved(self, original: str, rewritten: str) -> bool:
        """Check if original intent is preserved (heuristic)."""
        if not rewritten:
            return False

        original_name = self._extract_name(original)
        rewritten_name = self._extract_name(rewritten)

        if original_name != rewritten_name:
            return False

        original_sections = set(
            line.strip()
            for line in original.split("\n")
            if line.strip().startswith("#") and not line.strip().startswith("##")
        )

        rewritten_sections = set(
            line.strip()
            for line in rewritten.split("\n")
            if line.strip().startswith("#") and not line.strip().startswith("##")
        )

        if original_sections:
            overlap = len(original_sections & rewritten_sections)
            preservation_rate = overlap / len(original_sections)
            return preservation_rate >= 0.5

        return True

    def _check_issue_resolution(
        self, diagnosis: SkillDiagnosis, fixer_output: FixerOutput
    ) -> IssueResolution:
        """Check how many issues were resolved."""
        critical_issues = [i for i in diagnosis.issues if i.severity == "critical"]
        major_issues = [i for i in diagnosis.issues if i.severity == "major"]
        minor_issues = [i for i in diagnosis.issues if i.severity == "minor"]

        changelog_text = " ".join(fixer_output.changelog).lower()

        critical_resolved = sum(1 for i in critical_issues if i.id.lower() in changelog_text)
        major_resolved = sum(1 for i in major_issues if i.id.lower() in changelog_text)
        minor_resolved = sum(1 for i in minor_issues if i.id.lower() in changelog_text)

        total_resolved = critical_resolved + major_resolved + minor_resolved
        total_issues = len(diagnosis.issues)

        resolution_rate = total_resolved / total_issues if total_issues > 0 else 1.0

        return IssueResolution(
            critical_resolved=critical_resolved,
            critical_total=len(critical_issues),
            major_resolved=major_resolved,
            major_total=len(major_issues),
            minor_resolved=minor_resolved,
            minor_total=len(minor_issues),
            resolution_rate=resolution_rate,
        )

    def _check_regressions(self, manifest: SkillManifest, rewritten: str) -> list[Regression]:
        """Check for regressions introduced by rewrite."""
        regressions = []

        new_refs = self._extract_file_references(rewritten)
        for ref in new_refs:
            if ref not in manifest.cross_references.all_file_references:
                if ref not in manifest.cross_references.all_present_files:
                    regressions.append(
                        Regression(
                            severity="major",
                            description=f"New phantom reference introduced: {ref}",
                            location="body",
                        )
                    )

        if not self._validate_frontmatter(rewritten):
            regressions.append(
                Regression(
                    severity="critical",
                    description="Frontmatter broken by rewrite",
                    location="frontmatter",
                )
            )

        return regressions

    def _check_structural_issues(self, content: str) -> list[StructuralIssue]:
        """Check for structural issues."""
        issues = []

        lines = content.split("\n")
        line_count = len(lines)

        if line_count > 700:
            issues.append(
                StructuralIssue(
                    category="length",
                    description=f"SKILL.md too long: {line_count} lines",
                    severity="major",
                )
            )

        desc_len = self._extract_description_length(content)
        if desc_len > 1024:
            issues.append(
                StructuralIssue(
                    category="description",
                    description=f"Description too long: {desc_len} chars",
                    severity="critical",
                )
            )

        return issues

    def _extract_name(self, content: str) -> str:
        """Extract name from frontmatter."""
        try:
            if content.startswith("---\n"):
                end_pos = content.find("\n---\n", 4)
                if end_pos != -1:
                    frontmatter_text = content[4:end_pos]
                    data = yaml.safe_load(frontmatter_text)
                    return data.get("name", "")
        except Exception:
            pass
        return ""

    def _extract_description_length(self, content: str) -> int:
        """Extract description length from frontmatter."""
        try:
            if content.startswith("---\n"):
                end_pos = content.find("\n---\n", 4)
                if end_pos != -1:
                    frontmatter_text = content[4:end_pos]
                    data = yaml.safe_load(frontmatter_text)
                    desc = data.get("description", "")
                    return len(desc)
        except Exception:
            pass
        return 0

    def _extract_file_references(self, content: str) -> list[str]:
        """Extract file references from content."""
        import re

        refs = re.findall(
            r"(?:scripts|references|assets)/([\w\-./]+\.\w+)",
            content,
            re.IGNORECASE,
        )
        return list(set(refs))
