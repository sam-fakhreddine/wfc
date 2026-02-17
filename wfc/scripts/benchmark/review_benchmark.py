"""Benchmark runner for measuring reviewer accuracy (precision, recall, F1).

Compares actual reviewer findings against a labeled dataset of expected findings
to compute per-reviewer and overall metrics.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BenchmarkResult:
    """Metrics for a single reviewer."""

    reviewer_id: str
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float


@dataclass
class BenchmarkSuite:
    """Aggregate results from a full benchmark run."""

    results: list[BenchmarkResult]
    overall_f1: float
    duration_seconds: float


def _categories_match(expected_category: str, actual_category: str) -> bool:
    """Check if categories match via substring matching (either direction)."""
    e = expected_category.lower()
    a = actual_category.lower()
    return e in a or a in e


def _safe_divide(numerator: float, denominator: float) -> float:
    """Division that returns 0.0 on zero denominator."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _compute_f1(precision: float, recall: float) -> float:
    """F1 = 2 * precision * recall / (precision + recall), 0.0 if both zero."""
    denom = precision + recall
    if denom == 0:
        return 0.0
    return 2.0 * precision * recall / denom


class ReviewBenchmark:
    """Benchmark runner that evaluates reviewer findings against labeled test cases."""

    def __init__(self, dataset_path: Path | None = None) -> None:
        if dataset_path is None:
            dataset_path = Path(__file__).parent / "dataset.json"
        self._dataset_path = dataset_path

    def load_dataset(self) -> list[dict]:
        """Load and return the benchmark dataset."""
        with open(self._dataset_path, encoding="utf-8") as f:
            return json.load(f)

    def evaluate_findings(self, test_case: dict, actual_findings: list[dict]) -> dict:
        """Compare actual findings against expected for a single test case.

        Returns a dict with keys: test_case_id, true_positives,
        false_positives, false_negatives, per_reviewer (reviewer_id -> counts).
        """
        tp = 0
        fp = 0
        fn = 0
        per_reviewer: dict[str, dict] = defaultdict(
            lambda: {"true_positives": 0, "false_positives": 0, "false_negatives": 0}
        )

        expected = test_case["expected_findings"]
        matched_actual = set()

        for ef in expected:
            rid = ef["reviewer_id"]
            cat = ef["category"]
            should_detect = ef["should_detect"]

            found = False
            for i, af in enumerate(actual_findings):
                if i in matched_actual:
                    continue
                if af["reviewer_id"] == rid and _categories_match(cat, af["category"]):
                    found = True
                    matched_actual.add(i)
                    break

            if should_detect:
                if found:
                    tp += 1
                    per_reviewer[rid]["true_positives"] += 1
                else:
                    fn += 1
                    per_reviewer[rid]["false_negatives"] += 1
            else:
                if found:
                    fp += 1
                    per_reviewer[rid]["false_positives"] += 1

        for i, af in enumerate(actual_findings):
            if i not in matched_actual:
                rid = af["reviewer_id"]
                fp += 1
                per_reviewer[rid]["false_positives"] += 1

        return {
            "test_case_id": test_case["id"],
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "per_reviewer": dict(per_reviewer),
        }

    def compute_metrics(self, evaluations: list[dict]) -> list[BenchmarkResult]:
        """Compute precision/recall/F1 per reviewer from evaluation dicts.

        Each evaluation dict has: reviewer_id, true_positives, false_positives,
        false_negatives.
        """
        agg: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
        for ev in evaluations:
            rid = ev["reviewer_id"]
            agg[rid]["tp"] += ev["true_positives"]
            agg[rid]["fp"] += ev["false_positives"]
            agg[rid]["fn"] += ev["false_negatives"]

        results = []
        for rid, counts in sorted(agg.items()):
            tp = counts["tp"]
            fp_val = counts["fp"]
            fn_val = counts["fn"]
            precision = _safe_divide(tp, tp + fp_val)
            recall = _safe_divide(tp, tp + fn_val)
            f1 = _compute_f1(precision, recall)
            results.append(
                BenchmarkResult(
                    reviewer_id=rid,
                    true_positives=tp,
                    false_positives=fp_val,
                    false_negatives=fn_val,
                    precision=precision,
                    recall=recall,
                    f1=f1,
                )
            )
        return results

    def run(self, reviewer_findings: dict[str, list[dict]]) -> BenchmarkSuite:
        """Run full benchmark suite.

        Args:
            reviewer_findings: mapping of reviewer_id -> list of finding dicts.
                Each finding must have: reviewer_id, category, severity, confidence.
                Optionally: file, line_start, test_case_id for matching.

        Returns:
            BenchmarkSuite with per-reviewer results and overall F1.
        """
        start = time.monotonic()
        dataset = self.load_dataset()

        findings_by_tc: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
        for _rid, findings in reviewer_findings.items():
            for f in findings:
                tc_id = f.get("test_case_id")
                if tc_id:
                    findings_by_tc[tc_id][f["reviewer_id"]].append(f)

        unmatched_findings: dict[str, list[dict]] = defaultdict(list)
        for _rid, findings in reviewer_findings.items():
            for f in findings:
                if not f.get("test_case_id"):
                    key = f"{f.get('file', '')}:{f.get('line_start', '')}"
                    unmatched_findings[key].append(f)

        per_reviewer_evals: list[dict] = []
        for tc in dataset:
            tc_id = tc["id"]
            actual: list[dict] = []
            if tc_id in findings_by_tc:
                for flist in findings_by_tc[tc_id].values():
                    actual.extend(flist)
            else:
                key = f"{tc.get('file', '')}:{tc.get('line_start', '')}"
                if key in unmatched_findings:
                    actual = unmatched_findings[key]

            ev = self.evaluate_findings(tc, actual)

            for rid, counts in ev["per_reviewer"].items():
                per_reviewer_evals.append(
                    {
                        "reviewer_id": rid,
                        "true_positives": counts["true_positives"],
                        "false_positives": counts["false_positives"],
                        "false_negatives": counts["false_negatives"],
                    }
                )

            covered_rids = set(ev["per_reviewer"].keys())
            for ef in tc["expected_findings"]:
                rid = ef["reviewer_id"]
                if rid not in covered_rids:
                    if ef["should_detect"]:
                        per_reviewer_evals.append(
                            {
                                "reviewer_id": rid,
                                "true_positives": 0,
                                "false_positives": 0,
                                "false_negatives": 1,
                            }
                        )

        results = self.compute_metrics(per_reviewer_evals)
        duration = time.monotonic() - start

        if results:
            overall_f1 = sum(r.f1 for r in results) / len(results)
        else:
            overall_f1 = 0.0

        return BenchmarkSuite(
            results=results,
            overall_f1=overall_f1,
            duration_seconds=duration,
        )
