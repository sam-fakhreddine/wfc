"""Tests for TASK-010: wfc metrics CLI command."""

from __future__ import annotations

import json

import pytest

import wfc.observability as obs
from wfc.observability.cli import cmd_metrics


@pytest.fixture(autouse=True)
def _setup_obs(monkeypatch):
    obs.reset()
    monkeypatch.setenv("WFC_OBSERVABILITY_PROVIDERS", "memory")
    obs.init()
    yield
    obs.reset()


class TestCmdMetrics:
    """Test wfc metrics command."""

    def test_json_output(self, capsys):
        registry = obs.get_registry()
        registry.counter("test.counter").increment(5)
        registry.gauge("test.gauge").set(42)

        cmd_metrics(format="json")
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "metrics" in data
        names = {m["name"] for m in data["metrics"]}
        assert "test.counter" in names
        assert "test.gauge" in names

    def test_table_output(self, capsys):
        registry = obs.get_registry()
        registry.counter("reviews.completed").increment(3)

        cmd_metrics(format="table")
        captured = capsys.readouterr()
        assert "reviews.completed" in captured.out
        assert "3" in captured.out

    def test_empty_metrics(self, capsys):
        cmd_metrics(format="json")
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["metrics"] == []
