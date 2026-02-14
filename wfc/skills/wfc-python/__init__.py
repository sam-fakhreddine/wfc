"""
wfc-python - Python Development Standards

Python-specific skill that inherits universal standards from wfc-code-standards
and adds Python tooling, libraries, and enforcement patterns.

Inherits from wfc-code-standards:
    - Architecture (three-tier, SOLID, composition, factories)
    - Code quality (500-line limit, DRY, error handling, resource lifecycle)
    - Observability (structured logging, no print, no string interpolation)
    - Testing (unit/integration/e2e, fixtures, parametrize, coverage)
    - Async safety (no blocking, timeouts, cancellation)
    - Dependencies (lock files, CVE scanning, version constraints)
    - Documentation (public API docstrings)

Python-specific additions:
    Toolchain:
        - UV exclusively (uv run, uv add, uv sync - never pip/pipx/conda/poetry)

    Language:
        - Python 3.12+ (type statement, generic syntax, f-string nesting)
        - Black formatting (line-length 88, target py312)
        - Full type annotations on all signatures
        - PEP 562 lazy imports in __init__.py
        - Pythonic conventions (comprehensions, pathlib, StrEnum, dataclasses)

    Libraries:
        - python-dotenv, fire, faker, joblib, orjson, structlog, tenacity

    Frameworks:
        - pydantic, httpx, FastAPI

    Testing:
        - pytest exclusive (unittest forbidden)
        - pytest-asyncio, pytest-mock, faker

    Enforcement:
        - Banned patterns (regex) for automated scanning
"""

from __future__ import annotations

import re
from typing import Any

__version__ = "0.1.0"

TOOLCHAIN: dict[str, str] = {
    "package_manager": "uv",
    "run": "uv run",
    "add_dep": "uv add",
    "add_dev_dep": "uv add --dev",
    "sync": "uv sync",
    "lock": "uv lock",
    "global_tool": "uv tool install",
}

PREFERRED_LIBRARIES: dict[str, str] = {
    "config": "python-dotenv",
    "cli": "fire",
    "test-data": "faker",
    "parallelism": "joblib",
    "json": "orjson",
    "logging": "structlog",
    "retry": "tenacity",
}

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
    "pydantic-settings>=2.2",
    "httpx>=0.27",
    "joblib>=1.3",
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
    "type_annotations": True,
    "pep562_lazy_imports": True,
    "slots_on_dataclasses": True,
    "formatter": "black",
    "line_length": 88,
    "linter": "ruff",
    "type_checker": "mypy --strict",
    "uv_exclusive": True,
    "centralized_logging": True,
    "thread_identified_logging": True,
    "pytest_exclusive": True,
    "docstrings_google_style": True,
    "ruff_black_ignore": ["E111", "E114", "E117", "E501", "W191", "E203"],
}

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
        "pattern": re.compile(
            r"^\s*(?:from\s+requests\s+import|import\s+requests)\b", re.MULTILINE
        ),
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
        "pattern": re.compile(r"^\s*print\s*\((?!.*#\s*noqa)", re.MULTILINE),
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
        "pattern": re.compile(r"^\s*import\s+logging\b(?!.*#\s*noqa)", re.MULTILINE),
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

BANNED: list[str] = [p["description"] for p in BANNED_PATTERNS]  # type: ignore[misc]

__all__ = [
    "API_DEPENDENCIES",
    "BANNED",
    "BANNED_PATTERNS",
    "CLI_DEPENDENCIES",
    "CODING_STANDARDS",
    "CORE_DEPENDENCIES",
    "DEV_DEPENDENCIES",
    "PREFERRED_FRAMEWORKS",
    "PREFERRED_LIBRARIES",
    "TOOLCHAIN",
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
            violations.append(
                {
                    "id": str(entry["id"]),
                    "description": str(entry["description"]),
                    "fix": str(entry["fix"]),
                }
            )
    return violations


_LAZY_IMPORTS: dict[str, str] = {}


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return [*__all__, *_LAZY_IMPORTS]
