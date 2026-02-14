---
name: wfc-code-standards
description: Language-agnostic coding standards for all WFC projects. Enforces architecture (three-tier, SOLID, composition over inheritance), code quality (500-line limit, DRY, early returns, structured errors), observability (structured logging, no print/console.log), testing philosophy (unit/integration/e2e, fixtures, parametrization), async safety (never block the event loop), dependency management (lock files, CVE scanning, version pinning), and documentation (public API docstrings). Referenced by all language-specific skills. Not a user-invocable skill.
license: MIT
---

# WFC:CODE-STANDARDS - Universal Coding Standards

Language-agnostic standards that apply to **every** WFC project regardless of language. Language-specific skills (wfc-python, etc.) inherit these and add tooling-specific rules.

## Architecture

### Three-Tier Architecture

All backend/service code follows three tiers. No exceptions.

```
┌─────────────────────────────────┐
│  PRESENTATION (Routes/CLI/UI)   │  Thin. Parses input, calls logic, formats output.
├─────────────────────────────────┤
│  LOGIC (Services/Use Cases)     │  All business rules live here. No I/O knowledge.
├─────────────────────────────────┤
│  DATA (Repositories/Clients)    │  Database, API calls, file system. No business rules.
└─────────────────────────────────┘
```

**Rules**:
- Presentation **never** imports data tier directly (always goes through logic)
- Logic tier has **zero** knowledge of HTTP, CLI, or UI frameworks
- Data tier has **zero** business logic - it fetches, stores, and returns
- Each tier is independently testable (mock the tier below)

### SOLID Principles

| Principle | Rule | Violation Signal |
|-----------|------|-----------------|
| **SRP** | One class/module = one reason to change | Class has methods touching different domains |
| **OCP** | Extend via new implementations, not modifying existing | `if type == "X"` chains growing with each feature |
| **LSP** | Subtypes must be substitutable for their base | Override changes behavior callers depend on |
| **ISP** | Small, focused interfaces | Implementers forced to stub methods they don't need |
| **DIP** | Depend on abstractions, not concretions | Constructor takes concrete class instead of interface/protocol |

**The most important two**: SRP (one responsibility per unit) and DIP (inject dependencies via interfaces, never hardcode concrete implementations).

### Composition Over Inheritance

**Rule**: Maximum 1 level of inheritance. Beyond that, use composition.

```
# BAD: Deep inheritance tree
Animal → Pet → Dog → GuideDog → TrainedGuideDog

# GOOD: Compose behaviors
GuideDog has: Animal (data), PetBehavior, GuidingCapability, TrainingRecord
```

**When inheritance is OK**:
- Extending a framework's base class (one level)
- Enum/error type hierarchies (flat)

**When to use composition**:
- Behavior varies independently
- Multiple capabilities needed
- Testing requires swapping implementations

### Factory Patterns

Use factories when object creation involves decisions. Don't use them for simple construction.

**When to use**:
- Creation depends on runtime conditions (config, input type, feature flags)
- Registry of implementations (plugins, handlers, strategies)
- Object requires complex setup (connection pools, configuration chains)

**When NOT to use**:
- Simple dataclass/struct construction
- Only one implementation exists
- No conditional logic in creation

## Code Quality

### 500-Line File Limit (Hard Cap)

No source file may exceed 500 lines. This is a hard cap, not a guideline.

**When approaching the limit**:
1. Extract a class into its own module
2. Group related functions into a submodule
3. Move constants/types to a dedicated file

**What counts**: All lines including comments, docstrings, blank lines. The file is the unit of cognitive load.

### DRY - Don't Repeat Yourself

Extract when you see 3+ repetitions. Not 2 - that's premature abstraction. At 3, the pattern is confirmed.

### Elegance Rules

1. **Simplest solution wins** - don't reach for a pattern until forced to
2. **Stdlib/builtins first** - don't add a dependency for something the language provides
3. **Flat is better than nested** - max 3 levels of indentation; restructure beyond that
4. **Early returns** - guard clauses at the top, happy path at the bottom
5. **Explicit over implicit** - named constants over magic values, clear names over clever abbreviations
6. **Delete dead code** - commented-out code and unused imports are noise, not documentation

### Error Handling

**Rules**:
- Define a structured exception/error hierarchy per project (base error, then domain errors)
- **Never** silently swallow errors - log and re-raise, or handle explicitly
- **Never** use bare catch-all (`except:`, `catch (Exception)`, `catch(...)`) - always specify the type
- Add context to errors when re-throwing: what operation failed, what input caused it
- Use error groups/multi-errors when multiple operations can fail independently

