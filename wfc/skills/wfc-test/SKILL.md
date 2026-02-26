---
name: wfc-test
description: >
  Generates structured test cases from formal input sources: a PROPERTIES.md
  file with SAFETY(...), LIVENESS(...), or INVARIANT(...) syntax, and/or a
  TASKS.md file with Given/When/Then acceptance criteria. Produces a
  TRACEABILITY-REPORT.md identifying uncovered properties and criteria.

  Invoke only when ALL are true: a conforming input document exists; user
  explicitly requests test generation; target language and framework confirmed.

  Trigger phrases: "generate tests from properties/requirements", "create
  tests from PROPERTIES.md / TASKS.md", "derive test cases from formal
  properties", explicit /wfc-test command.

  Not for:
  - Writing tests without a conforming PROPERTIES.md or TASKS.md as input
  - Fuzz or generative testing (QuickCheck, Hypothesis, fast-check)
  - Debugging or fixing failing tests
  - Running or managing test suites
  - Authoring or validating PROPERTIES.md or TASKS.md input documents
license: MIT
---

# WFC:TEST — Formal-Specification-Driven Test Generation

Generates test cases mapped one-to-one against formal property definitions
and structured acceptance criteria. Does not execute tests, does not report
code coverage, and does not generate tests without conforming input documents.

## Preconditions (Required Before Invocation)

The agent MUST verify all of the following before proceeding. If any
precondition fails, emit the corresponding error and halt.

| Precondition | Failure message |
|---|---|
| PROPERTIES.md exists OR TASKS.md exists | `ERROR: No PROPERTIES.md or TASKS.md found. Provide at least one conforming input document.` |
| PROPERTIES.md entries use `SAFETY(...)`, `LIVENESS(...)`, or `INVARIANT(...)` syntax | `ERROR: PROPERTIES.md contains unrecognized property types. Supported: SAFETY, LIVENESS, INVARIANT.` |
| TASKS.md acceptance criteria use Given/When/Then format | `WARNING: Task "{task}" has no parseable Given/When/Then criteria — skipped. Record in TRACEABILITY-REPORT.md.` |
| Target language and test framework confirmed by user or detectable from project files | `ERROR: Cannot determine target language and test framework. Specify explicitly (e.g., "Python/pytest", "TypeScript/Jest").` |

## What It Does

### 1. Formal Property Test Generator

**Input**: PROPERTIES.md with entries conforming to:

```
SAFETY(expression): human-readable description
LIVENESS(expression): human-readable description
INVARIANT(expression): human-readable description
```

**Property-to-test mapping** (deterministic, not invented):

- `SAFETY(expr)`: Generate a test that asserts `expr` holds after every
  state-mutating operation on the relevant component. Test fails if any
  mutation violates the expression.
- `LIVENESS(expr)`: Generate a test that asserts `expr` becomes true within
  a bounded number of steps or a configurable timeout. Document the bound
  in the test.
- `
