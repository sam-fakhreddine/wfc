---
name: wfc-python
description: |-
  Internal skill — loaded automatically by wfc-build, wfc-implement, wfc-test,
  and wfc-review when ALL conditions are true:

  1. TARGET LANGUAGE: Code being written, reviewed, or scaffolded is Python
  2. PROJECT CONTEXT: Confirmed WFC project via one of:
     - `[tool.wfc]` table in pyproject.toml, OR `wfc.yaml` at project root,
       OR user explicitly requests "WFC standards" or "WFC scaffolding"
  3. TASK TYPE: Writing, modifying, or reviewing application code in:
     - `api/` (FastAPI routes, Pydantic schemas)
     - `services/` (business logic, orchestration)
     - `repositories/` (data access, external APIs)
     - `models/` (domain objects, value types)
     - Test files that validate the above

  NOT for: General Python questions; standalone scripts; Jupyter notebooks;
  CI/CD config; database migrations; build/packaging scripts; auto-generated
  code (protobufs, gRPC stubs); Poetry/pip projects declining UV migration.
license: MIT
---

# WFC:PYTHON - Python Development Standards

Python-specific standards for WFC projects. **Requires `wfc-code-standards` skill loaded** — inherits universal standards (three-tier architecture, SOLID, composition over inheritance, 500-line limit, DRY, structured logging, testing philosophy, async safety, dependency management, documentation).

This skill adds Python-specific: syntax requirements, tooling (UV, black, ruff, mypy), libraries, frameworks, and enforcement patterns.

## Python Coding Standards

**These are non-negotiable.** Every Python file WFC produces must follow these conventions, **in addition to** the universal standards in `wfc-code-standards`.

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

Use PEP 562 for lazy imports in `__init__.py` files when exporting from submodules that import heavy dependencies (network libraries, crypto, ORMs, large frameworks).

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

- Use PEP 562 when exporting modules that import: httpx, pydantic, structlog, orjson, ORMs, crypto libraries
- Keep module-level imports to stdlib and lightweight constants
- Heavy dependencies load lazily through `__getattr__`
- Always implement `__dir__` alongside `__getattr__` for discoverability
- Avoid circular dependencies: use absolute imports in lazy-loaded modules

### Architecture in Python (see wfc-code-standards)

Three-tier, SOLID, composition over inheritance, DRY, 500-line limit, and elegance rules are defined in `wfc-code-standards`. Below is the **Python-specific implementation**.

**Python project structure** (three-tier):

```
project/
├── api/              # PRESENTATION: FastAPI routes, Pydantic schemas
│   ├── routes.py
│   └── schemas.py
├── services/         # LOGIC: Business rules, orchestration
│   ├── orders.py
│   └── payments.py
├── repositories/     # DATA: Database, APIs, file I/O
│   ├── orders.py
│   └── cache.py
└── models/           # DOMAIN: Dataclasses, enums, value objects
    └── order.py
```

**File naming conventions**:

- Module names: `snake_case.py` (e.g., `order_service.py`, not `OrderService.py`)
- Class names: `PascalCase` matching domain concept (e.g., `OrderService` in `order_service.py` or `orders.py`)
- Protocol definitions: Place in same file as consumer, or `protocols.py` if shared across 3+ consumers

**SOLID in Python** - use `Protocol` for DIP and ISP:

```python
from typing import Protocol

# Interface segregation via Protocol (not ABC)
class Readable(Protocol):
    def get(self, id: str) -> Model: ...

class Writable(Protocol):
    def save(self, model: Model) -> None: ...

# Dependency inversion via constructor injection
class OrderService:
    def __init__(
        self,
        repo: OrderRepository,     # Protocol, not concrete class
        notifier: Notifier,         # Protocol, not SmtpNotifier
    ) -> None:
        self.repo = repo
        self.notifier = notifier
```
