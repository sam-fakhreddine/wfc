---
name: wfc-code-standards
description: Language-agnostic coding standards for all WFC projects. Enforces the Defensive Programming Standard (DPS) across 13 dimensions including architecture (three-tier, functional core/imperative shell, SOLID, composition over inheritance, immutability by default, least privilege API surface), code quality (500-line limit, DRY, early returns, structured errors, idempotent operations, fail fast at boundaries), boundary validation (schema-first, reject unknown, safe access), state management (enumerated states, transition maps, guarded transitions), error contracts (structured errors with correlation IDs), retry and timeout (explicit timeouts, bounded retries, backoff), observability (structured logging, metrics, correlation IDs), concurrency safety (optimistic locking, no shared mutable state), security (parameterized queries, least privilege, rate limiting), configuration (explicit defaults, fail-fast startup, env validation), infrastructure requirements (health checks, graceful shutdown, DLQ), testing philosophy (unit/integration/e2e, required negative test categories), async safety (never block the event loop), and dependency management (lock files, CVE scanning, version pinning). Referenced by all language-specific skills. Not a user-invocable skill.
license: MIT
---

# WFC:CODE-STANDARDS - Universal Coding Standards

Language-agnostic standards that apply to **every** WFC project regardless of language. Language-specific skills (wfc-python, etc.) inherit these and add tooling-specific rules.

All standards are organized around the **Defensive Programming Standard (DPS)** — 13 dimensions that ensure production-grade code from the first line.

## Definition of Done (DPS-0)

A feature is not complete until ALL applicable items are satisfied:

- [ ] All external inputs validated at the boundary (DPS-1)
- [ ] All mutating operations are idempotent (DPS-2)
- [ ] All state transitions enforced via explicit rules (DPS-3)
- [ ] All errors return structured responses (DPS-4)
- [ ] All external calls have timeouts and retry caps (DPS-5)
- [ ] All logs are structured with correlation IDs (DPS-6)
- [ ] All shared state access is race-free (DPS-7)
- [ ] All permissions are least-privilege (DPS-8)
- [ ] All config has explicit defaults and startup validation (DPS-9)
- [ ] All new services have health checks (DPS-10)
- [ ] All new features have negative test cases (DPS-11)
- [ ] All list/search APIs implement pagination

This checklist applies to new features and significant modifications. Pure refactors that don't change behavior are exempt from items they don't touch.

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

### Functional Core / Imperative Shell

The three-tier architecture tells you *what* to separate. This tells you *how* to think about it.

```
┌────────────────────────────────────────────┐
│  IMPERATIVE SHELL (I/O, side effects)      │  Reads files, calls APIs, writes DB.
│  ┌──────────────────────────────────────┐  │  Thin. Orchestrates. No decisions.
│  │  FUNCTIONAL CORE (pure logic)        │  │
│  │  No I/O. No side effects.            │  │  All business rules. Takes data in,
│  │  Same input → same output. Always.   │  │  returns data out. Trivially testable.
│  └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

**Rules**:
- **Business logic is pure**: Functions in the logic tier take data in and return data out. No database calls, no file reads, no network requests, no randomness, no current time. These are injected as arguments or returned as "commands" for the shell to execute.
- **I/O lives at the edges**: The presentation and data tiers handle all side effects. The shell reads from the world, passes data to the core, gets results back, and writes to the world.
- **Testing the core needs zero mocks**: If you need mocks to test your business logic, the boundary is in the wrong place. Pure functions are tested with input/output pairs.
- **Side effects are explicit**: When a function must trigger a side effect, it returns a description of what should happen (a command, an event, a result object) rather than performing it directly.

**Why this matters**: Pure functions are trivially testable, trivially composable, trivially parallelizable, and trivially debuggable. When a test fails, you look at input and output — no mocking infrastructure, no setup/teardown ceremony, no "did the mock get called with the right args" fragility.

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

### Immutability by Default

Data should be immutable unless there's a specific reason to mutate it. Mutable shared state is the root cause of entire bug categories.

**Rules**:
- **Default to immutable data structures**: Frozen dataclasses, readonly records, const declarations, `val` not `var`. Opt into mutability only when the algorithm requires it.
- **Never mutate function arguments**: If a function needs a modified version, return a new copy. Callers should never be surprised that their data changed.
- **Collections are immutable by default**: Return frozen/unmodifiable collections from APIs. If the caller needs to modify, they copy.
- **Configuration is immutable after load**: Parse config once at startup, freeze it, inject it everywhere. No runtime config mutation.

**When mutability is OK**:
- Builder patterns during construction (freeze after `.build()`)
- Performance-critical inner loops (local mutation, not shared)
- Accumulator patterns (local to a single function scope)

**Why this matters**: Immutable data can be shared freely between threads, cached without worry, and reasoned about without tracing every code path that might modify it. When you see `user.name`, you know it's the same value everywhere — nobody changed it behind your back.

```
# BAD: mutable shared state
def process_users(users):
    users.sort(key=lambda u: u.name)  # Surprise! Caller's list is now sorted
    return users[:10]

