"""
Tests for ModelRouter (TASK-013).

TDD: These tests are written BEFORE the implementation.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from wfc.scripts.skills.review.model_router import ModelRouter


@pytest.fixture()
def default_router():
    """Router loaded from the real model_routing.json config."""
    return ModelRouter()


@pytest.fixture()
def temp_config(tmp_path: Path):
    """Create a temp config file for isolated tests."""
    config = {
        "default": "claude-sonnet-4-5-20250929",
        "reviewers": {
            "security": "claude-opus-4-6",
            "correctness": "claude-sonnet-4-5-20250929",
            "performance": "claude-sonnet-4-5-20250929",
            "maintainability": "claude-haiku-4-5-20251001",
            "reliability": "claude-opus-4-6",
        },
        "validation_cross_check": "claude-haiku-4-5-20251001",
        "auto_routing": {
            "small_diff_lines": 50,
            "large_diff_lines": 500,
            "small_model": "claude-haiku-4-5-20251001",
            "medium_model": "claude-sonnet-4-5-20250929",
            "large_high_stakes_model": "claude-opus-4-6",
            "large_other_model": "claude-sonnet-4-5-20250929",
            "high_stakes_reviewers": ["security", "reliability"],
        },
    }
    config_path = tmp_path / "model_routing.json"
    config_path.write_text(json.dumps(config))
    return config_path


@pytest.fixture()
def router_with_temp_config(temp_config: Path):
    return ModelRouter(config_path=temp_config)



def test_load_default_config(default_router: ModelRouter):
    """Loads real json; security reviewer should map to opus."""
    cfg = default_router._config
    assert cfg.reviewers["security"] == "claude-opus-4-6"


def test_config_missing_returns_defaults(tmp_path: Path):
    """When config file is missing, router still works with built-in defaults."""
    missing = tmp_path / "nonexistent.json"
    router = ModelRouter(config_path=missing)
    assert router._config.default != ""
    # security should still map to some model
    model = router.get_model("security", diff_lines=200)
    assert model != ""



def test_explicit_config_security_opus(router_with_temp_config: ModelRouter):
    """Security reviewer always gets Opus in medium diff range."""
    model = router_with_temp_config.get_model("security", diff_lines=200)
    assert model == "claude-opus-4-6"


def test_explicit_config_maintainability_haiku(router_with_temp_config: ModelRouter):
    """Maintainability (style) reviewer gets Haiku in medium diff range."""
    model = router_with_temp_config.get_model("maintainability", diff_lines=200)
    assert model == "claude-haiku-4-5-20251001"



def test_auto_routing_small_diff(router_with_temp_config: ModelRouter):
    """All reviewers get Haiku for a 20-line diff."""
    for reviewer in ["security", "correctness", "performance", "maintainability", "reliability"]:
        model = router_with_temp_config.get_model(reviewer, diff_lines=20)
        assert model == "claude-haiku-4-5-20251001", (
            f"Expected haiku for {reviewer} on small diff, got {model}"
        )


def test_explicit_overrides_auto_small(router_with_temp_config: ModelRouter):
    """Even security gets small_model on a tiny diff (auto wins over explicit for small diffs)."""
    model = router_with_temp_config.get_model("security", diff_lines=10)
    assert model == "claude-haiku-4-5-20251001"



def test_auto_routing_large_diff_security(router_with_temp_config: ModelRouter):
    """Security (high-stakes) gets Opus on an 800-line diff."""
    model = router_with_temp_config.get_model("security", diff_lines=800)
    assert model == "claude-opus-4-6"


def test_auto_routing_large_diff_maintainability(router_with_temp_config: ModelRouter):
    """Maintainability (not high-stakes) gets Sonnet on an 800-line diff."""
    model = router_with_temp_config.get_model("maintainability", diff_lines=800)
    assert model == "claude-sonnet-4-5-20250929"



def test_auto_routing_medium_uses_explicit(router_with_temp_config: ModelRouter):
    """200-line diff falls in medium range → explicit per-reviewer config applies."""
    # security → opus (explicit)
    assert router_with_temp_config.get_model("security", diff_lines=200) == "claude-opus-4-6"
    assert router_with_temp_config.get_model("maintainability", diff_lines=200) == "claude-haiku-4-5-20251001"
    assert router_with_temp_config.get_model("correctness", diff_lines=200) == "claude-sonnet-4-5-20250929"



def test_fallback_unknown_reviewer(router_with_temp_config: ModelRouter):
    """Unknown reviewer ID returns the default model."""
    model = router_with_temp_config.get_model("unknown_reviewer", diff_lines=200)
    assert model == "claude-sonnet-4-5-20250929"



def test_cross_check_model_is_haiku(router_with_temp_config: ModelRouter):
    """Validation cross-check model should be Haiku (cheap + fast)."""
    model = router_with_temp_config.get_cross_check_model()
    assert model == "claude-haiku-4-5-20251001"



def test_cost_estimate(router_with_temp_config: ModelRouter):
    """Opus should cost more than Haiku for equivalent token usage."""
    opus_cost = router_with_temp_config.estimate_cost(
        "security",
        prompt_tokens=1000,
        completion_tokens=500,
    )
    haiku_cost = router_with_temp_config.estimate_cost(
        "maintainability",
        prompt_tokens=1000,
        completion_tokens=500,
    )
    assert opus_cost > haiku_cost, f"Opus cost {opus_cost} should exceed Haiku cost {haiku_cost}"


def test_cost_estimate_unknown_reviewer_uses_default(router_with_temp_config: ModelRouter):
    """Unknown reviewer falls back to default model for cost estimation."""
    cost = router_with_temp_config.estimate_cost(
        "unknown_reviewer",
        prompt_tokens=1000,
        completion_tokens=500,
    )
    assert cost >= 0.0


def test_cost_estimate_zero_tokens(router_with_temp_config: ModelRouter):
    """Zero tokens yields zero cost."""
    cost = router_with_temp_config.estimate_cost("security", 0, 0)
    assert cost == 0.0
