"""Reporter agent - generates deliverable summaries."""

from typing import Callable, Optional

from .schemas import (
    FixerOutput,
    FunctionalQAResult,
    ReportSummary,
    SkillDiagnosis,
    SkillFixReport,
    SkillManifest,
    ValidationResult,
)


class SkillReporter:
    """
    Generates human-readable reports from pipeline outputs.

    Uses LLM if available, otherwise rule-based formatting.
    """

    def generate_report(
        self,
        manifest: SkillManifest,
        diagnosis: SkillDiagnosis,
        fixer_output: Optional[FixerOutput],
        validation: Optional[ValidationResult],
        functional_qa: Optional[FunctionalQAResult] = None,
        response_fn: Optional[Callable[[str], str]] = None,
    ) -> SkillFixReport:
        """
        Generate final report.

        Args:
            manifest: Cataloger manifest
            diagnosis: Analyst diagnosis
            fixer_output: Fixer output (None if Grade A)
            validation: Structural QA validation (None if Grade A)
            functional_qa: Optional functional QA results
            response_fn: Optional LLM for narrative generation

        Returns:
            SkillFixReport with complete summary
        """
        skill_name = manifest.frontmatter.name
        original_grade = diagnosis.overall_grade

        if fixer_output is None:
            return self._generate_no_changes_report(manifest, diagnosis)

        if validation:
            if validation.verdict == "PASS":
                final_grade = self._estimate_grade_after(validation, diagnosis)
            else:
                final_grade = original_grade
        else:
            final_grade = original_grade

        summary = ReportSummary(
            skill_name=skill_name,
            original_grade=original_grade,
            final_grade=final_grade,
            structural_verdict=validation.verdict if validation else "NOT_RUN",
            functional_verdict=functional_qa.verdict if functional_qa else "NOT_RUN",
            original_line_count=validation.line_count["original"] if validation else 0,
            rewritten_line_count=validation.line_count["rewritten"] if validation else 0,
            original_description_length=(
                validation.description_length["original"] if validation else 0
            ),
            rewritten_description_length=(
                validation.description_length["rewritten"] if validation else 0
            ),
        )

        triggering_changes = self._extract_triggering_changes(fixer_output, diagnosis)

        structural_changes = fixer_output.changelog[:5]

        report_text = self._format_report(
            summary, triggering_changes, structural_changes, fixer_output, validation, functional_qa
        )

        return SkillFixReport(
            summary=summary,
            triggering_changes=triggering_changes,
            structural_changes=structural_changes,
            script_issues=fixer_output.script_issues,
            unresolved_items=fixer_output.unresolved,
            rewritten_files=fixer_output.rewritten_files,
            report_text=report_text,
        )

    def _generate_no_changes_report(
        self, manifest: SkillManifest, diagnosis: SkillDiagnosis
    ) -> SkillFixReport:
        """Generate report for Grade A skills (no changes needed)."""
        summary = ReportSummary(
            skill_name=manifest.frontmatter.name,
            original_grade="A",
            final_grade="A",
            structural_verdict="PASS",
            functional_verdict="NOT_RUN",
            original_line_count=manifest.body.total_lines,
            rewritten_line_count=manifest.body.total_lines,
            original_description_length=manifest.frontmatter.description_length,
            rewritten_description_length=manifest.frontmatter.description_length,
        )

        report_text = f"""# Skill Fix Report: {manifest.frontmatter.name}

## Summary
- Skill: {manifest.frontmatter.name}
- Original grade: A → Final grade: A
- Structural verdict: PASS
- Functional verdict: NOT_RUN
- Line count: {manifest.body.total_lines} (unchanged)
- Description: {manifest.frontmatter.description_length} chars (unchanged)

## Result
✅ **No changes needed** - Skill is already Grade A.

{diagnosis.summary}
"""

        return SkillFixReport(
            summary=summary,
            triggering_changes="No changes needed (Grade A)",
            structural_changes=[],
            script_issues=[],
            unresolved_items=[],
            rewritten_files={},
            report_text=report_text,
        )

    def _extract_triggering_changes(
        self, fixer_output: FixerOutput, diagnosis: SkillDiagnosis
    ) -> str:
        """Extract description/triggering changes."""
        triggering_issues = [
            i for i in diagnosis.issues if "TRIGGER" in i.dimension or "DESCRIPTION" in i.dimension
        ]

        if not triggering_issues:
            return "No triggering changes needed"

        changes = []
        for issue in triggering_issues:
            if issue.id in " ".join(fixer_output.changelog):
                changes.append(f"- {issue.fix_directive}")

        if not changes:
            return "No triggering changes made"

        return "\n".join(changes)

    def _estimate_grade_after(self, validation: ValidationResult, diagnosis: SkillDiagnosis) -> str:
        """Estimate grade after fixes."""
        if (
            validation.issues_resolved.resolution_rate > 0.8
            and not validation.regressions
            and validation.line_count["rewritten"] < 500
        ):
            return "A"
        elif validation.issues_resolved.resolution_rate > 0.6:
            return "B"
        else:
            return "C"

    def _format_report(
        self,
        summary: ReportSummary,
        triggering_changes: str,
        structural_changes: list[str],
        fixer_output: FixerOutput,
        validation: Optional[ValidationResult],
        functional_qa: Optional[FunctionalQAResult],
    ) -> str:
        """Format complete report."""
        report = f"""# Skill Fix Report: {summary.skill_name}

## Summary
- Skill: {summary.skill_name}
- Original grade: {summary.original_grade} → Final grade: {summary.final_grade}
- Structural verdict: {summary.structural_verdict}
- Functional verdict: {summary.functional_verdict}
- Line count: {summary.original_line_count} → {summary.rewritten_line_count}
- Description: {summary.original_description_length} → {summary.rewritten_description_length} chars

## Triggering Changes
{triggering_changes}

## Structural Changes
"""

        if structural_changes:
            for i, change in enumerate(structural_changes, 1):
                report += f"{i}. {change}\n"
        else:
            report += "None\n"

        report += "\n## Script Issues (Human Action Required)\n"
        if fixer_output.script_issues:
            for issue in fixer_output.script_issues:
                report += f"- {issue}\n"
        else:
            report += "None\n"

        report += "\n## Unresolved Items\n"
        if fixer_output.unresolved:
            for item in fixer_output.unresolved:
                report += f"- {item}\n"
        else:
            report += "None\n"

        if validation:
            report += "\n## Validation Details\n"
            report += f"- Intent preserved: {validation.intent_preserved}\n"
            report += f"- Issues resolved: {validation.issues_resolved.resolution_rate:.1%}\n"
            report += f"- Regressions: {len(validation.regressions)}\n"
            report += f"- Final recommendation: {validation.final_recommendation}\n"

        report += "\n## Rewritten Files\n"
        if fixer_output.rewritten_files:
            for path in fixer_output.rewritten_files.keys():
                report += f"- {path}\n"
        else:
            report += "None\n"

        return report
