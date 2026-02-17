"""Dual-Judge Evaluation Engine for WFC review quality assessment.

Two independent judges score a WFC review against ground truth using
precision, recall, severity_accuracy, and F1.
Inter-judge agreement is measured via Cohen's Kappa.
"""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class JudgeScore:
    """Scores produced by a single judge evaluating a WFC review."""

    precision: float
    recall: float
    severity_accuracy: float
    f1: float
    notes: str


@dataclass
class DualJudgeResult:
    """Combined result from two independent judges."""

    judge_1: JudgeScore
    judge_2: JudgeScore
    agreement: float
    consensus_precision: float
    consensus_recall: float
    consensus_f1: float


def _compute_f1(precision: float, recall: float) -> float:
    """Compute F1 from precision and recall. Returns 0.0 if both are 0."""
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _categories_match(cat_a: str, cat_b: str) -> bool:
    """Match categories via case-insensitive substring check (either direction)."""
    a = cat_a.lower()
    b = cat_b.lower()
    return a in b or b in a


def _finding_matches(reported: dict, expected: dict) -> bool:
    """Return True if reported finding matches expected finding.

    Match criteria:
    - Same category (substring match, case-insensitive)
    - line_start within +-5 lines
    """
    if not _categories_match(reported.get("category", ""), expected.get("category", "")):
        return False
    reported_line = reported.get("line_start", 0)
    expected_line = expected.get("line_start", 0)
    return abs(reported_line - expected_line) <= 5


def _score_review(
    review_output: list[dict],
    ground_truth: list[dict],
    notes: str = "",
) -> JudgeScore:
    """Core pure-Python scoring logic used by both judges.

    Precision = |matched_findings| / |review_output|  (0 if review_output empty)
    Recall    = |matched_findings| / |ground_truth|    (1.0 if ground_truth empty)
    Severity accuracy = mean(1 - |rep_sev - exp_sev| / 10) for matched findings
    F1        = 2*P*R / (P+R) if both > 0, else 0
    """
    if not ground_truth:
        if not review_output:
            return JudgeScore(
                precision=1.0,
                recall=1.0,
                severity_accuracy=1.0,
                f1=1.0,
                notes=notes or "True negative: empty ground truth, no findings reported",
            )
        else:
            return JudgeScore(
                precision=0.0,
                recall=1.0,
                severity_accuracy=0.0,
                f1=0.0,
                notes=notes or "True negative: empty ground truth, but findings were reported",
            )

    if not review_output:
        return JudgeScore(
            precision=0.0,
            recall=0.0,
            severity_accuracy=0.0,
            f1=0.0,
            notes=notes or "No findings reported",
        )

    matched_reported: set[int] = set()
    matched_expected: set[int] = set()
    severity_scores: list[float] = []

    for ei, expected in enumerate(ground_truth):
        for ri, reported in enumerate(review_output):
            if ri in matched_reported:
                continue
            if _finding_matches(reported, expected):
                matched_reported.add(ri)
                matched_expected.add(ei)
                rep_sev = float(reported.get("severity", 5.0))
                exp_sev = float(expected.get("severity", 5.0))
                severity_scores.append(1.0 - abs(rep_sev - exp_sev) / 10.0)
                break

    n_matched = len(matched_expected)
    precision = n_matched / len(review_output)
    recall = n_matched / len(ground_truth)
    severity_accuracy = sum(severity_scores) / len(severity_scores) if severity_scores else 0.0
    f1 = _compute_f1(precision, recall)

    return JudgeScore(
        precision=precision,
        recall=recall,
        severity_accuracy=severity_accuracy,
        f1=f1,
        notes=notes,
    )


_JUDGE_PROMPTS = {
    1: (
        "You are Judge 1 (Precision-focused). Evaluate the following WFC review output "
        "against the ground truth findings. Score precision (fraction of reported findings "
        "that are real), recall (fraction of real bugs found), and severity accuracy.\n\n"
        "Review output:\n{review_output}\n\nGround truth:\n{ground_truth}\n\n"
        'Respond in JSON: {{"precision": float, "recall": float, '
        '"severity_accuracy": float, "notes": str}}'
    ),
    2: (
        "You are Judge 2 (Recall-focused). Independently evaluate the WFC review output "
        "against the ground truth findings. Score recall (fraction of real bugs found), "
        "precision (fraction of reported findings that are real), and severity accuracy.\n\n"
        "Ground truth:\n{ground_truth}\n\nReview output:\n{review_output}\n\n"
        'Respond in JSON: {{"precision": float, "recall": float, '
        '"severity_accuracy": float, "notes": str}}'
    ),
}