# GOOD: immutable by default
def process_users(users):
    return sorted(users, key=lambda u: u.name)[:10]  # New list, original untouched
```

### Least Privilege / Minimal API Surface

Expose the minimum possible interface. Everything is private by default, public only when needed.

**Rules**:
- **Private by default**: Functions, classes, methods, and fields start as private/internal. Promote to public only when an external consumer needs it.
- **Narrow function signatures**: Accept the minimum data needed. A function that needs a user's email takes `email: str`, not `user: User`.
- **Return the minimum data needed**: Don't return an entire object when the caller only needs a status code.
- **Module exports are curated**: Use `__all__`, package-private, `internal` packages, or equivalent. Don't expose implementation details.
- **Permissions follow the same principle**: Database users get only the permissions they need. API tokens scope to the operations required. File permissions are restrictive by default.

**Why**: A smaller API surface means fewer things that can break, fewer things to test, fewer things to document, and fewer things that consumers can depend on (and that you can never change). Every public API is a promise.

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

### Error Handling and Error Contract (DPS-4)

**Rules**:
- Define a structured exception/error hierarchy per project (base error, then domain errors)
- **Never** silently swallow errors - log and re-raise, or handle explicitly
- **Never** use bare catch-all (`except:`, `catch (Exception)`, `catch(...)`) - always specify the type
- Add context to errors when re-throwing: what operation failed, what input caused it
- Use error groups/multi-errors when multiple operations can fail independently

**Error contract**: All errors returned to callers MUST include:

```json
{
  "code": "MACHINE_READABLE_CODE",
  "message": "Human-readable description of what went wrong",
  "correlationId": "req-abc-123"
}
```

- **Machine-readable code**: Stable string that clients can switch on (e.g., `ORDER_NOT_FOUND`, `RATE_LIMIT_EXCEEDED`). Never use HTTP status codes as error codes — they're transport, not domain
- **Human-readable message**: Describes what went wrong in terms the caller can act on. No raw stack traces. No "something went wrong"
- **Correlation ID**: Links this error to logs, traces, and upstream requests. Propagated from request context, not generated per error
- **No raw stack traces to callers**: Stack traces go to logs (with correlation ID). Callers get structured errors. Internal details are security risks and useless to API consumers

**Philosophy**: Errors are data. They carry context. They have types. They are part of the API contract.

### Boundary Validation (DPS-1)

Detect bad state at the boundary. Reject it immediately with a clear error. Never let invalid data propagate into the system where it becomes a mystery bug three layers deep.

**Schema validation at entry**:
- Validate the **shape** of all external input before touching it: required fields present, types correct, enums in range, sizes bounded
- Use schema libraries (pydantic, zod, JSON Schema, protobuf) — hand-rolled validation drifts from intent
- **No business logic executes before validation passes** — validation is the first thing that happens at every entry point

**Validation rules**:
- **Reject unknown fields**: If the schema doesn't define it, reject it. Silent acceptance of extra fields hides API misuse and version drift
- **Enforce max payload size**: Every ingress point (HTTP, queue, file upload) has an explicit size cap. No unbounded reads
- **Validate enum values against allowed set**: Don't trust that a string is one of your valid states — check it
- **Normalize inputs**: Trim whitespace, normalize case where appropriate — do this in the validation layer, not scattered through business logic
- **Validate semantics, not just shape**: A date in the future, a negative quantity, an email without `@` — shape says "it's a string", semantics says "it's valid"
- **Safe access on external data**: Use `payload.get("key", default)` not `payload["key"]` — external data is untrusted

```
# BAD: silent propagation
def process_order(order):
    # order.items could be None... we'll find out 3 functions later
    total = calculate_total(order.items)

