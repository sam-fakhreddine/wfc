"""Shared dataclasses and typed dicts for the CLAUDE.md remediation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Context Mapper output
# ---------------------------------------------------------------------------


@dataclass
class ClaudeMdMetrics:
    location: str
    total_lines: int
    total_sections: int
    section_names: list[str]
    code_blocks: int
    instruction_count: int
    estimated_tokens: int
    commands_referenced: list[str]
    paths_referenced: list[str]
    tools_referenced: list[str]
    has_project_summary: bool
    has_directory_map: bool
    has_commands_section: bool
    has_code_style_section: bool
    has_workflow_section: bool
    has_architecture_section: bool
    has_progressive_disclosure: bool


@dataclass
class CodebaseMetrics:
    language: str
    framework: str
    package_manager: str
    available_scripts: list[str]
    top_level_dirs: list[str]
    has_linter_config: bool
    linter_type: str | None
    has_formatter_config: bool
    formatter_type: str | None
    has_ci_config: bool
    has_test_framework: bool
    test_framework: str | None
    has_hooks_config: bool
    has_mcp_config: bool
    has_slash_commands: bool
    has_existing_docs: bool
    doc_locations: list[str]


@dataclass
class CrossReference:
    commands_valid: list[dict[str, Any]]
    paths_valid: list[dict[str, Any]]
    tools_valid: list[dict[str, Any]]
    codebase_features_not_in_claude_md: list[str]
    claude_md_claims_not_in_codebase: list[str]


@dataclass
class ContextManifest:
    claude_md: ClaudeMdMetrics
    subdirectory_claude_mds: list[dict[str, Any]]
    codebase: CodebaseMetrics
    cross_reference: CrossReference
    red_flags: list[str]


# ---------------------------------------------------------------------------
# Analyst output
# ---------------------------------------------------------------------------


@dataclass
class DimensionScore:
    score: int  # 0-3
    evidence: str


@dataclass
class DimensionSummary:
    avg_score: float
    summary: str


@dataclass
class Issue:
    id: str
    dimension: str
    category: str
    severity: str  # critical | major | minor
    description: str
    impact: str
    fix_directive: str
    migration_target: str


@dataclass
class InstructionBudgetAnalysis:
    estimated_claude_code_system_instructions: int
    claude_md_instructions: int
    total_estimated: int
    budget_remaining: int
    budget_status: str  # healthy | tight | overdrawn


@dataclass
class Diagnosis:
    scores: dict[str, DimensionScore]
    dimension_summaries: dict[str, DimensionSummary]
    issues: list[Issue]
    instruction_budget_analysis: InstructionBudgetAnalysis
    overall_grade: str  # A | B | C | D | F
    rewrite_recommended: bool
    rewrite_scope: str  # full | trim_only | restructure | extract_and_trim


# ---------------------------------------------------------------------------
# Fixer output
# ---------------------------------------------------------------------------


@dataclass
class ExtractedFile:
    path: str
    content: str


@dataclass
class RewriteMetrics:
    original_lines: int
    rewritten_lines: int
    original_instructions: int
    rewritten_instructions: int
    lines_removed: int
    lines_extracted: int
    hooks_recommended: int
    slash_commands_recommended: int
    subdirectory_files_created: int


@dataclass
class FixerOutput:
    rewritten_content: str  # The fixed CLAUDE.md content
    changelog: list[str]
    migration_plan: str
    extracted_files: list[ExtractedFile]
    metrics: RewriteMetrics


# ---------------------------------------------------------------------------
# QA Validator output
# ---------------------------------------------------------------------------


@dataclass
class BudgetCheck:
    original_lines: int
    rewritten_lines: int
    original_instructions: int
    rewritten_instructions: int
    budget_status: str  # improved | unchanged | regressed


@dataclass
class ContentIntegrity:
    stale_commands: list[str]
    stale_paths: list[str]
    contradictions: list[str]


@dataclass
class IssueResolution:
    total_critical_major: int
    resolved: int
    unresolved: list[str]


@dataclass
class Regression:
    description: str
    severity: str  # critical | major | minor


@dataclass
class ValidationResult:
    verdict: str  # PASS | FAIL | PASS_WITH_NOTES
    budget_check: BudgetCheck
    content_integrity: ContentIntegrity
    intent_preserved: bool
    lost_content_without_destination: list[str]
    issues_resolved: IssueResolution
    separation_violations: list[str]
    migration_plan_issues: list[str]
    regressions: list[Regression]
    final_recommendation: str  # ship | revise | escalate_to_human
    revision_notes: str


# ---------------------------------------------------------------------------
# Pipeline result
# ---------------------------------------------------------------------------


@dataclass
class RemediationResult:
    """Final result returned by the orchestrator."""

    project_root: str
    claude_md_path: str
    grade_before: str
    grade_after: str
    verdict: str
    original_lines: int
    rewritten_lines: int
    original_instructions: int
    rewritten_instructions: int
    rewritten_content: str | None  # None if grade was A or pipeline failed
    extracted_files: list[ExtractedFile] = field(default_factory=list)
    migration_plan: str = ""
    changelog: list[str] = field(default_factory=list)
    report: str = ""
    error: str | None = None

    @property
    def no_changes_needed(self) -> bool:
        return self.grade_before == "A"

    @property
    def succeeded(self) -> bool:
        return self.error is None and self.verdict in ("PASS", "PASS_WITH_NOTES")
