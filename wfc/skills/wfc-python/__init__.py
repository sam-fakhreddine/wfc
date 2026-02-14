"""
wfc-python - Python Development Standards

Internal skill defining preferred Python libraries, frameworks, coding standards,
and UV-exclusive toolchain for WFC projects. Referenced by wfc-build, wfc-implement,
wfc-test, and wfc-review.

Toolchain:
    - UV exclusively (uv run, uv add, uv sync - never pip/pipx/conda/poetry)

Standards:
    - Python 3.12+ required (type statement, generic syntax, f-string nesting)
    - Black formatting (line-length 88, no overrides, PEP 8 synced via ruff ignores)
    - Full type annotations on all signatures
    - PEP 562 lazy imports in __init__.py
    - Three-tier architecture (presentation / logic / data)
    - SOLID principles (SRP, OCP, LSP, ISP, DIP)
    - Factory patterns for conditional/registry-based object creation
    - Composition over inheritance (Protocol, not deep class trees)
    - Structured error handling (exception hierarchies, no bare except)
    - Centralized logging (structlog, configure once, thread-identified)
    - Context managers for all resource lifecycle
    - Atomic writes (temp file + os.replace, never half-written files)
    - Thread-safe operations (locks for shared state, named threads)
    - Google-style docstrings on all public APIs
    - pytest exclusive (unittest forbidden), pytest-asyncio, pytest-mock
    - Async safety (no blocking I/O in async, asyncio.to_thread for CPU work)
    - Lock files committed, version pinning (>=X.Y), CVE scanning (pip-audit)
    - DRY - extract at 3+ repetitions
    - 500-line hard cap per file
    - Pythonic conventions (comprehensions, pathlib, StrEnum, dataclasses)

Preferred Libraries:
    - python-dotenv: Configuration from .env files
    - fire: CLI generation from functions/classes
    - faker: Realistic test data generation
    - joblib: Parallel execution and disk caching
    - orjson: Fast JSON serialization (10-50x stdlib)
    - structlog: Structured key-value logging
    - tenacity: Retry with exponential backoff

Preferred Frameworks:
    - pydantic: Data validation at system boundaries
    - httpx: HTTP client (async-first, replaces requests)
    - FastAPI: Web API framework
"""

from __future__ import annotations

import re
from typing import Any

__version__ = "0.1.0"

# UV-exclusive toolchain
TOOLCHAIN: dict[str, str] = {
    "package_manager": "uv",
    "run": "uv run",
    "add_dep": "uv add",
    "add_dev_dep": "uv add --dev",
    "sync": "uv sync",
    "lock": "uv lock",
    "global_tool": "uv tool install",
}

# Standard library set for quick reference by other skills
PREFERRED_LIBRARIES: dict[str, str] = {
    "config": "python-dotenv",
    "cli": "fire",
    "test-data": "faker",
    "parallelism": "joblib",
    "json": "orjson",
    "logging": "structlog",
    "retry": "tenacity",
}

# Preferred frameworks for specific domains
PREFERRED_FRAMEWORKS: dict[str, str] = {
    "validation": "pydantic",
    "http-client": "httpx",
    "web-api": "fastapi",
    "settings": "pydantic-settings",
}

CORE_DEPENDENCIES: list[str] = [
    "python-dotenv>=1.0",
    "orjson>=3.9",
    "structlog>=24.1",
    "tenacity>=8.2",
    "pydantic>=2.6",
    "httpx>=0.27",
]

API_DEPENDENCIES: list[str] = [
    "fastapi>=0.110",
    "uvicorn>=0.27",
]

CLI_DEPENDENCIES: list[str] = [
    "fire>=0.5",
]

DEV_DEPENDENCIES: list[str] = [
    "faker>=22.0",
    "pytest>=8.0",
    "pytest-cov>=4.1",
    "pytest-asyncio>=0.23",
]