# GOOD: validate at boundary
def process_order(order):
    if not order.items:
        raise InvalidOrderError("Order must have at least one item", order_id=order.id)
    total = calculate_total(order.items)
```

**Preconditions at function entry**: Public functions that require non-null, non-empty, or bounded inputs should assert it in the first lines, not discover it mid-computation.

**Internal service calls**: Treat responses from other services as external data. Validate before use. Never assume optional fields exist. APIs change without warning — even internal ones.

### Defensive at Boundaries, Trust Internally

Related to boundary validation: put all your armor at the gates, not inside the castle.

**Validate here** (system boundaries):
- User input (HTTP requests, CLI args, form data)
- External API responses (they can change without warning)
- Internal service responses (treat as untrusted — APIs drift)
- Configuration files and environment variables
- Queue messages and event payloads
- File contents read from disk

**Trust here** (internal code):
- Function-to-function calls within the same module
- Data that already passed boundary validation
- Return values from your own functions

**Why**: Defensive programming everywhere creates noise - null checks on every line, redundant validation at every layer, try/catch around internal calls "just in case." It makes code harder to read, slower to run, and gives false confidence. Validate once at the boundary, and let the type system + tests handle the rest.

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

### Idempotency

Operations should be safe to retry. Running the same operation twice must produce the same result as running it once.

**Rules**:
- **Writes**: Use upsert/create-or-update, not blind insert. A retry after a crash shouldn't create duplicates.
- **Deletes**: Deleting something that doesn't exist is a no-op, not an error.
- **Side effects**: Guard with idempotency keys or check-before-act patterns. If the effect already happened, skip it.
- **Migrations**: Schema migrations, data backfills, and deploy scripts must be re-runnable without damage.
- **APIs**: POST endpoints that create resources should accept client-generated idempotency keys. PUT/DELETE are naturally idempotent.

**Why this matters**: Networks fail. Processes crash. Queues redeliver. Users double-click. If your operation isn't idempotent, every retry is a potential data corruption. Design for "at-least-once" delivery and you never worry about "exactly-once."

**Idempotency patterns by context**:

| Context | Pattern |
|---------|---------|
| Database writes | Upsert / ON CONFLICT DO UPDATE |
| Queue consumers | Dedup by message ID or idempotency key |
| File operations | Atomic write (temp + rename) |
| API endpoints | Client-provided idempotency key in header |
| Cron jobs / scheduled tasks | Check last-run state before executing |
| Provisioning / IaC | Declarative desired state, not imperative steps |

### State Management (DPS-3)

No implicit states. Every stateful entity must have explicitly enumerated states and guarded transitions.

**Rules**:
- **Enumerate all states**: Use enums, Literal types, or constant sets — never raw strings for state values
- **Define an explicit transition map**: Valid transitions are declared, not scattered across if/else chains. The map IS the documentation
- **Guard every transition**: Setting state must validate that the transition from current → target is legal. Invalid transitions raise explicit errors, never silently no-op
- **No orphan states**: Every state must be reachable and every state must have at least one exit (except terminal states)

```
# BAD: implicit state, no guards
order.status = "shipped"  # Was it even "paid"? Who knows.

# GOOD: explicit transitions
TRANSITIONS = {
    "pending": {"paid", "cancelled"},
    "paid": {"shipped", "refunded"},
    "shipped": {"delivered", "returned"},
    "delivered": set(),  # terminal
    "cancelled": set(),  # terminal
}

def transition(order, target):
    if target not in TRANSITIONS.get(order.status, set()):
        raise InvalidTransitionError(f"Cannot go from {order.status} to {target}")
    order.status = target
