"""
Validate Orchestrator

Coordinates analysis → report generation.
"""

from pathlib import Path
from typing import Optional

from .analyzer import SmartAnalysis, ValidateAnalyzer


class ValidateOrchestrator:
    """
    Orchestrates validation analysis.

    ELEGANT: Simple coordination.
    MULTI-TIER: Logic layer only.
    """

    def __init__(self):
        self.analyzer = ValidateAnalyzer()

    def analyze(
        self, subject: str, content: Optional[str] = None, output_dir: Optional[Path] = None
    ) -> SmartAnalysis:
        """
        Perform analysis and generate report.

        Returns SmartAnalysis with verdict.
        """

        if content is None:
            content = self._load_plan_content()

        analysis = self.analyzer.analyze(subject, content)

        if output_dir:
            report_path = output_dir / "VALIDATE.md"
            self._generate_report(analysis, report_path)

        return analysis

    def _load_plan_content(self) -> str:
        """Load content from plan directory"""
        return "[Plan content would be loaded here]"

    def _generate_report(self, analysis: SmartAnalysis, path: Path) -> None:
        """Generate VALIDATE.md report"""
        lines = [
            "# Validation Analysis",
            "",
            f"## Subject: {analysis.subject}",
            f"## Verdict: {analysis.verdict.value}",
            f"## Overall Score: {analysis.overall_score:.1f}/10",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            analysis.executive_summary,
            "",
            "---",
            "",
            "## Dimension Analysis",
            "",
        ]

        for dim in analysis.dimensions:
            lines.extend(
                [
                    f"### {dim.dimension} — Score: {dim.score}/10",
                    "",
                    "**Strengths:**",
                ]
            )
            for strength in dim.strengths:
                lines.append(f"- {strength}")
            lines.append("")
            lines.append("**Concerns:**")
            for concern in dim.concerns:
                lines.append(f"- {concern}")
            lines.extend(
                [
                    "",
                    f"**Recommendation:** {dim.recommendation}",
                    "",
                ]
            )

        if analysis.alternatives:
            lines.extend(
                [
                    "---",
                    "",
                    "## Simpler Alternatives",
                    "",
                ]
            )
            for alt in analysis.alternatives:
                lines.append(f"- {alt}")
            lines.append("")

        lines.extend(
            [
                "---",
                "",
                "## Final Recommendation",
                "",
                analysis.final_recommendation,
                "",
            ]
        )

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write("\n".join(lines))
