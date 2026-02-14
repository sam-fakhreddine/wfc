"""
wfc-python - Python Development Standards

Internal skill defining preferred Python libraries, frameworks, coding standards,
and UV-exclusive toolchain for WFC projects. Referenced by wfc-build, wfc-implement,
wfc-test, and wfc-review.

Toolchain:
    - UV exclusively (uv run, uv add, uv sync - never pip/pipx/conda/poetry)

Standards:
    - Python 3.12+ required (type statement, generic syntax, f-string nesting)
    - Black formatting (line-length 88, no overrides)
    - Full type annotations on all signatures
    - PEP 562 lazy imports in __init__.py
    - Three-tier architecture (presentation / logic / data)
    - SOLID principles (SRP, OCP, LSP, ISP, DIP)
    - Composition over inheritance (Protocol, not deep class trees)
    - Structured error handling (exception hierarchies, no bare except)
    - Context managers for all resource lifecycle
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

CODING_STANDARDS: dict[str, str | int | bool] = {
    "python_version": ">=3.12",
    "formatter": "black",
    "line_length": 88,
    "linter": "ruff",
    "max_file_lines": 500,
    "type_annotations": True,
    "pep562_lazy_imports": True,
    "three_tier_architecture": True,
    "solid_principles": True,
    "composition_over_inheritance": True,
    "structured_error_handling": True,
    "context_managers_for_resources": True,
    "slots_on_dataclasses": True,
    "uv_exclusive": True,
}

# Banned tools/commands
BANNED: list[str] = [
    "pip",
    "pip install",
    "pip freeze",
    "pipx",
    "conda",
    "poetry",
    "python -m",
    "import requests",
    "import json",
    "from typing import Optional",
    "from typing import List",
    "from typing import Dict",
    "from typing import Tuple",
    "bare except:",
]

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
]


# PEP 562 - lazy imports for heavier objects
def __getattr__(name: str) -> Any:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return __all__
