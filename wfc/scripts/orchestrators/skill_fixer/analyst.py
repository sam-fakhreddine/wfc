"""Analyst agent - LLM diagnosis with fallback heuristics.

Uses LLM if response_fn provided, otherwise applies rule-based heuristics.
"""

import json
from typing import Callable, Dict, List, Optional

from .prompts import prepare_analyst_prompt
from .schemas import DimensionScore, DimensionSummary, Issue, SkillDiagnosis, SkillManifest


class SkillAnalyst:
    """
    Analyzes skills against rubric with LLM or fallback heuristics.

    Gracefully degrades to heuristic analysis when no LLM available.
    """

    def analyze(
        self,
        skill_content: str,
        manifest: SkillManifest,
        response_fn: Optional[Callable[[str], str]] = None,
    ) -> SkillDiagnosis:
        """
        Analyze skill against rubric.

        Args:
            skill_content: Full SKILL.md content
            manifest: Cataloger manifest
            response_fn: Optional LLM response function

        Returns:
            SkillDiagnosis with scores and issues
        """
        if response_fn:
            return self._analyze_with_llm(skill_content, manifest, response_fn)
        else:
            return self._analyze_fallback(skill_content, manifest)

    def _analyze_with_llm(
        self,
        skill_content: str,
        manifest: SkillManifest,
        response_fn: Callable[[str], str],
    ) -> SkillDiagnosis:
        """Analyze with LLM."""
        prompt = prepare_analyst_prompt(str(manifest.skill_path))

        response = response_fn(prompt)

        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "{" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            else:
                raise ValueError("No JSON found in response")

            data = json.loads(json_str)

            return self._dict_to_diagnosis(data)
        except Exception:
            return self._analyze_fallback(skill_content, manifest)

    def _analyze_fallback(self, skill_content: str, manifest: SkillManifest) -> SkillDiagnosis:
        """Fallback heuristic analysis."""
        issues: List[Issue] = []
        scores: Dict[str, DimensionScore] = {}

        desc_len = manifest.frontmatter.description_length

        if desc_len == 0 or manifest.frontmatter.description.upper() in ["TODO", "TBD"]:
            issues.append(
                Issue(
                    id="SK-01",
                    dimension="TRIGGER_COVERAGE",
                    severity="critical",
                    description="Empty or placeholder description",
                    fix_directive="Write comprehensive description covering all user phrasings",
                    evidence=[manifest.frontmatter.description],
                )
            )
            scores["TRIGGER_COVERAGE"] = DimensionScore(score=0, rationale="Empty/TODO description")

        elif desc_len < 50:
            issues.append(
                Issue(
                    id="SK-02",
                    dimension="TRIGGER_COVERAGE",
                    severity="major",
                    description="Description too short/timid",
                    fix_directive="Expand description to cover all triggering phrasings",
                    evidence=[f"Length: {desc_len} chars"],
                )
            )
            scores["TRIGGER_COVERAGE"] = DimensionScore(score=1, rationale="Too short")

        elif desc_len > 1024:
            issues.append(
                Issue(
                    id="SK-03",
                    dimension="TRIGGER_FORMAT",
                    severity="critical",
                    description="Description exceeds 1024 character limit",
                    fix_directive="Condense description to <1024 chars",
                    evidence=[f"Length: {desc_len} chars"],
                )
            )
            scores["TRIGGER_FORMAT"] = DimensionScore(score=0, rationale="Too long")

        else:
            scores["TRIGGER_COVERAGE"] = DimensionScore(score=2, rationale="Adequate length")
            scores["TRIGGER_FORMAT"] = DimensionScore(score=3, rationale="Within limits")

        if manifest.body.total_lines > 700:
            issues.append(
                Issue(
                    id="SK-11",
                    dimension="ANTI_BLOAT",
                    severity="major",
                    description="SKILL.md exceeds 700 lines",
                    fix_directive="Extract content into references/ or condense",
                    evidence=[f"{manifest.body.total_lines} lines"],
                )
            )
            scores["ANTI_BLOAT"] = DimensionScore(score=0, rationale="Too long")
        else:
            scores["ANTI_BLOAT"] = DimensionScore(score=3, rationale="Reasonable length")

        if manifest.body.section_count < 2:
            issues.append(
                Issue(
                    id="SK-05",
                    dimension="STRUCTURE_PATTERN",
                    severity="minor",
                    description="Too few sections for clear structure",
                    fix_directive="Add sections for better organization",
                    evidence=[f"{manifest.body.section_count} sections"],
                )
            )
            scores["STRUCTURE_PATTERN"] = DimensionScore(score=1, rationale="Minimal structure")
        else:
            scores["STRUCTURE_PATTERN"] = DimensionScore(score=2, rationale="Structured")

        if manifest.cross_references.referenced_but_missing:
            issues.append(
                Issue(
                    id="SK-08",
                    dimension="FILE_INTEGRITY",
                    severity="critical",
                    description="Phantom file references (files don't exist)",
                    fix_directive="Remove references or create missing files",
                    evidence=manifest.cross_references.referenced_but_missing,
                )
            )
            scores["FILE_INTEGRITY"] = DimensionScore(score=0, rationale="Broken references")
        else:
            scores["FILE_INTEGRITY"] = DimensionScore(score=3, rationale="All refs valid")

        if manifest.filesystem.scripts_non_executable:
            issues.append(
                Issue(
                    id="SK-10",
                    dimension="SCRIPT_QUALITY",
                    severity="major",
                    description="Non-executable scripts",
                    fix_directive="Add execute permissions: chmod +x",
                    evidence=manifest.filesystem.scripts_non_executable,
                )
            )
            scores["SCRIPT_QUALITY"] = DimensionScore(score=1, rationale="Scripts not executable")
        elif manifest.filesystem.scripts_count > 0:
            scores["SCRIPT_QUALITY"] = DimensionScore(score=3, rationale="Scripts executable")

        if scores:
            avg_score = sum(s.score for s in scores.values()) / len(scores)
        else:
            avg_score = 0.0

        critical_count = sum(1 for issue in issues if issue.severity == "critical")

        if avg_score >= 2.5 and critical_count == 0:
            grade = "A"
        elif avg_score >= 2.0 and critical_count < 2:
            grade = "B"
        elif avg_score >= 1.5 and critical_count < 4:
            grade = "C"
        elif avg_score >= 1.0:
            grade = "D"
        else:
            grade = "F"

        if grade in ["D", "F"]:
            rewrite_scope = "full"
        elif critical_count > 0:
            rewrite_scope = "partial"
        elif desc_len < 50 or desc_len > 1024:
            rewrite_scope = "description_only"
        else:
            rewrite_scope = "cosmetic"

        dimension_summaries = {
            "TRIGGERING": DimensionSummary(
                category="TRIGGERING",
                avg_score=sum(s.score for k, s in scores.items() if "TRIGGER" in k)
                / max(1, len([k for k in scores if "TRIGGER" in k])),
                dimensions=[k for k in scores if "TRIGGER" in k],
                key_issues=[i.description for i in issues if "TRIGGER" in i.dimension],
            ),
            "INSTRUCTION": DimensionSummary(
                category="INSTRUCTION",
                avg_score=sum(
                    s.score for k, s in scores.items() if k in ["ANTI_BLOAT", "STRUCTURE_PATTERN"]
                )
                / max(1, len([k for k in scores if k in ["ANTI_BLOAT", "STRUCTURE_PATTERN"]])),
                dimensions=[k for k in scores if k in ["ANTI_BLOAT", "STRUCTURE_PATTERN"]],
                key_issues=[
                    i.description
                    for i in issues
                    if i.dimension in ["ANTI_BLOAT", "STRUCTURE_PATTERN"]
                ],
            ),
            "OPERATIONAL": DimensionSummary(
                category="OPERATIONAL",
                avg_score=sum(
                    s.score for k, s in scores.items() if k in ["FILE_INTEGRITY", "SCRIPT_QUALITY"]
                )
                / max(1, len([k for k in scores if k in ["FILE_INTEGRITY", "SCRIPT_QUALITY"]])),
                dimensions=[k for k in scores if k in ["FILE_INTEGRITY", "SCRIPT_QUALITY"]],
                key_issues=[
                    i.description
                    for i in issues
                    if i.dimension in ["FILE_INTEGRITY", "SCRIPT_QUALITY"]
                ],
            ),
        }

        return SkillDiagnosis(
            scores=scores,
            dimension_summaries=dimension_summaries,
            issues=issues,
            overall_grade=grade,
            rewrite_recommended=(grade != "A"),
            rewrite_scope=rewrite_scope,
            summary=f"Fallback analysis: Grade {grade}, {len(issues)} issues, avg score {avg_score:.1f}",
        )

    def _dict_to_diagnosis(self, data: Dict) -> SkillDiagnosis:
        """Convert dict from LLM to SkillDiagnosis."""
        scores = {
            k: DimensionScore(**v) if isinstance(v, dict) else v
            for k, v in data.get("scores", {}).items()
        }

        dimension_summaries = {
            k: DimensionSummary(**v) if isinstance(v, dict) else v
            for k, v in data.get("dimension_summaries", {}).items()
        }

        issues = [Issue(**i) if isinstance(i, dict) else i for i in data.get("issues", [])]

        return SkillDiagnosis(
            scores=scores,
            dimension_summaries=dimension_summaries,
            issues=issues,
            overall_grade=data.get("overall_grade", "C"),
            rewrite_recommended=data.get("rewrite_recommended", True),
            rewrite_scope=data.get("rewrite_scope", "full"),
            summary=data.get("summary", ""),
        )
