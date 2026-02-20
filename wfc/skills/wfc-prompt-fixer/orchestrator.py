"""
Prompt Fixer Orchestrator

Coordinates 3-agent pipeline: Analyzer → Fixer → Reporter
CRITICAL: Orchestrator NEVER implements, ONLY coordinates.
"""

import glob
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .workspace import WorkspaceManager


@dataclass
class FixResult:
    """Result from fixing a prompt."""

    prompt_name: str
    prompt_path: Path
    workspace: Path
    grade_before: str
    grade_after: str
    report_path: Path
    changes_made: bool
    wfc_mode: bool


class PromptFixerOrchestrator:
    """
    Orchestrates the 3-agent prompt fixing pipeline.

    Workflow:
    1. Create workspace
    2. Spawn Analyzer → get grade + issues
    3. If grade A: skip to Reporter (no changes)
    4. Spawn Fixer (with retry loop) → fix issues
    5. Spawn Reporter → generate deliverable
    6. Optional: Create PR
    """

    def __init__(self, cwd: Optional[Path] = None):
        """Initialize orchestrator."""
        self.cwd = cwd or Path.cwd()
        self.workspace_manager = WorkspaceManager()

    def fix_prompt(
        self,
        prompt_path: Path,
        wfc_mode: Optional[bool] = None,
        auto_pr: bool = False,
    ) -> FixResult:
        """
        Fix a single prompt.

        Args:
            prompt_path: Path to the prompt file
            wfc_mode: Enable WFC-specific checks (auto-detect if None)
            auto_pr: Auto-create PR with fixes

        Returns:
            FixResult with grade, changes, report path
        """
        if wfc_mode is None:
            wfc_mode = self._detect_wfc_mode(prompt_path)

        workspace = self.workspace_manager.create(prompt_path, wfc_mode=wfc_mode)
        print(f"📁 Workspace: {workspace}")

        print("\n🔍 Phase 1: Analyzing prompt...")
        analysis = self._spawn_analyzer(workspace, wfc_mode)
        grade_before = analysis["grade"]
        print(f"   Grade: {grade_before}")

        if grade_before == "A":
            print("   ✅ No changes needed")
            report_path = self._skip_to_reporter(workspace, no_changes=True)
            return FixResult(
                prompt_name=prompt_path.stem,
                prompt_path=prompt_path,
                workspace=workspace,
                grade_before=grade_before,
                grade_after=grade_before,
                report_path=report_path,
                changes_made=False,
                wfc_mode=wfc_mode,
            )

        print(f"\n🔧 Phase 2: Fixing issues (grade {grade_before})...")
        fix_result = self._spawn_fixer_with_retry(workspace, max_retries=2)
        grade_after = fix_result.get("grade_after", grade_before)
        print(f"   Grade after: {grade_after}")

        print("\n📊 Phase 3: Generating report...")
        report_path = self._spawn_reporter(workspace)
        print(f"   Report: {report_path}")

        if auto_pr:
            print("\n🚀 Creating PR...")
            self._create_pr(prompt_path, workspace, grade_before, grade_after)

        return FixResult(
            prompt_name=prompt_path.stem,
            prompt_path=prompt_path,
            workspace=workspace,
            grade_before=grade_before,
            grade_after=grade_after,
            report_path=report_path,
            changes_made=True,
            wfc_mode=wfc_mode,
        )

    def fix_batch(
        self,
        pattern: str,
        wfc_mode: bool = True,
        auto_pr: bool = False,
    ) -> List[FixResult]:
        """
        Fix multiple prompts in batch (4 parallel).

        Args:
            pattern: Glob pattern for prompt files
            wfc_mode: Enable WFC-specific checks
            auto_pr: Auto-create PR with fixes

        Returns:
            List of FixResults
        """
        files = glob.glob(pattern, recursive=True)
        prompt_paths = [Path(f) for f in files if Path(f).is_file()]

        if not prompt_paths:
            print(f"❌ No files match pattern: {pattern}")
            return []

        print(f"📦 Batch mode: {len(prompt_paths)} prompts")

        results = []
        batch_size = 4

        for i in range(0, len(prompt_paths), batch_size):
            batch = prompt_paths[i : i + batch_size]
            print(f"\n🔄 Processing batch {i // batch_size + 1} ({len(batch)} prompts)")

            # TODO: Spawn parallel agents for this batch
            for prompt_path in batch:
                try:
                    result = self.fix_prompt(prompt_path, wfc_mode=wfc_mode, auto_pr=False)
                    results.append(result)
                except Exception as e:
                    print(f"⚠️  Failed to fix {prompt_path}: {e}")

        if auto_pr and results:
            print("\n🚀 Creating batch PR...")
            self._create_batch_pr(results)

        return results

    def _detect_wfc_mode(self, prompt_path: Path) -> bool:
        """
        Auto-detect if WFC mode should be enabled.

        Checks:
        - Filename is SKILL.md or PROMPT.md
        - Has YAML frontmatter with 'name:' field
        - Path matches wfc/skills/* or wfc/references/reviewers/*
        """
        if prompt_path.name in ["SKILL.md", "PROMPT.md"]:
            return True

        path_str = str(prompt_path)
        if "wfc/skills/" in path_str or "wfc/references/reviewers/" in path_str:
            return True

        if prompt_path.exists():
            content = prompt_path.read_text()
            if content.startswith("---\n") and "\nname:" in content[:200]:
                return True

        return False

    def _spawn_analyzer(self, workspace: Path, wfc_mode: bool) -> dict:
        """
        Spawn Analyzer agent (Router + Diagnostician combined).

        Agent reads:
        - workspace/input/prompt.md
        - references/antipatterns.json
        - references/rubric.json

        Agent writes:
        - workspace/01-analyzer/analysis.json

        Returns:
            Analysis dict with {grade, scores, issues, wfc_mode}
        """
        # TODO: Implement actual agent spawning via Task tool
        print("   [TODO: Spawn Analyzer subagent]")

        analysis = {
            "grade": "B",
            "scores": {
                "XML_SEGMENTATION": {"score": 2, "evidence": "Some segmentation"},
                "INSTRUCTION_HIERARCHY": {"score": 2, "evidence": "Clear hierarchy"},
            },
            "issues": [
                {
                    "id": "ISSUE-001",
                    "category": "STRUCTURE",
                    "severity": "major",
                    "description": "Missing XML tags",
                    "fix_directive": "Wrap sections in XML tags",
                }
            ],
            "wfc_mode": wfc_mode,
            "rewrite_recommended": True,
        }

        self.workspace_manager.write_analysis(workspace, analysis)

        return analysis

    def _spawn_fixer_with_retry(self, workspace: Path, max_retries: int = 2) -> dict:
        """
        Spawn Fixer agent with retry loop (Rewriter + Validator combined).

        Retry logic:
        1. Spawn Fixer
        2. Fixer validates itself
        3. If validation FAIL: retry (max 2 times)
        4. If validation PASS: return

        Returns:
            Fix result dict
        """
        for attempt in range(max_retries + 1):
            if attempt > 0:
                print(f"   Retry {attempt}/{max_retries}")

            # TODO: Implement actual agent spawning
            print(f"   [TODO: Spawn Fixer subagent (attempt {attempt + 1})]")

            fix_result = {
                "verdict": "PASS",
                "grade_after": "A",
                "changes": ["Added XML tags", "Fixed vague spec"],
            }

            self.workspace_manager.write_fix(
                workspace,
                fixed_prompt="# Fixed Prompt\n\nMock fixed content",
                changelog=fix_result["changes"],
                unresolved=[],
            )

            if fix_result["verdict"] == "PASS":
                return fix_result

        return {"verdict": "FAIL", "grade_after": "C", "changes": []}

    def _skip_to_reporter(self, workspace: Path, no_changes: bool = True) -> Path:
        """Skip to Reporter when no changes needed (grade A)."""
        print("   [TODO: Spawn Reporter subagent (no changes)]")

        report = """## Summary
- Original grade: A
- Final grade: A
- Verdict: PASS (no changes needed)
- Token delta: 0 tokens

## Critical Changes
None - prompt is already well-formed.

## Rewritten Prompt
(Original prompt unchanged)
"""

        return self.workspace_manager.write_report(workspace, report)

    def _spawn_reporter(self, workspace: Path) -> Path:
        """
        Spawn Reporter agent.

        Agent reads all workspace files and generates final report.

        Returns:
            Path to report.md
        """
        print("   [TODO: Spawn Reporter subagent]")

        report = """## Summary
- Original grade: B
- Final grade: A
- Verdict: PASS
- Token delta: +50 tokens

## Critical Changes
1. Added XML tags for structure
2. Fixed vague output specification
3. Added verification step

## Unresolved Items
None

## Rewritten Prompt
(See workspace/02-fixer/fixed_prompt.md)
"""

        return self.workspace_manager.write_report(workspace, report)

    def _create_pr(
        self, prompt_path: Path, workspace: Path, grade_before: str, grade_after: str
    ) -> None:
        """Create PR for single prompt fix."""
        # TODO: Implement PR creation
        print(f"   [TODO: Create PR - {grade_before} → {grade_after}]")

    def _create_batch_pr(self, results: List[FixResult]) -> None:
        """Create single PR for batch of fixes."""
        # TODO: Implement batch PR creation
        print(f"   [TODO: Create batch PR for {len(results)} prompts]")
