---
applyTo: "**/*.py"
---
# Python Review Rules — Defensive Programming Standard

## Critical (Block Merge)

### Security (DPS-8)

- `eval()`, `exec()`, `os.system()`, `pickle.loads()` — flag as arbitrary code execution risk
- `subprocess.run(..., shell=True)` or `subprocess.call(..., shell=True)` — flag command injection
- SQL string concatenation (`f"SELECT ... {user_input}"`) — must use parameterized queries
- Hardcoded secrets: `API_KEY = "sk-..."`, `PASSWORD = "..."` — must use env vars or secret manager
- Wildcard permissions or `*` in access control without explicit justification comment

### Silent Failures (DPS-4)

- Bare `except:` or `except Exception:` without re-raise or structured error — flag silent failure
- `except SomeError: pass` — swallowed error, must at minimum log with correlationId
- Functions that return `None` on error instead of raising — flag ambiguous failure path
- Test functions that use `return True/False` instead of `assert` — tests will silently pass
- Raw stack traces in API responses — must return structured error (code + message + correlationId)
- `logging.error("something went wrong")` — error messages must be specific and include context

### Data Integrity (DPS-7)

- `dict.copy()` on nested config dicts — must use `copy.deepcopy()` for nested structures
- Mutable default arguments (`def f(items=[])`) — shared state bug across calls
- Read-modify-write on shared state without lock or conditional check — race condition
- `Path.home()` at class/module level — fires at import time, untestable. Use `@staticmethod` or lazy eval
- `signal.SIGALRM` without platform guard — Unix-only, breaks on Windows

### Boundary Validation (DPS-1)

- External data (API params, file contents, webhook payloads) used without validation — must validate before use
- `payload["key"]` on external input — must use `payload.get("key", default)` safe access pattern
- Missing type/range checks on numeric inputs (negative values, overflow, zero-division)
- Business logic executing before input validation — validation must come first

## Important (Warn)

### Idempotency (DPS-2)

- Mutating operations (POST handlers, event processors, write functions) without idempotency check
- Side effects (sending email, webhook, state change) before verifying operation hasn't already been processed
- Database writes using INSERT without ON CONFLICT or upsert pattern

### State Management (DPS-3)

- State stored as raw strings instead of enum/Literal — must use enumerated states
- State transitions via if/else chains without a transition map — must define valid transitions explicitly
- Setting state without checking current state — must validate transition is legal

### Retry and Timeout (DPS-5)

- `requests.get()`, `urllib`, `httpx` calls without `timeout=` parameter — flag unbounded wait
- `subprocess.run()` without `timeout=` — flag unbounded process wait
- Retry loops without max attempt cap — flag infinite retry risk
- `time.sleep()` in retry loops without total timeout cap — flag unbounded backoff
- `socket` operations without `settimeout()` — flag blocking socket

### Observability (DPS-6)

- `print()` for logging in production code — must use `logging` module with structured format
- `logger.info(f"User {user_id} did {action}")` — use lazy formatting: `logger.info("User %s did %s", user_id, action)`
- Log statements that include passwords, tokens, API keys, or full request bodies — flag secret leak
- Error handlers that don't log the exception — silent swallow

### Configuration (DPS-9)

- `os.getenv("KEY")` without default value or startup validation — flag missing-config-at-runtime risk
- Config values defaulting to `None` without null handling downstream — must have explicit safe default
- Feature flags defaulting to `True`/enabled — must default OFF

### WFC-Specific

- Bare `python`, `pip`, `pytest` in any string that looks like a command — must use `uv run` prefix
- `warnings.warn()` at module level — fires on any import. Put in `__init__()` or a function
- `from wfc.skills.wfc_implement.submodule import X` — PEP 562 bridge requires two-step import
- Missing `check=False` on `subprocess.run()` calls that handle their own error

## Style (Inform Only)

- Prefer `pathlib.Path` over `os.path` for new code
- Prefer `dataclass` or `TypedDict` over raw dicts for structured data with known keys
- Prefer `enum.Enum` or `typing.Literal` for fixed sets of values (DPS-3)
- Test files should use `pytest` fixtures, not `setUp`/`tearDown` (unless extending `unittest.TestCase`)

## Test-Specific Rules (DPS-11)

- Every test function MUST contain at least one `assert` — `return` is not an assertion
- Test names should describe behavior: `test_rejects_empty_input` not `test_validate`
- Mock boundaries: mock external I/O (network, disk, subprocess), never mock the unit under test
- `monkeypatch.chdir(tmp_path)` for functions that use relative paths like `Path(".git/hooks")`
- Parametrized tests preferred over copy-paste variants
- Required negative test cases for new features:
  - Invalid inputs (wrong type, empty, too large, malformed)
  - Invalid state transitions (operation in wrong state)
  - Timeout behavior (external call times out)
  - Retry exhaustion (all retries fail)
  - Duplicate processing (same event twice)
  - Partial failure (one of N steps fails midway)
