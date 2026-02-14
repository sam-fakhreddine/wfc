---
name: wfc-python
description: Internal Python development standards for WFC projects. Enforces Python 3.12+, black formatting, full typing, PEP 562 lazy imports, SOLID/DRY principles, three-tier architecture, 500-line file limit, and Pythonic conventions. Defines preferred libraries (python-dotenv, fire, faker, joblib, orjson, structlog, tenacity). Referenced by wfc-build, wfc-implement, wfc-test, and wfc-review. Not a user-invocable skill.
license: MIT
---

# WFC:PYTHON - Python Development Standards

Internal skill that defines how WFC builds Python projects. Referenced by other skills during implementation and review.

## Python Coding Standards

**These are non-negotiable.** Every Python file WFC produces must follow these conventions.

### Python 3.12+ Required

Target `requires-python = ">=3.12"`. Use modern features:

```python
# type statement (3.12+) - replaces TypeAlias
type Vector = list[float]
type Handler[T] = Callable[[T], Awaitable[None]]
type Result[T, E] = T | E

# Generic syntax on classes/functions (3.12+)
class Repository[T]:
    def get(self, id: str) -> T | None: ...
    def list(self, *, limit: int = 100) -> list[T]: ...

def transform[T, R](items: Iterable[T], fn: Callable[[T], R]) -> list[R]:
    return [fn(item) for item in items]

# f-string improvements (3.12+) - nested quotes, multiline
msg = f"User {user.name!r} has {len(user.roles)} roles"
query = f"""
    SELECT * FROM {table}
    WHERE status = {status!r}
"""

# ExceptionGroup + except* (3.11+)
try:
    async with TaskGroup() as tg:
        tg.create_task(fetch_users())
        tg.create_task(fetch_orders())
except* ValueError as eg:
    for exc in eg.exceptions:
        log.error("validation_failed", error=str(exc))
except* ConnectionError as eg:
    log.error("connection_failed", count=len(eg.exceptions))

# match/case (3.10+)
match response.status_code:
    case 200:
        return orjson.loads(response.content)
    case 404:
        return None
    case 429:
        raise RateLimitError(retry_after=response.headers.get("Retry-After"))
    case status if status >= 500:
        raise ServerError(status)
    case _:
        raise UnexpectedStatus(response.status_code)

# Structural pattern matching with guards
match event:
    case {"type": "click", "target": str(target)} if target.startswith("#"):
        handle_anchor(target)
    case {"type": "submit", "data": dict(data)}:
        process_form(data)
```

### Black Formatting (Non-Negotiable)

Black is the **only** formatter. No exceptions, no overrides.

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ["py312"]
```

**Rules**:
- Line length: 88 (black default)
- No `# fmt: off` / `# fmt: on` unless absolutely unavoidable
- No single-line compound statements: `if x: return` goes on two lines
- Trailing commas on multi-line collections (black enforces this)
- Double quotes for strings (black default)

### Full Type Annotations (Mandatory)

Every function signature, every return type, every class attribute. No untyped code.

```python
from collections.abc import Callable, Iterable, Sequence
from typing import Any, Self

# Function signatures - always typed
def process_batch(
    items: Sequence[dict[str, Any]],
    *,
    batch_size: int = 100,
    on_error: Callable[[Exception], None] | None = None,
) -> list[ProcessResult]:
    ...

# Class attributes - always typed
class Config:
    host: str
    port: int
    debug: bool = False
    tags: list[str] = field(default_factory=list)

# Use modern union syntax
def find_user(user_id: str) -> User | None:  # Not Optional[User]
    ...

# Use collections.abc, not typing
def merge(a: Iterable[int], b: Iterable[int]) -> list[int]:  # Not List, Iterable from typing
    ...

# Use Self for fluent interfaces (3.11+)
class Builder:
    def with_name(self, name: str) -> Self:
        self.name = name
        return self
```

**Rules**:
- `str | None` not `Optional[str]`
- `list[int]` not `List[int]`
- `dict[str, Any]` not `Dict[str, Any]`
- `collections.abc.Callable` not `typing.Callable`
- Use `Self` for methods returning own type
- Use `type` statement for type aliases (3.12+)
- Use generics syntax on classes `class Foo[T]:` (3.12+)

### PEP 562 - Module-Level `__getattr__`

Use PEP 562 for lazy imports in `__init__.py` files. Keeps import time fast.

