---
name: wfc-test
description: >
  Generates structured, example-based unit tests (pytest, JUnit, Jest) from
  formal input sources: a PROPERTIES.md file with SAFETY(...), LIVENESS(...),
  or INVARIANT(...) syntax, and/or a TASKS.md file with Given/When/Then
  acceptance criteria. Produces a TRACEABILITY-REPORT.md identifying uncovered
  properties and criteria. Does NOT generate property-based or fuzz tests
  (Hypothesis, QuickCheck).

  Requires: user-provided input document and explicit target language/framework.

  Trigger phrases: "generate tests from PROPERTIES.md", "create unit tests from
  requirements", "/wfc-test".

  Not for:
  - Writing tests without a conforming PROPERTIES.md or TASKS.md as input
  - Fuzz or generative testing (QuickCheck, Hypothesis, fast-check)
  - Explaining testing methodologies or theory
  - Debugging, fixing, or running tests
  - Authoring or validating the input PROPERTIES.md or TASKS.md documents
  - Detecting languages or frameworks automatically (must be explicit)
license: MIT
---

# WFC:TEST — Formal-Specification-Driven Test Generation

Generates concrete, example-based test cases mapped to formal property
definitions and acceptance criteria. Does not execute tests, does not report
code coverage.

## Preconditions (Required Before Invocation)

The agent MUST verify all of the following before proceeding. If any
precondition fails, emit the corresponding error and halt.

| Precondition | Failure message |
|---|---|
| User provides content for PROPERTIES.md OR TASKS.md | `ERROR: No input content provided. Please paste or attach the PROPERTIES.md or TASKS.md content.` |
| PROPERTIES.md entries use `SAFETY(...)`, `LIVENESS(...)`, or `INVARIANT(...)` syntax | `ERROR: PROPERTIES.md contains unrecognized property types. Supported: SAFETY, LIVENESS, INVARIANT.` |
| TASKS.md acceptance criteria use Given/When/Then format | `WARNING: Task "{task}" has no parseable Given/When/Then criteria — skipped. Record in TRACEABILITY-REPORT.md.` |
| Target language and test framework explicitly specified by user | `ERROR: Target language and framework not specified. Please explicitly state the target (e.g., "Python/pytest", "TypeScript/Jest").` |
| LIVENESS properties include a bounded constraint (time or steps) | `ERROR: LIVENESS property "{expr}" is missing a bounded constraint (e.g., "within 5s"). Example-based tests require explicit limits.` |

## What It Does

### 1. Formal Property Test Generator

**Input**: PROPERTIES.md content conforming to:

```
SAFETY(expression): human-readable description
LIVENESS(expression) within [bound]: human-readable description
INVARIANT(expression): human-readable description
```

**Property-to-test mapping**:
The agent generates **example-based test code**. It does not invent logic but
translates the formal expression into a code assertion.

- `SAFETY(expr)`: Generate a test setup and a test method that asserts `expr`
  evaluates to `false` (or throws) when violated, and `true` otherwise.
  *Note: If implementation details (class/function names) are not provided,
  generate a placeholder test with a `TODO: Implement component instantiation`
  comment.*
- `LIVENESS(expr) within [bound]`: Generate a test that polls or waits for
  `expr` to become true, failing if the `bound` (timeout) is exceeded.
- `INVARIANT(expr)`: Generate a test that asserts `expr` is true for the
  initial state and remains true after a sample set of state transitions.

### 2. Acceptance Criteria Test Generator

**Input**: TASKS.md content with Given/When/Then blocks.

**Mapping**:

- Map each `Scenario` to a test function/method.
- Translate `Given` to test setup/arrange steps.
- Translate `When` to the action/act step.
- Translate `Then` to assertions/assert steps.

### 3. Traceability Reporting

Produces a `TRACEABILITY-REPORT.md` containing:

1. A list of parsed properties/criteria.
2. The generated test file location/name for each.
3. A list of skipped items (malformed syntax or missing bounds).
4. **Coverage Gap Analysis**: A list of properties for which no test was
   generated (e.g., due to missing implementation context).
