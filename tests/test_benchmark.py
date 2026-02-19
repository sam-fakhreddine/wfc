"""Tests for benchmark dataset infrastructure (TASK-013).

TDD tests for the ReviewBenchmark system that measures reviewer accuracy
(precision, recall, F1) against a labeled dataset of 20+ test cases.
"""

from pathlib import Path

import pytest

from wfc.scripts.benchmark import BenchmarkSuite, ReviewBenchmark

DATASET_PATH = Path(__file__).parent.parent / "wfc" / "scripts" / "benchmark" / "dataset.json"
REVIEWER_IDS = {"security", "correctness", "performance", "maintainability", "reliability"}
REQUIRED_FIELDS = {
    "id",
    "name",
    "description",
    "code_snippet",
    "file",
    "line_start",
    "expected_findings",
    "tags",
}


@pytest.fixture
def benchmark():
    return ReviewBenchmark(dataset_path=DATASET_PATH)


@pytest.fixture
def dataset(benchmark):
    return benchmark.load_dataset()


def test_load_dataset(benchmark):
    """Loads all 20+ test cases."""
    dataset = benchmark.load_dataset()
    assert isinstance(dataset, list)
    assert len(dataset) >= 20, f"Expected at least 20 test cases, got {len(dataset)}"


def test_dataset_schema_valid(dataset):
    """All test cases have required fields."""
    for tc in dataset:
        missing = REQUIRED_FIELDS - set(tc.keys())
        assert not missing, f"Test case {tc.get('id', '?')} missing fields: {missing}"
        for ef in tc["expected_findings"]:
            assert "reviewer_id" in ef, f"Missing reviewer_id in {tc['id']}"
            assert "category" in ef, f"Missing category in {tc['id']}"
            assert "should_detect" in ef, f"Missing should_detect in {tc['id']}"


def test_dataset_covers_all_reviewers(dataset):
    """All 5 reviewers have test cases."""
    covered = set()
    for tc in dataset:
        for ef in tc["expected_findings"]:
            covered.add(ef["reviewer_id"])
    missing = REVIEWER_IDS - covered
    assert not missing, f"Reviewers without test cases: {missing}"


def test_evaluate_true_positive(benchmark):
    """Correct detection scored properly."""
    test_case = {
        "id": "TC-TEST-TP",
        "expected_findings": [
            {"reviewer_id": "security", "category": "sql-injection", "should_detect": True}
        ],
    }
    actual_findings = [
        {"reviewer_id": "security", "category": "sql-injection", "severity": 9, "confidence": 8}
    ]
    result = benchmark.evaluate_findings(test_case, actual_findings)
    assert result["true_positives"] == 1
    assert result["false_negatives"] == 0
    assert result["false_positives"] == 0


def test_evaluate_false_negative(benchmark):
    """Missed detection scored properly."""
    test_case = {
        "id": "TC-TEST-FN",
        "expected_findings": [
            {"reviewer_id": "security", "category": "sql-injection", "should_detect": True}
        ],
    }
    actual_findings = []
    result = benchmark.evaluate_findings(test_case, actual_findings)
    assert result["true_positives"] == 0
    assert result["false_negatives"] == 1
    assert result["false_positives"] == 0


def test_evaluate_false_positive(benchmark):
    """Spurious finding scored properly."""
    test_case = {
        "id": "TC-TEST-FP",
        "expected_findings": [
            {"reviewer_id": "security", "category": "sql-injection", "should_detect": False}
        ],
    }
    actual_findings = [
        {"reviewer_id": "security", "category": "sql-injection", "severity": 5, "confidence": 4}
    ]
    result = benchmark.evaluate_findings(test_case, actual_findings)
    assert result["true_positives"] == 0
    assert result["false_negatives"] == 0
    assert result["false_positives"] == 1


