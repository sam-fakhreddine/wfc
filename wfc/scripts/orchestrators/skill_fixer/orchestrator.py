"""Orchestrator - coordinates 6-agent pipeline with retry loop."""

from dataclasses import asdict
from pathlib import Path
from typing import Callable, Optional

from .analyst import SkillAnalyst
from .cataloger import SkillCataloger
from .fixer import SkillFixer
from .functional_qa import FunctionalQA
from .reporter import SkillReporter
from .schemas import SkillFixReport
from .structural_qa import StructuralQA
from .workspace import WorkspaceManager


class SkillFixerOrchestrator:
    """
    Orchestrates 6-agent skill fixing pipeline.

    Workflow:
    1. Cataloger (local, deterministic)
    2. Analyst (LLM or fallback)
    3. Fixer (LLM or fallback) with retry loop
    4. Structural QA (rule-based + optional LLM)
    5. Functional QA (optional, slow)
    6. Reporter (LLM or rule-based)
    """

    def __init__(self):
        """Initialize orchestrator."""
        self.workspace_manager = WorkspaceManager()
        self.cataloger = SkillCataloger()
        self.analyst = SkillAnalyst()
        self.fixer = SkillFixer()
        self.structural_qa = StructuralQA()
        self.functional_qa = FunctionalQA()
        self.reporter = SkillReporter()

    def fix_skill(
        self,
        skill_path: Path,
        run_functional_qa: bool = False,
        analyst_fn: Optional[Callable[[str], str]] = None,
        fixer_fn: Optional[Callable[[str], str]] = None,
        qa_fn: Optional[Callable[[str], str]] = None,
        reporter_fn: Optional[Callable[[str], str]] = None,
        max_retries: int = 2,
    ) -> SkillFixReport:
        """
        Fix a single skill.

        Args:
            skill_path: Path to skill directory
            run_functional_qa: Whether to run functional QA (slow)
            analyst_fn: Optional LLM response function for analyst
            fixer_fn: Optional LLM response function for fixer
            qa_fn: Optional LLM response function for QA
            reporter_fn: Optional LLM response function for reporter
            max_retries: Maximum retry attempts (default 2)

        Returns:
            SkillFixReport with complete results
        """
        workspace = self.workspace_manager.create(skill_path, run_functional_qa)

        print("Phase 1: Cataloger (filesystem inventory)...")
        manifest = self.cataloger.catalog(skill_path)
        self.workspace_manager.write_manifest(workspace, asdict(manifest))

        print("Phase 2: Analyst (diagnosis)...")
        skill_content = (skill_path / "SKILL.md").read_text(errors="replace")
        diagnosis = self.analyst.analyze(skill_content, manifest, response_fn=analyst_fn)
        self.workspace_manager.write_diagnosis(workspace, asdict(diagnosis))

        print(f"  Grade: {diagnosis.overall_grade}")
        print(f"  Issues: {len(diagnosis.issues)}")

        if diagnosis.overall_grade == "A":
            print("  ✅ Grade A - no fixes needed")
            report = self.reporter.generate_report(
                manifest, diagnosis, None, None, None, reporter_fn
            )
            self.workspace_manager.write_report(workspace, report.report_text)
            return report

        print("Phase 3: Fixer (rewriting)...")
        revision_notes = None
        fixer_output = None
        validation = None

        for attempt in range(max_retries + 1):
            if attempt > 0:
                print(f"  Retry {attempt}/{max_retries}")

            fixer_output = self.fixer.fix(
                skill_content, manifest, diagnosis, revision_notes, response_fn=fixer_fn
            )

            self.workspace_manager.write_fix(
                workspace,
                fixer_output.rewritten_files,
                fixer_output.changelog,
                fixer_output.script_issues,
                fixer_output.unresolved,
            )

            print("Phase 4: Structural QA (validation)...")
            validation = self.structural_qa.validate(
                skill_content, manifest, diagnosis, fixer_output, response_fn=qa_fn
            )

            self.workspace_manager.write_validation(workspace, asdict(validation))

            print(f"  Verdict: {validation.verdict}")
            print(f"  Recommendation: {validation.final_recommendation}")

            if validation.verdict in ["PASS", "PASS_WITH_NOTES"]:
                break

            if attempt < max_retries:
                revision_notes = validation.revision_notes
                print(f"  Revision notes: {revision_notes}")
            else:
                print("  Max retries reached")
                break

        functional_result = None
        if run_functional_qa and validation and validation.verdict != "FAIL":
            print("Phase 5: Functional QA (optional)...")
            functional_result = self.functional_qa.evaluate(
                skill_path, fixer_output.rewritten_files if fixer_output else {}
            )
            self.workspace_manager.write_functional_qa(workspace, asdict(functional_result))
            print(f"  Verdict: {functional_result.verdict}")

        print("Phase 6: Reporter (final report)...")
        report = self.reporter.generate_report(
            manifest, diagnosis, fixer_output, validation, functional_result, reporter_fn
        )

        self.workspace_manager.write_report(workspace, report.report_text)

        print(f"\n✅ Report: {workspace / '06-reporter' / 'report.md'}")

        return report
