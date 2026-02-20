"""
Prompt Fixer Orchestrator

Coordinates 3-agent pipeline: Analyzer → Fixer → Reporter
CRITICAL: Orchestrator NEVER implements, ONLY coordinates.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple

from .workspace import WorkspaceManager

SAFE_GLOB_PREFIXES = ("wfc/", "references/", "./wfc/", "./references/")
MAX_RECURSIVE_DEPTH = 2
MAX_GLOB_MATCHES = 1000


def validate_glob_pattern(pattern: any) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate glob pattern for safety (PROP-003, PROP-011).

    Prevents:
    - Path traversal attacks (.. in patterns)
    - Filesystem enumeration DoS (/**/* patterns)
    - Unauthorized file access (patterns outside safe directories)
    - Excessive recursion depth (>2 levels of **)

    Args:
        pattern: Glob pattern to validate (must be str)

    Returns:
        Tuple of (is_valid, error_message, validated_pattern)
        - is_valid: True if pattern is safe
        - error_message: None if valid, error description if invalid
        - validated_pattern: Normalized pattern if valid, None if invalid

    Examples:
        >>> validate_glob_pattern("wfc/skills/**/*.md")
        (True, None, "wfc/skills/**/*.md")

        >>> validate_glob_pattern("../etc/passwd")
        (False, "Pattern contains path traversal (..)", None)

        >>> validate_glob_pattern("/etc/passwd")
        (False, "Pattern is an absolute path", None)
    """
    if not isinstance(pattern, str):
        return (False, f"Pattern must be a string, got {type(pattern).__name__}", None)

    if not pattern or not pattern.strip():
        return (False, "Pattern cannot be empty or whitespace-only", None)

    pattern = pattern.strip()

    if ".." in pattern:
        return (False, "Pattern contains path traversal (..)", None)

    if pattern.startswith("/"):
        return (False, "Pattern is an absolute path (starts with /)", None)

    if not any(pattern.startswith(prefix) for prefix in SAFE_GLOB_PREFIXES):
        return (
            False,
            f"Pattern must start with one of: {', '.join(SAFE_GLOB_PREFIXES)}",
            None,
        )

    recursive_count = pattern.count("**")
    if recursive_count > MAX_RECURSIVE_DEPTH:
        return (
            False,
            f"Pattern has too many recursive globs (**): {recursive_count} "
            f"(max {MAX_RECURSIVE_DEPTH})",
            None,
        )

    return (True, None, pattern)


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
        keep_workspace: bool = False,
    ) -> FixResult:
        """
        Fix a single prompt.

        Args:
            prompt_path: Path to the prompt file
            wfc_mode: Enable WFC-specific checks (auto-detect if None)
            auto_pr: Auto-create PR with fixes
            keep_workspace: Keep workspace on failure for debugging (PROP-002)

        Returns:
            FixResult with grade, changes, report path
        """
        if wfc_mode is None:
            wfc_mode = self._detect_wfc_mode(prompt_path)

        workspace = self.workspace_manager.create(prompt_path, wfc_mode=wfc_mode)
        print(f"📁 Workspace: {workspace}")

        cleanup_on_failure = not keep_workspace
        should_cleanup = False

        try:
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
        except Exception:
            should_cleanup = cleanup_on_failure
            raise
        finally:
            if should_cleanup:
                self.workspace_manager.cleanup(workspace)

    def fix_batch(
        self,
        pattern: str,
        wfc_mode: bool = True,
        auto_pr: bool = False,
        keep_workspace: bool = False,
    ) -> List[FixResult]:
        """
        Fix multiple prompts in batch (4 parallel).

        Args:
            pattern: Glob pattern for prompt files
            wfc_mode: Enable WFC-specific checks
            auto_pr: Auto-create PR with fixes
            keep_workspace: Keep workspaces on failure for debugging (PROP-002)

        Returns:
            List of FixResults

        Raises:
            ValueError: If glob pattern is invalid or unsafe
        """
        is_valid, error_msg, validated_pattern = validate_glob_pattern(pattern)
        if not is_valid:
            raise ValueError(f"Invalid glob pattern: {error_msg}")

        cwd = Path.cwd()
        all_matches = list(cwd.glob(validated_pattern))

        prompt_paths = [p for p in all_matches if p.is_file()]

        if len(prompt_paths) > MAX_GLOB_MATCHES:
            print(
                f"⚠️  Warning: Pattern matched {len(prompt_paths)} files, "
                f"truncating to first {MAX_GLOB_MATCHES}"
            )
            prompt_paths = prompt_paths[:MAX_GLOB_MATCHES]

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
                    result = self.fix_prompt(
                        prompt_path,
                        wfc_mode=wfc_mode,
                        auto_pr=False,
                        keep_workspace=keep_workspace,
                    )
                    results.append(result)
                except Exception as e:
                    print(f"⚠️  Failed to fix {prompt_path}: {e}")

        if auto_pr and results:
            print("\n🚀 Creating batch PR...")
            self._create_batch_pr(results)

        return results

    @lru_cache(maxsize=128)
    def _detect_wfc_mode(self, prompt_path: Path) -> bool:
        """
        Auto-detect if WFC mode should be enabled.

        Checks:
        - Filename is SKILL.md or PROMPT.md
        - Has YAML frontmatter with 'name:' field (properly delimited)
        - Path matches wfc/skills/* or wfc/references/reviewers/*

        Uses @lru_cache for performance optimization (TASK-010).
        Limits file reads to 10KB to prevent memory issues on large files.

        Args:
            prompt_path: Path to the prompt file

        Returns:
            True if WFC mode should be enabled, False otherwise
        """
        if prompt_path.name in ["SKILL.md", "PROMPT.md"]:
            return True

        path_str = str(prompt_path)
        if "wfc/skills/" in path_str or "wfc/references/reviewers/" in path_str:
            return True

        if not prompt_path.exists():
            return False

        try:
            with open(prompt_path, encoding="utf-8") as f:
                content = f.read(10000)

            if not content.startswith("---\n"):
                return False

            closing_pos = content.find("\n---\n", 4)
            if closing_pos == -1:
                return False

            frontmatter = content[4:closing_pos]
            if "\nname:" in frontmatter or frontmatter.startswith("name:"):
                return True

        except (UnicodeDecodeError, PermissionError, OSError):
            return False

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
