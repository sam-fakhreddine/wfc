"""
Review Orchestrator

Coordinates 5 fixed reviewers -> fingerprint dedup -> consensus score -> report.
Uses ReviewerEngine, Fingerprinter, and ConsensusScore as the default (and only) mode.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from .consensus_score import ConsensusScore, ConsensusScoreResult
from .fingerprint import Fingerprinter
from .reviewer_engine import ReviewerEngine

if TYPE_CHECKING:
    from wfc.scripts.knowledge.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)


@dataclass
class ReviewRequest:
    """Request for code review."""

    task_id: str
    files: list[str]
    diff_content: str = ""
    properties: list[dict] = field(default_factory=list)


@dataclass
class ReviewResult:
    """Complete review result."""

    task_id: str
    consensus: ConsensusScoreResult
    report_path: Path
    passed: bool


class ReviewOrchestrator:
    """
    Orchestrates the 5-reviewer consensus review.

    Two-phase workflow:
    1. prepare_review() - build task specs for 5 reviewers
    2. finalize_review() - parse responses, deduplicate, score, report
    """

    def __init__(
        self,
        reviewer_engine: ReviewerEngine | None = None,
        retriever: KnowledgeRetriever | None = None,
    ):
        self.engine = reviewer_engine or ReviewerEngine(retriever=retriever)
        self.fingerprinter = Fingerprinter()
        self.scorer = ConsensusScore()

    @staticmethod
    def _validate_output_path(path: Path) -> None:
        """
        Validate output path for security.

        Raises:
            ValueError: If path is unsafe or invalid
        """
        if not path.is_absolute():
            raise ValueError(f"Output path must be absolute: {path}")

        try:
            resolved = path.resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Cannot resolve path {path}: {e}")

        sensitive_dirs = [
            Path("/etc"),
            Path("/bin"),
            Path("/sbin"),
            Path("/usr/bin"),
            Path("/usr/sbin"),
            Path("/System"),
            Path.home() / ".ssh",
            Path.home() / ".aws",
        ]

        for sensitive in sensitive_dirs:
            if resolved.is_relative_to(sensitive):
                raise ValueError(f"Cannot write to sensitive directory: {resolved}")

        if not resolved.parent.exists():
            try:
                resolved.parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                raise ValueError(f"Cannot create parent directory {resolved.parent}: {e}")

    def prepare_review(self, request: ReviewRequest) -> list[dict]:
        """Phase 1: Build task specs for the 5 reviewers."""
        return self.engine.prepare_review_tasks(
            files=request.files,
            diff_content=request.diff_content,
            properties=request.properties if request.properties else None,
        )

    def finalize_review(
        self,
        request: ReviewRequest,
        task_responses: list[dict],
        output_dir: Path,
    ) -> ReviewResult:
        """Phase 2: Parse responses, deduplicate, score, report.

        1. Parse subagent responses into ReviewerResults
        2. Collect all findings, tag with reviewer_id
        3. Deduplicate via Fingerprinter
        4. Calculate ConsensusScore
        5. Generate markdown report
        6. Return ReviewResult
        """
        reviewer_results = self.engine.parse_results(task_responses)

        all_findings: list[dict] = []
        for result in reviewer_results:
            for finding in result.findings:
                tagged = dict(finding)
                tagged["reviewer_id"] = result.reviewer_id
                tagged["line_start"] = int(tagged.get("line_start", 0))
                tagged["line_end"] = int(tagged.get("line_end", tagged["line_start"]))
                tagged["severity"] = float(tagged.get("severity", 0))
                tagged["confidence"] = float(tagged.get("confidence", 0))
                tagged.setdefault("file", "unknown")
                tagged.setdefault("category", "general")
                all_findings.append(tagged)

        deduped = self.fingerprinter.deduplicate(all_findings)

        cs_result = self.scorer.calculate(deduped)

        report_path = output_dir / f"REVIEW-{request.task_id}.md"
        self._generate_report(request, cs_result, reviewer_results, report_path)

        return ReviewResult(
            task_id=request.task_id,
            consensus=cs_result,
            report_path=report_path,
            passed=cs_result.passed,
        )

    def _generate_report(
        self,
        request: ReviewRequest,
        cs_result: ConsensusScoreResult,
        reviewer_results: list,
        path: Path,
    ) -> None:
        """Generate markdown review report."""
        status = "PASSED" if cs_result.passed else "FAILED"
        lines = [
            f"# Review Report: {request.task_id}",
            "",
            f"**Status**: {status}",
            f"**Consensus Score**: CS={cs_result.cs:.2f} ({cs_result.tier})",
            f"**Reviewers**: {cs_result.n}",
            f"**Findings**: {len(cs_result.findings)}",
            "",
        ]

        if cs_result.minority_protection_applied:
            lines.append("**Minority Protection Rule**: Applied")
            lines.append("")

        lines.extend(["---", "", "## Reviewer Summaries", ""])

        for result in reviewer_results:
            status_icon = "PASS" if result.passed else "FAIL"
            lines.extend(
                [
                    f"### {status_icon}: {result.reviewer_name}",
                    f"**Score**: {result.score:.1f}/10",
                    f"**Summary**: {result.summary}",
                    f"**Findings**: {len(result.findings)}",
                    "",
                ]
            )

        if cs_result.findings:
            lines.extend(["---", "", "## Findings", ""])

            for scored_finding in cs_result.findings:
                f = scored_finding.finding
                lines.extend(
                    [
                        f"### [{scored_finding.tier.upper()}] {f.file}:{f.line_start}",
                        f"**Category**: {f.category}",
                        f"**Severity**: {f.severity:.1f}",
                        f"**Confidence**: {f.confidence:.1f}",
                        f"**Reviewers**: {', '.join(f.reviewer_ids)} (k={f.k})",
                        f"**R_i**: {scored_finding.R_i:.2f}",
                        "",
                        f"**Description**: {f.description}",
                        "",
                    ]
                )

                if len(f.descriptions) > 1:
                    lines.append("**Additional descriptions**:")
                    for desc in f.descriptions[1:]:
                        lines.append(f"- {desc}")
                    lines.append("")

                if f.remediation:
                    lines.append("**Remediation**:")
                    for rem in f.remediation:
                        lines.append(f"- {rem}")
                    lines.append("")

        lines.extend(["---", "", "## Summary", "", cs_result.summary, ""])

        self._validate_output_path(path)
        with open(path, "w") as fh:
            fh.write("\n".join(lines))
