"""Tests for KnowledgeFactory — all 5 modes plus timeout and logging."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from wfc.scripts.knowledge.factory import (
    DegradedRetriever,
    KnowledgeComponents,
    KnowledgeFactory,
)


@pytest.fixture(autouse=True)
def _reset_cached_health():
    """Reset class-level cached health between tests."""
    KnowledgeFactory._cached_health = None
    yield
    KnowledgeFactory._cached_health = None


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Remove knowledge env vars so tests start clean."""
    monkeypatch.delenv("WFC_KNOWLEDGE_URL", raising=False)
    monkeypatch.delenv("WFC_KNOWLEDGE_TOKEN", raising=False)
    monkeypatch.delenv("WFC_KNOWLEDGE_TIMEOUT", raising=False)


@patch("wfc.scripts.knowledge.factory.KnowledgeFactory._create_remote")
@patch("wfc.scripts.knowledge.remote.KnowledgeHTTPConfig")
def test_remote_mode(mock_config_cls, mock_create_remote, monkeypatch):
    """WFC_KNOWLEDGE_URL set, server reachable -> remote components."""
    monkeypatch.setenv("WFC_KNOWLEDGE_URL", "http://knowledge:8000")
    monkeypatch.setenv("WFC_KNOWLEDGE_TOKEN", "tok123")

    mock_config = MagicMock()
    mock_config_cls.return_value = mock_config

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "ok", "api_version": 1}
    mock_config.client.get.return_value = mock_resp

    expected = KnowledgeComponents(
        retriever=MagicMock(),
        writer=MagicMock(),
        rag_engine=MagicMock(),
        mode="remote",
    )
    mock_create_remote.return_value = expected

    result = KnowledgeFactory.create()

    assert result.mode == "remote"
    mock_config.client.get.assert_called_once()
    mock_resp.raise_for_status.assert_called_once()
    mock_create_remote.assert_called_once_with(mock_config, "default")


@patch("wfc.scripts.knowledge.factory.KnowledgeFactory._create_local")
def test_local_mode_unset(mock_create_local):
    """No WFC_KNOWLEDGE_URL -> local components, no HTTP calls."""
    expected = KnowledgeComponents(
        retriever=MagicMock(), writer=MagicMock(), rag_engine=MagicMock(), mode="local"
    )
    mock_create_local.return_value = expected

    result = KnowledgeFactory.create()

    assert result.mode == "local"
    mock_create_local.assert_called_once_with("default")


@patch("wfc.scripts.knowledge.factory.KnowledgeFactory._create_local")
def test_local_fallback_same_provider(mock_create_local):
    """URL set, health check fails, cached health has same provider -> full local."""
    KnowledgeFactory._cached_health = {"embedding_provider": "TfidfEmbeddings"}

    expected = KnowledgeComponents(
        retriever=MagicMock(), writer=MagicMock(), rag_engine=MagicMock(), mode="local"
    )
    mock_create_local.return_value = expected

    with patch("wfc.scripts.knowledge.embeddings.get_embedding_provider") as mock_get_embed:
        mock_provider = MagicMock()
        type(mock_provider).__name__ = "TfidfEmbeddings"
        mock_get_embed.return_value = mock_provider

        result = KnowledgeFactory._create_fallback("default", "http://knowledge:8000")

    assert result.mode == "local"
    mock_create_local.assert_called_once_with("default")


def test_degraded_mode_embedding_mismatch():
    """URL set, health check fails, cached health has different provider -> degraded."""
    KnowledgeFactory._cached_health = {
        "embedding_provider": "SentenceTransformerEmbeddings",
    }

    with patch("wfc.scripts.knowledge.embeddings.get_embedding_provider") as mock_get_embed:
        mock_provider = MagicMock()
        type(mock_provider).__name__ = "TfidfEmbeddings"
        mock_get_embed.return_value = mock_provider

        result = KnowledgeFactory._create_fallback("default", "http://knowledge:8000")

    assert result.mode == "degraded"
    assert isinstance(result.retriever, DegradedRetriever)
    assert result.retriever.retrieve("security", "diff content") == []


