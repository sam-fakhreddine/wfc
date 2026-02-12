"""
Extended Thinking Support for WFC

Orchestrators use this to decide when agents should use deep reasoning.
Provides consistent logic across all WFC skills for enabling extended thinking.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class ThinkingMode(Enum):
    """Extended thinking modes"""
    NORMAL = "normal"           # Standard reasoning
    EXTENDED = "extended"       # Deep reasoning enabled
    UNLIMITED = "unlimited"     # No thinking budget limit


@dataclass
class ThinkingConfig:
    """Configuration for extended thinking"""
    mode: ThinkingMode
    reason: str  # Why extended thinking was enabled
    budget_tokens: Optional[int] = None  # Token budget (None = unlimited)

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
        custom_indicators: Optional[List[str]] = None
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

        # High complexity tasks
        if complexity in ['L', 'XL']:
            reasons.append(f"High complexity ({complexity})")
            mode = ThinkingMode.EXTENDED

        # Critical properties
        critical_properties = {'SAFETY', 'LIVENESS', 'SECURITY', 'CORRECTNESS'}
        has_critical = bool(set(properties) & critical_properties)
        if has_critical:
            critical = set(properties) & critical_properties
            reasons.append(f"Critical properties: {', '.join(critical)}")
            mode = ThinkingMode.EXTENDED

        # Retry - failed before, think harder
        if retry_count > 0:
            reasons.append(f"Retry #{retry_count} - think harder to avoid previous failures")
            mode = ThinkingMode.UNLIMITED  # No budget on retries

        # Architecture decisions
        if is_architecture:
            reasons.append("Architecture decisions require careful reasoning")
            mode = ThinkingMode.EXTENDED

        # Complex dependencies
        if has_dependencies:
            reasons.append("Complex dependencies require careful coordination")
            mode = ThinkingMode.EXTENDED

        # Custom indicators
        if custom_indicators:
            for indicator in custom_indicators:
                reasons.append(indicator)
                mode = ThinkingMode.EXTENDED

        # Determine budget
        budget = None
        if mode == ThinkingMode.EXTENDED:
            # Budget based on complexity
            budget_map = {'S': 500, 'M': 1000, 'L': 2500, 'XL': 5000}
            budget = budget_map.get(complexity, 1000)
        elif mode == ThinkingMode.UNLIMITED:
            budget = None  # Unlimited

        reason = "; ".join(reasons) if reasons else "Standard task"

        return ThinkingConfig(
            mode=mode,
            reason=reason,
            budget_tokens=budget
        )

    @staticmethod
    def for_simple_task() -> ThinkingConfig:
        """Quick config for simple tasks (no extended thinking)"""
        return ThinkingConfig(
            mode=ThinkingMode.NORMAL,
            reason="Simple task, standard reasoning sufficient"
        )

    @staticmethod
    def for_complex_task(reason: str, budget: Optional[int] = None) -> ThinkingConfig:
        """Quick config for complex tasks (extended thinking)"""
        return ThinkingConfig(
            mode=ThinkingMode.EXTENDED,
            reason=reason,
            budget_tokens=budget
        )

    @staticmethod
    def for_retry(retry_count: int) -> ThinkingConfig:
        """Quick config for retry tasks (unlimited thinking)"""
        return ThinkingConfig(
            mode=ThinkingMode.UNLIMITED,
            reason=f"Retry #{retry_count} - analyze previous failures deeply",
            budget_tokens=None
        )


# Convenience functions
def enable_thinking(reason: str, budget: Optional[int] = None) -> ThinkingConfig:
    """Enable extended thinking with reason"""
    return ThinkingConfig(
        mode=ThinkingMode.EXTENDED,
        reason=reason,
        budget_tokens=budget
    )


def enable_unlimited_thinking(reason: str) -> ThinkingConfig:
    """Enable unlimited thinking with reason"""
    return ThinkingConfig(
        mode=ThinkingMode.UNLIMITED,
        reason=reason,
        budget_tokens=None
    )


def disable_thinking() -> ThinkingConfig:
    """Disable extended thinking (normal mode)"""
    return ThinkingConfig(
        mode=ThinkingMode.NORMAL,
        reason="Standard task"
    )


# Example usage
if __name__ == '__main__':
    print("Extended Thinking Decision Examples\n")

    # Example 1: Simple task
    config = ExtendedThinkingDecider.should_use_extended_thinking(
        complexity='S',
        properties=[],
        retry_count=0
    )
    print(f"1. Simple task: {config.mode.value}")
    print(f"   Reason: {config.reason}\n")

    # Example 2: High complexity
    config = ExtendedThinkingDecider.should_use_extended_thinking(
        complexity='XL',
        properties=['MAINTAINABILITY'],
        retry_count=0
    )
    print(f"2. High complexity: {config.mode.value}")
    print(f"   Reason: {config.reason}")
    print(f"   Budget: {config.budget_tokens} tokens\n")

    # Example 3: Critical properties
    config = ExtendedThinkingDecider.should_use_extended_thinking(
        complexity='M',
        properties=['SAFETY', 'SECURITY'],
        retry_count=0
    )
    print(f"3. Critical properties: {config.mode.value}")
    print(f"   Reason: {config.reason}")
    print(f"   Budget: {config.budget_tokens} tokens\n")

    # Example 4: Retry
    config = ExtendedThinkingDecider.should_use_extended_thinking(
        complexity='M',
        properties=[],
        retry_count=2
    )
    print(f"4. Retry task: {config.mode.value}")
    print(f"   Reason: {config.reason}")
    print(f"   Budget: {config.budget_tokens or 'Unlimited'}\n")

    # Example 5: Prompt section
    config = ExtendedThinkingDecider.for_complex_task(
        "Complex algorithm with edge cases",
        budget=2500
    )
    print("5. Prompt section example:")
    print(config.to_prompt_section())