_DEFAULT_MODEL = "claude-opus-4-6"


class EvalJudge:
    """Dual-judge evaluation engine for WFC review quality assessment."""

    def __init__(self, model: str = _DEFAULT_MODEL) -> None:
        self._model = model

    def evaluate(
        self,
        review_output: list[dict],
        ground_truth: list[dict],
    ) -> DualJudgeResult:
        """Score a WFC review against ground truth using two independent judges.

        Both judges run the same pure-Python scoring algorithm with identical
        inputs. In production each would call an LLM via build_judge_task /
        parse_judge_response. For unit tests and offline use, the scores are
        computed deterministically from the matching algorithm.
        """
        score_1 = _score_review(review_output, ground_truth, notes="Judge 1")
        score_2 = _score_review(
            review_output, ground_truth, notes="Judge 2 (deterministic fallback)"
        )

        all_scores_1 = [score_1.precision, score_1.recall, score_1.f1]
        all_scores_2 = [score_2.precision, score_2.recall, score_2.f1]
        agreement = self.cohen_kappa(all_scores_1, all_scores_2)

        consensus_precision = (score_1.precision + score_2.precision) / 2
        consensus_recall = (score_1.recall + score_2.recall) / 2
        consensus_f1 = (score_1.f1 + score_2.f1) / 2

        return DualJudgeResult(
            judge_1=score_1,
            judge_2=score_2,
            agreement=agreement,
            consensus_precision=consensus_precision,
            consensus_recall=consensus_recall,
            consensus_f1=consensus_f1,
        )

    def build_judge_task(
        self,
        review_output: list[dict],
        ground_truth: list[dict],
        judge_id: int,
    ) -> dict:
        """Build a task spec for a judge (model call).

        Returns a dict with 'model' and 'prompt' keys. The prompt is
        deterministic: same inputs and judge_id always produce the same prompt.
        """
        prompt_template = _JUDGE_PROMPTS.get(judge_id, _JUDGE_PROMPTS[1])
        prompt = prompt_template.format(
            review_output=json.dumps(review_output, indent=2),
            ground_truth=json.dumps(ground_truth, indent=2),
        )
        return {"model": self._model, "prompt": prompt}

    def parse_judge_response(self, response: str) -> JudgeScore:
        """Parse a JSON judge response into a JudgeScore.

        Fail-open: returns zeros on any parse error.
        Expected JSON: {"precision": float, "recall": float,
                        "severity_accuracy": float, "notes": str}}
        """
        _zero = JudgeScore(
            precision=0.0,
            recall=0.0,
            severity_accuracy=0.0,
            f1=0.0,
            notes="parse error",
        )
        if not response or not response.strip():
            return _zero
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            return _zero

        required = {"precision", "recall", "severity_accuracy", "notes"}
        if not required.issubset(data.keys()):
            return _zero

        try:
            precision = float(data["precision"])
            recall = float(data["recall"])
            severity_accuracy = float(data["severity_accuracy"])
            notes = str(data["notes"])
        except (TypeError, ValueError):
            return _zero

        f1 = _compute_f1(precision, recall)
        return JudgeScore(
            precision=precision,
            recall=recall,
            severity_accuracy=severity_accuracy,
            f1=f1,
            notes=notes,
        )

    @staticmethod
    def cohen_kappa(
        scores_1: list[float],
        scores_2: list[float],
        threshold: float = 0.5,
    ) -> float:
        """Compute Cohen's Kappa for agreement between two judge score lists.

        Scores are binarized at threshold (>= threshold -> 1, else -> 0).

        kappa = (p_o - p_e) / (1 - p_e)
        where:
          p_o = observed agreement (fraction where both agree)
          p_e = expected agreement by chance

        Returns 0.0 for edge cases (empty lists, p_e == 1.0).
        """
        n = len(scores_1)
        if n == 0 or n != len(scores_2):
            return 0.0

        bin_1 = [1 if s >= threshold else 0 for s in scores_1]
        bin_2 = [1 if s >= threshold else 0 for s in scores_2]

        agree = sum(1 for a, b in zip(bin_1, bin_2) if a == b)
        p_o = agree / n

        p1_pos = sum(bin_1) / n
        p2_pos = sum(bin_2) / n
        p1_neg = 1.0 - p1_pos
        p2_neg = 1.0 - p2_pos
        p_e = p1_pos * p2_pos + p1_neg * p2_neg

        if p_e == 1.0:
            return 1.0 if bin_1 == bin_2 else 0.0

        return (p_o - p_e) / (1.0 - p_e)