CODING_STANDARDS: dict[str, str | int | bool | list[str]] = {
    "python_version": ">=3.12",
    "formatter": "black",
    "line_length": 88,
    "linter": "ruff",
    "type_checker": "mypy --strict",
    "max_file_lines": 500,
    "type_annotations": True,
    "pep562_lazy_imports": True,
    "three_tier_architecture": True,
    "solid_principles": True,
    "composition_over_inheritance": True,
    "factory_patterns": True,
    "structured_error_handling": True,
    "context_managers_for_resources": True,
    "atomic_writes": True,
    "centralized_logging": True,
    "thread_safe_operations": True,
    "thread_identified_logging": True,
    "docstrings_google_style": True,
    "pytest_exclusive": True,
    "async_safety": True,
    "lockfile_committed": True,
    "cve_scanning": True,
    "slots_on_dataclasses": True,
    "uv_exclusive": True,
    # Black-owned PEP 8 rules that ruff must ignore to avoid conflicts
    "ruff_black_ignore": ["E111", "E114", "E117", "E501", "W191", "E203"],
}

# Structured banned patterns for other skills to scan code against.
# Each entry has: id, regex pattern (compiled), human description, and suggested fix.
# Patterns are designed to avoid false positives (e.g. won't flag "uv pip install"
# when checking for bare "pip install", won't flag "except ValueError:" for bare except).
BANNED_PATTERNS: list[dict[str, str | re.Pattern[str]]] = [
    {
        "id": "pip-install",
        "pattern": re.compile(r"(?<!uv\s)(?<!uv\s\s)pip\s+install\b"),
        "description": "Bare pip install (use 'uv pip install' or 'uv add')",
        "fix": "uv add <package> (or uv pip install for one-offs)",
    },
    {
        "id": "pip-freeze",
        "pattern": re.compile(r"\bpip\s+freeze\b"),
        "description": "pip freeze (use 'uv lock' for lockfiles)",
        "fix": "uv lock",
    },
    {
        "id": "pipx",
        "pattern": re.compile(r"\bpipx\s"),
        "description": "pipx usage (use 'uv tool install')",
        "fix": "uv tool install <tool>",
    },
    {
        "id": "conda",
        "pattern": re.compile(r"\bconda\s+(install|create|activate)\b"),
        "description": "conda usage (use uv exclusively)",
        "fix": "uv add / uv venv",
    },
    {
        "id": "poetry",
        "pattern": re.compile(r"\bpoetry\s+(add|install|lock|run)\b"),
        "description": "poetry usage (use uv exclusively)",
        "fix": "uv add / uv sync / uv lock / uv run",
    },
    {
        "id": "bare-python-m",
        "pattern": re.compile(r"(?<!uv\srun\s)\bpython\s+-m\b"),
        "description": "Bare 'python -m' (use 'uv run python -m' or 'uv run <tool>')",
        "fix": "uv run pytest (or uv run python -m <module>)",
    },
    {
        "id": "import-requests",
        "pattern": re.compile(r"^\s*(?:from\s+requests\s+import|import\s+requests)\b", re.MULTILINE),
        "description": "requests library (use httpx instead)",
        "fix": "import httpx",
    },
    {
        "id": "import-stdlib-json",
        "pattern": re.compile(r"^\s*import\s+json\b(?!.*#\s*noqa)", re.MULTILINE),
        "description": "stdlib json (use orjson for 10-50x performance)",
        "fix": "import orjson",
    },
    {
        "id": "typing-optional",
        "pattern": re.compile(r"(?:from\s+typing\s+import\s+.*\bOptional\b|\bOptional\[)"),
        "description": "typing.Optional (use X | None syntax, Python 3.10+)",
        "fix": "X | None",
    },
    {
        "id": "typing-list",
        "pattern": re.compile(r"(?:from\s+typing\s+import\s+.*\bList\b|\bList\[)"),
        "description": "typing.List (use builtin list[], Python 3.9+)",
        "fix": "list[...]",
    },
    {
        "id": "typing-dict",
        "pattern": re.compile(r"(?:from\s+typing\s+import\s+.*\bDict\b|\bDict\[)"),
        "description": "typing.Dict (use builtin dict[], Python 3.9+)",
        "fix": "dict[...]",
    },
    {
        "id": "typing-tuple",
        "pattern": re.compile(r"(?:from\s+typing\s+import\s+.*\bTuple\b|\bTuple\[)"),
        "description": "typing.Tuple (use builtin tuple[], Python 3.9+)",
        "fix": "tuple[...]",
    },
    {
        "id": "bare-except",
        "pattern": re.compile(r"^\s*except\s*:", re.MULTILINE),
        "description": "Bare except: catches everything including SystemExit/KeyboardInterrupt",
        "fix": "except Exception: (or a more specific exception type)",
    },
    {
        "id": "unittest-import",
        "pattern": re.compile(
            r"^\s*(?:from\s+unittest\s+import|import\s+unittest)\b", re.MULTILINE
        ),
        "description": "unittest is forbidden (use pytest exclusively)",
        "fix": "import pytest (with fixtures, parametrize, and pytest.raises)",
    },
    {
        "id": "unittest-testcase",
        "pattern": re.compile(r"\bclass\s+\w+\(.*\bTestCase\b.*\)"),
        "description": "unittest.TestCase subclass (use plain pytest functions)",
        "fix": "def test_<what>_<condition>_<expected>() -> None: ...",
    },
    {
        "id": "print-statement",
        "pattern": re.compile(
            r"^\s*print\s*\((?!.*#\s*noqa)", re.MULTILINE
        ),
        "description": "print() statement (use structlog for all logging)",
        "fix": "log = structlog.get_logger(); log.info('event', key=value)",
    },
    {
        "id": "fstring-in-log",
        "pattern": re.compile(
            r"""\blog\.\w+\(\s*f['"]""",
        ),
        "description": "f-string in log call (breaks log aggregation)",
        "fix": 'log.info("event", key=value) - use key-value pairs',
    },
    {
        "id": "stdlib-logging",
        "pattern": re.compile(
            r"^\s*import\s+logging\b(?!.*#\s*noqa)", re.MULTILINE
        ),
        "description": "stdlib logging (use structlog exclusively)",
        "fix": "import structlog; log = structlog.get_logger()",
    },
    {
        "id": "requests-in-async",
        "pattern": re.compile(
            r"async\s+def\s+\w+.*\n(?:.*\n)*?.*\brequests\.\w+",
            re.MULTILINE,
        ),
        "description": "requests library used in async function (blocks event loop)",
        "fix": "async with httpx.AsyncClient() as client: resp = await client.get(url)",
    },
    {
        "id": "time-sleep-in-async",
        "pattern": re.compile(
            r"async\s+def\s+\w+.*\n(?:.*\n)*?.*\btime\.sleep\b",
            re.MULTILINE,
        ),
        "description": "time.sleep() in async function (blocks event loop)",
        "fix": "await asyncio.sleep(seconds)",
    },
]