```

**Why**: Implicit state machines are the #1 source of "but how did it get into THAT state?" bugs. When transitions are explicit, invalid states are impossible and debugging is trivial — you read the map.

### Retry and Timeout (DPS-5)

All external calls must have explicit timeouts and bounded retry policies. This applies to ALL calls — not just async.

**Timeout rules**:
- **Every HTTP request** must set `timeout=` — no unbounded waits
- **Every subprocess call** must set `timeout=` — no runaway processes
- **Every database query** must have a statement timeout or connection timeout
- **Every socket operation** must call `settimeout()` or equivalent
- **Every file operation over network** (NFS, S3, etc.) must have a timeout

**Retry rules**:
- **Max attempts must be explicit** — no infinite retry loops
- **Backoff strategy required** — exponential backoff preferred, never fixed-interval hammering
- **Total timeout cap** — the sum of all retries must have an upper bound
- **No `time.sleep()` in retry loops without a cap** — unbounded backoff is a hung process
- **Retries must be idempotent** — if the operation isn't safe to retry, don't retry it

**Timeout defaults** (override per use case):
| Call Type | Default Timeout |
|-----------|----------------|
| HTTP API call | 30 seconds |
| Database query | 10 seconds |
| Subprocess | 60 seconds |
| Queue publish | 5 seconds |
| File I/O (network) | 30 seconds |

```
# BAD: unbounded wait
response = requests.get(url)

# GOOD: explicit timeout + retry
for attempt in range(3):
    try:
        response = requests.get(url, timeout=30)
        break
    except requests.Timeout:
        if attempt == 2:
            raise
        time.sleep(2 ** attempt)  # exponential backoff, capped at 3 attempts
```

### Security Standard (DPS-8)

Security is not a feature — it's a constraint on every feature.

**Rules**:
- **Parameterized queries only**: Never concatenate user input into SQL, NoSQL, LDAP, or shell commands. Use parameterized queries, prepared statements, or ORM methods
- **Principle of least privilege**: Database users, API tokens, IAM roles, file permissions — scope to the minimum required. No wildcards (`*`) unless explicitly justified in a comment
- **Rate limiting on public endpoints**: Every public-facing API must have rate limits. No exceptions
- **Secrets management**: Secrets come from environment variables or secret managers, never hardcoded, never in URLs, never in logs, never in error responses
- **Input sanitization**: Beyond validation (DPS-1), sanitize for the output context — HTML-encode for web, shell-escape for commands, parameterize for queries

### Configuration Standard (DPS-9)

Config is the boundary between your code and the environment. Treat it defensively.

**Rules**:
- **Explicit defaults for all config values**: `None` without downstream handling is a crash waiting to happen. Every config key has a documented, safe default
- **Feature flags default to OFF**: New features ship disabled. Enable explicitly after verification. A missing flag means "off", not "on"
- **Fail at startup on missing critical config**: If the service cannot function without `DATABASE_URL`, crash immediately at startup with a clear error message — don't wait until the first request hits the missing config
- **Environment variables validated at startup**: Read all env vars once, validate types and ranges, fail fast if invalid. No lazy `os.getenv()` scattered through business logic
- **Config is immutable after load**: Parse once, freeze, inject everywhere. No runtime config mutation

```
# BAD: lazy access, no default, crashes at runtime
def handle_request():
    db_url = os.getenv("DATABASE_URL")  # None if not set
    connect(db_url)  # crashes here, at request time

# GOOD: validated at startup
def load_config():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise SystemExit("FATAL: DATABASE_URL not set")
    return AppConfig(database_url=db_url)