```python
# wfc/skills/wfc-python/__init__.py pattern
__version__ = "0.1.0"

# Lightweight exports available immediately
PREFERRED_LIBRARIES = { ... }

# Heavy imports loaded on demand via PEP 562
def __getattr__(name: str) -> Any:
    if name == "PythonStandards":
        from wfc.skills.wfc_python.standards import PythonStandards
        return PythonStandards
    if name == "LibraryRegistry":
        from wfc.skills.wfc_python.registry import LibraryRegistry
        return LibraryRegistry
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__() -> list[str]:
    return [
        *__all__,
        "PythonStandards",
        "LibraryRegistry",
    ]
```

**Rules**:
- Every `__init__.py` should use PEP 562 for non-trivial imports
- Keep module-level imports to stdlib and lightweight constants
- Heavy dependencies load lazily through `__getattr__`
- Always implement `__dir__` alongside `__getattr__` for discoverability

### 500-Line File Limit (Hard Cap)

No Python file exceeds 500 lines. If it does, it needs to be split.

**How to split**:
- Extract classes into their own modules
- Group related functions into submodules
- Use `__init__.py` with PEP 562 to re-export the public API

```
# BAD: one monolithic file
utils.py (800 lines)

# GOOD: split by responsibility
utils/
├── __init__.py       # PEP 562 re-exports
├── text.py           # Text processing functions
├── dates.py          # Date/time helpers
└── validation.py     # Input validation
```

**Rules**:
- 500 lines is a hard cap, not a target - shorter is better
- If a file is approaching 300 lines, consider if it has multiple responsibilities
- Tests can be longer than 500 lines only if they cannot logically split

### Three-Tier Architecture

Separate **presentation**, **business logic**, and **data access**. Never mix tiers.

```
project/
├── api/              # PRESENTATION: HTTP handlers, CLI, serialization
│   ├── routes.py     #   Request/response handling only
│   └── schemas.py    #   Input/output shapes (Pydantic, dataclasses)
├── services/         # BUSINESS LOGIC: Rules, orchestration, workflows
│   ├── orders.py     #   OrderService: business rules
│   └── payments.py   #   PaymentService: payment workflows
├── repositories/     # DATA ACCESS: Database, APIs, file I/O
│   ├── orders.py     #   OrderRepository: queries, persistence
│   └── cache.py      #   CacheRepository: Redis/disk cache
└── models/           # DOMAIN: Pure data structures, no behavior
    └── order.py      #   Order dataclass, enums, value objects
```

**Tier rules**:

| Tier | Can Import | Cannot Import |
|------|-----------|---------------|
| Presentation | Services, Models | Repositories |
| Business Logic | Repositories, Models | Presentation |
| Data Access | Models | Presentation, Services |
| Models | stdlib only | Everything else |

```python
# GOOD: presentation calls service, service calls repository
class OrderAPI:
    def __init__(self, service: OrderService) -> None:
        self.service = service

    def create(self, request: CreateOrderRequest) -> OrderResponse:
        order = self.service.create_order(request.to_domain())
        return OrderResponse.from_domain(order)

class OrderService:
    def __init__(self, repo: OrderRepository) -> None:
        self.repo = repo

    def create_order(self, order: Order) -> Order:
        # business rules here
        return self.repo.save(order)

# BAD: API handler directly queries database
class OrderAPI:
    def create(self, request):
        db.execute("INSERT INTO orders ...")  # NO - tier violation
```

### SOLID Principles

**S - Single Responsibility**: One reason to change per class/module.
```python
# BAD: class does validation, persistence, and notification
class OrderProcessor:
    def process(self, order):
        self.validate(order)
        self.save_to_db(order)
        self.send_email(order)

# GOOD: separate responsibilities
class OrderValidator:
    def validate(self, order: Order) -> ValidationResult: ...

class OrderRepository:
    def save(self, order: Order) -> Order: ...

class OrderNotifier:
    def notify(self, order: Order) -> None: ...
```

**O - Open/Closed**: Extend via new classes, not modifying existing ones.
```python
# Use Protocol for extension points
from typing import Protocol

class Exporter(Protocol):
    def export(self, data: list[dict[str, Any]]) -> bytes: ...

class CSVExporter:
    def export(self, data: list[dict[str, Any]]) -> bytes: ...

class JSONExporter:
    def export(self, data: list[dict[str, Any]]) -> bytes: ...

# Adding PDFExporter doesn't modify existing code
```

**L - Liskov Substitution**: Subtypes must be substitutable.

