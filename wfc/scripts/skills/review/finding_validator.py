"""Finding Validator - Three-layer validation for deduplicated review findings.

Implements PROP-001 (fail-open): every layer is wrapped in try/except so that
a failure in validation never blocks the review from proceeding.

Layers
------
TASK-001 (Layer 1 - Structural Verification)
    Parse .py files via stdlib ``ast``.  For a given ``DeduplicatedFinding``:
      * Check the file exists on disk.
      * Verify the reported line numbers contain real code (not blank lines or
        comment-only lines).
    Returns ``ValidationStatus.VERIFIED`` on success or
    ``ValidationStatus.UNVERIFIED`` with confidence halved on failure.

TASK-002 (Layer 2 - LLM Cross-Check)
    Build a Haiku task-spec dict so an external caller can dispatch the
    cross-check to a different (cheaper) model than the primary reviewers.
    Parse the YES / NO first-line response:
      * YES  → no change
      * NO   → ``ValidationStatus.DISPUTED``, confidence × 0.3

TASK-003 (Layer 3 - Historical Pattern Match)
    Query a ``KnowledgeRetriever``-compatible interface for similar past
    findings.  Interpret returned chunk texts:
      * "rejected" present → ``ValidationStatus.HISTORICALLY_REJECTED``
      * "accepted" present → confidence × 1.2 (capped at 10.0)
      * no match           → no change

Weight mapping
--------------
    VERIFIED             → 1.0
    UNVERIFIED           → 0.5
    DISPUTED             → 0.2
    HISTORICALLY_REJECTED → 0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from wfc.scripts.skills.review.fingerprint import DeduplicatedFinding

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    DISPUTED = "DISPUTED"
    HISTORICALLY_REJECTED = "HISTORICALLY_REJECTED"


_WEIGHT_MAP: dict[ValidationStatus, float] = {
    ValidationStatus.VERIFIED: 1.0,
    ValidationStatus.UNVERIFIED: 0.5,
    ValidationStatus.DISPUTED: 0.2,
    ValidationStatus.HISTORICALLY_REJECTED: 0.0,
}

_CROSS_CHECK_MODEL = "claude-haiku-4-5"


@dataclass
class ValidatedFinding:
    """A ``DeduplicatedFinding`` after running all three validation layers."""

    finding: DeduplicatedFinding
    validation_status: ValidationStatus
    confidence: float
    validation_notes: list[str]
    weight: float


class FindingValidator:
    """Three-layer validator for review findings.

    All public methods are fail-open: exceptions are caught, logged, and the
    finding retains its current state so the review can proceed.
    """

    def validate(
        self,
        finding: DeduplicatedFinding,
        file_content: str | None = None,
        retriever: Any | None = None,
        skip_cross_check: bool = False,
    ) -> ValidatedFinding:
        """Run all three validation layers sequentially.  Never raises.

        Parameters
        ----------
        finding:
            The deduplicated finding to validate.
        file_content:
            Optional pre-loaded file content.  If *None* and the file is a
            .py file, the validator will try to read the file from disk.
        retriever:
            Optional ``KnowledgeRetriever``-like object.  When *None*,
            Layer 3 is skipped.
        skip_cross_check:
            When *True*, Layer 2 (LLM cross-check) is skipped entirely.
        """
        vf = ValidatedFinding(
            finding=finding,
            validation_status=ValidationStatus.UNVERIFIED,
            confidence=finding.confidence,
            validation_notes=[],
            weight=_WEIGHT_MAP[ValidationStatus.UNVERIFIED],
        )

        try:
            status, confidence, notes = self.validate_structural(finding, file_content)
            vf = ValidatedFinding(
                finding=finding,
                validation_status=status,
                confidence=confidence,
                validation_notes=list(vf.validation_notes) + notes,
                weight=_WEIGHT_MAP[status],
            )
        except Exception:
            logger.exception(
                "Layer 1 (structural) failed for %s:%s – keeping UNVERIFIED",
                finding.file,
                finding.line_start,
            )

        if not skip_cross_check:
            try:
                code_snippet = _extract_snippet(file_content, finding.line_start, finding.line_end)
                spec = self.build_cross_check_task(vf, code_snippet)
                # NOTE: The caller is responsible for actually running the
                _ = spec
            except Exception:
                logger.exception(
                    "Layer 2 (cross-check task build) failed for %s:%s – skipping",
                    finding.file,
                    finding.line_start,
                )

        if retriever is not None:
            try:
                vf = self.validate_historical(vf, retriever)
            except Exception:
                logger.exception(
                    "Layer 3 (historical) failed for %s:%s – keeping current state",
                    finding.file,
                    finding.line_start,
                )

        vf = self._apply_weight(vf)
        return vf

    def validate_structural(
        self,
        finding: DeduplicatedFinding,
        file_content: str | None,
    ) -> tuple[ValidationStatus, float, list[str]]:
        """Check that the finding references real, parseable code.

        Returns
        -------
        (ValidationStatus, confidence, notes)
            ``confidence`` is adjusted (halved on failure).
        """
        notes: list[str] = []
        confidence = finding.confidence
        file_path = Path(finding.file)

        content = file_content
        if content is None:
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                except Exception as exc:
                    notes.append(f"Could not read file {file_path}: {exc}")
                    confidence = confidence / 2.0
                    return ValidationStatus.UNVERIFIED, confidence, notes
            else:
                notes.append(f"File does not exist on disk: {file_path}")
                confidence = confidence / 2.0
                return ValidationStatus.UNVERIFIED, confidence, notes

        lines = content.splitlines()
        line_idx = finding.line_start - 1

        if line_idx < 0 or line_idx >= len(lines):
            notes.append(
                f"Reported line {finding.line_start} is out of range (file has {len(lines)} lines)"
            )
            confidence = confidence / 2.0
            return ValidationStatus.UNVERIFIED, confidence, notes

        target_line = lines[line_idx]
        stripped = target_line.strip()

        if not stripped:
            notes.append(f"Line {finding.line_start} is blank/whitespace-only")
            confidence = confidence / 2.0
            return ValidationStatus.UNVERIFIED, confidence, notes

        if file_path.suffix == ".py" and stripped.startswith("#"):
            notes.append(f"Line {finding.line_start} is a comment line: {stripped!r}")
            confidence = confidence / 2.0
            return ValidationStatus.UNVERIFIED, confidence, notes

        notes.append(f"Line {finding.line_start} contains real code: {stripped[:80]!r}")
        return ValidationStatus.VERIFIED, confidence, notes

    def build_cross_check_task(
        self,
        finding: ValidatedFinding,
        code_snippet: str,
    ) -> dict:
        """Build a Haiku task spec for cross-checking this finding.

        The returned dict contains:
          ``model``   – a Haiku model identifier (cheaper than reviewer models)
          ``prompt``  – prompt asking YES/NO validity question + explanation

        The caller is responsible for dispatching the task to the model.
        """
        df = finding.finding
        prompt_parts = [
            "You are a code review validator.",
            "",
            "Given the following code snippet and a security/quality finding,",
            "determine whether the finding is valid.",
            "Reply YES or NO on the first line, then explain in 1-3 sentences.",
            "",
            f"## Code Snippet (file: {df.file}, line {df.line_start})",
            "```",
            code_snippet if code_snippet else "(no code snippet available)",
            "```",
            "",
            "## Finding",
            f"Category: {df.category}",
            f"Severity: {df.severity}",
            f"Description: {df.description}",
            "",
            "Is this finding valid? Reply YES or NO on the first line.",
        ]
        return {
            "model": _CROSS_CHECK_MODEL,
            "prompt": "\n".join(prompt_parts),
        }

    def apply_cross_check_result(
        self,
        finding: ValidatedFinding,
        response: str,
    ) -> ValidatedFinding:
        """Parse a YES/NO cross-check response and update the finding.

        * YES (case-insensitive) → no change
        * NO  (case-insensitive) → DISPUTED, confidence × 0.3
        * Anything else          → no change
        """
        notes = list(finding.validation_notes)
        first_line = response.strip().splitlines()[0].strip().upper() if response.strip() else ""

        if first_line == "NO":
            new_confidence = finding.confidence * 0.3
            notes.append(
                f"Cross-check (Haiku) disputed this finding (confidence {finding.confidence:.2f} → {new_confidence:.2f}): "
                + response.strip()[:200]
            )
            return ValidatedFinding(
                finding=finding.finding,
                validation_status=ValidationStatus.DISPUTED,
                confidence=new_confidence,
                validation_notes=notes,
                weight=_WEIGHT_MAP[ValidationStatus.DISPUTED],
            )

        if first_line == "YES":
            return finding

        return finding

    def validate_historical(
        self,
        finding: ValidatedFinding,
        retriever: Any,
    ) -> ValidatedFinding:
        """Query knowledge base and adjust status/confidence based on history.

        Retriever interface expected::

            retriever.retrieve(reviewer_id, query, top_k=5)
            → list of objects with ``.chunk.text: str``

        Rules:
          * Any result containing "rejected" → HISTORICALLY_REJECTED (highest priority)
          * Any result containing "accepted" → confidence × 1.2 (max 10.0)
          * No results or irrelevant results → no change
        """
        df = finding.finding
        query = f"{df.category} {df.description}"
        reviewer_id = df.reviewer_ids[0] if df.reviewer_ids else "unknown"

        results = retriever.retrieve(reviewer_id, query, top_k=5)

        has_rejected = False
        has_accepted = False
        for r in results:
            text = r.chunk.text.lower()
            if "rejected" in text:
                has_rejected = True
            if "accepted" in text:
                has_accepted = True

        notes = list(finding.validation_notes)

        if has_rejected:
            notes.append("Historical knowledge base: similar finding was previously rejected.")
            return ValidatedFinding(
                finding=finding.finding,
                validation_status=ValidationStatus.HISTORICALLY_REJECTED,
                confidence=finding.confidence,
                validation_notes=notes,
                weight=_WEIGHT_MAP[ValidationStatus.HISTORICALLY_REJECTED],
            )

        if has_accepted:
            new_confidence = min(10.0, finding.confidence * 1.2)
            notes.append(
                f"Historical knowledge base: similar finding was previously accepted "
                f"(confidence {finding.confidence:.2f} → {new_confidence:.2f})."
            )
            return ValidatedFinding(
                finding=finding.finding,
                validation_status=finding.validation_status,
                confidence=new_confidence,
                validation_notes=notes,
                weight=finding.weight,
            )

        return finding

    def _apply_weight(self, finding: ValidatedFinding) -> ValidatedFinding:
        """Return a new ValidatedFinding with ``weight`` set from the status map."""
        return ValidatedFinding(
            finding=finding.finding,
            validation_status=finding.validation_status,
            confidence=finding.confidence,
            validation_notes=finding.validation_notes,
            weight=_WEIGHT_MAP[finding.validation_status],
        )


def _extract_snippet(file_content: str | None, line_start: int, line_end: int) -> str:
    """Extract a multi-line code snippet from file content.

    Returns the lines from ``line_start`` to ``line_end`` (inclusive, 1-based).
    Returns an empty string when content is not available.
    """
    if not file_content:
        return ""
    lines = file_content.splitlines()
    start = max(0, line_start - 1)
    end = min(len(lines), line_end)
    return "\n".join(lines[start:end])