**Philosophy**: Errors are data. They carry context. They have types. They are part of the API contract.

### Resource Lifecycle

All resources (files, connections, handles, locks) must use the language's structured lifecycle mechanism:
- Python: context managers (`with`/`async with`)
- Go: `defer`
- Rust: RAII / `Drop`
- TypeScript/JS: `using` (Stage 3) or try/finally
- Java/Kotlin: try-with-resources / `use`

**Never** rely on garbage collection to close resources. Explicit lifecycle, always.

### Atomic Writes

When writing files that represent state (config, data, caches), use atomic write patterns:
1. Write to a temporary file in the same directory
2. Flush and sync to disk
3. Atomically rename/move to the target path

This prevents half-written files on crash. A file either exists with complete content or doesn't exist.

## Observability

### Structured Logging

Text logs are dead. We log **events**, not sentences.

**Rules**:
- **No print/console.log/fmt.Println for logging** - use structured logging libraries
- **No string interpolation in log calls** - it breaks aggregation and indexing
- **Log events as key-value pairs** - machine-parseable, queryable, aggregatable
- **Bind context early** - request ID, user ID, correlation ID bound once, available everywhere
- **Never log secrets or PII** - API keys, passwords, emails, SSNs are never logged

```
# BAD (every language)
log("User 123 failed to login with error: timeout")
log(f"Processing order {order_id}")

# GOOD (every language)
log.error("login_failed", user_id=123, error="timeout")
log.info("order_processing", order_id=order_id)
```

**Context propagation**: In request-based systems, bind context (request ID, user ID) at the middleware/handler entry point. All downstream log calls automatically include this context without passing it manually.

**Error logging**: Always include:
- Event name (what happened)
- Error type (class/type of error)
- Error message (human-readable)
- Stack trace (when available and appropriate)
- Operation context (what was being attempted)

### Log Levels

| Level | When to Use |
|-------|------------|
| **debug** | Detailed flow for development - never in production hot paths |
| **info** | Normal operations: request started, task completed, config loaded |
| **warning** | Degraded but functional: retrying, fallback used, deprecated call |
| **error** | Operation failed but system continues: payment failed, API timeout |
| **critical/fatal** | System cannot continue: database unreachable, config missing |

## Testing Philosophy

### Organization

All projects organize tests into three tiers:

```
tests/
├── conftest / fixtures / helpers    # Shared test infrastructure
├── unit/                            # Fast, isolated, no I/O, no network
├── integration/                     # Real dependencies (DB, APIs, filesystem)
└── e2e/                             # Full system tests, deployed environment
```

**Unit tests** run in milliseconds. They test logic in isolation. Mock everything external.

**Integration tests** use real dependencies. They verify that your code talks to the real world correctly.

**E2E tests** validate the entire system. They are slow, expensive, and catch what unit + integration miss.

### Test Naming

Name tests for what they verify, not how they work:

```
test_<what>_<condition>_<expected>

# GOOD
test_create_order_with_empty_cart_raises_validation_error
test_user_login_with_expired_token_returns_401

# BAD
test_order_1
test_happy_path
test_edge_case
```

### Test Design Rules

- **Fixtures over setup/teardown**: Use the language's fixture mechanism (pytest fixtures, Jest beforeEach, Go TestMain). Shared state setup belongs in reusable fixtures, not copy-pasted setup blocks.
- **Parametrize over loops**: Never write a loop inside a test. Use parametrized/table-driven tests. Each parameter set is a distinct test case with its own failure message.
- **One assertion focus per test**: A test should verify one behavior. Multiple assertions are fine when they all verify aspects of the same behavior. Multiple unrelated assertions mean multiple tests.
- **Deterministic test data**: Seed random generators. Use factories with fixed seeds. Tests must be reproducible - same input, same output, every run.
- **No test interdependence**: Tests must pass in any order. No test may depend on another test's side effects.

### Coverage

- **80%+ on business logic** (services/logic tier) - this is the floor, not the ceiling
- Don't chase 100% on presentation or data tiers - those are better covered by integration tests
- Coverage is a diagnostic, not a target: 80% coverage with meaningful assertions > 95% coverage with `assert true`

### Mocking Rules

