"""JSON schema and validation for the WFC evaluation dataset."""

from __future__ import annotations

import json
from pathlib import Path

EXAMPLE_SCHEMA = {
    "type": "object",
    "required": ["id", "language", "source_code", "findings", "example_type"],
    "properties": {
        "id": {"type": "string"},
        "language": {
            "type": "string",
            "enum": ["python", "typescript", "go", "java"],
        },
        "source_code": {"type": "string", "minLength": 1},
        "example_type": {
            "type": "string",
            "enum": ["true_positive", "true_negative", "false_positive_trap"],
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["line_start", "category", "severity", "description"],
                "properties": {
                    "line_start": {"type": "integer", "minimum": 1},
                    "line_end": {"type": "integer", "minimum": 1},
                    "category": {"type": "string"},
                    "severity": {"type": "number", "minimum": 0, "maximum": 10},
                    "description": {"type": "string"},
                },
            },
        },
        "notes": {"type": "string"},
    },
}

_VALID_LANGUAGES = {"python", "typescript", "go", "java"}
_VALID_EXAMPLE_TYPES = {"true_positive", "true_negative", "false_positive_trap"}


def validate_example(example: dict) -> list[str]:
    """Validate a single example against schema. Returns list of errors (empty = valid)."""
    errors: list[str] = []

    if not isinstance(example, dict):
        return ["Example must be a JSON object"]

    required_fields = ["id", "language", "source_code", "findings", "example_type"]
    for field in required_fields:
        if field not in example:
            errors.append(f"Missing required field: '{field}'")

    if errors:
        return errors

    if not isinstance(example["id"], str) or not example["id"]:
        errors.append("Field 'id' must be a non-empty string")

    if example["language"] not in _VALID_LANGUAGES:
        errors.append(
            f"Field 'language' must be one of {sorted(_VALID_LANGUAGES)}, "
            f"got '{example['language']}'"
        )

    if not isinstance(example["source_code"], str) or len(example["source_code"]) < 1:
        errors.append("Field 'source_code' must be a non-empty string")

    if example["example_type"] not in _VALID_EXAMPLE_TYPES:
        errors.append(
            f"Field 'example_type' must be one of {sorted(_VALID_EXAMPLE_TYPES)}, "
            f"got '{example['example_type']}'"
        )

    if not isinstance(example["findings"], list):
        errors.append("Field 'findings' must be an array")
    else:
        for i, finding in enumerate(example["findings"]):
            finding_errors = _validate_finding(finding, index=i)
            errors.extend(finding_errors)

    if "notes" in example and not isinstance(example["notes"], str):
        errors.append("Field 'notes' must be a string if present")

    return errors


def _validate_finding(finding: dict, index: int) -> list[str]:
    """Validate a single finding object. Returns list of errors."""
    errors: list[str] = []
    prefix = f"findings[{index}]"

    if not isinstance(finding, dict):
        return [f"{prefix}: must be a JSON object"]

    required = ["line_start", "category", "severity", "description"]
    for field in required:
        if field not in finding:
            errors.append(f"{prefix}: missing required field '{field}'")

    if errors:
        return errors

    if not isinstance(finding["line_start"], int) or finding["line_start"] < 1:
        errors.append(f"{prefix}.line_start must be an integer >= 1")

    if "line_end" in finding:
        if not isinstance(finding["line_end"], int) or finding["line_end"] < 1:
            errors.append(f"{prefix}.line_end must be an integer >= 1")

    if not isinstance(finding["category"], str) or not finding["category"]:
        errors.append(f"{prefix}.category must be a non-empty string")

    if not isinstance(finding["severity"], (int, float)):
        errors.append(f"{prefix}.severity must be a number")
    elif not (0 <= finding["severity"] <= 10):
        errors.append(f"{prefix}.severity must be between 0 and 10")

    if not isinstance(finding["description"], str) or not finding["description"]:
        errors.append(f"{prefix}.description must be a non-empty string")

    return errors


def validate_dataset(examples: list[dict]) -> dict:
    """Validate full dataset. Returns {valid: int, invalid: int, errors: list[str]}."""
    valid = 0
    invalid = 0
    all_errors: list[str] = []

    for i, example in enumerate(examples):
        example_id = example.get("id", f"<index {i}>")
        errs = validate_example(example)
        if errs:
            invalid += 1
            for err in errs:
                all_errors.append(f"[{example_id}] {err}")
        else:
            valid += 1

    return {"valid": valid, "invalid": invalid, "errors": all_errors}


def load_dataset(directory: Path) -> list[dict]:
    """Load all .json files from directory, sorted by filename."""
    examples: list[dict] = []
    for json_file in sorted(directory.glob("*.json")):
        with json_file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            examples.append(data)
    return examples
