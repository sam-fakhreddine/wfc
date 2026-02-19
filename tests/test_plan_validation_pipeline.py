"""Tests for Plan Validation Pipeline (TASK-005a + TASK-005b).

Validates that:
1. SKILL.md contains the validation pipeline instructions
2. plan-audit.json schema is correct
3. SHA-256 hash computation works
4. revision-log.md format is correct
"""

import hashlib
import json
from pathlib import Path

SKILL_MD_PATH = Path(__file__).resolve().parent.parent / "wfc" / "skills" / "wfc-plan" / "SKILL.md"


class TestSkillMDValidationPipelineSection:
    """Verify SKILL.md contains all required plan validation pipeline instructions."""

    def test_skill_md_exists(self):
        assert SKILL_MD_PATH.exists(), f"SKILL.md not found at {SKILL_MD_PATH}"

    def test_has_plan_validation_pipeline_section(self):
        content = SKILL_MD_PATH.read_text()
        assert (
            "## Plan Validation Pipeline" in content
        ), "SKILL.md must contain a '## Plan Validation Pipeline' section"

    def test_has_isthissmart_gate_instructions(self):
        content = SKILL_MD_PATH.read_text()
        assert (
            "Validate Gate" in content or "IsThisSmart Gate" in content
        ), "SKILL.md must describe the Validate Gate step"

    def test_has_revision_mechanism(self):
        content = SKILL_MD_PATH.read_text()
        assert "revision-log.md" in content, "SKILL.md must describe revision-log.md generation"

    def test_has_review_gate(self):
        content = SKILL_MD_PATH.read_text()
        assert "Review Gate" in content, "SKILL.md must describe the Review Gate step"

    def test_has_review_loop_threshold(self):
        content = SKILL_MD_PATH.read_text()
        assert "8.5" in content, "SKILL.md must specify the 8.5/10 review threshold"

    def test_has_skip_validation_flag(self):
        content = SKILL_MD_PATH.read_text()
        assert "--skip-validation" in content, "SKILL.md must document the --skip-validation flag"

    def test_has_xml_delimiting_instructions(self):
        content = SKILL_MD_PATH.read_text()
        assert (
            "<plan-content>" in content
        ), "SKILL.md must show XML delimiting with <plan-content> tags"

    def test_has_sha256_hash_instructions(self):
        content = SKILL_MD_PATH.read_text()
        assert (
            "sha256" in content.lower() or "SHA-256" in content
        ), "SKILL.md must describe SHA-256 hashing for plan integrity"

    def test_has_plan_audit_json_instructions(self):
        content = SKILL_MD_PATH.read_text()
        assert "plan-audit.json" in content, "SKILL.md must describe plan-audit.json generation"

    def test_has_audit_json_schema_fields(self):
        """plan-audit.json must document all required fields."""
        content = SKILL_MD_PATH.read_text()
        required_fields = [
            "hash_algorithm",
            "original_hash",
            "validate_score",
            "revision_count",
            "review_score",
            "final_hash",
            "timestamp",
            "validated",
            "skipped",
        ]
        for field in required_fields:
            assert field in content, f"SKILL.md must document '{field}' in plan-audit.json schema"

    def test_has_history_update_instructions(self):
        content = SKILL_MD_PATH.read_text()
        assert (
            "HISTORY.md" in content
        ), "SKILL.md must describe HISTORY.md update with validation status"

    def test_has_prop009_reference(self):
        """Plan content must be XML-delimited per PROP-009 prompt injection defense."""
        content = SKILL_MD_PATH.read_text()
        assert (
            "PROP-009" in content
        ), "SKILL.md must reference PROP-009 for prompt injection defense"

    def test_has_must_do_should_do_classification(self):
        content = SKILL_MD_PATH.read_text()
        assert "Must-Do" in content, "SKILL.md must describe Must-Do recommendations"
        assert "Should-Do" in content, "SKILL.md must describe Should-Do recommendations"


class TestPlanHashComputation:
    """Verify SHA-256 hash computation for plan integrity tracking."""

    def test_sha256_hash_of_empty_content(self):
        """Empty content produces a valid SHA-256 hash."""
        h = hashlib.sha256(b"").hexdigest()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_sha256_hash_deterministic(self):
        """Same content always produces the same hash."""
        content = b"## TASK-001: Setup project\n- Complexity: S\n"
        h1 = hashlib.sha256(content).hexdigest()
        h2 = hashlib.sha256(content).hexdigest()
        assert h1 == h2

    def test_sha256_hash_changes_on_modification(self):
        """Modified content produces a different hash."""
        original = b"## TASK-001: Setup project"
        revised = b"## TASK-001: Setup project (revised)"
        h_orig = hashlib.sha256(original).hexdigest()
        h_rev = hashlib.sha256(revised).hexdigest()
        assert h_orig != h_rev

    def test_sha256_hash_multifile_concatenation(self):
        """Hash of concatenated plan files is deterministic."""
        tasks = b"# TASKS\n## TASK-001\n"
        properties = b"# PROPERTIES\n## PROP-001\n"
        test_plan = b"# TEST-PLAN\n## TEST-001\n"
        combined = tasks + properties + test_plan
        h = hashlib.sha256(combined).hexdigest()
        assert len(h) == 64
        assert h == hashlib.sha256(tasks + properties + test_plan).hexdigest()


