# wfc-plan - MOCK / STUB

**This is a mock implementation for testing wfc-implement until full wfc-plan is built.**

## What wfc-plan Will Do (Real Implementation)

Adaptive planning that produces:

- `TASKS.md` - Ordered tasks with dependency graph
- `PROPERTIES.md` - Formal invariants (SAFETY, LIVENESS, INVARIANT, PERFORMANCE)
- `TEST-PLAN.md` - Test strategy and cases

## Mock Behavior

For testing wfc-implement, this mock provides sample TASKS.md, PROPERTIES.md, and TEST-PLAN.md files.

### Mock TASKS.md

```markdown
# Implementation Tasks

## TASK-001: Setup Project Structure
- **Complexity**: S
- **Dependencies**: []
- **Properties**: []
- **Description**: Create initial project directories and files
- **Acceptance Criteria**:
  - `src/` directory exists
  - `tests/` directory exists
  - `README.md` exists

## TASK-002: Implement Core Logic
- **Complexity**: M
- **Dependencies**: [TASK-001]
- **Properties**: [PROP-001]
- **Description**: Implement main business logic
- **Files Likely Affected**: [`src/core.py`]
- **Acceptance Criteria**:
  - Core function implemented
  - Returns expected output
  - Handles edge cases

## TASK-003: Add Tests
- **Complexity**: S
- **Dependencies**: [TASK-002]
- **Properties**: [PROP-001]
- **Description**: Add test coverage for core logic
- **Files Likely Affected**: [`tests/test_core.py`]
- **Acceptance Criteria**:
  - All core functions tested
  - Edge cases covered
  - 100% coverage
```

### Mock PROPERTIES.md

```markdown
# Formal Properties

## PROP-001: Correctness
- **Type**: INVARIANT
- **Statement**: Core function always returns valid output for valid input
- **Rationale**: Ensure reliability of core functionality
- **Acceptance Criteria**:
  - Valid input → valid output
  - Invalid input → clear error
  - No silent failures
```

### Mock TEST-PLAN.md

```markdown
# Test Plan

## Test Strategy
- Unit tests for all core functions
- Integration tests for end-to-end flows
- Property-based tests for PROP-001

## Test Cases

### TC-001: Core Function Valid Input
- **Property**: PROP-001
- **Input**: Valid data
- **Expected**: Valid output
- **Priority**: HIGH

### TC-002: Core Function Invalid Input
- **Property**: PROP-001
- **Input**: Invalid data
- **Expected**: Clear error message
- **Priority**: HIGH
```

## Usage

```python
from wfc.skills.plan.mock import generate_mock_plan

# Generate mock plan files
generate_mock_plan(output_dir="./plan")
```

This will create mock TASKS.md, PROPERTIES.md, and TEST-PLAN.md for testing.
