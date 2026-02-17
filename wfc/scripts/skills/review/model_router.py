"""
ModelRouter - per-reviewer model selection with auto-routing by diff size.

Priority:
  1. Small diff  (< small_diff_lines):  all reviewers → small_model (Haiku)
  2. Large diff  (>= large_diff_lines): high-stakes → large_high_stakes_model (Opus),
                                        others       → large_other_model (Sonnet)
  3. Medium diff (50-499 lines):        explicit per-reviewer config or default
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_COSTS: dict[str, dict[str, float]] = {
    "claude-opus-4-6": {"input": 0.015, "output": 0.075},
    "claude-sonnet-4-5-20250929": {"input": 0.003, "output": 0.015},
    "claude-haiku-4-5-20251001": {"input": 0.00025, "output": 0.00125},
}


@dataclass
class RoutingConfig:
    default: str
    reviewers: dict[str, str] = field(default_factory=dict)
    validation_cross_check: str = ""
    auto_routing: dict = field(default_factory=dict)


class ModelRouter:
    """
    Recommend the most cost-effective Claude model for each reviewer given
    diff size and explicit per-reviewer configuration.
    """

    DEFAULT_CONFIG_PATH: Path = (
        Path(__file__).parent.parent.parent.parent.parent / "config" / "model_routing.json"
    )

    def __init__(self, config_path: str | Path | None = None) -> None:
        self._config = self._load_config(
            Path(config_path) if config_path is not None else self.DEFAULT_CONFIG_PATH
        )

    def get_model(self, reviewer_id: str, diff_lines: int = 0) -> str:
        """
        Return the recommended model for *reviewer_id* given *diff_lines*.

        Priority:
          - small diff  → small_model (auto, overrides explicit config)
          - large diff  → large_high_stakes_model / large_other_model (auto)
          - medium diff → explicit reviewers[reviewer_id] → default
        """
        ar = self._config.auto_routing
        small_threshold: int = ar.get("small_diff_lines", 50)
        large_threshold: int = ar.get("large_diff_lines", 500)

        if diff_lines < small_threshold:
            return ar.get("small_model", self._config.default)

        if diff_lines >= large_threshold:
            high_stakes: list[str] = ar.get("high_stakes_reviewers", [])
            if reviewer_id in high_stakes:
                return ar.get("large_high_stakes_model", self._config.default)
            return ar.get("large_other_model", self._config.default)

        return self._config.reviewers.get(reviewer_id, self._config.default)

    def get_cross_check_model(self) -> str:
        """Return the model designated for LLM cross-check validation."""
        return self._config.validation_cross_check or self._config.default

    def estimate_cost(
        self,
        reviewer_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        diff_lines: int = 200,
    ) -> float:
        """
        Rough cost in USD for the model assigned to *reviewer_id*.

        Uses medium-range diff_lines by default so that per-reviewer
        explicit config applies (most representative call-site scenario).
        """
        model = self.get_model(reviewer_id, diff_lines=diff_lines)
        pricing = MODEL_COSTS.get(model)
        if pricing is None:
            pricing = MODEL_COSTS.get(self._config.default, {"input": 0.0, "output": 0.0})
        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]
        return input_cost + output_cost

    def _load_config(self, path: Path) -> RoutingConfig:
        """Load config from JSON. Returns built-in defaults if file is missing."""
        if not path.exists():
            logger.warning("model_routing.json not found at %s; using built-in defaults", path)
            return self._default_config()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return RoutingConfig(
                default=data.get("default", "claude-sonnet-4-5-20250929"),
                reviewers=data.get("reviewers", {}),
                validation_cross_check=data.get("validation_cross_check", ""),
                auto_routing=data.get("auto_routing", {}),
            )
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to parse %s: %s; using built-in defaults", path, exc)
            return self._default_config()

    @staticmethod
    def _default_config() -> RoutingConfig:
        """Hardcoded defaults matching model_routing.json."""
        return RoutingConfig(
            default="claude-sonnet-4-5-20250929",
            reviewers={
                "security": "claude-opus-4-6",
                "correctness": "claude-sonnet-4-5-20250929",
                "performance": "claude-sonnet-4-5-20250929",
                "maintainability": "claude-haiku-4-5-20251001",
                "reliability": "claude-opus-4-6",
            },
            validation_cross_check="claude-haiku-4-5-20251001",
            auto_routing={
                "small_diff_lines": 50,
                "large_diff_lines": 500,
                "small_model": "claude-haiku-4-5-20251001",
                "medium_model": "claude-sonnet-4-5-20250929",
                "large_high_stakes_model": "claude-opus-4-6",
                "large_other_model": "claude-sonnet-4-5-20250929",
                "high_stakes_reviewers": ["security", "reliability"],
            },
        )