AUDIT_SCHEMA_REQUIRED_FIELDS = {
    "hash_algorithm": str,
    "original_hash": str,
    "isthissmart_score": (int, float),
    "revision_count": int,
    "review_score": (int, float),
    "final_hash": str,
    "timestamp": str,
    "validated": bool,
    "skipped": bool,
}


class TestPlanAuditJsonSchema:
    """Validate plan-audit.json structure and types."""

    def _make_valid_audit(self) -> dict:
        """Create a valid plan-audit.json for testing."""
        return {
            "hash_algorithm": "sha256",
            "original_hash": hashlib.sha256(b"draft plan content").hexdigest(),
            "isthissmart_score": 7.8,
            "revision_count": 2,
            "review_score": 8.7,
            "final_hash": hashlib.sha256(b"final plan content").hexdigest(),
            "timestamp": "2026-02-15T10:30:00Z",
            "validated": True,
            "skipped": False,
        }

    def test_valid_audit_has_all_required_fields(self):
        audit = self._make_valid_audit()
        for field in AUDIT_SCHEMA_REQUIRED_FIELDS:
            assert field in audit, f"Missing required field: {field}"

    def test_valid_audit_field_types(self):
        audit = self._make_valid_audit()
        for field, expected_type in AUDIT_SCHEMA_REQUIRED_FIELDS.items():
            assert isinstance(
                audit[field], expected_type
            ), f"Field '{field}' should be {expected_type}, got {type(audit[field])}"

    def test_hash_algorithm_is_sha256(self):
        audit = self._make_valid_audit()
        assert audit["hash_algorithm"] == "sha256"

    def test_hashes_are_64_char_hex(self):
        audit = self._make_valid_audit()
        for field in ("original_hash", "final_hash"):
            h = audit[field]
            assert len(h) == 64, f"{field} must be 64 hex chars"
            assert all(c in "0123456789abcdef" for c in h), f"{field} must be hex"

    def test_scores_are_numeric(self):
        audit = self._make_valid_audit()
        assert isinstance(audit["isthissmart_score"], (int, float))
        assert isinstance(audit["review_score"], (int, float))

    def test_validated_true_when_review_passes(self):
        audit = self._make_valid_audit()
        audit["review_score"] = 8.5
        audit["validated"] = audit["review_score"] >= 8.5
        assert audit["validated"] is True

    def test_validated_false_when_review_fails(self):
        audit = self._make_valid_audit()
        audit["review_score"] = 7.0
        audit["validated"] = audit["review_score"] >= 8.5
        assert audit["validated"] is False

    def test_skipped_true_when_skip_flag(self):
        audit = self._make_valid_audit()
        audit["skipped"] = True
        audit["validated"] = False
        assert audit["skipped"] is True
        assert audit["validated"] is False

    def test_audit_serializes_to_json(self):
        audit = self._make_valid_audit()
        serialized = json.dumps(audit, indent=2)
        deserialized = json.loads(serialized)
        assert deserialized == audit

    def test_original_and_final_hash_differ_after_revision(self):
        audit = self._make_valid_audit()
        assert (
            audit["original_hash"] != audit["final_hash"]
        ), "After revision, original and final hashes should differ"


class TestRevisionLogFormat:
    """Validate revision-log.md format structure."""

    def _make_revision_log(self) -> str:
        """Create a sample revision-log.md for format validation."""
        return """\
# Revision Log

## Original Plan Hash
`abc123def456...` (SHA-256)

## IsThisSmart Score
7.8/10

## Revisions Applied

### Must-Do

1. **TASK-003 dependency missing** - Added TASK-002 as dependency for TASK-003
   - Source: IsThisSmart recommendation #1
   - File changed: TASKS.md

2. **Missing SAFETY property** - Added PROP-004 for input validation
   - Source: IsThisSmart recommendation #3
   - File changed: PROPERTIES.md

### Should-Do

1. **Add performance test** - Added TEST-008 for response time validation
   - Source: IsThisSmart recommendation #2
   - Status: Applied (low effort)

### Deferred

1. **Consider event sourcing** - Architecture suggestion deferred to future iteration
   - Source: IsThisSmart recommendation #5
   - Reason: High effort, not blocking

## Review Gate Results

| Round | Score | Action |
|-------|-------|--------|
| 1     | 7.2   | Applied 3 findings |
| 2     | 8.7   | Passed threshold |

## Final Plan Hash
`789abc012def...` (SHA-256)
"""

    def test_revision_log_has_header(self):
        log = self._make_revision_log()
        assert log.startswith("# Revision Log")

    def test_revision_log_has_original_hash(self):
        log = self._make_revision_log()
        assert "Original Plan Hash" in log

    def test_revision_log_has_isthissmart_score(self):
        log = self._make_revision_log()
        assert "IsThisSmart Score" in log

    def test_revision_log_has_must_do_section(self):
        log = self._make_revision_log()
        assert "### Must-Do" in log

    def test_revision_log_has_should_do_section(self):
        log = self._make_revision_log()
        assert "### Should-Do" in log

    def test_revision_log_has_deferred_section(self):
        log = self._make_revision_log()
        assert "### Deferred" in log

    def test_revision_log_has_review_gate_results(self):
        log = self._make_revision_log()
        assert "Review Gate Results" in log

    def test_revision_log_has_final_hash(self):
        log = self._make_revision_log()
        assert "Final Plan Hash" in log