**I - Interface Segregation**: Use `Protocol` with narrow interfaces.
```python
# BAD: fat interface
class Repository(Protocol):
    def get(self, id: str) -> Model: ...
    def list(self) -> list[Model]: ...
    def save(self, model: Model) -> None: ...
    def delete(self, id: str) -> None: ...
    def export(self) -> bytes: ...

# GOOD: segregated
class Readable(Protocol):
    def get(self, id: str) -> Model: ...

class Writable(Protocol):
    def save(self, model: Model) -> None: ...
```

**D - Dependency Inversion**: Depend on abstractions (Protocol), not concretions.
```python
# GOOD: constructor injection with Protocol
class OrderService:
    def __init__(
        self,
        repo: OrderRepository,     # Protocol, not concrete class
        notifier: Notifier,         # Protocol, not SmtpNotifier
    ) -> None:
        self.repo = repo
        self.notifier = notifier
```

### DRY - Don't Repeat Yourself

- Extract repeated logic into functions when used 3+ times
- Use base classes or mixins for shared behavior across classes
- Shared constants go in a `constants.py` or the relevant module
- But: don't create premature abstractions for 1-2 uses

### Pythonic Conventions

```python
# Comprehensions over manual loops for transforms
squares = [x**2 for x in numbers if x > 0]
lookup = {item.id: item for item in items}

# Context managers for resource management
with open(path) as f:
    data = f.read()

# Unpacking
first, *rest = items
x, y = point

# Walrus operator for compute-and-check
if (match := pattern.search(text)) is not None:
    process(match.group(1))

# Enumerate, zip - never manual indexing
for i, item in enumerate(items):
    ...
for key, value in zip(keys, values, strict=True):
    ...

# EAFP over LBYL
try:
    value = mapping[key]
except KeyError:
    value = default

# Dataclasses for data containers (not plain dicts)
@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float

# slots=True for performance (3.10+)
# frozen=True for immutability when appropriate
# kw_only=True to prevent positional arg mistakes (3.10+)

# Use pathlib, not os.path
from pathlib import Path
config_path = Path.home() / ".config" / "app" / "settings.json"

# Use enum for fixed sets of values
from enum import StrEnum  # 3.11+

class Status(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    ARCHIVED = "archived"
```

### Elegance Rules

- Simplest solution that works. No cleverness for its own sake.
- If a stdlib solution exists, use it before reaching for a library
- Flat is better than nested - max 3 levels of indentation
- Early returns over deep nesting
- Explicit is better than implicit - no magic

```python
# BAD: clever but unreadable
result = (lambda f: (lambda x: x(x))(lambda y: f(lambda *a: y(y)(*a))))(func)

# GOOD: clear and direct
result = func(input_data)

# BAD: deep nesting
def process(data):
    if data:
        if data.valid:
            if data.ready:
                return transform(data)
            else:
                return None
        else:
            return None
    else:
        return None

# GOOD: early returns
def process(data: Data | None) -> Result | None:
    if not data or not data.valid or not data.ready:
        return None
    return transform(data)
```

## Preferred Libraries

These are the **standard libraries** for all WFC Python projects. Use them by default unless the project has specific constraints.

### 1. python-dotenv - Configuration Management

**What**: Load environment variables from `.env` files.

**When to use**: Every project that needs configuration (API keys, database URLs, feature flags).

**Pattern**:
```python
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
API_KEY = os.getenv("API_KEY")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
```

**Rules**:
- Always call `load_dotenv()` early in the entry point
- Always provide sensible defaults for non-secret values
- Never commit `.env` files - commit `.env.example` with placeholder values
- Use `python-dotenv` over manual `os.environ` parsing

### 2. fire - CLI Generation

**What**: Automatically generate CLIs from Python functions and classes.

**When to use**: Any script or tool that needs a command-line interface.

**Pattern**:
```python
import fire

def process(input_file: str, output_file: str = "out.json", verbose: bool = False):
    """Process input file and write results."""
    ...

if __name__ == "__main__":
    fire.Fire(process)
```

**Class-based CLI**:
```python
import fire

class Pipeline:
    def train(self, data: str, epochs: int = 10):
        """Train the model."""
        ...

    def predict(self, model: str, input: str):
        """Run predictions."""
        ...

if __name__ == "__main__":
    fire.Fire(Pipeline)
```

**Rules**:
- Prefer `fire` over `argparse` or `click` for internal tools
- Use type hints on function signatures - fire uses them
- Add docstrings - fire uses them for `--help`
- Use class-based CLI for multi-command tools

### 3. faker - Test Data Generation

**What**: Generate realistic fake data for tests and development.

**When to use**: Tests, seed scripts, development fixtures, demos.

