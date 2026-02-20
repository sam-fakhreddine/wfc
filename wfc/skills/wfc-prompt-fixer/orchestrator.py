"""
Prompt Fixer Orchestrator

Coordinates 3-agent pipeline: Analyzer → Fixer → Reporter
CRITICAL: Orchestrator NEVER implements, ONLY coordinates.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .workspace import WorkspaceError, WorkspaceManager

SAFE_GLOB_PREFIXES = ("wfc/", "references/", "./wfc/", "./references/")
MAX_RECURSIVE_DEPTH = 2
MAX_GLOB_MATCHES = 1000


def validate_analysis_schema(analysis: Dict) -> Tuple[bool, List[str]]:
    """
    Validate analysis.json schema (PROP-006).

    Required fields:
    - classification (dict)
    - scores (dict)
    - issues (list)
    - overall_grade (str: A-F)
    - average_score (float)
    - rewrite_recommended (bool)
    - rewrite_scope (str)
    - wfc_mode (bool)
    - summary (str)

    Args:
        analysis: Analysis dictionary to validate

    Returns:
        Tuple of (is_valid, errors)
        - is_valid: True if schema is valid
        - errors: List of error messages (empty if valid)
    """
    errors = []

    required_fields = [
        "classification",
        "scores",
        "issues",
        "overall_grade",
        "average_score",
        "rewrite_recommended",
        "rewrite_scope",
        "wfc_mode",
        "summary",
    ]

    for field in required_fields:
        if field not in analysis:
            errors.append(f"Missing required field: {field}")

    grade = analysis.get("overall_grade")
    if grade is not None and grade not in ["A", "B", "C", "D", "F"]:
        errors.append(f"Invalid overall_grade: {grade} (must be A-F)")

    issues = analysis.get("issues", [])
    if isinstance(issues, list):
        for i, issue in enumerate(issues):
            if not isinstance(issue, dict):
                errors.append(f"Issue {i} is not a dictionary")
                continue

            severity = issue.get("severity")
            if severity is not None and severity not in ["critical", "major", "minor"]:
                errors.append(
                    f"Issue {i} has invalid severity: {severity} "
                    f"(must be critical, major, or minor)"
                )

    return (len(errors) == 0, errors)


def validate_fix_result_schema(fix_result: Dict) -> Tuple[bool, List[str]]:
    """
    Validate validation.json schema from Fixer agent (PROP-006).

    Required fields:
    - verdict (str: PASS | FAIL | PASS_WITH_NOTES)
    - intent_preserved (bool)
    - issues_resolved (dict)
    - regressions (list)
    - scope_creep (list)
    - grade_after (str: A-F)
    - final_recommendation (str: ship | revise)
    - revision_notes (str, optional for PASS verdicts)

    Args:
        fix_result: Fix result dictionary to validate

    Returns:
        Tuple of (is_valid, errors)
        - is_valid: True if schema is valid
        - errors: List of error messages (empty if valid)
    """
    errors = []

    required_fields = [
        "verdict",
        "intent_preserved",
        "issues_resolved",
        "regressions",
        "scope_creep",
        "grade_after",
        "final_recommendation",
    ]

    for field in required_fields:
        if field not in fix_result:
            errors.append(f"Missing required field: {field}")

    verdict = fix_result.get("verdict")
    if verdict is not None and verdict not in ["PASS", "FAIL", "PASS_WITH_NOTES"]:
        errors.append(f"Invalid verdict: {verdict} (must be PASS, FAIL, or PASS_WITH_NOTES)")

    grade = fix_result.get("grade_after")
    if grade is not None and grade not in ["A", "B", "C", "D", "F"]:
        errors.append(f"Invalid grade_after: {grade} (must be A-F)")

    rec = fix_result.get("final_recommendation")
    if rec is not None and rec not in ["ship", "revise"]:
        errors.append(f"Invalid final_recommendation: {rec} (must be ship or revise)")

    intent_preserved = fix_result.get("intent_preserved")
    if intent_preserved is not None and not isinstance(intent_preserved, bool):
        errors.append("intent_preserved must be a boolean")

    return (len(errors) == 0, errors)


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
            grade_before = analysis.get("overall_grade", analysis.get("grade", "UNKNOWN"))
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

        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = []
        batch_size = 4
        max_workers = 4

        for i in range(0, len(prompt_paths), batch_size):
            batch = prompt_paths[i : i + batch_size]
            print(f"\n🔄 Processing batch {i // batch_size + 1} ({len(batch)} prompts)")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_path = {
                    executor.submit(
                        self.fix_prompt,
                        prompt_path,
                        wfc_mode=wfc_mode,
                        auto_pr=False,
                        keep_workspace=keep_workspace,
                    ): prompt_path
                    for prompt_path in batch
                }

                for future in as_completed(future_to_path):
                    prompt_path = future_to_path[future]
                    try:
                        result = future.result()
                        results.append(result)
                        print(
                            f"  ✅ {prompt_path.name}: {result.grade_before} → {result.grade_after}"
                        )
                    except Exception as e:
                        print(f"  ⚠️  Failed to fix {prompt_path.name}: {e}")

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

    def _get_agent_template_path(self, agent_name: str) -> Path:
        """
        Get path to agent template file.

        Args:
            agent_name: Name of agent (analyzer, fixer, reporter)

        Returns:
            Path to agent template markdown file
        """
        orchestrator_dir = Path(__file__).parent
        agent_template = orchestrator_dir / "agents" / f"{agent_name}.md"

        if not agent_template.exists():
            raise WorkspaceError(
                f"Agent template not found: {agent_template}. "
                f"Expected agents/{agent_name}.md in wfc-prompt-fixer package."
            )

        return agent_template

    def _prepare_analyzer_prompt(self, workspace: Path, wfc_mode: bool) -> str:
        """
        Prepare analyzer agent prompt by loading template and injecting context.

        This implements the "prompt generator" pattern from TASK-003A spike:
        - Load agent template from agents/analyzer.md
        - Inject workspace path
        - Reference metadata.json for wfc_mode flag
        - Return prompt string for Claude to use with Task tool

        Args:
            workspace: Path to workspace directory
            wfc_mode: Whether WFC-specific checks are enabled

        Returns:
            Prepared prompt string for Analyzer agent
        """
        template_path = self._get_agent_template_path("analyzer")
        template = template_path.read_text()

        prompt = template.replace("{workspace}", str(workspace))

        prompt = prompt.replace("{wfc_mode}", str(wfc_mode).lower())

        return prompt

    def _prepare_fixer_prompt(self, workspace: Path) -> str:
        """
        Prepare fixer agent prompt by loading template and injecting context.

        This implements the "prompt generator" pattern from TASK-003:
        - Load agent template from agents/fixer.md
        - Inject workspace path
        - Return prompt string for Claude to use with Task tool

        Args:
            workspace: Path to workspace directory

        Returns:
            Prepared prompt string for Fixer agent

        Raises:
            WorkspaceError: If fixer.md template file not found
        """
        template_path = self._get_agent_template_path("fixer")

        try:
            template = template_path.read_text()
        except FileNotFoundError as e:
            raise WorkspaceError(
                f"Agent template not found: {template_path}. "
                f"Expected agents/fixer.md in wfc-prompt-fixer package."
            ) from e

        prompt = template.replace("{workspace}", str(workspace))

        return prompt

    def _prepare_reporter_prompt(self, workspace: Path, no_changes: bool = False) -> str:
        """
        Prepare reporter agent prompt by loading template and injecting context.

        This implements the "prompt generator" pattern from TASK-003:
        - Load agent template from agents/reporter.md
        - Inject workspace path
        - Return prompt string for Claude to use with Task tool

        Args:
            workspace: Path to workspace directory
            no_changes: If True, indicates grade A (no changes needed)

        Returns:
            Prepared prompt string for Reporter agent

        Raises:
            WorkspaceError: If reporter.md template file not found
        """
        template_path = self._get_agent_template_path("reporter")

        try:
            template = template_path.read_text()
        except FileNotFoundError as e:
            raise WorkspaceError(
                f"Agent template not found: {template_path}. "
                f"Expected agents/reporter.md in wfc-prompt-fixer package."
            ) from e

        prompt = template.replace("{workspace}", str(workspace))

        return prompt

    def _spawn_analyzer(self, workspace: Path, wfc_mode: bool) -> dict:
        """
        Spawn Analyzer agent (Router + Diagnostician combined).

        ARCHITECTURE (from TASK-003A spike):
        This method implements the "prompt generator" pattern:
        1. Prepare agent prompt from agents/analyzer.md template
        2. Print instructions for Claude to invoke Task tool
        3. Wait for agent to write analysis.json to workspace
        4. Read and validate analysis.json
        5. Return analysis dict

        Agent reads:
        - workspace/input/prompt.md
        - references/antipatterns.json
        - references/rubric.json

        Agent writes:
        - workspace/01-analyzer/analysis.json

        Returns:
            Analysis dict with {grade, scores, issues, wfc_mode}

        Raises:
            WorkspaceError: If analysis.json not found or invalid schema
            TimeoutError: If agent doesn't complete within 300 seconds
        """
        import time

        agent_prompt = self._prepare_analyzer_prompt(workspace, wfc_mode)

        # NOTE: In production, Claude will see this message and use Task tool
        print("   [Analyzer agent prompt prepared]")
        print(f"   [Workspace: {workspace}]")
        print(f"   [WFC mode: {wfc_mode}]")
        print(f"   [Prompt length: {len(agent_prompt)} chars]")
        print(
            "   [INSTRUCTION: Use Task tool with subagent_type='general-purpose' "
            "and the prepared prompt]"
        )

        analysis_path = workspace / "01-analyzer" / "analysis.json"
        timeout_seconds = 300
        poll_interval = 2
        elapsed = 0

        while not analysis_path.exists():
            if elapsed >= timeout_seconds:
                raise TimeoutError(
                    f"Analyzer agent did not complete within {timeout_seconds}s. "
                    f"Expected output at {analysis_path}"
                )
            time.sleep(poll_interval)
            elapsed += poll_interval
            if elapsed % 30 == 0:
                print(f"   [Waiting for analyzer... {elapsed}s elapsed]")

        analysis = self.workspace_manager.read_analysis(workspace)

        is_valid, errors = validate_analysis_schema(analysis)
        if not is_valid:
            error_msg = "\n".join(f"  - {err}" for err in errors)
            raise WorkspaceError(
                f"Invalid analysis.json schema:\n{error_msg}\n"
                f"Analysis file may be corrupted or agent failed to generate valid output."
            )

        return analysis

    def _spawn_fixer_with_retry(self, workspace: Path, max_retries: int = 2) -> dict:
        """
        Spawn Fixer agent with retry loop (Rewriter + Validator combined).

        ARCHITECTURE (from TASK-003 pattern):
        This method implements the "prompt generator" pattern with retry logic:
        1. Prepare agent prompt from agents/fixer.md template
        2. Print instructions for Claude to invoke Task tool
        3. Wait for agent to write validation.json to workspace
        4. Read and validate validation.json schema (PROP-006)
        5. If verdict is FAIL, retry with exponential backoff (PROP-007)
        6. Return validation result dict

        Retry logic with exponential backoff (PROP-007):
        - Attempt 0: no delay
        - Attempt 1: 2^1 = 2 seconds delay
        - Attempt 2: 2^2 = 4 seconds delay
        - Max backoff capped at 30 seconds

        Agent reads:
        - workspace/input/prompt.md
        - workspace/01-analyzer/analysis.json
        - workspace/02-fixer/revision_notes.md (if retry)

        Agent writes:
        - workspace/02-fixer/fixed_prompt.md
        - workspace/02-fixer/changelog.md
        - workspace/02-fixer/unresolved.md
        - workspace/02-fixer/validation.json

        Args:
            workspace: Path to workspace directory
            max_retries: Maximum number of retry attempts (default 2)

        Returns:
            Validation result dict with {verdict, grade_after, intent_preserved, ...}

        Raises:
            WorkspaceError: If validation.json not found or invalid schema
        """
        import json
        import time

        for attempt in range(max_retries + 1):
            if attempt > 0:
                backoff_seconds = min(2**attempt, 30)
                print(f"   Retry {attempt}/{max_retries} (waiting {backoff_seconds}s)")
                time.sleep(backoff_seconds)

            agent_prompt = self._prepare_fixer_prompt(workspace)

            # NOTE: In production, Claude will see this message and use Task tool
            print(f"   [Fixer agent prompt prepared (attempt {attempt + 1})]")
            print(f"   [Workspace: {workspace}]")
            print(f"   [Prompt length: {len(agent_prompt)} chars]")
            print(
                "   [INSTRUCTION: Use Task tool with subagent_type='general-purpose' "
                "and the prepared prompt]"
            )

            validation_path = workspace / "02-fixer" / "validation.json"
            timeout_seconds = 300
            poll_interval = 2
            elapsed = 0

            while not validation_path.exists():
                if elapsed >= timeout_seconds:
                    raise TimeoutError(
                        f"Fixer agent did not complete within {timeout_seconds}s. "
                        f"Expected output at {validation_path}"
                    )
                time.sleep(poll_interval)
                elapsed += poll_interval
                if elapsed % 30 == 0:
                    print(f"   [Waiting for fixer... {elapsed}s elapsed]")

            try:
                with open(validation_path) as f:
                    validation_result = json.load(f)
            except json.JSONDecodeError as e:
                raise WorkspaceError(
                    f"Invalid JSON in validation file {validation_path}: {e}. "
                    f"File may be corrupted."
                ) from e

            is_valid, errors = validate_fix_result_schema(validation_result)
            if not is_valid:
                error_msg = "\n".join(f"  - {err}" for err in errors)
                raise WorkspaceError(
                    f"Invalid validation.json schema:\n{error_msg}\n"
                    f"Validation file may be corrupted or agent failed to generate valid output."
                )

            verdict = validation_result.get("verdict", "UNKNOWN")

            if verdict == "PASS" or verdict == "PASS_WITH_NOTES":
                return validation_result

            if attempt < max_retries:
                revision_notes = validation_result.get("revision_notes", "")
                if revision_notes:
                    notes_path = workspace / "02-fixer" / "revision_notes.md"
                    notes_path.write_text(revision_notes)
                    print(f"   Validation FAIL. Revision notes written to {notes_path.name}")

        return validation_result

    def _skip_to_reporter(self, workspace: Path, no_changes: bool = True) -> Path:
        """
        Skip to Reporter when no changes needed (grade A).

        ARCHITECTURE (from TASK-005):
        This method implements the "prompt generator" pattern:
        1. Prepare agent prompt from agents/reporter.md template
        2. Print instructions for Claude to invoke Task tool
        3. Wait for agent to write report.md to workspace
        4. Return report path

        Agent reads:
        - workspace/input/prompt.md
        - workspace/01-analyzer/analysis.json
        - workspace/metadata.json

        Agent writes:
        - workspace/03-reporter/report.md

        Args:
            workspace: Path to workspace directory
            no_changes: If True, indicates grade A (no changes needed)

        Returns:
            Path to report.md file
        """
        import time

        agent_prompt = self._prepare_reporter_prompt(workspace, no_changes=True)

        # NOTE: In production, Claude will see this message and use Task tool
        print("   [Reporter agent prompt prepared (no changes path)]")
        print(f"   [Workspace: {workspace}]")
        print(f"   [Prompt length: {len(agent_prompt)} chars]")
        print(
            "   [INSTRUCTION: Use Task tool with subagent_type='general-purpose' "
            "and the prepared prompt]"
        )

        report_path = workspace / "03-reporter" / "report.md"
        timeout_seconds = 300
        poll_interval = 2
        elapsed = 0

        while not report_path.exists():
            if elapsed >= timeout_seconds:
                raise TimeoutError(
                    f"Reporter agent did not complete within {timeout_seconds}s. "
                    f"Expected output at {report_path}"
                )
            time.sleep(poll_interval)
            elapsed += poll_interval
            if elapsed % 30 == 0:
                print(f"   [Waiting for reporter... {elapsed}s elapsed]")

        return self.workspace_manager.read_report(workspace)

    def _spawn_reporter(self, workspace: Path) -> Path:
        """
        Spawn Reporter agent.

        ARCHITECTURE (from TASK-005):
        This method implements the "prompt generator" pattern:
        1. Prepare agent prompt from agents/reporter.md template
        2. Print instructions for Claude to invoke Task tool
        3. Wait for agent to write report.md to workspace
        4. Return report path

        Agent reads all workspace files:
        - workspace/input/prompt.md
        - workspace/01-analyzer/analysis.json
        - workspace/02-fixer/fixed_prompt.md
        - workspace/02-fixer/changelog.md
        - workspace/02-fixer/unresolved.md
        - workspace/02-fixer/validation.json
        - workspace/metadata.json

        Agent writes:
        - workspace/03-reporter/report.md

        Returns:
            Path to report.md file
        """
        import time

        agent_prompt = self._prepare_reporter_prompt(workspace, no_changes=False)

        # NOTE: In production, Claude will see this message and use Task tool
        print("   [Reporter agent prompt prepared]")
        print(f"   [Workspace: {workspace}]")
        print(f"   [Prompt length: {len(agent_prompt)} chars]")
        print(
            "   [INSTRUCTION: Use Task tool with subagent_type='general-purpose' "
            "and the prepared prompt]"
        )

        report_path = workspace / "03-reporter" / "report.md"
        timeout_seconds = 300
        poll_interval = 2
        elapsed = 0

        while not report_path.exists():
            if elapsed >= timeout_seconds:
                raise TimeoutError(
                    f"Reporter agent did not complete within {timeout_seconds}s. "
                    f"Expected output at {report_path}"
                )
            time.sleep(poll_interval)
            elapsed += poll_interval
            if elapsed % 30 == 0:
                print(f"   [Waiting for reporter... {elapsed}s elapsed]")

        return self.workspace_manager.read_report(workspace)

    def _create_pr(
        self, prompt_path: Path, workspace: Path, grade_before: str, grade_after: str
    ) -> None:
        """
        Create PR for single prompt fix (TASK-005).

        Workflow:
        1. Create branch: claude/fix-prompt-{timestamp}
        2. Copy fixed_prompt.md to original location
        3. Commit with message including grade change
        4. Push to remote
        5. Create PR using gh CLI

        Args:
            prompt_path: Original prompt file path
            workspace: Workspace directory
            grade_before: Grade before fixing
            grade_after: Grade after fixing
        """
        import subprocess
        import time

        timestamp = int(time.time())
        branch_name = f"claude/fix-prompt-{prompt_path.stem}-{timestamp}"

        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            print(f"   Created branch: {branch_name}")

            fixed_prompt_path = workspace / "02-fixer" / "fixed_prompt.md"
            if fixed_prompt_path.exists():
                import shutil

                shutil.copy2(fixed_prompt_path, prompt_path)
                print(f"   Copied fixed prompt to: {prompt_path}")

            subprocess.run(
                ["git", "add", str(prompt_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )

            sanitized_name = prompt_path.name.replace("\n", " ").replace("\r", " ")[:100]
            commit_message = f"fix(prompt): improve {sanitized_name} ({grade_before} → {grade_after})\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            print(f"   Committed changes: {grade_before} → {grade_after}")

            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            print(f"   Pushed to origin/{branch_name}")

            sanitized_title_name = prompt_path.name.replace("[", "").replace("]", "")[:100]
            sanitized_workspace = str(workspace).replace("`", "")[:200]
            pr_title = f"Fix prompt: {sanitized_title_name} ({grade_before} → {grade_after})"
            pr_body = f"""## Summary

Automated prompt fix using wfc-prompt-fixer.

- **Original grade:** {grade_before}
- **Final grade:** {grade_after}
- **Workspace:** `{sanitized_workspace}`

## Changes

See workspace files for detailed analysis and changelog:
- `{sanitized_workspace}/01-analyzer/analysis.json` - Diagnostic results
- `{sanitized_workspace}/02-fixer/changelog.md` - List of changes
- `{sanitized_workspace}/03-reporter/report.md` - Full report

Generated with Claude Code.
"""
            subprocess.run(
                ["gh", "pr", "create", "--title", pr_title, "--body", pr_body],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            print(f"   PR created: {pr_title}")

        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  PR creation failed: {e}")
            print(f"   You can manually create PR from branch: {branch_name}")

    def _create_batch_pr(self, results: List[FixResult]) -> None:
        """Create single PR for batch of fixes."""
        # TODO: Implement batch PR creation
        print(f"   [TODO: Create batch PR for {len(results)} prompts]")
