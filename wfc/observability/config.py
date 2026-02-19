"""
Observability configuration.

Loads from .wfc/observability.toml with env var overrides.
"""

from __future__ import annotations

import logging
import os
import tomllib
import uuid
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ObservabilityConfig:
    """Configuration for the observability system."""

    providers: list[str] = field(default_factory=lambda: ["null"])
    session_id: str = ""
    parent_session_id: str = ""
    file_output_dir: str = ".development/observability"
    console_verbosity: int = 1

    def __post_init__(self):
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        if not self.parent_session_id:
            self.parent_session_id = os.environ.get("WFC_SESSION_ID", "")

    @classmethod
    def load(cls, config_path: str | None = None) -> ObservabilityConfig:
        """
        Load config from .wfc/observability.toml with env var overrides.

        Priority: env vars > TOML file > defaults.
        """
        config_data: dict = {}

        toml_path = Path(config_path) if config_path else cls._find_config_file()
        if toml_path and toml_path.exists():
            try:
                with open(toml_path, "rb") as f:
                    config_data = tomllib.load(f)
                logger.debug("Loaded observability config from %s", toml_path)
            except Exception:
                logger.warning("Failed to parse %s — using defaults", toml_path, exc_info=True)

        config = cls(
            providers=config_data.get("providers", ["null"]),
            file_output_dir=config_data.get("file_output_dir", ".development/observability"),
            console_verbosity=config_data.get("console_verbosity", 1),
        )

        env_providers = os.environ.get("WFC_OBSERVABILITY_PROVIDERS")
        if env_providers:
            config.providers = [p.strip() for p in env_providers.split(",") if p.strip()]

        env_verbosity = os.environ.get("WFC_OBSERVABILITY_VERBOSITY")
        if env_verbosity:
            try:
                config.console_verbosity = int(env_verbosity)
            except ValueError:
                pass

        env_output_dir = os.environ.get("WFC_OBSERVABILITY_OUTPUT_DIR")
        if env_output_dir:
            config.file_output_dir = env_output_dir

        return config

    @staticmethod
    def _find_config_file() -> Path | None:
        """Search for .wfc/observability.toml from cwd upward."""
        current = Path.cwd()
        for _ in range(10):
            candidate = current / ".wfc" / "observability.toml"
            if candidate.exists():
                return candidate
            parent = current.parent
            if parent == current:
                break
            current = parent
        return None