def test_evaluate_true_negative(benchmark):
    """True negative: should NOT flag and did not flag."""
    test_case = {
        "id": "TC-TEST-TN",
        "expected_findings": [
            {"reviewer_id": "security", "category": "sql-injection", "should_detect": False}
        ],
    }
    actual_findings = []
    result = benchmark.evaluate_findings(test_case, actual_findings)
    assert result["true_positives"] == 0
    assert result["false_negatives"] == 0
    assert result["false_positives"] == 0


def test_evaluate_substring_category_match(benchmark):
    """Category matching works with substring match."""
    test_case = {
        "id": "TC-TEST-SUB",
        "expected_findings": [
            {"reviewer_id": "security", "category": "injection", "should_detect": True}
        ],
    }
    actual_findings = [
        {"reviewer_id": "security", "category": "sql-injection", "severity": 9, "confidence": 8}
    ]
    result = benchmark.evaluate_findings(test_case, actual_findings)
    assert result["true_positives"] == 1
    assert result["false_negatives"] == 0


def test_compute_metrics_perfect_score(benchmark):
    """All correct -> F1=1.0."""
    evaluations = [
        {
            "reviewer_id": "security",
            "true_positives": 5,
            "false_positives": 0,
            "false_negatives": 0,
        },
        {
            "reviewer_id": "correctness",
            "true_positives": 3,
            "false_positives": 0,
            "false_negatives": 0,
        },
    ]
    results = benchmark.compute_metrics(evaluations)
    for r in results:
        assert r.precision == 1.0
        assert r.recall == 1.0
        assert r.f1 == 1.0


def test_compute_metrics_zero_score(benchmark):
    """All wrong -> F1=0.0."""
    evaluations = [
        {
            "reviewer_id": "security",
            "true_positives": 0,
            "false_positives": 5,
            "false_negatives": 3,
        },
    ]
    results = benchmark.compute_metrics(evaluations)
    assert len(results) == 1
    assert results[0].precision == 0.0
    assert results[0].recall == 0.0
    assert results[0].f1 == 0.0


def test_compute_metrics_mixed(benchmark):
    """Partial match -> correct F1 calculation."""
    evaluations = [
        {
            "reviewer_id": "security",
            "true_positives": 3,
            "false_positives": 1,
            "false_negatives": 1,
        },
    ]
    results = benchmark.compute_metrics(evaluations)
    r = results[0]
    assert abs(r.precision - 0.75) < 1e-6
    assert abs(r.recall - 0.75) < 1e-6
    assert abs(r.f1 - 0.75) < 1e-6


def test_compute_metrics_precision_only_zero(benchmark):
    """Zero precision but nonzero recall edge case."""
    evaluations = [
        {
            "reviewer_id": "performance",
            "true_positives": 0,
            "false_positives": 3,
            "false_negatives": 0,
        },
    ]
    results = benchmark.compute_metrics(evaluations)
    r = results[0]
    assert r.precision == 0.0
    assert r.f1 == 0.0


def test_run_full_suite(benchmark, dataset):
    """End-to-end benchmark run with synthetic reviewer findings."""
    reviewer_findings: dict[str, list[dict]] = {}
    for tc in dataset:
        for ef in tc["expected_findings"]:
            rid = ef["reviewer_id"]
            if ef["should_detect"]:
                if rid not in reviewer_findings:
                    reviewer_findings[rid] = []
                reviewer_findings[rid].append(
                    {
                        "reviewer_id": rid,
                        "category": ef["category"],
                        "severity": ef.get("min_severity", 5),
                        "confidence": 8,
                        "file": tc["file"],
                        "line_start": tc["line_start"],
                        "test_case_id": tc["id"],
                    }
                )

    suite = benchmark.run(reviewer_findings)
    assert isinstance(suite, BenchmarkSuite)
    assert isinstance(suite.results, list)
    assert suite.duration_seconds >= 0
    assert abs(suite.overall_f1 - 1.0) < 1e-6, f"Expected perfect F1, got {suite.overall_f1}"
