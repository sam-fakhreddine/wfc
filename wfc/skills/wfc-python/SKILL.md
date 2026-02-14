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

Black is the **only** formatter. No exceptions, no overrides. PEP 8 is enforced via
ruff, but **black wins** on any style conflict. Ruff must ignore the rules that black
owns (line length, indentation, whitespace in expressions).

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ["py312"]
```

**Black / PEP 8 sync** - ruff must ignore rules that black controls:

```toml
[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM", "TCH"]
# Rules that conflict with black - black is authoritative on these:
#   E111 - indentation (black owns this)
#   E114 - indentation of comment (black owns this)
#   E117 - over-indented (black owns this)
#   E501 - line too long (black wraps at 88, ruff must not second-guess)
#   W191 - indentation contains tabs (black uses spaces, but owns decision)
#   E203 - whitespace before ':' (black intentionally does `x[1 : 2]`)
ignore = ["E111", "E114", "E117", "E501", "W191", "E203"]
```

**Run order**: `black` first (formats), then `ruff check` (lints the result). Never
run ruff's formatter (`ruff format`) - we use black exclusively.

**Rules**:
- Line length: 88 (black default) - ruff defers to black via E501 ignore
- No `# fmt: off` / `# fmt: on` unless absolutely unavoidable
- No single-line compound statements: `if x: return` goes on two lines
- Trailing commas on multi-line collections (black enforces this)
- Double quotes for strings (black default)
- PEP 8 compliance via ruff's `E` + `W` rules, minus the black-owned subset above

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

### Error Handling

Structured, intentional error handling. No silent failures, no bare excepts.

```python
# Custom exception hierarchy per domain
class AppError(Exception):
    """Base for all application errors."""

class ValidationError(AppError):
    """Input validation failed."""
    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class NotFoundError(AppError):
    """Resource not found."""
    def __init__(self, resource: str, identifier: str) -> None:
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} not found: {identifier}")

class ExternalServiceError(AppError):
    """External dependency failed."""
```

**Rules**:
- Never bare `except:` or `except Exception:` without re-raise or structured logging
- Define a project-level exception hierarchy rooted in one base class
- Exceptions carry structured context (fields, not just strings)
- Log errors with structlog context, then raise or handle - never silently swallow
- Use `ExceptionGroup` + `except*` for concurrent error handling (3.11+)

```python
# BAD: swallowing errors
try:
    result = api_call()
except Exception:
    pass  # NO - silent failure

# BAD: bare except
try:
    result = api_call()
except:  # NO - catches SystemExit, KeyboardInterrupt
    pass

# GOOD: specific, logged, structured
try:
    result = api_call()
except httpx.TimeoutException as exc:
    log.error("api_timeout", url=url, timeout=timeout)
    raise ExternalServiceError("API timed out") from exc
```

### Composition Over Inheritance

Prefer composition and Protocol over deep inheritance trees.

```python
# BAD: inheritance for code reuse
class BaseProcessor:
    def validate(self): ...
    def transform(self): ...
    def save(self): ...

class OrderProcessor(BaseProcessor):
    def process(self):
        self.validate()
        self.transform()
        self.save()

# GOOD: composition with injected collaborators
@dataclass(slots=True)
class OrderProcessor:
    validator: Validator
    transformer: Transformer
    repo: Repository

    def process(self, order: Order) -> Order:
        self.validator.validate(order)
        transformed = self.transformer.transform(order)
        return self.repo.save(transformed)
```

**Rules**:
- Max 1 level of inheritance (concrete class extends at most one base)
- Use Protocol for polymorphism, not ABC (unless you need `__init_subclass__`)
- Use dataclass composition to assemble behavior from parts
- Mixins only when composition is genuinely awkward (rare)

### Factory Patterns

Use factories when object construction is non-trivial, conditional, or involves
registries. Factories centralize creation logic so callers don't need to know
concrete types.

```python
from typing import Protocol
from dataclasses import dataclass

# Protocol for the product
class Notifier(Protocol):
    def send(self, message: str, recipient: str) -> None: ...

# Concrete implementations
@dataclass(slots=True)
class EmailNotifier:
    smtp_host: str

    def send(self, message: str, recipient: str) -> None:
        ...  # send via SMTP

@dataclass(slots=True)
class SlackNotifier:
    webhook_url: str

    def send(self, message: str, recipient: str) -> None:
        ...  # post to Slack webhook

# Factory function - simplest form, use when creation logic is a single branch
def create_notifier(channel: str, **kwargs: str) -> Notifier:
    match channel:
        case "email":
            return EmailNotifier(smtp_host=kwargs["smtp_host"])
        case "slack":
            return SlackNotifier(webhook_url=kwargs["webhook_url"])
        case _:
            raise ValueError(f"Unknown notification channel: {channel}")

# Registry-based factory - use when third parties register implementations
_REGISTRY: dict[str, type[Notifier]] = {}

def register_notifier(name: str, cls: type[Notifier]) -> None:
    _REGISTRY[name] = cls

def get_notifier(name: str, **kwargs: str) -> Notifier:
    if name not in _REGISTRY:
        raise KeyError(f"No notifier registered for {name!r}")
    return _REGISTRY[name](**kwargs)

# Usage - callers never import concrete classes
notifier = create_notifier("email", smtp_host="mail.example.com")
notifier.send("Hello", "user@example.com")
```

**When to use factories**:
- Object creation depends on runtime config or environment (e.g. "email" vs "slack")
- Multiple implementations behind a Protocol - callers shouldn't pick the concrete class
- Construction requires validation, defaults, or multi-step setup
- Plugin/registry systems where implementations are registered dynamically

**When NOT to use factories**:
- Single implementation - just instantiate directly
- Dataclass with straightforward fields - no factory needed
- Only 1-2 callers - a factory adds indirection for no benefit

### Context Managers & Dunder Methods

Implement proper resource management and Pythonic interfaces.

```python
from contextlib import contextmanager, asynccontextmanager

# Context manager for resource lifecycle
@contextmanager
def db_transaction(conn: Connection) -> Iterator[Transaction]:
    tx = conn.begin()
    try:
        yield tx
        tx.commit()
    except Exception:
        tx.rollback()
        raise

# Async context manager
@asynccontextmanager
async def http_session() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(timeout=30) as client:
        yield client

# Meaningful dunder methods on domain objects
@dataclass(frozen=True, slots=True)
class Money:
    amount: int  # cents
    currency: str = "USD"

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __str__(self) -> str:
        return f"${self.amount / 100:.2f} {self.currency}"

    def __bool__(self) -> bool:
        return self.amount != 0
```

**Atomic Writes** - never leave files in a half-written state:
```python
import os
import tempfile
from pathlib import Path

def atomic_write(path: Path, content: str | bytes, encoding: str = "utf-8") -> None:
    """Write to a file atomically via temp file + rename.

    If the process crashes mid-write, the original file remains intact.
    Works on the same filesystem (os.replace is atomic on POSIX).
    """
    mode = "wb" if isinstance(content, bytes) else "w"
    # Write to temp file in the same directory (same filesystem = atomic rename)
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with open(fd, mode, encoding=encoding if mode == "w" else None) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())  # ensure data hits disk
        os.replace(tmp_path, path)  # atomic on POSIX
    except BaseException:
        # Clean up temp file on any failure
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise
```

**When to use atomic writes**:
- Config files, state files, lockfiles - anything where corruption = broken system
- Any file that other processes may read concurrently
- Files written from background threads or async tasks

**When NOT needed**:
- Temporary/scratch files that are disposable
- Append-only logs (use `open(path, "a")` with line buffering instead)

**Rules**:
- Always use context managers for resources (files, connections, locks, transactions)
- **Atomic writes**: Use write-to-temp + `os.replace` for any file that must not be left half-written
- Prefer `contextlib.contextmanager` over writing `__enter__`/`__exit__` manually
- Implement `__repr__` on all domain objects (dataclass gives this free)
- Implement `__str__` when human-readable output matters
- Implement `__eq__` and `__hash__` via `frozen=True` dataclass, not manually

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

**Centralized Configuration** - configure once at application startup, never per-module:
```python
# app/logging.py - single source of truth for all logging config
import logging
import threading

import structlog


def setup_logging(*, json_output: bool = False, level: str = "INFO") -> None:
    """Call exactly once at application startup (main, FastAPI lifespan, etc.)."""

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_thread_info,  # always identify which thread is logging
    ]

    if json_output:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()  # type: ignore[assignment]

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping()[level],
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _add_thread_info(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Inject thread name and ID into every log line."""
    t = threading.current_thread()
    event_dict["thread_name"] = t.name
    event_dict["thread_id"] = t.ident
    return event_dict
```

**Usage in any module** - import structlog, never configure it:
```python
# services/order.py
import structlog

log = structlog.get_logger()

def process_order(order_id: str) -> None:
    log.info("processing_order", order_id=order_id)
    # Output includes thread_name="MainThread" thread_id=140234... automatically
```

**Thread-aware logging output** - every log line identifies its thread:
```
2025-01-15T09:30:01Z [info] processing_order  order_id=abc-123  thread_name=Worker-3  thread_id=140234567890
2025-01-15T09:30:01Z [info] db_query_complete  table=orders  ms=12  thread_name=Worker-3  thread_id=140234567890
2025-01-15T09:30:02Z [info] processing_order  order_id=def-456  thread_name=Worker-7  thread_id=140234567891
```

**Rules**:
- **Centralized config**: Call `setup_logging()` exactly once at app entry point - never in library code, never per-module
- Use `structlog` over stdlib `logging` or `print()` statements
- Always log key-value pairs, not formatted strings: `log.info("event", key=value)` not `log.info(f"event: {value}")`
- Use `bind()` to carry context (request_id, user_id) through call chains
- **Thread identification**: Always include the `_add_thread_info` processor - when multithreaded, you must know which thread produced each log line
- Use `contextvars` (not thread-locals) to propagate context across async tasks and threads
- Use `ConsoleRenderer` in development, `JSONRenderer` in production
- Never log secrets or PII
- Never call `structlog.configure()` from library/module code - only from the app entry point

**Async context propagation** - bind once in middleware, available everywhere:
```python
import structlog
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_request_id: ContextVar[str] = ContextVar("request_id", default="")

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            return await call_next(request)
        finally:
            structlog.contextvars.unbind_contextvars("request_id")
```

**Error logging** - always include the exception chain:
```python
log = structlog.get_logger()

try:
    result = await process_order(order_id)
except PaymentError as exc:
    # Log the error with structured context + exception info
    log.error(
        "order_payment_failed",
        order_id=order_id,
        error_type=type(exc).__name__,
        error_msg=str(exc),
        exc_info=True,  # includes full traceback in output
    )
    raise
```

**Banned patterns** (CI must fail):
```python
# FORBIDDEN - print() for any purpose other than CLI user output
print(f"Processing order {order_id}")  # BAD

# FORBIDDEN - f-strings in log calls break aggregation
log.info(f"Order {order_id} completed")  # BAD

# FORBIDDEN - stdlib logging
import logging  # BAD (in application code)
logging.info("something happened")  # BAD

# CORRECT - structured key-value pairs
log.info("order_completed", order_id=order_id)  # GOOD
```

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

## Preferred Frameworks

Beyond the 7 core libraries, these are the standard frameworks for specific domains.

### Pydantic - Data Validation & Settings

**The** validation library. Use for API schemas, config, and any external data boundary.

```python
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

# API request/response schemas
class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(pattern=r"^[\w.-]+@[\w.-]+\.\w+$")
    age: int = Field(ge=0, le=150)

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be blank")
        return v.strip()

# Settings from environment (replaces python-dotenv for typed config)
class Settings(BaseSettings):
    database_url: str
    api_key: str
    debug: bool = False
    workers: int = 4

    model_config = {"env_file": ".env"}

settings = Settings()  # Reads from env + .env file, fully typed
```

**Rules**:
- Use Pydantic models at **system boundaries** (API input, config, external data)
- Use `pydantic-settings` for typed config (upgrades python-dotenv pattern)
- Use plain dataclasses for internal domain objects (lighter weight)
- Never pass raw dicts across module boundaries - validate into Pydantic models first

### httpx - HTTP Client

**The** HTTP client. Async-first, sync-compatible, replaces `requests`.

```python
import httpx
import orjson

# Sync
response = httpx.get("https://api.example.com/data", timeout=10)
data = orjson.loads(response.content)

# Async
async with httpx.AsyncClient(timeout=30) as client:
    response = await client.get("https://api.example.com/data")
    data = orjson.loads(response.content)

# With tenacity retry
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
async def fetch(client: httpx.AsyncClient, url: str) -> dict:
    resp = await client.get(url)
    resp.raise_for_status()
    return orjson.loads(resp.content)
```

**Rules**:
- Use `httpx` over `requests` (async support, HTTP/2, modern API)
- Always set explicit `timeout` - never use default infinite timeout
- Use `AsyncClient` as context manager for connection pooling
- Parse responses with `orjson.loads(resp.content)` not `resp.json()`

### FastAPI - Web APIs

**The** API framework when building web services.

```python
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel

app = FastAPI()

# Dependency injection (aligns with SOLID DI principle)
async def get_db() -> AsyncIterator[Database]:
    async with Database() as db:
        yield db

class UserResponse(BaseModel):
    id: str
    name: str
    email: str

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Database = Depends(get_db),
) -> UserResponse:
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return UserResponse.model_validate(user)
```

**Rules**:
- Use FastAPI for any HTTP API project (not Flask, not Django REST)
- Use Pydantic models for request/response schemas
- Use `Depends()` for dependency injection (maps to SOLID DI)
- Keep route handlers thin - delegate to service layer (three-tier)
- Use async handlers with `httpx.AsyncClient` for downstream calls

## Async & Concurrency

Use `asyncio` with `TaskGroup` for concurrent I/O. Use `joblib` for CPU-bound parallelism.

### When to Use Async

| Workload | Use | Why |
|----------|-----|-----|
| HTTP calls to external APIs | `async` + `httpx.AsyncClient` | I/O-bound, concurrent requests |
| Database queries | `async` + async driver | I/O-bound, connection pooling |
| File I/O (many files) | `async` + `aiofiles` | I/O-bound, parallel reads |
| CPU-heavy computation | `joblib.Parallel` (sync) | CPU-bound, multiprocess |
| Simple scripts | sync | Not worth async overhead |

### TaskGroup Pattern (3.11+)

```python
import asyncio
import httpx
import structlog

log = structlog.get_logger()

async def fetch_all(urls: list[str]) -> list[dict]:
    """Fetch multiple URLs concurrently with structured error handling."""
    results: list[dict] = []

    async with httpx.AsyncClient(timeout=30) as client:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(client.get(url)) for url in urls]

    for task in tasks:
        resp = task.result()
        results.append(orjson.loads(resp.content))

    return results

# With error handling via except*
async def fetch_resilient(urls: list[str]) -> list[dict | None]:
    results: dict[str, dict | None] = {url: None for url in urls}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            async with asyncio.TaskGroup() as tg:
                for url in urls:
                    tg.create_task(_fetch_one(client, url, results))
    except* httpx.HTTPStatusError as eg:
        for exc in eg.exceptions:
            log.warning("fetch_failed", url=str(exc.request.url), status=exc.response.status_code)
    except* httpx.ConnectError as eg:
        log.error("connection_failures", count=len(eg.exceptions))

    return list(results.values())

async def _fetch_one(
    client: httpx.AsyncClient,
    url: str,
    results: dict[str, dict | None],
) -> None:
    resp = await client.get(url)
    resp.raise_for_status()
    results[url] = orjson.loads(resp.content)
```

### Async Context Managers

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

@asynccontextmanager
async def managed_client(
    base_url: str,
    timeout: int = 30,
) -> AsyncIterator[httpx.AsyncClient]:
    """Reusable async HTTP client with structured logging."""
    log.info("client_open", base_url=base_url)
    async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
        yield client
    log.info("client_closed", base_url=base_url)

# FastAPI lifespan (replaces @app.on_event)
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    log.info("app_starting")
    app.state.http_client = httpx.AsyncClient(timeout=30)
    yield
    # Shutdown
    await app.state.http_client.aclose()
    log.info("app_stopped")

app = FastAPI(lifespan=lifespan)
```

### Async Safety (Blocking I/O Footguns)

The event loop must never be blocked. A single blocking call stalls every concurrent task.

**Forbidden in `async def`**:
```python
# BAD: blocks the entire event loop
async def bad_fetch():
    import requests                          # FORBIDDEN in async
    return requests.get("https://api.com")   # blocks everything

async def bad_sleep():
    import time
    time.sleep(5)                            # FORBIDDEN - use asyncio.sleep

async def bad_file_read():
    with open("big.csv") as f:               # FORBIDDEN for large files
        return f.read()
```

**Correct patterns**:
```python
import asyncio
import httpx
import aiofiles
import structlog

log = structlog.get_logger()

# Non-blocking HTTP
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        return resp.json()

# Non-blocking sleep
async def poll_until_ready(check: Callable[[], bool]) -> None:
    while not check():
        await asyncio.sleep(1)  # yields to event loop

# Non-blocking file I/O (large files)
async def read_large_file(path: Path) -> str:
    async with aiofiles.open(path) as f:
        return await f.read()

# Wrapping blocking/CPU-bound code with asyncio.to_thread
async def hash_password(password: str) -> str:
    """CPU-bound bcrypt must not block the event loop."""
    return await asyncio.to_thread(bcrypt.hashpw, password.encode(), bcrypt.gensalt())

async def call_legacy_sdk(params: dict) -> dict:
    """Legacy SDK is sync-only - run in thread pool."""
    return await asyncio.to_thread(legacy_sdk.execute, params)
```

**Timeout handling**:
```python
# Use asyncio.timeout (3.11+) for deadline enforcement
async def fetch_with_deadline(url: str) -> dict:
    async with asyncio.timeout(10):  # 10 second hard deadline
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            return resp.json()

# Catch timeout at the caller
try:
    data = await fetch_with_deadline("https://slow-api.com")
except TimeoutError:
    log.warning("fetch_timed_out", url="https://slow-api.com")
```

**Cancellation safety**:
```python
# NEVER swallow CancelledError - always re-raise
async def managed_task() -> None:
    try:
        await do_work()
    except asyncio.CancelledError:
        await cleanup()  # release resources
        raise            # MUST re-raise - swallowing breaks TaskGroup
```

**Async safety rules**:
- **Never use `requests`** in async code - use `httpx.AsyncClient`
- **Never use `time.sleep()`** in async - use `asyncio.sleep()`
- **Never use `open()` for large files** in async - use `aiofiles`
- **Use `asyncio.to_thread()`** for blocking/CPU-bound calls in async context
- **Use `asyncio.timeout()`** (3.11+) for deadlines, not `asyncio.wait_for`
- **Never catch `CancelledError`** without re-raising - it breaks structured concurrency
- **Small files** (< 1MB): `open()` is fine in async - the overhead of aiofiles isn't worth it

### Thread Safety

When using threads (joblib, `threading`, `concurrent.futures`), protect shared state
and always identify which thread is doing what.

```python
import threading
from collections.abc import Iterator
from contextlib import contextmanager

import structlog

log = structlog.get_logger()

# Use threading.Lock for shared mutable state
class SafeCounter:
    """Thread-safe counter. Lock protects _value from data races."""

    __slots__ = ("_value", "_lock")

    def __init__(self) -> None:
        self._value = 0
        self._lock = threading.Lock()

    def increment(self) -> int:
        with self._lock:
            self._value += 1
            return self._value

    @property
    def value(self) -> int:
        with self._lock:
            return self._value


# Thread-safe file writing - combine atomic writes + lock
_write_lock = threading.Lock()

def threadsafe_write(path: Path, content: str) -> None:
    """Atomic write guarded by a lock so concurrent threads don't clobber."""
    with _write_lock:
        atomic_write(path, content)
    log.info("file_written", path=str(path))
    # Log automatically includes thread_name + thread_id from centralized config


# Name your threads - makes logs and debuggers useful
def run_workers(tasks: list[Callable[[], None]]) -> None:
    threads: list[threading.Thread] = []
    for i, task in enumerate(tasks):
        t = threading.Thread(
            target=task,
            name=f"Worker-{i}",  # shows up in logs via _add_thread_info
            daemon=True,
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
```

**Thread safety rules**:
- **Name all threads**: Use `name=` in `threading.Thread()` so logs identify the source
- **Protect shared state**: Use `threading.Lock()` around any mutable shared data
- **Prefer immutable data**: Frozen dataclasses, tuples, and `frozenset` don't need locks
- **Atomic writes under lock**: When multiple threads write the same file, combine `atomic_write` with a lock
- **Use `contextvars`** (not `threading.local`) for per-task context - works across both threads and async
- **Log thread identity**: The centralized `_add_thread_info` processor ensures every log line shows which thread produced it - never disable this in multithreaded code
- **Prefer `concurrent.futures.ThreadPoolExecutor`** over raw `threading.Thread` for pools

**Rules**:
- Use `asyncio.TaskGroup` (3.11+) over `asyncio.gather` - better error handling
- Use `except*` to handle errors from concurrent tasks by type
- Always use `async with` for async clients and connections
- Use `asynccontextmanager` for reusable async resource patterns
- Use FastAPI `lifespan` context manager, not deprecated `@app.on_event`
- Never mix `asyncio.run()` inside an already-running event loop
- CPU-bound work goes to `joblib.Parallel`, not async (GIL)
- **Thread identification**: Every thread must have a descriptive `name=` - no anonymous threads
- **Thread-safe I/O**: All file writes from threads must use `atomic_write` + lock

## Docstrings (Google Style)

Every public module, class, and function must have a docstring. We use **Google Style** formatting for automated docs generation (MkDocs/Sphinx).

### Format

```python
def calculate_velocity(distance: float, time: float) -> float:
    """Calculate velocity from distance and time.

    Computes simple linear velocity. For acceleration-aware
    calculations, use ``calculate_kinematics`` instead.

    Args:
        distance: The distance traveled in meters.
        time: The time elapsed in seconds.

    Returns:
        The velocity in meters per second.

    Raises:
        ValueError: If time is zero or negative.
    """
    if time <= 0:
        raise ValueError("Time must be positive")
    return distance / time


class OrderService:
    """Handles order lifecycle from creation through fulfillment.

    Coordinates validation, payment, and notification services
    following the three-tier architecture pattern.

    Attributes:
        repo: Repository for order persistence.
        notifier: Notification channel for order events.
    """

    def __init__(self, repo: OrderRepository, notifier: Notifier) -> None:
        self.repo = repo
        self.notifier = notifier

    async def create(self, items: list[LineItem]) -> Order:
        """Create a new order from line items.

        Validates items, calculates totals, persists the order,
        and sends a confirmation notification.

        Args:
            items: Non-empty list of line items for the order.

        Returns:
            The persisted order with a generated ID.

        Raises:
            ValidationError: If items is empty or contains invalid data.
            PaymentError: If payment authorization fails.
        """
        ...
```

### Module docstrings

```python
"""Order processing service.

Implements the order lifecycle: validation, payment, fulfillment.
Uses three-tier architecture with dependency injection via Protocol.
"""

from __future__ import annotations
```

**Rules**:
- **Triple double quotes** (`"""`) always - never single quotes, never backticks
- **Summary line**: Imperative mood, one line, ends with period. "Calculate velocity." not "Calculates velocity." or "This function calculates..."
- **Args/Returns/Raises**: Required on all public functions. Omit sections that don't apply (no empty `Args:` block)
- **Do NOT repeat type hints in docstrings** - types are already in the signature
- **Private functions** (`_helper`): Docstring optional, only add if logic is non-obvious
- **Module docstrings**: Required on all modules - brief summary of purpose and architectural role
- **Class docstrings**: Required on all public classes - describe purpose and list key `Attributes:`
- **One-liner docstrings**: OK for trivially obvious functions: `"""Return the user's full name."""`

## Testing Standards

**We use `pytest`. The `unittest` module is strictly forbidden.**

### pytest Conventions

```python
import pytest
from faker import Faker

Faker.seed(42)
fake = Faker()

# Test naming: test_<what>_<condition>_<expected>
def test_create_user_with_valid_data_returns_user() -> None:
    user = create_user(name=fake.name(), email=fake.email())
    assert user.id is not None
    assert user.name == user.name

def test_create_user_with_empty_name_raises_validation_error() -> None:
    with pytest.raises(ValidationError, match="name"):
        create_user(name="", email=fake.email())

# Fixtures for shared setup (with explicit scope)
@pytest.fixture
def sample_user() -> User:
    """Function-scoped (default) - created fresh per test."""
    return User(name=fake.name(), email=fake.email())

@pytest.fixture(scope="module")
def db_connection() -> Iterator[Connection]:
    """Module-scoped - shared across tests in the same file."""
    conn = create_connection()
    yield conn
    conn.close()

@pytest.fixture
async def async_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

# Parametrize for multiple cases - NEVER use loops inside tests
@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        ("hello", "HELLO"),
        ("world", "WORLD"),
        ("", ""),
    ],
)
def test_uppercase(input_value: str, expected: str) -> None:
    assert uppercase(input_value) == expected
```

### Async Testing (pytest-asyncio)

```python
import pytest

# pyproject.toml sets asyncio_mode = "auto", so no decorator needed
async def test_fetch_user_returns_data(async_client: httpx.AsyncClient) -> None:
    resp = await async_client.get("/users/123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "123"

# Parametrize works with async too
@pytest.mark.parametrize("status", ["active", "banned", "pending"])
async def test_user_status_filtering(
    async_client: httpx.AsyncClient,
    user_factory: UserFactory,
    status: str,
) -> None:
    await user_factory.create(status=status)
    resp = await async_client.get(f"/users?status={status}")
    assert resp.status_code == 200
    assert all(u["status"] == status for u in resp.json())
```

### Mocking (pytest-mock)

```python
# Use pytest-mock's mocker fixture - not unittest.mock.patch as decorator
def test_send_notification_calls_smtp(mocker: MockerFixture) -> None:
    mock_send = mocker.patch("app.services.smtp_client.send")
    notify_user(user_id="123", message="Hello")
    mock_send.assert_called_once_with(
        to="user@example.com",
        body="Hello",
    )

# Context manager form for scoped mocking
def test_service_retries_on_timeout(mocker: MockerFixture) -> None:
    mock_fetch = mocker.patch("app.services.http_client.get")
    mock_fetch.side_effect = [httpx.TimeoutException("timeout"), mock_response(200)]
    result = fetch_with_retry("/api/data")
    assert mock_fetch.call_count == 2
    assert result.status_code == 200
```

### Test Markers

```python
# Mark slow tests - run separately in CI
@pytest.mark.slow
def test_full_data_migration() -> None: ...

# Mark integration tests - need real dependencies
@pytest.mark.integration
async def test_database_roundtrip() -> None: ...

# pyproject.toml marker registration
# [tool.pytest.ini_options]
# markers = [
#     "slow: marks tests as slow (deselect with '-m \"not slow\"')",
#     "integration: marks tests requiring real services",
# ]
```

**Rules**:
- **pytest only**: `unittest` is forbidden - no `TestCase`, no `setUp`/`tearDown`, no `self.assert*`
- Test file naming: `test_<module>.py`
- Test function naming: `test_<what>_<condition>_<expected>`
- Use `Faker.seed(42)` at module level for reproducibility
- Use `pytest.fixture` for shared setup with explicit `scope=` when non-default
- **Fixture scopes**: `function` (default, safest), `module` (shared I/O like DB), `session` (expensive global setup only)
- Use `pytest.raises` for expected exceptions
- Use `@pytest.mark.parametrize` for data-driven tests - **never** loop inside a test
- Use `conftest.py` for shared fixtures across test files
- **Async tests**: Use `pytest-asyncio` with `asyncio_mode = "auto"` in pyproject.toml
- **Mocking**: Use `pytest-mock` (`mocker` fixture) - avoid `unittest.mock.patch` as decorator
- **Markers**: Register custom markers in pyproject.toml, use `@pytest.mark.slow` / `@pytest.mark.integration`
- Coverage target: 80%+ on business logic (services tier)

### Test Organization

```
tests/
├── conftest.py          # Shared fixtures (faker, db, client, factories)
├── unit/                # Fast, isolated, no I/O
│   ├── test_models.py
│   └── test_services.py
├── integration/         # Real dependencies (db, APIs)
│   ├── conftest.py      # DB fixtures, test containers
│   ├── test_repositories.py
│   └── test_api.py
└── e2e/                 # Full system tests
    └── test_workflows.py
```

## UV Toolchain (Exclusive)

**UV is the only Python toolchain.** No pip, no pipx, no conda, no poetry.

### Commands

```bash
# Project setup
uv init myproject                # Create new project
uv add structlog orjson tenacity # Add dependencies
uv add --dev pytest faker        # Add dev dependencies
uv sync                          # Install/sync all dependencies
uv lock                          # Generate/update lockfile

# Running code
uv run python script.py          # Run a script
uv run pytest                    # Run tests
uv run pytest -v --cov           # Tests with coverage
uv run black .                   # Format
uv run ruff check .              # Lint

# Package management
uv add httpx                     # Add a package
uv remove httpx                  # Remove a package
uv add --upgrade structlog       # Upgrade a package
uv tree                          # Show dependency tree

# Tools (replaces pipx)
uv tool install ruff             # Install CLI tool globally
uv tool run black .              # Run tool without installing
```

### What NEVER to Use

| Never | Always |
|-------|--------|
| `pip install` | `uv add` or `uv pip install` |
| `pip freeze` | `uv lock` / `uv.lock` file |
| `python script.py` | `uv run python script.py` |
| `python -m pytest` | `uv run pytest` |
| `pipx install tool` | `uv tool install tool` |
| `conda install` | `uv add` |
| `poetry add` | `uv add` |
| `pip install -e .` | `uv pip install -e .` |
| `virtualenv .venv` | `uv venv` (or automatic) |

### pyproject.toml (UV-native)

```toml
[project]
name = "myproject"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "python-dotenv>=1.0",
    "orjson>=3.9",
    "structlog>=24.1",
    "tenacity>=8.2",
    "pydantic>=2.6",
    "httpx>=0.27",
]

[project.optional-dependencies]
api = [
    "fastapi>=0.110",
    "uvicorn>=0.27",
]
cli = [
    "fire>=0.5",
]
dev = [
    "faker>=22.0",
    "pytest>=8.0",
    "pytest-cov>=4.1",
    "pytest-asyncio>=0.23",
]

[tool.black]
line-length = 88
target-version = ["py312"]

[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM", "TCH"]
# Black-owned rules - black is authoritative, ruff must not conflict
ignore = ["E111", "E114", "E117", "E501", "W191", "E203"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

**Grouping rationale**:
- **Core** (always installed): dotenv, orjson, structlog, tenacity, pydantic, httpx
- **api** (optional): FastAPI + uvicorn - only for web service projects
- **cli** (optional): fire - only for CLI tools
- **dev** (optional): faker, pytest - development and testing only

### Version Pinning Strategy

```toml
# Use >= for minimum version (allows compatible upgrades via lockfile)
dependencies = [
    "httpx>=0.27",       # >=minor: "at least this version"
    "pydantic>=2.6",     # >=minor: major version is our compat boundary
]

# NEVER do this:
# "httpx==0.27.0"       # BAD: too strict, blocks security patches
# "httpx"               # BAD: no lower bound, anything could resolve
# "httpx>=0.27,<1.0"    # UNNECESSARY: lockfile handles upper bounds
```

**Rules**:
- **`>=X.Y`** for all deps - set a minimum, let the lockfile pin the exact version
- **Never use `==`** - it blocks security patches and creates lockfile conflicts
- **Never omit a lower bound** - reproducibility requires knowing the minimum
- The **lockfile** (`uv.lock`) is the source of truth for exact versions in CI/prod

### Lock Files

```bash
# Generate/update lockfile after changing pyproject.toml
uv lock

# Verify lockfile matches pyproject.toml (CI check)
uv lock --check

# Install exactly what's locked (CI, Docker, prod)
uv sync --frozen

# Update a specific package to latest compatible version
uv add --upgrade httpx
uv lock  # regenerate lockfile
```

**Rules**:
- **Always commit `uv.lock`** to version control - it ensures deterministic builds
- **`uv sync --frozen`** in CI and Docker - never regenerate lockfile during builds
- **`uv lock --check`** in CI - fails if lockfile is out of sync with pyproject.toml
- **Never use `--upgrade` in CI** - upgrades happen locally, get committed, then CI uses `--frozen`
- **Review lockfile diffs** in PRs - transitive dependency changes can introduce vulnerabilities

### Security Auditing (CVE Scanning)

```bash
# Scan dependencies for known vulnerabilities
uv run pip-audit

# In CI (fail the build on any vulnerability)
uv run pip-audit --strict --desc
```

```yaml
# .github/workflows/ci.yml (add to quality job)
- name: Security audit
  run: uv run pip-audit --strict --desc
```

**Rules**:
- **`pip-audit`** is mandatory in CI - builds fail on known CVEs
- Add `pip-audit` to dev dependencies: `uv add --dev pip-audit`
- **Review advisories** before suppressing: `uv run pip-audit --ignore-vuln PYSEC-...` with comment explaining why
- **Transitive deps matter** - a vuln in a dep-of-a-dep is still your problem
- **Update promptly** - when `pip-audit` flags a vuln, `uv add --upgrade <package>` and regenerate lockfile

## Dockerfile (UV-Native)

Multi-stage build optimized for UV. Use this as the standard template.

```dockerfile
# ---- Build stage ----
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Then copy source and install project
COPY . .
RUN uv sync --frozen --no-dev

# ---- Runtime stage ----
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy only the virtual environment and source from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

# Use the venv Python directly (no uv needed at runtime)
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Rules**:
- Always multi-stage: build with UV, run without UV
- Copy `pyproject.toml` + `uv.lock` before source for layer caching
- Use `--frozen` to ensure lockfile is respected
- Use `--no-dev` in production builds
- Use `python:3.12-slim` not `python:3.12` (smaller image)
- Never install UV in the runtime stage

## CI/CD (GitHub Actions)

Standard workflow that enforces all WFC Python standards.

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync --frozen

      - name: Format check (black)
        run: uv run black --check .

      - name: Lint (ruff)
        run: uv run ruff check .

      - name: Type check (mypy)
        run: uv run mypy . --strict

      - name: Tests with coverage
        run: uv run pytest --cov --cov-report=term-missing --cov-fail-under=80

      - name: Check lockfile
        run: uv lock --check
```

**Rules**:
- All CI commands use `uv run` - no pip, no bare python
- Format, lint, type check, and test in that order
- `--cov-fail-under=80` enforces coverage threshold
- `uv lock --check` ensures lockfile is in sync with pyproject.toml
- Use `uv sync --frozen` to install exactly what's locked

## Integration with WFC Skills

### wfc-build / wfc-implement

When building Python features:
1. Use `uv add` to add dependencies, `uv run` to execute everything
2. Scaffold with preferred libraries + frameworks in pyproject.toml
3. Use `structlog` for all logging (not print/logging)
4. Use `orjson` for JSON operations (not stdlib json)
5. Use `tenacity` for any network/external calls
6. Use `httpx` for HTTP clients (not requests)
7. Use `pydantic` at system boundaries (API schemas, config, external data)
8. Use `FastAPI` for web APIs
9. Use `python-dotenv` or `pydantic-settings` for configuration
10. Use `fire` for CLI entry points
11. Use `faker` for test data generation
12. Follow three-tier: routes (presentation) -> services (logic) -> repositories (data)

### wfc-test

When generating tests for Python code:
1. Use `faker` with `Faker.seed(42)` for reproducible test data
2. Name tests: `test_<what>_<condition>_<expected>`
3. Use `conftest.py` for shared fixtures
4. Use `@pytest.mark.parametrize` for data-driven tests
5. Coverage target: 80%+ on services tier
6. Organize: `tests/unit/`, `tests/integration/`, `tests/e2e/`

### wfc-review

When reviewing Python code, flag:

**Toolchain violations**:
- `pip install` instead of `uv add`
- `python script.py` instead of `uv run python script.py`
- `python -m pytest` instead of `uv run pytest`
- Any use of pip, pipx, conda, poetry instead of uv

**Library violations**:
- `print()` statements that should use `structlog`
- f-strings inside log calls (`log.info(f"...")`) - use key-value pairs
- `import logging` (stdlib) that should use `structlog`
- `import json` that should use `orjson`
- `import requests` that should use `httpx`
- Hand-rolled retry loops that should use `tenacity`
- Hardcoded config that should use `python-dotenv` / `pydantic-settings`
- Raw dicts at API boundaries that should use `pydantic` models
- `argparse` boilerplate that could be replaced with `fire`
- Hand-written test fixtures that could use `faker`
- Sequential loops that could use `joblib.Parallel`

**Testing violations**:
- `import unittest` or `TestCase` subclasses (use pytest exclusively)
- `setUp()`/`tearDown()` methods instead of `@pytest.fixture`
- `self.assertEqual()` / `self.assertTrue()` instead of bare `assert`
- Loops inside tests instead of `@pytest.mark.parametrize`
- `unittest.mock.patch` as decorator instead of `pytest-mock` `mocker` fixture

**Async safety violations**:
- `requests.get()` / `requests.post()` inside `async def` (blocks event loop)
- `time.sleep()` inside `async def` (use `asyncio.sleep()`)
- `open()` for large files inside `async def` (use `aiofiles`)
- Catching `CancelledError` without re-raising
- Missing timeout on async network calls

**Documentation violations**:
- Public function/class without a docstring
- Non-Google-style docstrings (wrong section names, wrong formatting)
- Type hints repeated in docstring Args section
- Missing module-level docstring

**Dependency management violations**:
- `uv.lock` not committed to version control
- `==` pinned versions in pyproject.toml (use `>=`)
- No `pip-audit` in dev dependencies or CI
- `uv sync` without `--frozen` in CI/Docker

**Coding standard violations**:
- Missing type annotations on any function/method
- Code that fails `mypy --strict`
- Files exceeding 500 lines
- `Optional[X]` instead of `X | None`
- `typing.List`, `typing.Dict` instead of `list`, `dict`
- `TypeAlias` instead of `type` statement (3.12+)
- `asyncio.gather` instead of `asyncio.TaskGroup` (3.11+)
- `@app.on_event` instead of FastAPI `lifespan` context manager
- Tier violations (presentation importing data access directly)
- Classes with multiple responsibilities (SRP violation)
- Deep inheritance (>1 level) instead of composition
- Non-atomic file writes (raw `open()` + `write()` for config/state files)
- Missing factory pattern where object creation is conditional/registry-based
- Bare `except:` or silently swallowed exceptions
- Deep nesting (>3 levels) instead of early returns
- `os.path` instead of `pathlib.Path`
- Magic strings instead of `StrEnum`
- Missing `slots=True` on dataclasses
- Anonymous threads (no `name=` parameter)
- Shared mutable state without `threading.Lock`
- `structlog.configure()` called in library/module code instead of app entry point
- `# fmt: off` without justification
- Non-black-formatted code
- Dockerfile not using multi-stage build with UV
- CI using pip/python instead of uv commands

## Python Runtime Rules

These rules apply to all WFC Python projects:

**UV Toolchain (Exclusive)**:
- **Always** use `uv run` to execute Python code
- **Always** use `uv add` to add dependencies
- **Always** use `uv sync` to install/sync dependencies
- **Always** use `uv lock` to manage lockfiles
- **Always** use `uv tool install` for global CLI tools
- **Never** use `pip`, `pip install`, `pip freeze`
- **Never** use `python` or `python -m` directly
- **Never** use `pipx`, `conda`, or `poetry`

**Code Standards**:
- **Always** target Python 3.12+ (`requires-python = ">=3.12"`)
- **Always** use `black` for formatting (line-length 88, target py312)
- **Always** use `ruff` for linting
- **Always** use `mypy --strict` for type checking
- **Always** use full type annotations on all signatures
- **Always** use PEP 562 (`__getattr__` / `__dir__`) in `__init__.py`
- **Always** follow three-tier architecture (presentation / logic / data)
- **Always** apply SOLID principles (especially SRP and DI via Protocol)
- **Always** use factory patterns for conditional/registry-based object creation
- **Always** use composition over inheritance (Protocol, not deep class trees)
- **Always** use context managers for resource lifecycle
- **Always** use atomic writes for config/state files (temp + `os.replace`)
- **Always** define structured exception hierarchies per project
- **Always** use `asyncio.TaskGroup` for concurrent I/O (not `asyncio.gather`)
- **Always** use multi-stage Dockerfiles with UV for containerized projects
- **Always** use Google-style docstrings on all public APIs
- **Never** exceed 500 lines per file
- **Never** use `Optional`, `List`, `Dict`, `Tuple` from `typing` (use builtins)
- **Never** skip type annotations on public functions
- **Never** bare `except:` or silently swallow exceptions

**Logging & Observability**:
- **Always** configure structlog exactly once at app entry point (`setup_logging()`)
- **Always** include thread-identification processor in structlog config
- **Always** use `bind()` for request/session context propagation
- **Always** log key-value pairs: `log.info("event", key=value)`
- **Never** use `print()` for logging (structlog only)
- **Never** use f-strings in log calls (breaks aggregation)
- **Never** use stdlib `logging` (structlog only)

**Thread Safety**:
- **Always** name threads with `name=` parameter
- **Always** protect shared mutable state with `threading.Lock`
- **Always** use `atomic_write` + lock for concurrent file writes
- **Always** use `contextvars` (not `threading.local`) for per-task context
- **Never** leave threads anonymous - every thread must be identifiable in logs

**Async Safety**:
- **Always** use `httpx.AsyncClient` in async code (never `requests`)
- **Always** use `asyncio.sleep()` in async (never `time.sleep()`)
- **Always** use `asyncio.to_thread()` for blocking/CPU-bound calls in async context
- **Always** use `asyncio.timeout()` for deadline enforcement
- **Never** catch `CancelledError` without re-raising

**Testing**:
- **Always** use `pytest` (via `uv run pytest`) - unittest is **forbidden**
- **Always** use `pytest-asyncio` for async tests (`asyncio_mode = "auto"`)
- **Always** use `pytest-mock` (`mocker` fixture) for mocking
- **Always** use `faker` with `Faker.seed(42)` for test data
- **Always** use `@pytest.mark.parametrize` - never loop inside tests
- **Always** organize tests: `unit/`, `integration/`, `e2e/`
- **Always** target 80%+ coverage on business logic
- **Never** use `unittest.TestCase`, `setUp()`, `tearDown()`, or `self.assert*()`

**Dependency Management**:
- **Always** commit `uv.lock` to version control
- **Always** use `uv sync --frozen` in CI and Docker
- **Always** use `>=X.Y` version constraints (never `==`)
- **Always** run `pip-audit` in CI (`uv run pip-audit --strict`)
- **Always** use `uv lock --check` in CI to verify lockfile sync
- **Never** use `--upgrade` in CI - only locally

**Preferred Stack**:
- **Always** `httpx` over `requests`
- **Always** `orjson` over `json`
- **Always** `structlog` over `logging` / `print`
- **Always** `pydantic` at system boundaries
- **Always** `FastAPI` for web APIs
- **Always** `fire` for CLI tools
- **Always** `tenacity` for retries

---

**This is World Fucking Class Python.**
