"""Tests for the WFC evaluation framework: schema validation and dataset integrity."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pytest

from wfc.scripts.benchmark.eval_schema import (
    load_dataset,
    validate_dataset,
    validate_example,
)

EVAL_DATASET_DIR = (
    Path(__file__).parent.parent
    / "wfc"
    / "scripts"
    / "benchmark"
    / "eval_dataset"
)



@pytest.fixture(scope="module")
def all_examples() -> list[dict]:
    """Load all examples from the eval dataset directory once per test session."""
    return load_dataset(EVAL_DATASET_DIR)




class TestSchemaValidExample:
    def test_schema_valid_example_passes(self):
        """A well-formed example produces no validation errors."""
        example = {
            "id": "python-01-tp",
            "language": "python",
            "example_type": "true_positive",
            "source_code": "x = 1\n",
            "findings": [
                {
                    "line_start": 1,
                    "line_end": 1,
                    "category": "test",
                    "severity": 5.0,
                    "description": "Test finding",
                }
            ],
            "notes": "Optional note",
        }
        errors = validate_example(example)
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_schema_valid_true_negative_passes(self):
        """A true negative with an empty findings list is valid."""
        example = {
            "id": "go-05-tn",
            "language": "go",
            "example_type": "true_negative",
            "source_code": "func ok() error { return nil }\n",
            "findings": [],
        }
        errors = validate_example(example)
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_schema_valid_false_positive_trap_passes(self):
        """A false_positive_trap example with no findings is valid."""
        example = {
            "id": "typescript-08-fp",
            "language": "typescript",
            "example_type": "false_positive_trap",
            "source_code": "const x: unknown = {};\n",
            "findings": [],
            "notes": "Intentional",
        }
        errors = validate_example(example)
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_schema_finding_without_optional_line_end_passes(self):
        """Finding without line_end (optional) is still valid."""
        example = {
            "id": "java-02-tp",
            "language": "java",
            "example_type": "true_positive",
            "source_code": "String s = null;\n",
            "findings": [
                {
                    "line_start": 1,
                    "category": "null-dereference",
                    "severity": 8.0,
                    "description": "Null assigned to string",
                }
            ],
        }
        errors = validate_example(example)
        assert errors == [], f"Expected no errors, got: {errors}"




class TestSchemaMissingRequiredField:
    @pytest.mark.parametrize(
        "missing_field",
        ["id", "language", "source_code", "findings", "example_type"],
    )
    def test_schema_missing_required_field_fails(self, missing_field: str):
        """Removing any required field produces at least one error."""
        example = {
            "id": "python-01-tp",
            "language": "python",
            "example_type": "true_positive",
            "source_code": "x = 1\n",
            "findings": [],
        }
        del example[missing_field]
        errors = validate_example(example)
        assert len(errors) > 0, f"Expected error for missing field '{missing_field}'"
        assert any(missing_field in err for err in errors)

    def test_schema_missing_finding_required_field_fails(self):
        """A finding missing 'severity' produces an error."""
        example = {
            "id": "python-01-tp",
            "language": "python",
            "example_type": "true_positive",
            "source_code": "x = 1\n",
            "findings": [
                {
                    "line_start": 1,
                    "category": "test",
                    "description": "desc",
                }
            ],
        }
        errors = validate_example(example)
        assert len(errors) > 0
        assert any("severity" in err for err in errors)

    def test_schema_missing_finding_description_fails(self):
        """A finding missing 'description' produces an error."""
        example = {
            "id": "python-01-tp",
            "language": "python",
            "example_type": "true_positive",
            "source_code": "x = 1\n",
            "findings": [
                {
                    "line_start": 1,
                    "category": "test",
                    "severity": 5.0,
                }
            ],
        }
        errors = validate_example(example)
        assert len(errors) > 0
        assert any("description" in err for err in errors)




class TestSchemaInvalidFieldValues:
    def test_schema_invalid_language_fails(self):
        """An unsupported language value produces a validation error."""
        example = {
            "id": "rust-01-tp",
            "language": "rust",
            "example_type": "true_positive",
            "source_code": "fn main() {}\n",
            "findings": [],
        }
        errors = validate_example(example)
        assert len(errors) > 0
        assert any("language" in err for err in errors)

    def test_schema_invalid_example_type_fails(self):
        """An unsupported example_type value produces a validation error."""
        example = {
            "id": "python-01-tp",
            "language": "python",
            "example_type": "unknown_type",
            "source_code": "x = 1\n",
            "findings": [],
        }
        errors = validate_example(example)
        assert len(errors) > 0
        assert any("example_type" in err for err in errors)

    def test_schema_severity_out_of_range_fails(self):
        """Severity > 10 produces a validation error."""
        example = {
            "id": "python-01-tp",
            "language": "python",
            "example_type": "true_positive",
            "source_code": "x = 1\n",
            "findings": [
                {
                    "line_start": 1,
                    "category": "test",
                    "severity": 11.0,
                    "description": "desc",
                }
            ],
        }
        errors = validate_example(example)
        assert len(errors) > 0
        assert any("severity" in err for err in errors)

    def test_schema_severity_negative_fails(self):
        """Severity < 0 produces a validation error."""
        example = {
            "id": "python-01-tp",
            "language": "python",
            "example_type": "true_positive",
            "source_code": "x = 1\n",
            "findings": [
                {
                    "line_start": 1,
                    "category": "test",
                    "severity": -1.0,
                    "description": "desc",
                }
            ],
        }
        errors = validate_example(example)
        assert len(errors) > 0
        assert any("severity" in err for err in errors)

    def test_schema_empty_source_code_fails(self):
        """Empty source_code string produces a validation error."""
        example = {
            "id": "python-01-tp",
            "language": "python",
            "example_type": "true_positive",
            "source_code": "",
            "findings": [],
        }
        errors = validate_example(example)
        assert len(errors) > 0
        assert any("source_code" in err for err in errors)

    def test_schema_line_start_zero_fails(self):
        """line_start of 0 (below minimum of 1) produces a validation error."""
        example = {
            "id": "python-01-tp",
            "language": "python",
            "example_type": "true_positive",
            "source_code": "x = 1\n",
            "findings": [
                {
                    "line_start": 0,
                    "category": "test",
                    "severity": 5.0,
                    "description": "desc",
                }
            ],
        }
        errors = validate_example(example)
        assert len(errors) > 0
        assert any("line_start" in err for err in errors)




class TestLoadDataset:
    def test_load_dataset_returns_40_examples(self, all_examples: list[dict]):
        """The eval dataset directory must contain exactly 40 examples."""
        assert len(all_examples) == 40, (
            f"Expected 40 examples, got {len(all_examples)}"
        )

    def test_load_dataset_all_are_dicts(self, all_examples: list[dict]):
        """Every loaded item must be a dict (parsed JSON object)."""
        for i, ex in enumerate(all_examples):
            assert isinstance(ex, dict), f"Item {i} is not a dict: {type(ex)}"

    def test_load_dataset_all_have_ids(self, all_examples: list[dict]):
        """Every loaded example must have a non-empty 'id' field."""
        for ex in all_examples:
            assert "id" in ex and ex["id"], f"Example missing id: {ex}"

    def test_load_dataset_ids_are_unique(self, all_examples: list[dict]):
        """All example IDs must be unique within the dataset."""
        ids = [ex["id"] for ex in all_examples]
        assert len(ids) == len(set(ids)), "Duplicate IDs found in dataset"




class TestLanguageDistribution:
    def test_language_distribution_balanced(self, all_examples: list[dict]):
        """Each language must contribute at least 10 examples."""
        counts: dict[str, int] = defaultdict(int)
        for ex in all_examples:
            counts[ex.get("language", "MISSING")] += 1

        expected_languages = {"python", "typescript", "go", "java"}
        for lang in expected_languages:
            assert counts[lang] >= 10, (
                f"Language '{lang}' has only {counts[lang]} examples (expected >= 10)"
            )

    def test_language_distribution_exact(self, all_examples: list[dict]):
        """Each of the 4 languages must contribute exactly 10 examples."""
        counts: dict[str, int] = defaultdict(int)
        for ex in all_examples:
            counts[ex.get("language", "MISSING")] += 1

        expected = {"python": 10, "typescript": 10, "go": 10, "java": 10}
        for lang, expected_count in expected.items():
            assert counts[lang] == expected_count, (
                f"Language '{lang}': expected {expected_count}, got {counts[lang]}"
            )

    def test_no_unexpected_languages(self, all_examples: list[dict]):
        """No examples should use a language outside the supported set."""
        valid = {"python", "typescript", "go", "java"}
        for ex in all_examples:
            lang = ex.get("language", "MISSING")
            assert lang in valid, f"Unexpected language '{lang}' in example {ex.get('id')}"




class TestExampleTypeDistribution:
    def test_example_type_distribution(self, all_examples: list[dict]):
        """Each language must have at least one of each example type."""
        by_lang: dict[str, set[str]] = defaultdict(set)
        for ex in all_examples:
            lang = ex.get("language", "")
            etype = ex.get("example_type", "")
            by_lang[lang].add(etype)

        required_types = {"true_positive", "true_negative", "false_positive_trap"}
        for lang in {"python", "typescript", "go", "java"}:
            for etype in required_types:
                assert etype in by_lang[lang], (
                    f"Language '{lang}' has no example of type '{etype}'"
                )

    def test_true_positives_have_findings(self, all_examples: list[dict]):
        """All true_positive examples must have at least one finding."""
        for ex in all_examples:
            if ex.get("example_type") == "true_positive":
                assert len(ex.get("findings", [])) > 0, (
                    f"true_positive example '{ex.get('id')}' has no findings"
                )

    def test_true_negatives_have_no_findings(self, all_examples: list[dict]):
        """All true_negative examples must have an empty findings list."""
        for ex in all_examples:
            if ex.get("example_type") == "true_negative":
                assert ex.get("findings", []) == [], (
                    f"true_negative example '{ex.get('id')}' has unexpected findings"
                )

    def test_false_positive_traps_have_no_findings(self, all_examples: list[dict]):
        """All false_positive_trap examples must have an empty findings list."""
        for ex in all_examples:
            if ex.get("example_type") == "false_positive_trap":
                assert ex.get("findings", []) == [], (
                    f"false_positive_trap example '{ex.get('id')}' has unexpected findings"
                )




class TestAllExamplesValid:
    def test_all_examples_valid(self, all_examples: list[dict]):
        """validate_dataset must report 0 invalid examples across all 40."""
        result = validate_dataset(all_examples)
        assert result["invalid"] == 0, (
            f"{result['invalid']} invalid example(s) found:\n"
            + "\n".join(result["errors"])
        )
        assert result["valid"] == 40

    def test_validate_dataset_counts_match(self, all_examples: list[dict]):
        """valid + invalid totals must equal the number of examples passed in."""
        result = validate_dataset(all_examples)
        total = result["valid"] + result["invalid"]
        assert total == len(all_examples)

    def test_all_source_codes_non_empty(self, all_examples: list[dict]):
        """Every example must have non-empty source_code."""
        for ex in all_examples:
            assert ex.get("source_code", ""), (
                f"Example '{ex.get('id')}' has empty source_code"
            )

    def test_all_examples_have_notes(self, all_examples: list[dict]):
        """Every example should have a notes field for human context."""
        missing = [ex["id"] for ex in all_examples if not ex.get("notes")]
        assert missing == [], f"Examples missing 'notes': {missing}"



from wfc.scripts.benchmark.eval_judge import (
    JudgeScore,
    DualJudgeResult,
    EvalJudge,
)


class TestEvalJudge:
    """Tests for the Dual-Judge Evaluation Engine (TASK-011)."""


    @pytest.fixture
    def judge(self) -> EvalJudge:
        return EvalJudge()

    @pytest.fixture
    def sample_finding(self) -> dict:
        return {
            "line_start": 10,
            "line_end": 10,
            "category": "sql-injection",
            "severity": 8.0,
            "description": "Unsanitised SQL query",
        }

    @pytest.fixture
    def sample_ground_truth(self) -> list[dict]:
        return [
            {
                "line_start": 10,
                "line_end": 10,
                "category": "sql-injection",
                "severity": 8.0,
                "description": "SQL injection vulnerability",
            }
        ]


    def test_judge_score_fields(self):
        """JudgeScore must have precision, recall, severity_accuracy, f1, notes."""
        score = JudgeScore(
            precision=0.8,
            recall=0.6,
            severity_accuracy=0.9,
            f1=0.686,
            notes="test",
        )
        assert score.precision == 0.8
        assert score.recall == 0.6
        assert score.severity_accuracy == 0.9
        assert score.f1 == pytest.approx(0.686)
        assert score.notes == "test"


    def test_dual_judge_result_fields(self):
        """DualJudgeResult must expose both judges, agreement and consensus metrics."""
        j1 = JudgeScore(precision=0.8, recall=0.6, severity_accuracy=0.9, f1=0.686, notes="j1")
        j2 = JudgeScore(precision=0.7, recall=0.7, severity_accuracy=0.8, f1=0.700, notes="j2")
        result = DualJudgeResult(
            judge_1=j1,
            judge_2=j2,
            agreement=0.75,
            consensus_precision=0.75,
            consensus_recall=0.65,
            consensus_f1=0.693,
        )
        assert result.judge_1 is j1
        assert result.judge_2 is j2
        assert result.agreement == 0.75
        assert result.consensus_precision == 0.75
        assert result.consensus_recall == 0.65


    def test_evaluate_returns_dual_judge_result(self, judge, sample_finding, sample_ground_truth):
        """evaluate() must return a DualJudgeResult instance."""
        result = judge.evaluate([sample_finding], sample_ground_truth)
        assert isinstance(result, DualJudgeResult)

    def test_evaluate_consensus_precision_is_mean_of_judges(self, judge, sample_finding, sample_ground_truth):
        """consensus_precision must equal mean(judge_1.precision, judge_2.precision)."""
        result = judge.evaluate([sample_finding], sample_ground_truth)
        expected = (result.judge_1.precision + result.judge_2.precision) / 2
        assert result.consensus_precision == pytest.approx(expected)

    def test_evaluate_consensus_recall_is_mean_of_judges(self, judge, sample_finding, sample_ground_truth):
        """consensus_recall must equal mean(judge_1.recall, judge_2.recall)."""
        result = judge.evaluate([sample_finding], sample_ground_truth)
        expected = (result.judge_1.recall + result.judge_2.recall) / 2
        assert result.consensus_recall == pytest.approx(expected)

    def test_evaluate_consensus_f1_is_mean_of_judges(self, judge, sample_finding, sample_ground_truth):
        """consensus_f1 must equal mean(judge_1.f1, judge_2.f1)."""
        result = judge.evaluate([sample_finding], sample_ground_truth)
        expected = (result.judge_1.f1 + result.judge_2.f1) / 2
        assert result.consensus_f1 == pytest.approx(expected)

    def test_evaluate_agreement_in_range(self, judge, sample_finding, sample_ground_truth):
        """Cohen's Kappa agreement must be in [-1, 1]."""
        result = judge.evaluate([sample_finding], sample_ground_truth)
        assert -1.0 <= result.agreement <= 1.0


    def test_evaluate_empty_review_output_precision_zero(self, judge, sample_ground_truth):
        """When no findings are reported, precision must be 0.0."""
        result = judge.evaluate([], sample_ground_truth)
        assert result.judge_1.precision == 0.0
        assert result.judge_2.precision == 0.0

    def test_evaluate_empty_review_output_recall_zero(self, judge, sample_ground_truth):
        """When no findings are reported but ground truth exists, recall must be 0.0."""
        result = judge.evaluate([], sample_ground_truth)
        assert result.judge_1.recall == 0.0
        assert result.judge_2.recall == 0.0


    def test_evaluate_empty_ground_truth_recall_is_one(self, judge, sample_finding):
        """When ground truth is empty (true negative), recall must be 1.0."""
        result = judge.evaluate([sample_finding], [])
        assert result.judge_1.recall == 1.0
        assert result.judge_2.recall == 1.0

    def test_evaluate_both_empty_perfect_tn(self, judge):
        """When both review_output and ground_truth are empty, it's a perfect true-negative: precision=1.0, recall=1.0."""
        result = judge.evaluate([], [])
        assert result.judge_1.recall == 1.0
        assert result.judge_1.precision == 1.0
        assert result.judge_1.f1 == 1.0


    def test_finding_matches_within_5_lines(self, judge):
        """A finding within +-5 lines of the same category should match."""
        review_output = [{"line_start": 12, "category": "xss", "severity": 5.0, "description": "d"}]
        ground_truth = [{"line_start": 10, "category": "xss", "severity": 5.0, "description": "d"}]
        result = judge.evaluate(review_output, ground_truth)
        assert result.judge_1.recall == pytest.approx(1.0)

    def test_finding_no_match_beyond_5_lines(self, judge):
        """A finding more than 5 lines away should NOT match."""
        review_output = [{"line_start": 20, "category": "xss", "severity": 5.0, "description": "d"}]
        ground_truth = [{"line_start": 10, "category": "xss", "severity": 5.0, "description": "d"}]
        result = judge.evaluate(review_output, ground_truth)
        assert result.judge_1.recall == pytest.approx(0.0)

    def test_finding_no_match_different_category(self, judge):
        """A finding with different category should NOT match even if line is close."""
        review_output = [{"line_start": 10, "category": "sql-injection", "severity": 5.0, "description": "d"}]
        ground_truth = [{"line_start": 10, "category": "xss", "severity": 5.0, "description": "d"}]
        result = judge.evaluate(review_output, ground_truth)
        assert result.judge_1.recall == pytest.approx(0.0)

    def test_all_findings_match_perfect_recall_precision(self, judge):
        """When every reported finding matches ground truth, recall=1.0 and precision=1.0."""
        findings = [{"line_start": 10, "category": "xss", "severity": 5.0, "description": "d"}]
        result = judge.evaluate(findings, findings)
        assert result.judge_1.recall == pytest.approx(1.0)
        assert result.judge_1.precision == pytest.approx(1.0)


    def test_f1_computed_from_precision_recall(self, judge):
        """F1 must equal 2*P*R/(P+R) when both > 0."""
        review_output = [
            {"line_start": 10, "category": "xss", "severity": 5.0, "description": "d"},
            {"line_start": 50, "category": "xss", "severity": 5.0, "description": "d"},
        ]
        ground_truth = [{"line_start": 10, "category": "xss", "severity": 5.0, "description": "d"}]
        result = judge.evaluate(review_output, ground_truth)
        p = result.judge_1.precision
        r = result.judge_1.recall
        if p + r > 0:
            expected_f1 = 2 * p * r / (p + r)
            assert result.judge_1.f1 == pytest.approx(expected_f1, abs=1e-6)

    def test_f1_zero_when_no_matches(self, judge, sample_ground_truth):
        """F1 must be 0.0 when there are no matches."""
        review_output = [{"line_start": 99, "category": "other", "severity": 2.0, "description": "d"}]
        result = judge.evaluate(review_output, sample_ground_truth)
        assert result.judge_1.f1 == pytest.approx(0.0)


    def test_severity_accuracy_perfect_match(self, judge):
        """When reported severity exactly matches expected, severity_accuracy=1.0."""
        findings = [{"line_start": 10, "category": "xss", "severity": 8.0, "description": "d"}]
        ground_truth = [{"line_start": 10, "category": "xss", "severity": 8.0, "description": "d"}]
        result = judge.evaluate(findings, ground_truth)
        assert result.judge_1.severity_accuracy == pytest.approx(1.0)

    def test_severity_accuracy_partial_mismatch(self, judge):
        """severity_accuracy = 1 - |rep_sev - exp_sev| / 10 for matched findings."""
        findings = [{"line_start": 10, "category": "xss", "severity": 8.0, "description": "d"}]
        ground_truth = [{"line_start": 10, "category": "xss", "severity": 4.0, "description": "d"}]
        result = judge.evaluate(findings, ground_truth)
        assert result.judge_1.severity_accuracy == pytest.approx(0.6)

    def test_severity_accuracy_zero_when_no_matches(self, judge, sample_ground_truth):
        """severity_accuracy must be 0.0 when there are no matches."""
        review_output = [{"line_start": 99, "category": "other", "severity": 2.0, "description": "d"}]
        result = judge.evaluate(review_output, sample_ground_truth)
        assert result.judge_1.severity_accuracy == pytest.approx(0.0)


    def test_build_judge_task_returns_dict_with_model_and_prompt(self, judge, sample_finding, sample_ground_truth):
        """build_judge_task() must return a dict with 'model' and 'prompt' keys."""
        task = judge.build_judge_task([sample_finding], sample_ground_truth, judge_id=1)
        assert isinstance(task, dict)
        assert "model" in task
        assert "prompt" in task

    def test_build_judge_task_prompt_is_string(self, judge, sample_finding, sample_ground_truth):
        """build_judge_task() prompt must be a non-empty string."""
        task = judge.build_judge_task([sample_finding], sample_ground_truth, judge_id=1)
        assert isinstance(task["prompt"], str)
        assert len(task["prompt"]) > 0

    def test_build_judge_task_deterministic(self, judge, sample_finding, sample_ground_truth):
        """build_judge_task() must produce identical output for same inputs."""
        t1 = judge.build_judge_task([sample_finding], sample_ground_truth, judge_id=1)
        t2 = judge.build_judge_task([sample_finding], sample_ground_truth, judge_id=1)
        assert t1["prompt"] == t2["prompt"]
        assert t1["model"] == t2["model"]

    def test_build_judge_task_different_judge_ids_differ(self, judge, sample_finding, sample_ground_truth):
        """Different judge_id values must produce different prompts."""
        t1 = judge.build_judge_task([sample_finding], sample_ground_truth, judge_id=1)
        t2 = judge.build_judge_task([sample_finding], sample_ground_truth, judge_id=2)
        assert t1["prompt"] != t2["prompt"]


    def test_parse_judge_response_valid_json(self, judge):
        """parse_judge_response parses valid JSON into JudgeScore."""
        response = '{"precision": 0.8, "recall": 0.6, "severity_accuracy": 0.9, "notes": "ok"}'
        score = judge.parse_judge_response(response)
        assert isinstance(score, JudgeScore)
        assert score.precision == pytest.approx(0.8)
        assert score.recall == pytest.approx(0.6)
        assert score.severity_accuracy == pytest.approx(0.9)
        assert score.notes == "ok"

    def test_parse_judge_response_computes_f1(self, judge):
        """parse_judge_response must compute f1 from precision and recall."""
        response = '{"precision": 0.8, "recall": 0.6, "severity_accuracy": 0.9, "notes": "ok"}'
        score = judge.parse_judge_response(response)
        expected_f1 = 2 * 0.8 * 0.6 / (0.8 + 0.6)
        assert score.f1 == pytest.approx(expected_f1)

    def test_parse_judge_response_invalid_json_returns_zeros(self, judge):
        """parse_judge_response must return zeros on invalid JSON (fail-open)."""
        score = judge.parse_judge_response("this is not json")
        assert score.precision == 0.0
        assert score.recall == 0.0
        assert score.severity_accuracy == 0.0
        assert score.f1 == 0.0

    def test_parse_judge_response_missing_field_returns_zeros(self, judge):
        """parse_judge_response returns zeros if a required field is missing."""
        response = '{"precision": 0.8, "notes": "partial"}'
        score = judge.parse_judge_response(response)
        assert score.precision == 0.0
        assert score.recall == 0.0
        assert score.f1 == 0.0

    def test_parse_judge_response_empty_string_returns_zeros(self, judge):
        """parse_judge_response returns zeros on empty string input."""
        score = judge.parse_judge_response("")
        assert score.precision == 0.0
        assert score.recall == 0.0
        assert score.f1 == 0.0


    def test_cohen_kappa_perfect_agreement(self):
        """Cohen's Kappa must be 1.0 for identical binary lists."""
        scores_1 = [0.8, 0.2, 0.9, 0.1]
        scores_2 = [0.8, 0.2, 0.9, 0.1]
        kappa = EvalJudge.cohen_kappa(scores_1, scores_2)
        assert kappa == pytest.approx(1.0)

    def test_cohen_kappa_complete_disagreement(self):
        """Cohen's Kappa must be <= 0 for complete disagreement."""
        scores_1 = [0.8, 0.8, 0.8, 0.8]
        scores_2 = [0.2, 0.2, 0.2, 0.2]
        kappa = EvalJudge.cohen_kappa(scores_1, scores_2)
        assert kappa <= 0.0

    def test_cohen_kappa_partial_agreement(self):
        """Cohen's Kappa for partial agreement must be in (-1, 1)."""
        scores_1 = [0.8, 0.2, 0.8, 0.2]
        scores_2 = [0.8, 0.2, 0.2, 0.8]
        kappa = EvalJudge.cohen_kappa(scores_1, scores_2)
        assert -1.0 <= kappa <= 1.0

    def test_cohen_kappa_custom_threshold(self):
        """Cohen's Kappa must respect a custom threshold."""
        scores_1 = [0.6, 0.6, 0.4, 0.4]
        scores_2 = [0.6, 0.6, 0.4, 0.4]
        kappa = EvalJudge.cohen_kappa(scores_1, scores_2, threshold=0.5)
        assert kappa == pytest.approx(1.0)

    def test_cohen_kappa_empty_lists_returns_zero(self):
        """Cohen's Kappa on empty lists must return 0.0 (safe default)."""
        kappa = EvalJudge.cohen_kappa([], [])
        assert kappa == 0.0

    def test_cohen_kappa_all_same_class_returns_zero_or_one(self):
        """When both judges always predict same class, kappa is 0 (undefined) or 1."""
        scores_1 = [0.9, 0.9, 0.9]
        scores_2 = [0.9, 0.9, 0.9]
        kappa = EvalJudge.cohen_kappa(scores_1, scores_2)
        assert kappa == pytest.approx(0.0) or kappa == pytest.approx(1.0)