- **Mock at boundaries**: Mock the data tier when testing the logic tier. Mock external APIs. Don't mock the thing you're testing.
- **Prefer fakes over mocks**: A fake implementation (in-memory DB, stub API) is more reliable than a mock that mirrors internal expectations.
- **Verify behavior, not implementation**: Assert that the right result came back or the right side effect occurred. Don't assert internal call sequences unless the sequence IS the behavior.

## Async Safety

The event loop must never be blocked. A single blocking call in async code stalls every concurrent task in that runtime.

**Universal rules**:
- **No blocking I/O in async functions**: File reads, network calls, and sleeps must use async variants
- **No blocking sleep**: Use the async sleep variant (`asyncio.sleep`, `setTimeout`/`await delay`, etc.)
- **CPU-bound work in thread pools**: If you must call CPU-intensive or legacy blocking code from async context, dispatch it to a thread pool
- **Timeouts on all external calls**: Every network request, database query, and external API call must have an explicit timeout
- **Cancellation safety**: Never swallow cancellation signals. If you catch them for cleanup, always re-raise/re-propagate

**Why this matters**: One `requests.get()` or `time.sleep(5)` inside an async handler blocks the entire event loop. Every other request, websocket, and background task in that process is frozen until the blocking call completes.

## Dependency Management

### Version Constraints

- **Set a minimum version**: Every dependency must have a lower bound (`>=X.Y`)
- **Never pin exact versions in the manifest**: `==X.Y.Z` blocks security patches and creates merge conflicts. The lock file pins exact versions.
- **The lock file is the source of truth**: The manifest says "what I need", the lock file says "exactly what I got"

### Lock Files

- **Always commit the lock file** to version control
- **Use frozen/locked install in CI and Docker**: Never regenerate the lock file during builds
- **Verify lock file sync in CI**: Fail the build if the lock file is out of sync with the manifest
- **Upgrades happen locally**: Developer upgrades a dep, regenerates lockfile, commits both. CI uses frozen.

### Dependency Hygiene

- **Split dependencies**: Separate production deps from dev/test deps. Dev tools must never ship to production.
- **CVE scanning is mandatory**: Automated vulnerability scanning on every CI run. Builds fail on known CVEs.
- **Review transitive deps**: A vulnerability in a dependency's dependency is still your problem.
- **Audit before suppressing**: When suppressing a CVE alert, document why in the suppression comment.

## Documentation

### Public API Docstrings

Every public module, class, function, and method must have a docstring/doc comment. This is non-negotiable.

**What a docstring must contain**:
1. **Summary**: One sentence, imperative mood ("Calculate velocity." not "This function calculates velocity.")
2. **Description** (if non-obvious): Why this exists, when to use it vs alternatives
3. **Parameters**: Name and purpose (types come from the signature, not the docs)
4. **Returns**: What the caller gets back
5. **Errors/Exceptions**: What can go wrong and when

**What a docstring must NOT contain**:
- Type information that's already in the signature
- Implementation details that change with refactoring
- Changelog entries ("Added in v2.3")

**Private/internal functions**: Docstring optional. Only add if the logic is non-obvious.

**Module/package docstrings**: Required. Brief summary of purpose and architectural role (which tier, what domain).

## Code Review Checklist (Universal)

When reviewing code in any language, flag:

**Architecture violations**:
- Presentation tier importing data tier directly (bypassing logic)
- Business logic in route handlers / controllers / CLI commands
- Database queries or API calls in the logic tier
- God classes (>1 responsibility)
- Deep inheritance (>1 level) where composition would work

**Code quality violations**:
- Files exceeding 500 lines
- Bare catch-all error handling
- Silently swallowed errors
- Missing type annotations on public APIs
- Deep nesting (>3 levels) instead of early returns
- Magic strings/numbers instead of named constants
- Dead code (commented out blocks, unused imports)
- Resource handles not using structured lifecycle (with/defer/using)

**Observability violations**:
- print/console.log for logging
- String interpolation in log calls
- Missing context in error logs (no request ID, no operation name)
- Logging secrets or PII

**Testing violations**:
- Tests with loops instead of parametrization
- Tests that depend on execution order
- Missing assertions (test runs code but doesn't verify anything)
- Mocking the thing being tested instead of its dependencies
- No test for the error/edge cases

**Async violations**:
- Blocking I/O in async functions
- Missing timeouts on external calls
- Swallowed cancellation signals

**Dependency violations**:
- Lock file not committed
- Exact version pins in manifest (not lockfile)
- No CVE scanning in CI
- Dev dependencies in production bundle

---

**These standards are inherited by all language-specific skills.** Language skills add tooling, libraries, and syntax-specific rules on top.