# Legacy alias - flat list of human-readable descriptions for backward compat
BANNED: list[str] = [p["description"] for p in BANNED_PATTERNS]  # type: ignore[misc]

__all__ = [
    "TOOLCHAIN",
    "PREFERRED_LIBRARIES",
    "PREFERRED_FRAMEWORKS",
    "CORE_DEPENDENCIES",
    "API_DEPENDENCIES",
    "CLI_DEPENDENCIES",
    "DEV_DEPENDENCIES",
    "CODING_STANDARDS",
    "BANNED",
    "BANNED_PATTERNS",
    "check_violations",
]


def check_violations(source: str) -> list[dict[str, str]]:
    """Scan source code against BANNED_PATTERNS, returning all violations found.

    Returns a list of dicts with keys: id, description, fix.
    """
    violations: list[dict[str, str]] = []
    for entry in BANNED_PATTERNS:
        pattern: re.Pattern[str] = entry["pattern"]  # type: ignore[assignment]
        if pattern.search(source):
            violations.append({
                "id": str(entry["id"]),
                "description": str(entry["description"]),
                "fix": str(entry["fix"]),
            })
    return violations


# PEP 562 - guard against invalid attribute access on this module.
# No lazy imports needed here since all exports are lightweight dicts/lists.
# If heavier objects are added later (e.g. a RuleEngine), add them to _LAZY_IMPORTS
# and load on first access.
_LAZY_IMPORTS: dict[str, str] = {
    # "RuleEngine": "wfc.skills.wfc_python.rule_engine",  # example for future use
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value  # cache so __getattr__ isn't called again
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return [*__all__, *_LAZY_IMPORTS]
