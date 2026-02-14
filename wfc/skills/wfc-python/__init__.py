"""
wfc-python - Python Development Standards

Internal skill defining preferred Python libraries and patterns for WFC projects.
Referenced by wfc-build, wfc-implement, wfc-test, and wfc-review.

Preferred Libraries:
    - python-dotenv: Configuration from .env files
    - fire: CLI generation from functions/classes
    - faker: Realistic test data generation
    - joblib: Parallel execution and disk caching
    - orjson: Fast JSON serialization (10-50x stdlib)
    - structlog: Structured key-value logging
    - tenacity: Retry with exponential backoff
"""

__version__ = "0.1.0"

# Standard library set for quick reference by other skills
PREFERRED_LIBRARIES = {
    "config": "python-dotenv",
    "cli": "fire",
    "test-data": "faker",
    "parallelism": "joblib",
    "json": "orjson",
    "logging": "structlog",
    "retry": "tenacity",
}

CORE_DEPENDENCIES = [
    "python-dotenv>=1.0",
    "orjson>=3.9",
    "structlog>=24.1",
    "tenacity>=8.2",
]

CLI_DEPENDENCIES = [
    "fire>=0.5",
]

DEV_DEPENDENCIES = [
    "faker>=22.0",
    "pytest>=8.0",
    "pytest-cov>=4.1",
]

__all__ = [
    "PREFERRED_LIBRARIES",
    "CORE_DEPENDENCIES",
    "CLI_DEPENDENCIES",
    "DEV_DEPENDENCIES",
]
