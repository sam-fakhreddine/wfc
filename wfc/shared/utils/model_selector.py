"""
WFC Model Selector - ELEGANT & SIMPLE

Auto-selects the appropriate model (sonnet/opus/haiku) based on task complexity.

Design: Simple mapping, no ML, no over-thinking.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class ModelTier(Enum):
    """Model tiers for different task complexities."""

    HAIKU = "haiku"  # Fast, cheap, simple tasks
    SONNET = "sonnet"  # Balanced, most tasks
    OPUS = "opus"  # Powerful, complex tasks


@dataclass
class ModelConfig:
    """Model configuration."""

    tier: ModelTier
    model_id: str
    provider: str

    # Estimated performance characteristics
    tokens_per_second: int  # Rough throughput estimate
    cost_per_million: float  # Rough cost estimate


class ModelSelector:
    """
    Selects the appropriate model based on task complexity.

    Used by: wfc-implement (agent assignment)

    Design: Simple complexity -> model mapping. No ML needed.
    """

    # Default model configurations
    MODELS: Dict[ModelTier, ModelConfig] = {
        ModelTier.HAIKU: ModelConfig(
            tier=ModelTier.HAIKU,
            model_id="claude-haiku-4-5-20251001",
            provider="anthropic",
            tokens_per_second=100,
            cost_per_million=1.0,
        ),
        ModelTier.SONNET: ModelConfig(
            tier=ModelTier.SONNET,
            model_id="claude-sonnet-4-20250514",
            provider="anthropic",
            tokens_per_second=60,
            cost_per_million=3.0,
        ),
        ModelTier.OPUS: ModelConfig(
            tier=ModelTier.OPUS,
            model_id="claude-opus-4-20250514",
            provider="anthropic",
            tokens_per_second=30,
            cost_per_million=15.0,
        ),
    }

    # Complexity to model tier mapping
    COMPLEXITY_MAP: Dict[str, ModelTier] = {
        "S": ModelTier.HAIKU,  # Small: simple, fast model
        "M": ModelTier.SONNET,  # Medium: balanced model
        "L": ModelTier.OPUS,  # Large: powerful model
        "XL": ModelTier.OPUS,  # Extra Large: powerful model
    }

    def __init__(self, model_overrides: Optional[Dict[str, ModelConfig]] = None):
        """
        Initialize model selector.

        Args:
            model_overrides: Optional custom model configurations
        """
        self.models = self.MODELS.copy()
        if model_overrides:
            self.models.update(model_overrides)

    def select(self, complexity: str) -> ModelConfig:
        """
        Select model based on task complexity.

        Args:
            complexity: Task complexity (S, M, L, XL)

        Returns:
            ModelConfig for the selected model

        Raises:
            ValueError: If complexity is invalid
        """
        if complexity not in self.COMPLEXITY_MAP:
            raise ValueError(
                f"Invalid complexity: {complexity}. "
                f"Must be one of: {', '.join(self.COMPLEXITY_MAP.keys())}"
            )

        tier = self.COMPLEXITY_MAP[complexity]
        return self.models[tier]

    def select_by_tier(self, tier: ModelTier) -> ModelConfig:
        """
        Select model by tier directly.

        Args:
            tier: Model tier

        Returns:
            ModelConfig for the tier
        """
        return self.models[tier]

    def estimate_cost(self, complexity: str, estimated_tokens: int) -> float:
        """
        Estimate cost for a task.

        Args:
            complexity: Task complexity
            estimated_tokens: Estimated token usage

        Returns:
            Estimated cost in dollars
        """
        model = self.select(complexity)
        return (estimated_tokens / 1_000_000) * model.cost_per_million

    def estimate_duration(self, complexity: str, estimated_tokens: int) -> float:
        """
        Estimate duration for a task.

        Args:
            complexity: Task complexity
            estimated_tokens: Estimated token usage

        Returns:
            Estimated duration in seconds
        """
        model = self.select(complexity)
        return estimated_tokens / model.tokens_per_second


# Convenience function
def get_selector(model_overrides: Optional[Dict[str, ModelConfig]] = None) -> ModelSelector:
    """
    Get ModelSelector instance.

    Args:
        model_overrides: Optional custom model configurations

    Returns:
        ModelSelector instance
    """
    return ModelSelector(model_overrides)


if __name__ == "__main__":
    # Simple test
    selector = get_selector()

    for complexity in ["S", "M", "L", "XL"]:
        model = selector.select(complexity)
        print(f"{complexity} task -> {model.tier.value}: {model.model_id}")

        cost = selector.estimate_cost(complexity, 50_000)
        duration = selector.estimate_duration(complexity, 50_000)
        print(f"  Estimated: ${cost:.2f}, {duration:.1f}s\n")
