"""
Reviewer Engine

Two-phase execution engine that replaces PersonaReviewExecutor.
Phase 1: prepare_review_tasks() - builds Task tool specs for 5 fixed reviewers.
Phase 2: parse_results() - parses subagent responses into ReviewerResults.

This module does NOT spawn subagents. It prepares specifications that Claude Code
executes via the Task tool, maintaining proper subagent isolation.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .reviewer_loader import ReviewerConfig, ReviewerLoader

if TYPE_CHECKING:
    from wfc.scripts.knowledge.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)


@dataclass
class ReviewerResult:
    """Result from a single reviewer's analysis."""

    reviewer_id: str
    reviewer_name: str
    score: float
    passed: bool
    findings: list[dict] = field(default_factory=list)
    summary: str = ""
    relevant: bool = True
    token_count: int = 0


REVIEWER_NAMES: dict[str, str] = {
    "security": "Security Reviewer",
    "correctness": "Correctness Reviewer",
    "performance": "Performance Reviewer",
    "maintainability": "Maintainability Reviewer",
    "reliability": "Reliability Reviewer",
}


class ReviewerEngine:
    """
    Two-phase review engine for the 5 fixed reviewers.

    Replaces PersonaReviewExecutor with a simpler, deterministic approach:
    - No dynamic persona selection (always 5 fixed reviewers)
    - Prompts loaded from wfc/reviewers/<id>/PROMPT.md
    - Knowledge context from wfc/reviewers/<id>/KNOWLEDGE.md
    - Relevance gate skips reviewers whose domain doesn't match the diff
    """

    def __init__(
        self,
        loader: ReviewerLoader | None = None,
        retriever: KnowledgeRetriever | None = None,
    ):
        self.loader = loader or ReviewerLoader()
        self.retriever = retriever

    def prepare_review_tasks(
        self,
        files: list[str],
        diff_content: str = "",
        properties: list[dict] | None = None,
        model_router: object | None = None,
        single_model: str | None = None,
    ) -> list[dict]:
        """
        Phase 1: Prepare task specifications for Claude Code's Task tool.

        Loads all 5 reviewers, builds prompts with file list + diff + properties,
        and returns task specs. Irrelevant reviewers are marked with relevant=False
        so the caller can skip them.

        Args:
            files: List of file paths to review.
            diff_content: Git diff content (optional but recommended).
            properties: List of property dicts to verify (optional).

        Args:
            model_router: Optional ModelRouter instance. When provided, each spec
                gets a "model" key set by router.get_model(reviewer_id, diff_lines).
            single_model: When set, forces this model for ALL reviewers (overrides router).

        Returns:
            List of 5 task spec dicts, each with:
            - reviewer_id: str
            - reviewer_name: str
            - prompt: str (full prompt for the subagent)
            - temperature: float
            - relevant: bool
            - token_count: int (approximate token count of prompt)
            - model: str (only present when model_router or single_model is provided)
        """
        diff_files = files if files else []
        configs = self.loader.load_all(diff_files=diff_files)

        tasks: list[dict] = []
        for config in configs:
            prompt = self._build_task_prompt(config, files, diff_content, properties)
            token_count = len(prompt) // 4

            task_spec = {
                "reviewer_id": config.id,
                "reviewer_name": REVIEWER_NAMES.get(config.id, f"{config.id.title()} Reviewer"),
                "prompt": prompt,
                "temperature": config.temperature,
                "relevant": config.relevant,
                "token_count": token_count,
            }
            if single_model:
                task_spec["model"] = single_model
            elif model_router is not None:
                diff_lines = len(diff_content.splitlines()) if diff_content else 0
                task_spec["model"] = model_router.get_model(config.id, diff_lines)
            tasks.append(task_spec)

        total_tokens = sum(t["token_count"] for t in tasks)
        relevant_count = sum(1 for t in tasks if t["relevant"])
        logger.info(
            "Prepared %d review tasks (%d relevant, ~%d total tokens)",
            len(tasks),
            relevant_count,
            total_tokens,
        )

        return tasks

    def parse_results(self, task_responses: list[dict]) -> list[ReviewerResult]:
        """
        Phase 2: Parse subagent responses into ReviewerResults.

        Args:
            task_responses: List of dicts, each with:
                - reviewer_id: str
                - response: str (raw text output from subagent)

        Returns:
            List of ReviewerResult objects.
        """
        results: list[ReviewerResult] = []

        for item in task_responses:
            reviewer_id = item.get("reviewer_id", "unknown")
            response = item.get("response", "")
            reviewer_name = REVIEWER_NAMES.get(reviewer_id, f"{reviewer_id.title()} Reviewer")

            if not response.strip():
                results.append(
                    ReviewerResult(
                        reviewer_id=reviewer_id,
                        reviewer_name=reviewer_name,
                        score=0.0,
                        passed=False,
                        findings=[],
                        summary="No response received from reviewer.",
                        relevant=True,
                        token_count=0,
                    )
                )
                continue

            findings = self._parse_findings(response)
            score = self._extract_score(findings, response)
            summary = self._extract_summary(findings, response, reviewer_id)

            results.append(
                ReviewerResult(
                    reviewer_id=reviewer_id,
                    reviewer_name=reviewer_name,
                    score=score,
                    passed=score >= 7.0,
                    findings=findings,
                    summary=summary,
                    relevant=True,
                    token_count=0,
                )
            )

        return results

    def _build_task_prompt(
        self,
        config: ReviewerConfig,
        files: list[str],
        diff_content: str,
        properties: list[dict] | None,
    ) -> str:
        """
        Build the full prompt for a reviewer task.

        Combines: PROMPT.md content + knowledge context + file list + diff + properties.
        """
        parts: list[str] = []

        parts.append(config.prompt)

        if self.retriever is not None and diff_content:
            rag_results = self.retriever.retrieve(config.id, diff_content, top_k=5)
            knowledge_section = self.retriever.format_knowledge_section(
                rag_results, token_budget=self.retriever.config.token_budget
            )
            if knowledge_section:
                parts.append("\n---\n")
                parts.append(knowledge_section)
        elif config.knowledge:
            parts.append("\n---\n")
            parts.append("# Repository Knowledge\n")
            parts.append(config.knowledge)

        parts.append("\n---\n")
        parts.append("# Files to Review\n")
        if files:
            for file_path in files:
                parts.append(f"- `{file_path}`")
        else:
            parts.append("No files specified.")

        if diff_content:
            parts.append("\n# Diff\n")
            parts.append("```diff")
            parts.append(diff_content)
            parts.append("```")

        if properties:
            parts.append("\n# Properties to Verify\n")
            for prop in properties:
                prop_type = prop.get("type", "UNKNOWN")
                prop_stmt = prop.get("statement", "")
                parts.append(f"- **{prop_type}**: {prop_stmt}")

        parts.append("\n---\n")
        parts.append("# Instructions\n")
        parts.append(
            "Analyze the files and diff above according to your domain. "
            "Return your findings as a JSON array of objects using the Output Format "
            "defined in your prompt. If you find no issues, return an empty array `[]`.\n"
            "After the findings array, provide a brief summary line starting with "
            "`SUMMARY:` and a score line starting with `SCORE:` (0-10)."
        )

        return "\n".join(parts)

    def _parse_findings(self, response: str) -> list[dict]:
        """
        Extract JSON findings from reviewer response text.

        Handles:
        - JSON array at top level
        - Single JSON object (wrapped into a list)
        - JSON embedded in markdown code blocks
        - Multiple separate JSON objects
        """
        findings: list[dict] = []

        MAX_RESPONSE_LEN = 500_000
        if len(response) > MAX_RESPONSE_LEN:
            response = response[:MAX_RESPONSE_LEN]

        array_match = re.search(r"\[[\s\S]*?\]", response)
        if array_match:
            try:
                parsed = json.loads(array_match.group())
                if isinstance(parsed, list):
                    findings.extend(item for item in parsed if isinstance(item, dict))
                    if findings:
                        return findings
            except json.JSONDecodeError:
                pass

        json_blocks = re.findall(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", response)
        if not json_blocks:
            json_blocks = re.findall(r"(\{[^{}]*\})", response)

        for block in json_blocks:
            try:
                parsed = json.loads(block)
                if isinstance(parsed, dict):
                    findings.append(parsed)
            except json.JSONDecodeError:
                continue

        return findings

    def _extract_score(self, findings: list[dict], response: str) -> float:
        """Extract overall score from response."""
        score_match = re.search(r"SCORE:\s*([\d.]+)", response)
        if score_match:
            try:
                score = float(score_match.group(1))
                return max(0.0, min(10.0, score))
            except ValueError:
                pass

        if not findings:
            return 10.0

        max_severity = max(float(f.get("severity", 1)) for f in findings)
        return max(0.0, 10.0 - max_severity)

    def _extract_summary(self, findings: list[dict], response: str, reviewer_id: str) -> str:
        """Extract summary from response."""
        summary_match = re.search(r"SUMMARY:\s*(.+)", response)
        if summary_match:
            return summary_match.group(1).strip()

        if not findings:
            return f"{reviewer_id.title()} review: no issues found."

        count = len(findings)
        high_sev = sum(1 for f in findings if float(f.get("severity", 0)) >= 7)
        if high_sev:
            return f"{reviewer_id.title()} review: {count} finding(s), {high_sev} high severity."
        return f"{reviewer_id.title()} review: {count} finding(s)."