**Pattern**:
```python
from faker import Faker

fake = Faker()

# Generate test data
user = {
    "name": fake.name(),
    "email": fake.email(),
    "address": fake.address(),
    "created_at": fake.date_time_this_year().isoformat(),
}

# Reproducible data for tests
Faker.seed(42)
fake = Faker()
consistent_name = fake.name()  # Same every run
```

**Rules**:
- Always seed Faker in tests for reproducibility (`Faker.seed(42)`)
- Use locale-specific fakers when relevant: `Faker("fr_FR")`
- Prefer Faker over hand-written test data for realistic edge cases
- Use `fake.unique.email()` when uniqueness matters

### 4. joblib - Parallel Execution & Caching

**What**: Simple parallelism and transparent disk-caching for expensive computations.

**When to use**: CPU-bound work, batch processing, caching expensive function results.

**Parallel pattern**:
```python
from joblib import Parallel, delayed

def process_item(item):
    # expensive computation
    return result

results = Parallel(n_jobs=-1)(
    delayed(process_item)(item) for item in items
)
```

**Caching pattern**:
```python
from joblib import Memory

memory = Memory(".cache", verbose=0)

@memory.cache
def expensive_computation(data):
    # only runs once per unique input
    return result
```

**Rules**:
- Use `n_jobs=-1` to use all cores, `n_jobs=-2` to leave one free
- Use `Parallel` over `multiprocessing.Pool` for simple cases
- Cache directory (`.cache/`) should be in `.gitignore`
- Use `backend="threading"` for I/O-bound work, default `"loky"` for CPU-bound
- Add `verbose=10` during development to see progress

### 5. orjson - Fast JSON

**What**: Fast, correct JSON library (10-50x faster than stdlib `json`).

**When to use**: Any JSON serialization/deserialization, especially with large payloads or high throughput.

**Pattern**:
```python
import orjson

# Serialize (returns bytes)
data = {"key": "value", "count": 42}
json_bytes = orjson.dumps(data, option=orjson.OPT_INDENT_2)

# Deserialize
parsed = orjson.loads(json_bytes)

# Handles datetime, dataclass, numpy natively
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Event:
    name: str
    timestamp: datetime

event = Event(name="deploy", timestamp=datetime.now())
orjson.dumps(event)  # Just works
```

**Rules**:
- Use `orjson` over stdlib `json` in all WFC Python code
- `orjson.dumps()` returns `bytes`, not `str` - use `.decode()` when string is needed
- Use `orjson.OPT_INDENT_2` for human-readable output
- Use `orjson.OPT_SORT_KEYS` when deterministic output matters
- Leverage native datetime/dataclass serialization instead of custom encoders

### 6. structlog - Structured Logging

**What**: Structured, key-value logging that produces machine-readable logs.

**When to use**: All logging in WFC Python projects.

**Pattern**:
```python
import structlog

log = structlog.get_logger()

# Structured key-value logging
log.info("processing_started", file="data.csv", records=1000)
log.warning("slow_query", query="SELECT ...", duration_ms=450)
log.error("connection_failed", host="db.example.com", retries=3)

# Bind context for request lifecycle
logger = log.bind(request_id="abc-123", user_id=42)
logger.info("request_received")
logger.info("request_completed", status=200)
```

**Configuration**:
```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),  # Dev: colored output
        # Production: use structlog.processors.JSONRenderer()
    ],
)
```

**Rules**:
- Use `structlog` over stdlib `logging` or `print()` statements
- Always log key-value pairs, not formatted strings: `log.info("event", key=value)` not `log.info(f"event: {value}")`
- Use `bind()` to carry context (request_id, user_id) through call chains
- Use `ConsoleRenderer` in development, `JSONRenderer` in production
- Never log secrets or PII

### 7. tenacity - Retry Logic

**What**: General-purpose retry library with flexible backoff strategies.

**When to use**: API calls, network requests, database connections, any operation that can transiently fail.

**Pattern**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
)
def call_api(url: str) -> dict:
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
```

**With logging**:
```python
from tenacity import retry, before_sleep_log, stop_after_attempt, wait_exponential
import structlog

log = structlog.get_logger()

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    before_sleep=before_sleep_log(log, structlog.stdlib.INFO),
)
def resilient_operation():
    ...
```

**Rules**:
- Use `tenacity` over hand-rolled retry loops
- Always set `stop_after_attempt` - never retry forever
- Use exponential backoff for network calls (`wait_exponential`)
- Be specific about which exceptions to retry (`retry_if_exception_type`)
- Combine with `structlog` for retry visibility

## Library Combinations

These libraries work together. Use these patterns when combining them.

### CLI Tool with Config + Logging

```python
from dotenv import load_dotenv
import fire
import structlog
import os

