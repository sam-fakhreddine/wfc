"""api_client.py — Anthropic SDK wrapper for wfc-skill-validator-llm."""

from __future__ import annotations

import os

try:
    import anthropic
except ImportError as _err:
    raise ImportError(
        "Install wfc[llm-validate] to use LLM validation: uv pip install -e '.[llm-validate]'"
    ) from _err

_MODEL = "claude-sonnet-4-6"
_THINKING_BUDGET = 8000
_THINKING_BETA = "interleaved-thinking-2025-05-14"


def call_api(prompt: str, system_prompt: str = "", use_thinking: bool = False) -> str:
    """Call the Anthropic API and return the text response.

    Args:
        prompt: User message content.
        system_prompt: Optional system prompt. Applied with cache_control:ephemeral
            when non-empty to enable prompt caching on repeated calls.
        use_thinking: If True, enable extended thinking (Discovery stage only).
            Thinking blocks are discarded; only text blocks are returned.

    Returns:
        Text content of the model response.

    Raises:
        EnvironmentError: If ANTHROPIC_SKILLS_VALIDATOR env var is not set.
        ImportError: If anthropic package is not installed (raised at import time).
    """
    api_key = os.environ.get("ANTHROPIC_SKILLS_VALIDATOR")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_SKILLS_VALIDATOR env var not set. "
            "Export your Anthropic API key to run LLM validation."
        )

    client = anthropic.Anthropic(api_key=api_key)

    messages: list[dict] = [{"role": "user", "content": prompt}]

    kwargs: dict = {
        "model": _MODEL,
        "max_tokens": 4096,
        "messages": messages,
    }

    if system_prompt:
        kwargs["system"] = [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    if use_thinking:
        kwargs["thinking"] = {"type": "enabled", "budget_tokens": _THINKING_BUDGET}
        kwargs["betas"] = [_THINKING_BETA]

    response = client.messages.create(**kwargs)

    return "".join(block.text for block in response.content if block.type == "text")
