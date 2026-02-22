"""Logging configuration module.

Provides environment-based logging configuration with typed configuration objects.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LoggingConfig:
    """Logging configuration from environment variables.

    Environment Variables:
        LOG_LEVEL: DEBUG, INFO, WARNING, ERROR (default: INFO)
        LOG_FORMAT: json, console (default: depends on ENV)
        ENV: development, production (default: development)

    Attributes:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Output format (json, console)
        env: Environment (development, production)
    """

    log_level: str
    log_format: str
    env: str

    def __init__(self):
        """Create new config from environment variables."""
        env = os.getenv("ENV", "development").lower()
        if env not in ("development", "production"):
            env = "development"

        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
            log_level = "INFO"

        default_format = "json" if env == "production" else "console"
        log_format = os.getenv("LOG_FORMAT", default_format).lower()
        if log_format not in ("json", "console"):
            log_format = "console"

        object.__setattr__(self, "log_level", log_level)
        object.__setattr__(self, "log_format", log_format)
        object.__setattr__(self, "env", env)
