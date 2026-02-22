"""Schema definitions for skill fixer pipeline.

All dataclasses for the 6-agent pipeline phases.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class FrontmatterMetrics:
    """Metrics for SKILL.md YAML frontmatter."""

    name: str
    description: str
    description_length: int
    has_required_fields: bool
    frontmatter_valid: bool
    frontmatter_errors: List[str] = field(default_factory=list)


@dataclass
class BodyMetrics:
    """Metrics for SKILL.md body content."""

    total_lines: int
    section_count: int
    code_block_count: int
    file_reference_count: int
    sections: List[str] = field(default_factory=list)


@dataclass
class FilesystemMetrics:
    """Metrics for skill filesystem structure."""

    scripts_count: int
    references_count: int
    assets_count: int
    total_files: int
    scripts_executable: List[str] = field(default_factory=list)
    scripts_non_executable: List[str] = field(default_factory=list)
    scripts_missing_shebang: List[str] = field(default_factory=list)


@dataclass
class CrossReferences:
    """Cross-reference integrity tracking."""

    referenced_but_missing: List[str] = field(default_factory=list)
    present_but_unreferenced: List[str] = field(default_factory=list)
    all_file_references: List[str] = field(default_factory=list)
    all_present_files: List[str] = field(default_factory=list)


@dataclass
class SkillManifest:
    """Complete filesystem inventory from Cataloger."""

    skill_path: Path
    frontmatter: FrontmatterMetrics
    body: BodyMetrics
    filesystem: FilesystemMetrics
    cross_references: CrossReferences
    red_flags: List[str] = field(default_factory=list)
    skills_ref_available: bool = False
    skills_ref_output: Optional[str] = None


@dataclass
class DimensionScore:
    """Score for a single rubric dimension."""

    score: int
    rationale: str
    evidence: List[str] = field(default_factory=list)


@dataclass
class DimensionSummary:
    """Summary for a rubric dimension category."""

    category: str
    avg_score: float
    dimensions: List[str]
    key_issues: List[str] = field(default_factory=list)


@dataclass
class Issue:
    """Single issue identified by Analyst."""

    id: str
    dimension: str
    severity: str
    description: str
    fix_directive: str
    evidence: List[str] = field(default_factory=list)


@dataclass
class SkillDiagnosis:
    """Diagnosis output from Analyst."""

    scores: Dict[str, DimensionScore]
    dimension_summaries: Dict[str, DimensionSummary]
    issues: List[Issue]
    overall_grade: str
    rewrite_recommended: bool
    rewrite_scope: str
    summary: str


@dataclass
class FixerOutput:
    """Output from Fixer agent."""

    rewritten_files: Dict[str, str]
    changelog: List[str]
    script_issues: List[str]
    unresolved: List[str]


@dataclass
class IssueResolution:
    """Issue resolution tracking for Structural QA."""

    critical_resolved: int
    critical_total: int
    major_resolved: int
    major_total: int
    minor_resolved: int
    minor_total: int
    resolution_rate: float


@dataclass
class Regression:
    """Regression identified by Structural QA."""

    severity: str
    description: str
    location: str


@dataclass
class StructuralIssue:
    """Structural issue identified by Structural QA."""

    category: str
    description: str
    severity: str


@dataclass
class ValidationResult:
    """Validation result from Structural QA."""

    verdict: str
    frontmatter_valid: bool
    intent_preserved: bool
    issues_resolved: IssueResolution
    regressions: List[Regression]
    structural_issues: List[StructuralIssue]
    line_count: Dict[str, int]
    description_length: Dict[str, int]
    final_recommendation: str
    revision_notes: Optional[str] = None


@dataclass
class TestCase:
    """Test case for Functional QA."""

    id: str
    prompt: str
    expected_behavior: str
    test_type: str


@dataclass
class TestCaseResult:
    """Result from executing a single test case."""

    test_id: str
    original_skill_output: str
    rewritten_skill_output: str
    task_completion: int
    quality: int
    adherence: int
    edge_case_handling: int
    total_score: int
    passed: bool


@dataclass
class AggregateScores:
    """Aggregate scores from Functional QA."""

    avg_task_completion: float
    avg_quality: float
    avg_adherence: float
    avg_edge_case_handling: float
    total_avg: float
    regression_count: int


@dataclass
class FunctionalQAResult:
    """Result from Functional QA."""

    test_cases_run: int
    test_cases_source: str
    results: List[TestCaseResult]
    aggregate: AggregateScores
    verdict: str
    failure_reason: Optional[str] = None


@dataclass
class ReportSummary:
    """Summary section of final report."""

    skill_name: str
    original_grade: str
    final_grade: str
    structural_verdict: str
    functional_verdict: str
    original_line_count: int
    rewritten_line_count: int
    original_description_length: int
    rewritten_description_length: int


@dataclass
class SkillFixReport:
    """Final report from Reporter."""

    summary: ReportSummary
    triggering_changes: str
    structural_changes: List[str]
    script_issues: List[str]
    unresolved_items: List[str]
    rewritten_files: Dict[str, str]
    report_text: str
