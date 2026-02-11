---
name: wfc:test
description: Intelligent test generation from formal properties and requirements. Creates property-based tests that verify SAFETY, LIVENESS, and INVARIANT properties, generates requirement-based test cases from acceptance criteria, executes test suites, and reports coverage gaps. Use when implementing new features with defined properties or improving test coverage. Triggers on "generate tests", "create tests from properties", "improve test coverage", or explicit /wfc:test. Ideal for TDD workflows, property verification, and quality assurance. Not for debugging failing tests or test infrastructure setup.
license: MIT
user-invocable: true
disable-model-invocation: false
argument-hint: [--generate or --run]
---

# WFC:TEST - Test Generation from Properties

Generates comprehensive test suites from formal properties and requirements.

## What It Does

1. **Property-Based Test Generator** - Tests from PROPERTIES.md
2. **Requirement-Based Test Generator** - Tests from TASKS.md acceptance criteria
3. **Test Executor** - Runs generated tests
4. **Coverage Reporter** - Test coverage analysis

## Usage

```bash
# Generate tests
/wfc:test --generate

# Run tests
/wfc:test --run

# Generate and run
/wfc:test
```

## Outputs

- tests/ directory with generated test files
- COVERAGE-REPORT.md
- Test execution results

## Philosophy

**ELEGANT**: Tests follow from properties naturally
**MULTI-TIER**: Test each tier independently
**PARALLEL**: Run tests concurrently
