"""
AgenticValidator - Detect and recover from parse failures in reviewer output.

When a reviewer produces a non-empty response that yields zero findings after
parsing, this module builds a correction prompt for re-invocation. The caller
(orchestrator) decides whether to execute the retry.

Fail-open: On any internal error, returns the original empty results unchanged.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

REQUIRED_FINDING_KEYS = frozenset({"file", "line_start", "category", "severity", "description"})
_CORRECTION_MODEL = "claude-haiku-4-5"


class AgenticValidator:
    """Detect reviewer parse failures and build correction task specs.

    All public methods are fail-open: exceptions are caught, logged, and
    a safe default is returned so the review pipeline can proceed.
    """

    def check(
        self,
        reviewer_id: str,
        response: str,
        findings: list[dict],
    ) -> dict | None:
        """Check whether a reviewer's output needs a correction retry.

        Returns ``None`` if no intervention is needed, or a task-spec dict
        that the caller can dispatch to a cheaper model for reformatting.

        Parameters
        ----------
        reviewer_id:
            Identifier of the reviewer that produced the output.
        response:
            Raw text output from the reviewer.
        findings:
            Parsed findings list (may be empty if parsing failed).

        Returns
        -------
        dict | None
            A retry task spec with keys ``model``, ``prompt``,
            ``reviewer_id``, and ``retry_reason``, or ``None``.
        """
        try:
            return self._check_impl(reviewer_id, response, findings)
        except Exception:
            logger.exception(
                "AgenticValidator.check failed for %s -- returning None (fail-open)",
                reviewer_id,
            )
            return None

    def validate_finding_keys(self, finding: dict) -> tuple[bool, list[str]]:
        """Check that a finding dict contains all required keys.

        Returns
        -------
        (is_valid, missing_keys)
            ``is_valid`` is True when all required keys are present.
            ``missing_keys`` is a sorted list of any absent keys.
        """
        try:
            missing = sorted(REQUIRED_FINDING_KEYS - finding.keys())
            return len(missing) == 0, missing
        except Exception:
            return False, sorted(REQUIRED_FINDING_KEYS)

    def _check_impl(
        self,
        reviewer_id: str,
        response: str,
        findings: list[dict],
    ) -> dict | None:
        stripped = response.strip()
        if not stripped:
            return None
        if findings:
            return None

        MAX_EXCERPT = 2000
        excerpt = stripped[:MAX_EXCERPT]
        if len(stripped) > MAX_EXCERPT:
            excerpt += "\n[... truncated ...]"

        return {
            "model": _CORRECTION_MODEL,
            "prompt": self._build_correction_prompt(reviewer_id, excerpt),
            "reviewer_id": reviewer_id,
            "retry_reason": "non_empty_response_zero_findings",
        }

    def _build_correction_prompt(self, reviewer_id: str, excerpt: str) -> str:
        return (
            "You are a response parser assistant.\n\n"
            f"A {reviewer_id} code reviewer produced the following output, but the JSON "
            "findings could not be extracted. Please reformat the output as a valid JSON "
            "array of finding objects.\n\n"
            "Each finding MUST have these keys:\n"
            "- file (string): path to the file\n"
            "- line_start (int): starting line number\n"
            "- category (string): finding category\n"
            "- severity (float): severity 1-10\n"
            "- description (string): what the issue is\n\n"
            "Optional keys: line_end, confidence, remediation\n\n"
            "If the original output genuinely contains no findings, return: []\n\n"
            "## Original Reviewer Output\n\n"
            f"```\n{excerpt}\n```\n\n"
            "Return ONLY the JSON array, no other text."
        )
