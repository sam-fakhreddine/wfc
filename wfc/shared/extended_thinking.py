"""
Extended Thinking Support for WFC

Orchestrators use this to decide when agents should use deep reasoning.
Provides consistent logic across all WFC skills for enabling extended thinking.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)


class ThinkingMode(Enum):
    """Extended thinking modes"""

    NORMAL = "normal"
    EXTENDED = "extended"
    UNLIMITED = "unlimited"


@dataclass
class ThinkingConfig:
    """Configuration for extended thinking"""

    mode: ThinkingMode
    reason: str
    budget_tokens: Optional[int] = None

    def to_prompt_section(self) -> str:
        """
        Generate prompt section for extended thinking.

        Returns markdown section to inject into agent prompt.
        """
        if self.mode == ThinkingMode.NORMAL:
            return ""

        lines = [
            "",
            "⚡ **EXTENDED THINKING ENABLED**",
            "",
            f"**Reason:** {self.reason}",
            "",
            "You are authorized to:",
            "- Think deeply about edge cases and failure modes",
            "- Reason through multiple implementation approaches",
            "- Consider architectural implications and trade-offs",
            "- Explore potential bugs before they happen",
            "- Take time to get it right (quality > speed)",
            "",
            "**How to use:**",
            "1. Use `<thinking>` tags to show your reasoning",
            "2. Consider alternatives before choosing approach",
            "3. Think through edge cases explicitly",
            "4. Validate assumptions before coding",
            "",
        ]

        if self.budget_tokens:
            lines.append(f"**Thinking budget:** {self.budget_tokens} tokens")
        else:
            lines.append("**Thinking budget:** Unlimited - think as much as needed")

        lines.append("")

        return "\n".join(lines)


class ExtendedThinkingDecider:
    """
    Decides when to enable extended thinking for tasks.

    Used by orchestrators to assess task complexity and determine
    if deep reasoning would be beneficial.
    """

    @staticmethod
    def should_use_extended_thinking(
        complexity: str,
        properties: List[str],
        retry_count: int = 0,
        is_architecture: bool = False,
        has_dependencies: bool = False,
        custom_indicators: Optional[List[str]] = None,
    ) -> ThinkingConfig:
        """
        Decide if extended thinking should be used.

        Args:
            complexity: Task complexity (S, M, L, XL)
            properties: List of properties (SAFETY, LIVENESS, etc.)
            retry_count: Number of times task has been retried
            is_architecture: Task involves architecture decisions
            has_dependencies: Task has complex dependencies
            custom_indicators: Additional indicators for deep thinking

        Returns:
            ThinkingConfig with mode and reason
        """
        reasons = []
        mode = ThinkingMode.NORMAL

        if complexity in ["L", "XL"]:
            reasons.append(f"High complexity ({complexity})")
            mode = ThinkingMode.EXTENDED

        critical_properties = {"SAFETY", "LIVENESS", "SECURITY", "CORRECTNESS"}
        has_critical = bool(set(properties) & critical_properties)
        if has_critical:
            critical = set(properties) & critical_properties
            reasons.append(f"Critical properties: {', '.join(critical)}")
            mode = ThinkingMode.EXTENDED

        if retry_count >= 3:
            if retry_count > 4:
                reasons.append("⚠️ EXCEEDED MAX RETRIES (4 total) - task should be abandoned")
            else:
                reasons.append(f"Retry #{retry_count} - think harder to avoid previous failures")
            mode = ThinkingMode.UNLIMITED

        if is_architecture:
            reasons.append("Architecture decisions require careful reasoning")
            mode = ThinkingMode.EXTENDED

        if has_dependencies:
            reasons.append("Complex dependencies require careful coordination")
            mode = ThinkingMode.EXTENDED

        if custom_indicators:
            for indicator in custom_indicators:
                reasons.append(indicator)
                mode = ThinkingMode.EXTENDED

        budget = None
        if mode == ThinkingMode.EXTENDED:
            budget_map = {"S": 2000, "M": 5000, "L": 10000, "XL": 20000}
            budget = budget_map.get(complexity, 1000)
        elif mode == ThinkingMode.UNLIMITED:
            budget = None

        reason = "; ".join(reasons) if reasons else "Standard task"

        return ThinkingConfig(mode=mode, reason=reason, budget_tokens=budget)

    @staticmethod
    def for_simple_task() -> ThinkingConfig:
        """Quick config for simple tasks (no extended thinking)"""
        return ThinkingConfig(
            mode=ThinkingMode.NORMAL, reason="Simple task, standard reasoning sufficient"
        )

    @staticmethod
    def for_complex_task(reason: str, budget: Optional[int] = None) -> ThinkingConfig:
        """Quick config for complex tasks (extended thinking)"""
        return ThinkingConfig(mode=ThinkingMode.EXTENDED, reason=reason, budget_tokens=budget)

    @staticmethod
    def for_retry(retry_count: int) -> ThinkingConfig:
        """Quick config for retry tasks (unlimited thinking)"""
        return ThinkingConfig(
            mode=ThinkingMode.UNLIMITED,
            reason=f"Retry #{retry_count} - analyze previous failures deeply",
            budget_tokens=None,
        )


def enable_thinking(reason: str, budget: Optional[int] = None) -> ThinkingConfig:
    """Enable extended thinking with reason"""
    return ThinkingConfig(mode=ThinkingMode.EXTENDED, reason=reason, budget_tokens=budget)


def enable_unlimited_thinking(reason: str) -> ThinkingConfig:
    """Enable unlimited thinking with reason"""
    return ThinkingConfig(mode=ThinkingMode.UNLIMITED, reason=reason, budget_tokens=None)


def disable_thinking() -> ThinkingConfig:
    """Disable extended thinking (normal mode)"""
    return ThinkingConfig(mode=ThinkingMode.NORMAL, reason="Standard task")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    logger.info("Extended Thinking Decision Examples\n")

    config = ExtendedThinkingDecider.should_use_extended_thinking(
        complexity="S", properties=[], retry_count=0
    )
    logger.info(f"1. Simple task: {config.mode.value}")
    logger.info(f"   Reason: {config.reason}\n")

    config = ExtendedThinkingDecider.should_use_extended_thinking(
        complexity="XL", properties=["MAINTAINABILITY"], retry_count=0
    )
    logger.info(f"2. High complexity: {config.mode.value}")
    logger.info(f"   Reason: {config.reason}")
    logger.info(f"   Budget: {config.budget_tokens} tokens\n")

    config = ExtendedThinkingDecider.should_use_extended_thinking(
        complexity="M", properties=["SAFETY", "SECURITY"], retry_count=0
    )
    logger.info(f"3. Critical properties: {config.mode.value}")
    logger.info(f"   Reason: {config.reason}")
    logger.info(f"   Budget: {config.budget_tokens} tokens\n")

    config = ExtendedThinkingDecider.should_use_extended_thinking(
        complexity="M", properties=[], retry_count=2
    )
    logger.info(f"4. Retry task: {config.mode.value}")
    logger.info(f"   Reason: {config.reason}")
    logger.info(f"   Budget: {config.budget_tokens or 'Unlimited'}\n")

    config = ExtendedThinkingDecider.for_complex_task(
        "Complex algorithm with edge cases", budget=2500
    )
    logger.info("5. Prompt section example:")
    logger.info(config.to_prompt_section())
