# wfc-consensus-review - MOCK / STUB

**This is a mock implementation for testing wfc-implement until full wfc-consensus-review is built.**

## What wfc-consensus-review Will Do (Real Implementation)

Multi-agent code review system with specialized agents:

- **CR** (Correctness): Logic, edge cases, bugs
- **SEC** (Security): Vulnerabilities, auth, data exposure
- **PERF** (Performance): Efficiency, scalability
- **COMP** (Completeness): Requirements met, nothing missing

Returns consensus score (0-10) and detailed findings.

## Mock Behavior

For testing wfc-implement, this mock provides:

- Simple pass/fail based on basic checks
- Mock review report with findings
- Configurable failure scenarios for testing rollback

### Mock Review Logic

```python
def mock_review(files, properties):
    """
    Simple mock review:
    - PASS if tests exist and basic structure is good
    - FAIL if obvious issues detected
    """
    score = 8.5  # Default passing score
    findings = []

    # Check 1: Tests exist
    if no_test_files(files):
        score -= 2
        findings.append("Missing test files")

    # Check 2: Properties covered
    for prop in properties:
        if not_tested(prop, files):
            score -= 1
            findings.append(f"Property {prop} not tested")

    # Check 3: Basic security (no hardcoded secrets)
    if has_secrets(files):
        score = 0
        findings.append("CRITICAL: Hardcoded secrets detected")

    return {
        "score": score,
        "passed": score >= 7.0,
        "findings": findings
    }
```

### Mock Review Report

```json
{
  "review_id": "review-123",
  "task_id": "TASK-002",
  "status": "PASSED",
  "score": 8.5,
  "agents": {
    "CR": {
      "score": 9.0,
      "findings": ["Code logic is sound", "Edge cases handled"]
    },
    "SEC": {
      "score": 8.0,
      "findings": ["No critical vulnerabilities", "Consider input validation"]
    },
    "PERF": {
      "score": 8.5,
      "findings": ["Performance acceptable", "Minor optimization possible"]
    },
    "COMP": {
      "score": 9.0,
      "findings": ["All acceptance criteria met"]
    }
  },
  "consensus": "Code meets quality standards. Minor suggestions provided.",
  "passed": true
}
```

## Usage

```python
from wfc.skills.review.mock import mock_review

# Review code
result = mock_review(
    files=["src/core.py", "tests/test_core.py"],
    properties=["PROP-001", "PROP-002"]
)

if result["passed"]:
    print("✅ Review passed")
else:
    print("❌ Review failed")
```

## Configuration

Set environment variable to simulate failures:

```bash
# Always pass
export WFC_MOCK_REVIEW_MODE=pass

# Always fail (for testing rollback)
export WFC_MOCK_REVIEW_MODE=fail

# Random (for testing retry logic)
export WFC_MOCK_REVIEW_MODE=random
```
