"""api_client.py — Anthropic SDK wrapper for wfc-skill-validator-llm."""

from __future__ import annotations

import os
import threading

try:
    import anthropic
except ImportError as _err:
    raise ImportError(
        "Install wfc[llm-validate] to use LLM validation: uv pip install -e '.[llm-validate]'"
    ) from _err

_MODEL = os.environ.get("SKILLS_VALIDATOR_MODEL", "claude-sonnet-4-6")
_THINKING_BUDGET = 8000
_THINKING_BETA = "interleaved-thinking-2025-05-14"
_DEFAULT_TIMEOUT = 120.0

_usage_local = threading.local()


def get_accumulated_usage() -> dict[str, int]:
    """Return the accumulated token counts for the current thread.

    Returns:
        Dict with keys "input_tokens" and "output_tokens".
    """
    return {
        "input_tokens": getattr(_usage_local, "input_tokens", 0),
        "output_tokens": getattr(_usage_local, "output_tokens", 0),
    }


def reset_accumulated_usage() -> None:
    """Reset the thread-local token accumulator to zero."""
    _usage_local.input_tokens = 0
    _usage_local.output_tokens = 0


def _build_client() -> anthropic.Anthropic:
    """Build Anthropic client from environment variables.

    Env vars:
        ZAI_SKILLS_VALIDATOR: API key (preferred). Falls back to ANTHROPIC_SKILLS_VALIDATOR.
        ANTHROPIC_ALTERNATE: Optional custom base URL (e.g. https://api.z.ai/api/anthropic).
        SKILLS_VALIDATOR_MODEL: Optional model override (e.g. glm-5). Default: claude-sonnet-4-6.
        API_TIMEOUT_MS: Optional request timeout in milliseconds. Default: 120000.

    Raises:
        EnvironmentError: If no API key env var is set.
    """
    api_key = os.environ.get("ZAI_SKILLS_VALIDATOR") or os.environ.get("ANTHROPIC_SKILLS_VALIDATOR")
    if not api_key:
        raise EnvironmentError(
            "No API key found. Set ZAI_SKILLS_VALIDATOR (or ANTHROPIC_SKILLS_VALIDATOR) "
            "to run LLM validation."
        )

    timeout_ms = os.environ.get("API_TIMEOUT_MS")
    timeout = float(timeout_ms) / 1000.0 if timeout_ms else _DEFAULT_TIMEOUT

    base_url = os.environ.get("ANTHROPIC_ALTERNATE")

    kwargs: dict = {"api_key": api_key, "timeout": timeout}
    if base_url:
        kwargs["base_url"] = base_url

    return anthropic.Anthropic(**kwargs)


def call_api(prompt: str, system_prompt: str = "", use_thinking: bool = False) -> str:
    """Call the Anthropic API and return the text response.

    Token usage is accumulated in a thread-local counter. Call
    ``reset_accumulated_usage()`` before a run and ``get_accumulated_usage()``
    after to read actual input/output token counts.

    Args:
        prompt: User message content.
        system_prompt: Optional system prompt. Applied with cache_control:ephemeral
            when non-empty to enable prompt caching on repeated calls.
        use_thinking: If True, enable extended thinking (Discovery stage only).
            Thinking blocks are discarded; only text blocks are returned.

    Returns:
        Text content of the model response.

    Raises:
        EnvironmentError: If no API key env var is set.
        ImportError: If anthropic package is not installed (raised at import time).
    """
    client = _build_client()

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
        response = client.beta.messages.create(betas=[_THINKING_BETA], **kwargs)
    else:
        response = client.messages.create(**kwargs)

    try:
        _usage_local.input_tokens = (
            getattr(_usage_local, "input_tokens", 0) + response.usage.input_tokens
        )
        _usage_local.output_tokens = (
            getattr(_usage_local, "output_tokens", 0) + response.usage.output_tokens
        )
    except AttributeError:
        pass

    return "".join(block.text for block in response.content if block.type == "text")
