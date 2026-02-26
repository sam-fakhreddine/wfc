"""Tests for api_client.py — Anthropic SDK wrapper for wfc-skill-validator-llm."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _make_text_block(text: str):
    """Return a mock content block with type='text' and a .text attribute."""
    block = mock.MagicMock()
    block.type = "text"
    block.text = text
    return block


def _make_thinking_block(summary: str):
    """Return a mock content block with type='thinking'."""
    block = mock.MagicMock()
    block.type = "thinking"
    block.thinking = summary
    return block


def _make_response(*blocks):
    """Return a mock Anthropic Messages response with the given content blocks."""
    response = mock.MagicMock()
    response.content = list(blocks)
    return response


class TestMissingEnvVar:
    def test_missing_env_var_raises_environment_error(self):
        """EnvironmentError is raised when ANTHROPIC_SKILLS_VALIDATOR is not set."""
        from wfc.scripts.orchestrators.skill_validator_llm import api_client

        with mock.patch.dict("os.environ", {}, clear=True):
            env = {
                k: v
                for k, v in __import__("os").environ.items()
                if k != "ANTHROPIC_SKILLS_VALIDATOR"
            }
            with mock.patch.dict("os.environ", env, clear=True):
                with pytest.raises(
                    EnvironmentError, match="ANTHROPIC_SKILLS_VALIDATOR env var not set"
                ):
                    api_client.call_api("hello")

    def test_error_message_contains_export_hint(self):
        """EnvironmentError message mentions exporting the API key."""
        from wfc.scripts.orchestrators.skill_validator_llm import api_client

        import os

        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_SKILLS_VALIDATOR"}
        with mock.patch.dict("os.environ", env, clear=True):
            with pytest.raises(EnvironmentError, match="Export your Anthropic API key"):
                api_client.call_api("hello")


class TestCallApiBasic:
    def test_call_api_basic(self):
        """call_api builds the correct messages payload and returns text."""
        from wfc.scripts.orchestrators.skill_validator_llm import api_client

        response = _make_response(_make_text_block("Hello from the model"))

        with mock.patch.dict("os.environ", {"ANTHROPIC_SKILLS_VALIDATOR": "test-key"}):
            with mock.patch(
                "wfc.scripts.orchestrators.skill_validator_llm.api_client.anthropic.Anthropic"
            ) as MockClient:
                instance = MockClient.return_value
                instance.messages.create.return_value = response

                result = api_client.call_api("Test prompt")

        assert result == "Hello from the model"
        MockClient.assert_called_once_with(
            api_key="test-key",  # pragma: allowlist secret
            timeout=120.0,
        )
        call_kwargs = instance.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-sonnet-4-6"
        assert call_kwargs["messages"] == [{"role": "user", "content": "Test prompt"}]

    def test_model_is_sonnet(self):
        """The model is hardcoded to claude-sonnet-4-6."""
        from wfc.scripts.orchestrators.skill_validator_llm import api_client

        response = _make_response(_make_text_block("ok"))

        with mock.patch.dict("os.environ", {"ANTHROPIC_SKILLS_VALIDATOR": "test-key"}):
            with mock.patch(
                "wfc.scripts.orchestrators.skill_validator_llm.api_client.anthropic.Anthropic"
            ) as MockClient:
                instance = MockClient.return_value
                instance.messages.create.return_value = response

                api_client.call_api("prompt")

        call_kwargs = instance.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-sonnet-4-6"

    def test_max_tokens_is_4096(self):
        """max_tokens is set to 4096."""
        from wfc.scripts.orchestrators.skill_validator_llm import api_client

        response = _make_response(_make_text_block("ok"))

        with mock.patch.dict("os.environ", {"ANTHROPIC_SKILLS_VALIDATOR": "test-key"}):
            with mock.patch(
                "wfc.scripts.orchestrators.skill_validator_llm.api_client.anthropic.Anthropic"
            ) as MockClient:
                instance = MockClient.return_value
                instance.messages.create.return_value = response

                api_client.call_api("prompt")

        call_kwargs = instance.messages.create.call_args[1]
        assert call_kwargs["max_tokens"] == 4096


class TestCacheControl:
    def test_cache_control_applied_to_system_prompt(self):
        """When system_prompt is non-empty, the system block has cache_control:ephemeral."""
        from wfc.scripts.orchestrators.skill_validator_llm import api_client

        response = _make_response(_make_text_block("result"))

        with mock.patch.dict("os.environ", {"ANTHROPIC_SKILLS_VALIDATOR": "test-key"}):
            with mock.patch(
                "wfc.scripts.orchestrators.skill_validator_llm.api_client.anthropic.Anthropic"
            ) as MockClient:
                instance = MockClient.return_value
                instance.messages.create.return_value = response

                api_client.call_api("prompt", system_prompt="You are an expert.")

        call_kwargs = instance.messages.create.call_args[1]
        assert "system" in call_kwargs
        system_blocks = call_kwargs["system"]
        assert len(system_blocks) == 1
        block = system_blocks[0]
        assert block["type"] == "text"
        assert block["text"] == "You are an expert."
        assert block["cache_control"] == {"type": "ephemeral"}

    def test_no_cache_control_without_system_prompt(self):
        """When system_prompt is empty, no system key is included in the request."""
        from wfc.scripts.orchestrators.skill_validator_llm import api_client

        response = _make_response(_make_text_block("result"))

        with mock.patch.dict("os.environ", {"ANTHROPIC_SKILLS_VALIDATOR": "test-key"}):
            with mock.patch(
                "wfc.scripts.orchestrators.skill_validator_llm.api_client.anthropic.Anthropic"
            ) as MockClient:
                instance = MockClient.return_value
                instance.messages.create.return_value = response

                api_client.call_api("prompt")

        call_kwargs = instance.messages.create.call_args[1]
        assert "system" not in call_kwargs

    def test_empty_string_system_prompt_omits_system_key(self):
        """Explicitly passing system_prompt='' omits the system key."""
        from wfc.scripts.orchestrators.skill_validator_llm import api_client

        response = _make_response(_make_text_block("result"))

        with mock.patch.dict("os.environ", {"ANTHROPIC_SKILLS_VALIDATOR": "test-key"}):
            with mock.patch(
                "wfc.scripts.orchestrators.skill_validator_llm.api_client.anthropic.Anthropic"
            ) as MockClient:
                instance = MockClient.return_value
                instance.messages.create.return_value = response

                api_client.call_api("prompt", system_prompt="")

        call_kwargs = instance.messages.create.call_args[1]
        assert "system" not in call_kwargs


class TestExtendedThinking:
    def test_extended_thinking_params(self):
        """When use_thinking=True, beta.messages.create is used with betas and thinking."""
        from wfc.scripts.orchestrators.skill_validator_llm import api_client

        response = _make_response(_make_text_block("thinking result"))

        with mock.patch.dict("os.environ", {"ANTHROPIC_SKILLS_VALIDATOR": "test-key"}):
            with mock.patch(
                "wfc.scripts.orchestrators.skill_validator_llm.api_client.anthropic.Anthropic"
            ) as MockClient:
                instance = MockClient.return_value
                instance.beta.messages.create.return_value = response

                api_client.call_api("prompt", use_thinking=True)

        call_kwargs = instance.beta.messages.create.call_args[1]
        assert call_kwargs["thinking"] == {"type": "enabled", "budget_tokens": 8000}
        assert "interleaved-thinking-2025-05-14" in call_kwargs["betas"]

    def test_no_thinking_params_by_default(self):
        """By default (use_thinking=False), thinking and betas are absent."""
        from wfc.scripts.orchestrators.skill_validator_llm import api_client

        response = _make_response(_make_text_block("normal result"))

        with mock.patch.dict("os.environ", {"ANTHROPIC_SKILLS_VALIDATOR": "test-key"}):
            with mock.patch(
                "wfc.scripts.orchestrators.skill_validator_llm.api_client.anthropic.Anthropic"
            ) as MockClient:
                instance = MockClient.return_value
                instance.messages.create.return_value = response

                api_client.call_api("prompt")

        call_kwargs = instance.messages.create.call_args[1]
        assert "thinking" not in call_kwargs
        assert "betas" not in call_kwargs

    def test_thinking_blocks_discarded(self):
        """Thinking-type content blocks are discarded; only text blocks are returned."""
        from wfc.scripts.orchestrators.skill_validator_llm import api_client

        thinking_block = _make_thinking_block("internal reasoning here")
        text_block = _make_text_block("final answer")
        response = _make_response(thinking_block, text_block)

        with mock.patch.dict("os.environ", {"ANTHROPIC_SKILLS_VALIDATOR": "test-key"}):
            with mock.patch(
                "wfc.scripts.orchestrators.skill_validator_llm.api_client.anthropic.Anthropic"
            ) as MockClient:
                instance = MockClient.return_value
                instance.beta.messages.create.return_value = response

                result = api_client.call_api("prompt", use_thinking=True)

        assert result == "final answer"
        assert "internal reasoning" not in result

    def test_multiple_text_blocks_concatenated(self):
        """Multiple text blocks are concatenated in order."""
        from wfc.scripts.orchestrators.skill_validator_llm import api_client

        block1 = _make_text_block("Hello ")
        block2 = _make_text_block("world")
        response = _make_response(block1, block2)

        with mock.patch.dict("os.environ", {"ANTHROPIC_SKILLS_VALIDATOR": "test-key"}):
            with mock.patch(
                "wfc.scripts.orchestrators.skill_validator_llm.api_client.anthropic.Anthropic"
            ) as MockClient:
                instance = MockClient.return_value
                instance.messages.create.return_value = response

                result = api_client.call_api("prompt")

        assert result == "Hello world"


class TestFixtureFiles:
    """Verify fixture files exist and have expected content."""

    def test_discovery_fixture_exists(self):
        path = FIXTURES_DIR / "discovery-response.txt"
        assert path.exists(), f"Missing fixture: {path}"
        content = path.read_text()
        assert "Positive Triggers" in content
        assert "Negative Triggers" in content

    def test_logic_fixture_exists(self):
        path = FIXTURES_DIR / "logic-response.txt"
        assert path.exists(), f"Missing fixture: {path}"
        content = path.read_text()
        assert "Hallucination Risks" in content

    def test_edge_case_fixture_exists(self):
        path = FIXTURES_DIR / "edge-case-response.txt"
        assert path.exists(), f"Missing fixture: {path}"
        content = path.read_text()
        assert "Edge Cases" in content