@patch("wfc.scripts.knowledge.factory.KnowledgeFactory._create_local")
def test_no_cached_health_full_local(mock_create_local):
    """URL set, health check fails, no cached health -> full local (NOT degraded)."""
    expected = KnowledgeComponents(
        retriever=MagicMock(), writer=MagicMock(), rag_engine=MagicMock(), mode="local"
    )
    mock_create_local.return_value = expected

    result = KnowledgeFactory._create_fallback("default", "http://knowledge:8000")

    assert result.mode == "local"
    mock_create_local.assert_called_once_with("default")


@patch("wfc.scripts.knowledge.remote.KnowledgeHTTPConfig")
def test_health_timeout_configurable(mock_config_cls, monkeypatch):
    """Verify timeout is read from WFC_KNOWLEDGE_TIMEOUT env var."""
    monkeypatch.setenv("WFC_KNOWLEDGE_URL", "http://knowledge:8000")
    monkeypatch.setenv("WFC_KNOWLEDGE_TIMEOUT", "5.0")

    mock_config = MagicMock()
    mock_config_cls.return_value = mock_config

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "ok"}
    mock_config.client.get.return_value = mock_resp

    with patch("wfc.scripts.knowledge.factory.KnowledgeFactory._create_remote") as mock_remote:
        mock_remote.return_value = KnowledgeComponents(
            retriever=MagicMock(),
            writer=MagicMock(),
            rag_engine=MagicMock(),
            mode="remote",
        )
        KnowledgeFactory.create()

    mock_config.client.get.assert_called_once_with("/v1/knowledge/health", timeout=5.0)


@patch("wfc.scripts.knowledge.factory.KnowledgeFactory._create_local")
def test_mode_logging_local(mock_create_local, caplog):
    """Verify log message for local mode."""
    mock_create_local.return_value = KnowledgeComponents(
        retriever=MagicMock(), writer=MagicMock(), rag_engine=MagicMock(), mode="local"
    )

    with caplog.at_level(logging.INFO, logger="wfc.scripts.knowledge.factory"):
        KnowledgeFactory.create()

    assert "WFC_KNOWLEDGE_URL not set" in caplog.text


@patch("wfc.scripts.knowledge.remote.KnowledgeHTTPConfig")
def test_mode_logging_remote(mock_config_cls, monkeypatch, caplog):
    """Verify log message for remote mode."""
    monkeypatch.setenv("WFC_KNOWLEDGE_URL", "http://knowledge:8000")

    mock_config = MagicMock()
    mock_config_cls.return_value = mock_config
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "ok"}
    mock_config.client.get.return_value = mock_resp

    with (
        patch("wfc.scripts.knowledge.factory.KnowledgeFactory._create_remote") as mock_remote,
        caplog.at_level(logging.INFO, logger="wfc.scripts.knowledge.factory"),
    ):
        mock_remote.return_value = KnowledgeComponents(
            retriever=MagicMock(),
            writer=MagicMock(),
            rag_engine=MagicMock(),
            mode="remote",
        )
        KnowledgeFactory.create()

    assert "knowledge: remote" in caplog.text


def test_mode_logging_degraded(caplog):
    """Verify log message for degraded mode."""
    KnowledgeFactory._cached_health = {"embedding_provider": "SentenceTransformerEmbeddings"}

    with (
        patch("wfc.scripts.knowledge.embeddings.get_embedding_provider") as mock_get_embed,
        caplog.at_level(logging.ERROR, logger="wfc.scripts.knowledge.factory"),
    ):
        mock_provider = MagicMock()
        type(mock_provider).__name__ = "TfidfEmbeddings"
        mock_get_embed.return_value = mock_provider

        KnowledgeFactory._create_fallback("default", "http://knowledge:8000")

    assert "embedding mismatch" in caplog.text


def test_degraded_retriever_returns_empty():
    """DegradedRetriever.retrieve() always returns []."""
    r = DegradedRetriever()
    assert r.retrieve("security", "some diff") == []
    assert r.format_knowledge_section([], 500) == ""
