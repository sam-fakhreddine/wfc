---
name: wfc-python
description: Internal Python development guidelines and preferred libraries for WFC projects. Defines the standard Python toolkit including python-dotenv (config), fire (CLI), faker (test data), joblib (parallelism), orjson (fast JSON), structlog (logging), and tenacity (retries). Referenced by wfc-build, wfc-implement, and wfc-test when scaffolding or reviewing Python code. Not a user-invocable skill.
license: MIT
---

# WFC:PYTHON - Python Development Standards

Internal skill that defines how WFC builds Python projects. Referenced by other skills during implementation and review.

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
- `print()` statements that should use `structlog`
- `import json` that should use `orjson`
- Hand-rolled retry loops that should use `tenacity`
- Hardcoded config that should use `python-dotenv`
- `argparse` boilerplate that could be replaced with `fire`
- Hand-written test fixtures that could use `faker`
- Sequential loops that could use `joblib.Parallel`

## Python Runtime Rules

These rules apply to all WFC Python projects (from CLAUDE.md):

- **Always** use `uv` for Python operations (`uv run`, `uv pip install`)
- **Never** use bare `python`, `pip`, or `python -m`
- **Always** use `pytest` as the test framework
- **Always** use `black` for formatting and `ruff` for linting

---

**This is World Fucking Class Python.**
