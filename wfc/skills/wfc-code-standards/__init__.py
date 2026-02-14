"""
wfc-code-standards - Universal Coding Standards

Language-agnostic standards that apply to all WFC projects. Language-specific
skills (wfc-python, etc.) inherit these and add tooling-specific rules.

Architecture:
    - Three-tier (presentation / logic / data)
    - SOLID principles (SRP, OCP, LSP, ISP, DIP)
    - Composition over inheritance (max 1 level)
    - Factory patterns for conditional/registry-based creation

Code Quality:
    - 500-line hard cap per file
    - DRY (extract at 3+ repetitions)
    - Structured error hierarchies (no bare catch-all)
    - Resource lifecycle via language mechanisms (with/defer/using)
    - Atomic writes for state files
    - Idempotent operations (safe to retry, no duplicates)
    - Early returns, flat structure, explicit naming

Observability:
    - Structured logging (events, not sentences)
    - No print/console.log for logging
    - No string interpolation in log calls
    - Context binding (request ID, user ID)
    - Never log secrets or PII

Testing:
    - Three tiers: unit / integration / e2e
    - Fixtures over setup/teardown
    - Parametrize over loops
    - Deterministic test data (seeded)
    - 80%+ coverage on business logic
    - Mock at boundaries, not internals

Async Safety:
    - Never block the event loop
    - Timeouts on all external calls
    - CPU-bound work in thread pools
    - Cancellation safety (never swallow)

Dependencies:
    - Lock files committed to VCS
    - Frozen install in CI/Docker
    - CVE scanning mandatory
    - Minimum version constraints (>=X.Y, never ==)
    - Split prod/dev/test dependencies

Documentation:
    - Public API docstrings mandatory
    - Summary, params, returns, errors
    - Types in signatures, not docs
"""

from __future__ import annotations

__version__ = "0.1.0"

# Universal standards as a machine-readable dict.
# Language-specific skills merge their own settings on top.
STANDARDS: dict[str, str | int | bool] = {
    # Architecture
    "three_tier_architecture": True,
    "solid_principles": True,
    "composition_over_inheritance": True,
    "max_inheritance_depth": 1,
    "factory_patterns": True,

    # Code quality
    "max_file_lines": 500,
    "dry_threshold": 3,  # extract at 3+ repetitions
    "max_nesting_depth": 3,
    "early_returns": True,
    "structured_error_handling": True,
    "resource_lifecycle_enforced": True,
    "atomic_writes": True,
    "idempotent_operations": True,
    "no_dead_code": True,

    # Observability
    "structured_logging": True,
    "no_print_logging": True,
    "no_string_interpolation_in_logs": True,
    "context_binding": True,
    "no_pii_in_logs": True,

    # Testing
    "test_organization_three_tier": True,
    "fixtures_over_setup": True,
    "parametrize_over_loops": True,
    "deterministic_test_data": True,
    "min_coverage_business_logic": 80,
    "mock_at_boundaries": True,

    # Async safety
    "no_blocking_in_async": True,
    "timeouts_on_external_calls": True,
    "cpu_in_thread_pool": True,
    "cancellation_safety": True,

    # Dependencies
    "lockfile_committed": True,
    "frozen_install_in_ci": True,
    "cve_scanning": True,
    "min_version_constraints": True,
    "split_dependencies": True,

    # Documentation
    "public_api_docstrings": True,
}

# Universal review checklist categories. Language skills extend with specific items.
REVIEW_CHECKLIST: dict[str, list[str]] = {
    "architecture": [
        "Presentation tier importing data tier directly",
        "Business logic in route handlers / controllers / CLI commands",
        "Database queries or API calls in the logic tier",
        "God classes (>1 responsibility)",
        "Deep inheritance (>1 level) where composition would work",
    ],
    "code_quality": [
        "Files exceeding 500 lines",
        "Bare catch-all error handling",
        "Silently swallowed errors",
        "Missing type annotations on public APIs",
        "Deep nesting (>3 levels) instead of early returns",
        "Magic strings/numbers instead of named constants",
        "Dead code (commented out blocks, unused imports)",
        "Resource handles not using structured lifecycle",
    ],
    "observability": [
        "print/console.log for logging",
        "String interpolation in log calls",
        "Missing context in error logs",
        "Logging secrets or PII",
    ],
    "testing": [
        "Tests with loops instead of parametrization",
        "Tests that depend on execution order",
        "Missing assertions",
        "Mocking the thing being tested",
        "No test for error/edge cases",
    ],
    "async_safety": [
        "Blocking I/O in async functions",
        "Missing timeouts on external calls",
        "Swallowed cancellation signals",
    ],
    "idempotency": [
        "Blind inserts that create duplicates on retry",
        "Delete operations that error on missing resources",
        "Side effects without idempotency guards",
        "Migrations or scripts that break when run twice",
        "Queue consumers without dedup",
    ],
    "dependencies": [
        "Lock file not committed",
        "Exact version pins in manifest",
        "No CVE scanning in CI",
        "Dev dependencies in production bundle",
    ],
}

__all__ = [
    "STANDARDS",
    "REVIEW_CHECKLIST",
]
