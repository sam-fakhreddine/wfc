"""
Review Orchestrator

Coordinates 5 fixed reviewers -> fingerprint dedup -> consensus score -> report.
Uses ReviewerEngine, Fingerprinter, and ConsensusScore as the default (and only) mode.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from .consensus_score import ConsensusScore, ConsensusScoreResult
from .doc_auditor import DocAuditor, DocAuditReport
from .finding_validator import FindingValidator, ValidationStatus
from .fingerprint import Fingerprinter
from .reviewer_engine import ReviewerEngine

if TYPE_CHECKING:
    from wfc.scripts.knowledge.retriever import KnowledgeRetriever

    from .model_router import ModelRouter
    from .reviewer_engine import ReviewerResult

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
    doc_audit: DocAuditReport | None = None


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
        model_router: ModelRouter | None = None,
    ):
        self.engine = reviewer_engine or ReviewerEngine(retriever=retriever)
        self.fingerprinter = Fingerprinter()
        self.scorer = ConsensusScore()
        self.validator = FindingValidator()
        self.model_router = model_router

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
            try:
                sensitive_resolved = sensitive.resolve()
            except (OSError, RuntimeError):
                sensitive_resolved = sensitive
            if resolved.is_relative_to(sensitive_resolved):
                raise ValueError(f"Cannot write to sensitive directory: {resolved}")

        if not resolved.parent.exists():
            try:
                resolved.parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                raise ValueError(f"Cannot create parent directory {resolved.parent}: {e}")

    def prepare_review(self, request: ReviewRequest) -> list[dict]:
        """Phase 1: Build task specs for the 5 reviewers."""
        try:
            from wfc.observability.instrument import emit_event

            emit_event(
                "review.started",
                source="orchestrator",
                payload={
                    "task_id": request.task_id,
                    "file_count": len(request.files),
                    "reviewer_count": 5,
                },
            )
        except Exception:
            pass

        return self.engine.prepare_review_tasks(
            files=request.files,
            diff_content=request.diff_content,
            properties=request.properties if request.properties else None,
            model_router=self.model_router,
        )

    def finalize_review(
        self,
        request: ReviewRequest,
        task_responses: list[dict],
        output_dir: Path,
        skip_validation: bool = False,
    ) -> ReviewResult:
        """Phase 2: Parse responses, deduplicate, score, report.

        1. Parse subagent responses into ReviewerResults
        2. Collect all findings, tag with reviewer_id
        3. Deduplicate via Fingerprinter
        4. Calculate ConsensusScore
        5. Generate markdown report
        6. Return ReviewResult
        """
        _start_time = time.monotonic()
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

        validation_summary = {
            "before": len(deduped),
            "after": len(deduped),
            "verified": 0,
            "unverified": 0,
            "disputed": 0,
            "rejected": 0,
            "skipped": skip_validation,
        }
        weights: dict[str, float] = {}

        if not skip_validation:
            for df in deduped:
                try:
                    vf = self.validator.validate(df, skip_cross_check=True)
                    weights[df.fingerprint] = vf.weight
                    status = vf.validation_status
                    if status == ValidationStatus.HISTORICALLY_REJECTED:
                        validation_summary["rejected"] += 1
                    elif status == ValidationStatus.VERIFIED:
                        validation_summary["verified"] += 1
                    elif status == ValidationStatus.DISPUTED:
                        validation_summary["disputed"] += 1
                    else:
                        validation_summary["unverified"] += 1
                except Exception:
                    logger.exception(
                        "Validator failed for %s:%s -- keeping finding at weight 1.0 (fail-open)",
                        df.file,
                        df.line_start,
                    )
                    weights[df.fingerprint] = 1.0
                    validation_summary["unverified"] += 1

            rejected_fps = {fp for fp, w in weights.items() if w == 0.0}
            deduped = [df for df in deduped if df.fingerprint not in rejected_fps]
            validation_summary["after"] = len(deduped)

        cs_result = self.scorer.calculate(deduped, weights=weights if weights else None)

        report_path = output_dir / f"REVIEW-{request.task_id}.md"
        self._generate_report(
            request, cs_result, reviewer_results, report_path, self.model_router, validation_summary
        )

        doc_audit: DocAuditReport | None = None
        try:
            doc_audit = DocAuditor().analyze(
                task_id=request.task_id,
                files=request.files,
                diff_content=request.diff_content or "",
                output_dir=output_dir,
            )
            self._append_doc_audit_section(report_path, doc_audit)
        except Exception:
            logger.exception("Doc audit failed for %s -- skipped (fail-open)", request.task_id)

        try:
            from wfc.observability.instrument import emit_event, incr, observe

            emit_event(
                "review.scored",
                source="orchestrator",
                payload={
                    "task_id": request.task_id,
                    "cs": cs_result.cs,
                    "tier": cs_result.tier,
                    "passed": cs_result.passed,
                    "finding_count": len(cs_result.findings),
                    "mpr_applied": cs_result.minority_protection_applied,
                },
            )
            emit_event(
                "review.completed",
                source="orchestrator",
                payload={
                    "task_id": request.task_id,
                    "report_path": str(report_path),
                    "duration_seconds": time.monotonic() - _start_time,
                },
            )
            incr("review.completed")
            observe("review.duration", 0.0)
            observe("review.consensus_score", cs_result.cs)
        except Exception:
            pass

        return ReviewResult(
            task_id=request.task_id,
            consensus=cs_result,
            report_path=report_path,
            passed=cs_result.passed,
            doc_audit=doc_audit,
        )

    def _generate_report(
        self,
        request: ReviewRequest,
        cs_result: ConsensusScoreResult,
        reviewer_results: list[ReviewerResult],
        path: Path,
        model_router=None,
        validation_summary: dict | None = None,
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

        if validation_summary is not None:
            before = validation_summary.get("before", 0)
            after = validation_summary.get("after", 0)
            rejected = validation_summary.get("rejected", 0)
            verified = validation_summary.get("verified", 0)
            disputed = validation_summary.get("disputed", 0)
            unverified = validation_summary.get("unverified", 0)
            skipped = validation_summary.get("skipped", False)
            false_positive_rate = (rejected / before * 100) if before > 0 else 0.0
            lines.extend(
                [
                    "## Validation Summary",
                    "",
                    f"**Validation**: {'skipped' if skipped else 'performed'}",
                    f"**Findings before validation**: {before}",
                    f"**Findings after validation**: {after}",
                    f"**Verified**: {verified}",
                    f"**Unverified**: {unverified}",
                    f"**Disputed**: {disputed}",
                    f"**Rejected (excluded)**: {rejected}",
                    f"**False Positive Rate**: {false_positive_rate:.1f}%",
                    "",
                ]
            )

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

        if model_router is not None:
            lines.extend(["---", "", "## Cost Estimate", ""])
            total_cost = 0.0
            for task_result in reviewer_results:
                reviewer_id = task_result.reviewer_id
                prompt_tokens = task_result.token_count
                completion_tokens = max(200, len(task_result.summary) // 4)
                cost = model_router.estimate_cost(
                    reviewer_id,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )
                model = model_router.get_model(reviewer_id)
                lines.append(
                    f"- **{task_result.reviewer_name}**: model=`{model}`, "
                    f"~{prompt_tokens} prompt tokens, cost≈${cost:.4f}"
                )
                total_cost += cost
            lines.extend(["", f"**Total estimated cost**: ${total_cost:.4f}", ""])

        lines.extend(["---", "", "## Summary", "", cs_result.summary, ""])

        self._validate_output_path(path)
        with open(path, "w") as fh:
            fh.write("\n".join(lines))

    def _append_doc_audit_section(self, report_path: Path, doc_audit: DocAuditReport) -> None:
        """Append a Documentation Audit section to an existing review report."""
        n_gaps = len(doc_audit.gaps)
        n_ds = len(doc_audit.missing_docstrings)
        audit_file = doc_audit.report_path.name

        section_lines = [
            "",
            "---",
            "",
            "## Documentation Audit",
            "",
            f"**Doc files that may need updating**: {n_gaps}",
            f"**Missing docstrings in changed code**: {n_ds}",
            f"**Full audit report**: `{audit_file}`",
            "",
            doc_audit.summary,
            "",
        ]

        with open(report_path, "a") as fh:
            fh.write("\n".join(section_lines))