```

### Infrastructure Requirements (DPS-10)

Infrastructure is part of defensive programming. A service without a health check is a service you can't monitor.

**Required for new services**:
- **Health check endpoint**: `/health` or `/healthz` that returns 200 when the service can process requests and 503 when it can't (e.g., database unreachable)
- **Graceful shutdown**: Handle SIGTERM/SIGINT — stop accepting new work, drain in-flight requests, close connections, exit cleanly. Never hard-kill with active transactions
- **Dead-letter queue (DLQ)**: Async message consumers must have a DLQ for messages that fail after max retries. Unprocessable messages must not block the queue
- **Concurrency limits**: Define max concurrent requests, workers, connections. No unbounded concurrency — it's a resource exhaustion vector
- **Alarms defined alongside the service**: Monitoring is not an afterthought. Service deployment includes alert definitions for error rate, latency, and DLQ depth

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

### Metrics (DPS-6)

Logs tell you *what happened*. Metrics tell you *how the system is doing*.

**Required metrics for new services/endpoints**:
- **Error rate**: Count of errors per endpoint/operation, bucketed by error code
- **Latency**: p50, p95, p99 response time per endpoint
- **Retry count**: How often retries fire — a spike means an upstream is degraded
- **Queue depth**: For async consumers — growing depth means consumers can't keep up
- **Saturation**: Connection pool usage, thread pool usage, memory — how close to limits

**Alarm thresholds** (define alongside the service, not as afterthoughts):
- Sustained error rate above baseline
- p99 latency above SLA threshold
- DLQ depth growing (messages that can't be processed)
- Health check failures

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

### Required Negative Test Categories (DPS-11)

Every new feature MUST include tests for these scenarios. Happy-path-only tests are incomplete.

| Category | What to Test |
|----------|-------------|
| **Invalid inputs** | Wrong types, empty values, too large, malformed, boundary values (0, -1, MAX_INT) |
| **Invalid state transitions** | Operation called when entity is in the wrong state |
| **Retry exhaustion** | All retries fail — does the system handle it gracefully? |
| **Timeout behavior** | External call times out — does the system surface a clear error? |
| **Duplicate processing** | Same event/request arrives twice — is the result idempotent? |
| **Partial failure** | One of N operations fails midway — does the system roll back or leave consistent state? |

Tests that only cover the happy path give false confidence. The bugs that wake you up at 3am are always in the unhappy paths.

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
- I/O or side effects in pure logic functions (functional core violation)
- Public API surface larger than necessary (internal details exposed)

**Code quality violations**:
- Files exceeding 500 lines
- Bare catch-all error handling
- Silently swallowed errors
- Missing type annotations on public APIs
- Deep nesting (>3 levels) instead of early returns
- Magic strings/numbers instead of named constants
- Dead code (commented out blocks, unused imports)
- Resource handles not using structured lifecycle (with/defer/using)
- Invalid data propagating past system boundaries (fail fast violation)
- Redundant validation deep inside internal code (defensive at wrong layer)
- Mutable data structures where immutable would suffice
- Functions mutating their arguments instead of returning new values
- Shared mutable state between threads/tasks without synchronization

**Concurrency and data integrity violations (DPS-7)**:
- Read-modify-write without optimistic locking (version field, ETag, conditional write)
- Shared mutable state between concurrent operations without synchronization
- Race-prone patterns (check-then-act without atomicity)
- Database migrations that drop columns still read by running code (must be backward compatible)
- Background/async jobs that aren't idempotent

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

**Idempotency violations (DPS-2)**:
- Blind inserts that create duplicates on retry
- Delete operations that error on missing resources
- Side effects without idempotency guards (duplicate emails, double charges)
- Migrations / scripts that break when run twice
- Queue consumers without dedup

**State management violations (DPS-3)**:
- State stored as raw strings instead of enums/Literal types
- State transitions via ad-hoc if/else without a transition map
- Setting state without validating the transition is legal
- Orphan states (unreachable or no exit path)

**Retry and timeout violations (DPS-5)**:
- HTTP/subprocess/socket calls without explicit timeout
- Retry loops without max attempt cap
- No backoff strategy (fixed-interval hammering)
- `time.sleep()` in retry loops without total timeout cap

**Security violations (DPS-8)**:
- String concatenation in SQL/NoSQL/shell commands (must use parameterized)
- Wildcard permissions without justification comment
- Missing rate limiting on public endpoints
- Secrets in URLs, logs, or error responses

**Configuration violations (DPS-9)**:
- Config values with `None` default and no null handling downstream
- Feature flags defaulting to ON (must default OFF)
- Missing config causing runtime crash instead of startup failure
- Environment variables read lazily without startup validation

**Infrastructure violations (DPS-10)**:
- New service without health check endpoint
- No graceful shutdown handling (SIGTERM/SIGINT)
- Async consumer without dead-letter queue
- No concurrency limits on parallel operations
- Monitoring/alarms missing from service deployment

**Dependency violations**:
- Lock file not committed
- Exact version pins in manifest (not lockfile)
- No CVE scanning in CI
- Dev dependencies in production bundle

---

**These standards are inherited by all language-specific skills.** Language skills add tooling, libraries, and syntax-specific rules on top.