load_dotenv()
log = structlog.get_logger()

def run(input_file: str, workers: int = 4):
    """Process data with parallel workers."""
    api_key = os.getenv("API_KEY")
    log.info("starting", input=input_file, workers=workers)
    ...

if __name__ == "__main__":
    fire.Fire(run)
```

### Resilient API Client

```python
import orjson
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

log = structlog.get_logger()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def fetch_data(url: str) -> dict:
    log.info("fetching", url=url)
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    return orjson.loads(resp.content)
```

### Parallel Processing with Caching

```python
from joblib import Parallel, delayed, Memory
import structlog

log = structlog.get_logger()
memory = Memory(".cache", verbose=0)

@memory.cache
def expensive_step(item):
    return process(item)

def run_pipeline(items):
    log.info("pipeline_start", count=len(items))
    results = Parallel(n_jobs=-1)(
        delayed(expensive_step)(item) for item in items
    )
    log.info("pipeline_done", results=len(results))
    return results
```

## pyproject.toml Dependencies

When scaffolding a new Python project, include these in `pyproject.toml`:

```toml
[project]
dependencies = [
    "python-dotenv>=1.0",
    "orjson>=3.9",
    "structlog>=24.1",
    "tenacity>=8.2",
]

[project.optional-dependencies]
cli = [
    "fire>=0.5",
]
dev = [
    "faker>=22.0",
    "pytest>=8.0",
    "pytest-cov>=4.1",
]
all = [
    "fire>=0.5",
    "faker>=22.0",
    "pytest>=8.0",
    "pytest-cov>=4.1",
]
```

**Grouping rationale**:
- **Core** (always installed): dotenv, orjson, structlog, tenacity
- **cli** (optional): fire - only needed if project has CLI entry points
- **dev** (optional): faker, pytest - only needed during development/testing

## Integration with WFC Skills

### wfc-build / wfc-implement

When building Python features:
1. Scaffold with these libraries in the dependency list
2. Use `structlog` for all logging (not print/logging)
3. Use `orjson` for JSON operations (not stdlib json)
4. Use `tenacity` for any network/external calls
5. Use `python-dotenv` for configuration
6. Use `fire` for CLI entry points
7. Use `faker` for test data generation

### wfc-test

When generating tests for Python code:
1. Use `faker` with `Faker.seed(42)` for reproducible test data
2. Use `joblib.Parallel` for parallel test execution when appropriate

### wfc-review

When reviewing Python code, flag:

**Library violations**:
- `print()` statements that should use `structlog`
- `import json` that should use `orjson`
- Hand-rolled retry loops that should use `tenacity`
- Hardcoded config that should use `python-dotenv`
- `argparse` boilerplate that could be replaced with `fire`
- Hand-written test fixtures that could use `faker`
- Sequential loops that could use `joblib.Parallel`

**Coding standard violations**:
- Missing type annotations on any function/method
- Files exceeding 500 lines
- `Optional[X]` instead of `X | None`
- `typing.List`, `typing.Dict` instead of `list`, `dict`
- `TypeAlias` instead of `type` statement (3.12+)
- Tier violations (presentation importing data access directly)
- Classes with multiple responsibilities (SRP violation)
- Deep nesting (>3 levels) instead of early returns
- `os.path` instead of `pathlib.Path`
- Magic strings instead of `StrEnum`
- Missing `slots=True` on dataclasses
- `# fmt: off` without justification
- Non-black-formatted code

## Python Runtime Rules

These rules apply to all WFC Python projects:

- **Always** use `uv` for Python operations (`uv run`, `uv pip install`)
- **Never** use bare `python`, `pip`, or `python -m`
- **Always** use `pytest` as the test framework
- **Always** use `black` for formatting (line-length 88, target py312)
- **Always** use `ruff` for linting
- **Always** target Python 3.12+ (`requires-python = ">=3.12"`)
- **Always** use full type annotations on all signatures
- **Always** use PEP 562 (`__getattr__` / `__dir__`) in `__init__.py`
- **Always** follow three-tier architecture (presentation / logic / data)
- **Always** apply SOLID principles (especially SRP and DI via Protocol)
- **Never** exceed 500 lines per file
- **Never** use `Optional`, `List`, `Dict`, `Tuple` from `typing` (use builtins)
- **Never** skip type annotations on public functions

---

**This is World Fucking Class Python.**
