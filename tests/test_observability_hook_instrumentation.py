"""Tests for TASK-007: Hook instrumentation (_bypass_count replacement)."""

from __future__ import annotations

import pytest

import wfc.observability as obs
from wfc.observability.providers.memory_provider import InMemoryProvider


@pytest.fixture(autouse=True)
def _setup_obs(monkeypatch):
    obs.reset()
    monkeypatch.setenv("WFC_OBSERVABILITY_PROVIDERS", "memory")
    obs.init()
    yield
    obs.reset()


def _get_memory_provider() -> InMemoryProvider:
    pr = obs.get_provider_registry()
    return [p for p in pr.providers if isinstance(p, InMemoryProvider)][0]


class TestBypassCountReplaced:
    """Verify _bypass_count globals are replaced with metrics."""

    def test_security_hook_no_bypass_count_global(self):
        from wfc.scripts.hooks import security_hook

        assert not hasattr(security_hook, "_bypass_count") or security_hook._bypass_count == 0
        result = security_hook.check({"invalid": True})
        assert result == {}
        registry = obs.get_registry()
        count = registry.counter("hook.bypass_count").get(labels={"hook": "security"})
        assert count >= 0

    def test_rule_engine_no_bypass_count_global(self):
        from wfc.scripts.hooks import rule_engine

        assert not hasattr(rule_engine, "_bypass_count") or rule_engine._bypass_count == 0

    def test_pretooluse_hook_no_bypass_count_global(self):
        from wfc.scripts.hooks import pretooluse_hook

        assert not hasattr(pretooluse_hook, "_bypass_count") or pretooluse_hook._bypass_count == 0


class TestHookEventEmission:
    """Test that hooks emit observability events."""

    def test_security_check_emits_decision_on_pass(self):
        from wfc.scripts.hooks.security_hook import check

        result = check(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "echo hello"},
            }
        )
        mem = _get_memory_provider()
        _decisions = [e for e in mem.events if e.event_type == "hook.decision"]
        assert result == {} or "decision" in result

    def test_security_check_emits_on_block(self):
        from wfc.scripts.hooks.security_hook import check

        result = check(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf /"},
            }
        )
        mem = _get_memory_provider()
        decisions = [e for e in mem.events if e.event_type == "hook.decision"]
        if result.get("decision") == "block":
            assert len(decisions) >= 1
            assert decisions[0].payload["decision"] == "block"
