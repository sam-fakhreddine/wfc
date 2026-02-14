"""
wfc-python - Python Development Standards

Internal skill defining preferred Python libraries and coding standards
for WFC projects. Referenced by wfc-build, wfc-implement, wfc-test,
and wfc-review.

Standards:
    - Python 3.12+ required (type statement, generic syntax, f-string nesting)
    - Black formatting (line-length 88, no overrides)
    - Full type annotations on all signatures
    - PEP 562 lazy imports in __init__.py
    - Three-tier architecture (presentation / logic / data)
    - SOLID principles (SRP, OCP, LSP, ISP, DIP)
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
"""

from __future__ import annotations

from typing import Any

__version__ = "0.1.0"

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

CORE_DEPENDENCIES: list[str] = [
    "python-dotenv>=1.0",
    "orjson>=3.9",
    "structlog>=24.1",
    "tenacity>=8.2",
]

CLI_DEPENDENCIES: list[str] = [
    "fire>=0.5",
]

DEV_DEPENDENCIES: list[str] = [
    "faker>=22.0",
    "pytest>=8.0",
    "pytest-cov>=4.1",
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
    "slots_on_dataclasses": True,
}

__all__ = [
    "PREFERRED_LIBRARIES",
    "CORE_DEPENDENCIES",
    "CLI_DEPENDENCIES",
    "DEV_DEPENDENCIES",
    "CODING_STANDARDS",
]


# PEP 562 - lazy imports for heavier objects
def __getattr__(name: str) -> Any:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return __all__
