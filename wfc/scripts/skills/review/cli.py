"""CLI interface for the five-agent consensus review system.

Provides argument parsing, output formatting (text and JSON), and a main
entry point that coordinates prepare_review / finalize_review via the
ReviewOrchestrator.

The CLI does NOT execute actual review agents -- it prepares task specs and
formats output.  Claude Code (or a test harness) executes the Task tools
and passes results back.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from wfc.scripts.skills.review.orchestrator import ReviewOrchestrator, ReviewRequest, ReviewResult

if TYPE_CHECKING:
    pass


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for wfc review CLI."""
    parser = argparse.ArgumentParser(
        prog="wfc review",
        description="Five-agent consensus code review",
    )
    parser.add_argument("--files", nargs="+", required=True, help="Files to review")
    parser.add_argument("--diff", default="", help="Git diff content or path to diff file")
    parser.add_argument("--task-id", default="REVIEW-001", help="Task identifier")
    parser.add_argument("--output-dir", default=".", help="Output directory for report")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--emergency-bypass",
        action="store_true",
        help="Apply emergency bypass",
    )
    parser.add_argument("--bypass-reason", default="", help="Reason for emergency bypass")
    parser.add_argument("--bypassed-by", default="unknown", help="Who is bypassing")
    return parser


def format_text_output(result: ReviewResult) -> str:
    """Format review result as human-readable text."""
    cs_result = result.consensus
    status = "PASSED" if result.passed else "FAILED"
    findings = cs_result.findings

    lines = [
        f"Review: {result.task_id}",
        f"Status: {status}",
        f"Consensus Score: CS={cs_result.cs:.2f} ({cs_result.tier})",
        f"Findings: {len(findings)}",
        "",
    ]

    if findings:
        lines.append("Findings:")
        for sf in findings:
            f = sf.finding
            tier_label = sf.tier.upper()
            lines.append(
                f"  [{tier_label}] {f.file}:{f.line_start} - {f.category} "
                f"(severity={f.severity:.1f}, k={f.k})"
            )
        lines.append("")

    lines.append(f"Summary: {cs_result.summary}")

    return "\n".join(lines)


def format_json_output(result: ReviewResult) -> str:
    """Format review result as JSON."""
    cs_result = result.consensus
    findings_list = []
    for sf in cs_result.findings:
        f = sf.finding
        findings_list.append(
            {
                "file": f.file,
                "line_start": f.line_start,
                "line_end": f.line_end,
                "category": f.category,
                "severity": f.severity,
                "confidence": f.confidence,
                "description": f.description,
                "k": f.k,
                "R_i": sf.R_i,
                "tier": sf.tier,
                "reviewer_ids": f.reviewer_ids,
            }
        )

    data = {
        "task_id": result.task_id,
        "passed": result.passed,
        "cs": cs_result.cs,
        "tier": cs_result.tier,
        "findings_count": len(cs_result.findings),
        "findings": findings_list,
        "R_bar": cs_result.R_bar,
        "R_max": cs_result.R_max,
        "k_total": cs_result.k_total,
        "minority_protection_applied": cs_result.minority_protection_applied,
        "summary": cs_result.summary,
    }

    return json.dumps(data, indent=2)


def _resolve_diff(diff_arg: str) -> str:
    """Resolve --diff argument: if it's a file path, read it; otherwise return as-is."""
    if not diff_arg:
        return ""
    path = Path(diff_arg)
    if path.is_file():
        return path.read_text()
    return diff_arg


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point. Returns exit code (0=pass, 1=fail)."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.emergency_bypass and not args.bypass_reason:
        print("Error: --bypass-reason is required when --emergency-bypass is set.", file=sys.stderr)
        return 1

    diff_content = _resolve_diff(args.diff)

    request = ReviewRequest(
        task_id=args.task_id,
        files=args.files,
        diff_content=diff_content,
    )

    orchestrator = ReviewOrchestrator()

    task_specs = orchestrator.prepare_review(request)

    output_dir = Path(args.output_dir).resolve()
    result = orchestrator.finalize_review(request, task_specs, output_dir)

    if args.emergency_bypass:
        try:
            from wfc.scripts.skills.review.emergency_bypass import EmergencyBypass

            bypass = EmergencyBypass(audit_dir=output_dir)
            bypass.create_bypass(
                task_id=args.task_id,
                reason=args.bypass_reason,
                bypassed_by=args.bypassed_by,
                cs_result=result.consensus,
            )
        except ImportError:
            print(
                "Warning: emergency_bypass module not available, skipping bypass.",
                file=sys.stderr,
            )

    if args.format == "json":
        print(format_json_output(result))
    else:
        print(format_text_output(result))

    return 0 if result.passed else 1
