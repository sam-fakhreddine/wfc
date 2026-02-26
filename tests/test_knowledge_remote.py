"""Tests for remote knowledge clients (Liskov substitution verification).

Verifies that RemoteRetriever, RemoteWriter, and RemoteRAGEngine match the
public interface of their local counterparts and handle HTTP correctly.
"""

from __future__ import annotations

import hashlib
import inspect
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from wfc.scripts.knowledge.chunker import KnowledgeChunk
from wfc.scripts.knowledge.knowledge_writer import KnowledgeWriter, LearningEntry
from wfc.scripts.knowledge.rag_engine import RAGEngine, RetrievalResult
from wfc.scripts.knowledge.remote import (
    EXPECTED_API_VERSION,
    KnowledgeHTTPConfig,
    KnowledgeServerError,
    KnowledgeVersionError,
    RemoteRAGEngine,
    RemoteRetriever,
    RemoteWriter,
)
from wfc.scripts.knowledge.retriever import KnowledgeRetriever, TaggedResult


def _make_config(mock_client: MagicMock | None = None) -> KnowledgeHTTPConfig:
    """Create a KnowledgeHTTPConfig with a pre-injected mock client."""
    cfg = KnowledgeHTTPConfig(
        server_url="http://localhost:9090",
        auth_token="test-token-abc",
        machine_id="deadbeef",
    )
    if mock_client is not None:
        cfg._client = mock_client
    cfg._api_version_checked = True
    return cfg


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    """Build a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status.return_value = None
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
    return resp


class TestSignatureCompatibility:
    """Verify remote classes match local public method signatures."""

    @staticmethod
    def _public_methods(cls: type) -> dict[str, inspect.Signature]:
        return {
            name: inspect.signature(getattr(cls, name))
            for name in sorted(dir(cls))
            if not name.startswith("_") and callable(getattr(cls, name))
        }

    def test_remote_retriever_matches_knowledge_retriever(self) -> None:
        local = self._public_methods(KnowledgeRetriever)
        remote = self._public_methods(RemoteRetriever)

        target_methods = ["retrieve", "format_knowledge_section", "extract_diff_signals"]
        for method_name in target_methods:
            assert method_name in local, f"Local missing {method_name}"
            assert method_name in remote, f"Remote missing {method_name}"

            local_sig = local[method_name]
            remote_sig = remote[method_name]

            local_params = [
                (name, p.default, p.kind)
                for name, p in local_sig.parameters.items()
                if name != "self"
            ]
            remote_params = [
                (name, p.default, p.kind)
                for name, p in remote_sig.parameters.items()
                if name != "self"
            ]
            assert local_params == remote_params, (
                f"Signature mismatch for {method_name}: "
                f"local={local_params} vs remote={remote_params}"
            )

    def test_remote_writer_matches_knowledge_writer(self) -> None:
        local = self._public_methods(KnowledgeWriter)
        remote = self._public_methods(RemoteWriter)

        target_methods = [
            "append_entries",
            "promote_to_global",
            "extract_learnings",
            "prune_old_entries",
            "check_promotion_eligibility",
        ]
        for method_name in target_methods:
            assert method_name in local, f"Local missing {method_name}"
            assert method_name in remote, f"Remote missing {method_name}"

            local_sig = local[method_name]
            remote_sig = remote[method_name]

            local_params = [
                (name, p.default, p.kind)
                for name, p in local_sig.parameters.items()
                if name != "self"
            ]
            remote_params = [
                (name, p.default, p.kind)
                for name, p in remote_sig.parameters.items()
                if name != "self"
            ]
            assert local_params == remote_params, (
                f"Signature mismatch for {method_name}: "
                f"local={local_params} vs remote={remote_params}"
            )

    def test_remote_rag_engine_matches_rag_engine(self) -> None:
        local = self._public_methods(RAGEngine)
        remote = self._public_methods(RemoteRAGEngine)

        target_methods = ["index", "index_all", "query", "needs_reindex"]
        for method_name in target_methods:
            assert method_name in local, f"Local missing {method_name}"
            assert method_name in remote, f"Remote missing {method_name}"

            local_sig = local[method_name]
            remote_sig = remote[method_name]

            local_params = [
                (name, p.default, p.kind)
                for name, p in local_sig.parameters.items()
                if name != "self"
            ]
            remote_params = [
                (name, p.default, p.kind)
                for name, p in remote_sig.parameters.items()
                if name != "self"
            ]
            assert local_params == remote_params, (
                f"Signature mismatch for {method_name}: "
                f"local={local_params} vs remote={remote_params}"
            )


class TestRemoteRetriever:
    def test_retrieve_round_trip(self) -> None:
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = _mock_response(
            {
                "results": [
                    {
                        "text": "Always validate input",
                        "score": 0.92,
                        "reviewer_id": "security",
                        "section": "patterns_found",
                        "date": "2026-01-15",
                        "source": "review-123",
                        "chunk_id": "abc123",
                        "tier": "project",
                    }
                ]
            }
        )

        cfg = _make_config(mock_client)
        retriever = RemoteRetriever(cfg, project="myproj")

        diff = "--- a/foo.py\n+++ b/foo.py\n+def validate_input():\n"
        results = retriever.retrieve("security", diff, top_k=3)

        assert len(results) == 1
        assert isinstance(results[0], TaggedResult)
        assert results[0].chunk.text == "Always validate input"
        assert results[0].score == 0.92
        assert results[0].source_tier == "project"
        assert results[0].chunk.reviewer_id == "security"

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/knowledge/chunks/query"
        payload = call_args[1]["json"]
        assert payload["project"] == "myproj"
        assert payload["reviewer_id"] == "security"
        assert payload["top_k"] == 3

    def test_extract_diff_signals_is_local(self) -> None:
        """extract_diff_signals should NOT make any HTTP calls."""
        cfg = _make_config(None)
        retriever = RemoteRetriever(cfg, project="test")

        diff = "--- a/utils.py\n+++ b/utils.py\n+import os\n+def helper():\n"
        signals = retriever.extract_diff_signals(diff)

        assert "utils.py" in signals
        assert "helper" in signals
        assert "os" in signals

    def test_format_knowledge_section_is_local(self) -> None:
        """format_knowledge_section should NOT make any HTTP calls."""
        cfg = _make_config(None)
        retriever = RemoteRetriever(cfg, project="test")

        chunk = KnowledgeChunk(
            text="Test knowledge",
            reviewer_id="security",
            section="patterns_found",
            date="2026-01-01",
            source="test",
            chunk_id="abc",
        )
        results = [TaggedResult(chunk=chunk, score=0.9, source_tier="global")]
        output = retriever.format_knowledge_section(results, token_budget=500)

        assert "## Relevant Knowledge" in output
        assert "[global]" in output
        assert "Test knowledge" in output


class TestRemoteWriter:
    def test_append_entries_with_machine_id(self) -> None:
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = _mock_response({"appended": 2})

        cfg = _make_config(mock_client)
        writer = RemoteWriter(cfg, project="proj1")

        entries = [
            LearningEntry(
                text="Never use eval()",
                section="patterns_found",
                reviewer_id="security",
                source="review-1",
            ),
            LearningEntry(
                text="Sanitize SQL inputs",
                section="patterns_found",
                reviewer_id="security",
                source="review-2",
            ),
        ]

        result = writer.append_entries(entries)
        assert result == {"security": 2}

        call_args = mock_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["machine_id"] == "deadbeef"
        assert payload["project"] == "proj1"
        assert payload["reviewer_id"] == "security"
        assert len(payload["entries"]) == 2

    def test_append_entries_groups_by_reviewer(self) -> None:
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = _mock_response({"appended": 1})

        cfg = _make_config(mock_client)
        writer = RemoteWriter(cfg, project="proj1")

        entries = [
            LearningEntry(
                text="Entry A",
                section="patterns_found",
                reviewer_id="security",
                source="src",
            ),
            LearningEntry(
                text="Entry B",
                section="patterns_found",
                reviewer_id="performance",
                source="src",
            ),
        ]

        result = writer.append_entries(entries)
        assert "security" in result
        assert "performance" in result
        assert mock_client.post.call_count == 2

    def test_promote_to_global(self) -> None:
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = _mock_response({"promoted": True})

        cfg = _make_config(mock_client)
        writer = RemoteWriter(cfg, project="proj1")

        entry = LearningEntry(
            text="Important pattern",
            section="patterns_found",
            reviewer_id="security",
            source="review-1",
        )

        assert writer.promote_to_global(entry, "myproject") is True

    def test_extract_learnings_is_local(self) -> None:
        """extract_learnings should NOT make HTTP calls."""
        cfg = _make_config(None)
        writer = RemoteWriter(cfg, project="test")

        findings = [
            {"text": "SQL injection found", "severity": 9.5, "confidence": 9.0},
            {"text": "Minor style issue", "severity": 2.0, "confidence": 5.0},
        ]

        learnings = writer.extract_learnings(findings, "security", "review-1")
        assert len(learnings) >= 1
        assert learnings[0].section == "incidents_prevented"


class TestRemoteRAGEngine:
    def test_index_posts_file_content(self, tmp_path: Path) -> None:
        knowledge_file = tmp_path / "KNOWLEDGE.md"
        knowledge_file.write_text("# Test Knowledge\n\n## Patterns Found\n- entry\n")

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = _mock_response({"chunks_indexed": 3})

        cfg = _make_config(mock_client)
        engine = RemoteRAGEngine(cfg, project="proj1")

        count = engine.index("security", knowledge_file)
        assert count == 3

        call_args = mock_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["knowledge_md"].startswith("# Test Knowledge")
        assert payload["machine_id"] == "deadbeef"
        assert payload["reviewer_id"] == "security"

    def test_index_all_iterates_reviewers(self, tmp_path: Path) -> None:
        for name in ["security", "performance"]:
            d = tmp_path / name
            d.mkdir()
            (d / "KNOWLEDGE.md").write_text(f"# {name}\n")

        (tmp_path / "README.md").write_text("skip me")

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = _mock_response({"chunks_indexed": 1})

        cfg = _make_config(mock_client)
        engine = RemoteRAGEngine(cfg, project="proj1")

        result = engine.index_all(tmp_path)
        assert "security" in result
        assert "performance" in result
        assert len(result) == 2

    def test_index_all_returns_empty_when_no_dir(self) -> None:
        cfg = _make_config(None)
        engine = RemoteRAGEngine(cfg, project="proj1")
        assert engine.index_all(None) == {}

    def test_query_round_trip(self) -> None:
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = _mock_response(
            {
                "results": [
                    {
                        "text": "Use parameterized queries",
                        "score": 0.88,
                        "reviewer_id": "security",
                        "section": "patterns_found",
                        "date": "2026-02-01",
                        "source": "review-5",
                        "chunk_id": "xyz789",
                    }
                ]
            }
        )

        cfg = _make_config(mock_client)
        engine = RemoteRAGEngine(cfg, project="proj1")

        results = engine.query("security", "SQL injection", top_k=3)
        assert len(results) == 1
        assert isinstance(results[0], RetrievalResult)
        assert results[0].chunk.text == "Use parameterized queries"
        assert results[0].score == 0.88

    def test_needs_reindex_matching_hash(self, tmp_path: Path) -> None:
        knowledge_file = tmp_path / "KNOWLEDGE.md"
        content = "# Knowledge\n"
        knowledge_file.write_text(content)
        expected_hash = hashlib.sha256(content.encode()).hexdigest()

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = _mock_response({"file_hash": expected_hash})

        cfg = _make_config(mock_client)
        engine = RemoteRAGEngine(cfg, project="proj1")

        assert engine.needs_reindex("security", knowledge_file) is False

    def test_needs_reindex_different_hash(self, tmp_path: Path) -> None:
        knowledge_file = tmp_path / "KNOWLEDGE.md"
        knowledge_file.write_text("# Knowledge v2\n")

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = _mock_response({"file_hash": "oldhash123"})

        cfg = _make_config(mock_client)
        engine = RemoteRAGEngine(cfg, project="proj1")

        assert engine.needs_reindex("security", knowledge_file) is True

    def test_needs_reindex_server_error_returns_true(self, tmp_path: Path) -> None:
        knowledge_file = tmp_path / "KNOWLEDGE.md"
        knowledge_file.write_text("# Knowledge\n")

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.TimeoutException("timeout")

        cfg = _make_config(mock_client)
        engine = RemoteRAGEngine(cfg, project="proj1")

        assert engine.needs_reindex("security", knowledge_file) is True


class TestHTTPErrorHandling:
    def test_timeout_raises_knowledge_server_error(self) -> None:
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.side_effect = httpx.TimeoutException("timed out")

        cfg = _make_config(mock_client)

        with pytest.raises(KnowledgeServerError, match="timed out"):
            cfg._post("/v1/test", {})

    def test_http_status_error_raises_knowledge_server_error(self) -> None:
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = _mock_response({}, status_code=500)

        cfg = _make_config(mock_client)

        with pytest.raises(KnowledgeServerError, match="Server error 500"):
            cfg._post("/v1/test", {})

    def test_get_timeout_raises_knowledge_server_error(self) -> None:
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.TimeoutException("timed out")

        cfg = _make_config(mock_client)

        with pytest.raises(KnowledgeServerError, match="timed out"):
            cfg._get("/v1/test")


class TestAuthAndConfig:
    def test_auth_token_in_headers(self) -> None:
        cfg = KnowledgeHTTPConfig(
            server_url="http://localhost:9090",
            auth_token="secret-token-xyz",
            machine_id="deadbeef",
        )
        client = cfg.client
        assert client.headers["Authorization"] == "Bearer secret-token-xyz"
        assert client.headers["Content-Type"] == "application/json"
        cfg.close()

    def test_close_cleans_up_client(self) -> None:
        mock_client = MagicMock(spec=httpx.Client)
        cfg = _make_config(mock_client)
        cfg.close()
        mock_client.close.assert_called_once()
        assert cfg._client is None

    def test_close_is_idempotent(self) -> None:
        cfg = _make_config(None)
        cfg.close()
        cfg.close()


class TestAPIVersion:
    def test_version_mismatch_raises_error(self) -> None:
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = _mock_response({"api_version": 2})

        cfg = KnowledgeHTTPConfig(
            server_url="http://localhost:9090",
            auth_token="tok",
            machine_id="deadbeef",
        )
        cfg._client = mock_client

        with pytest.raises(KnowledgeVersionError, match="version 2"):
            cfg.check_api_version()

    def test_version_match_succeeds(self) -> None:
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = _mock_response(
            {"api_version": EXPECTED_API_VERSION, "status": "healthy"}
        )

        cfg = KnowledgeHTTPConfig(
            server_url="http://localhost:9090",
            auth_token="tok",
            machine_id="deadbeef",
        )
        cfg._client = mock_client

        data = cfg.check_api_version()
        assert data["status"] == "healthy"

    def test_version_check_cached(self) -> None:
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = _mock_response({"api_version": EXPECTED_API_VERSION})

        cfg = KnowledgeHTTPConfig(
            server_url="http://localhost:9090",
            auth_token="tok",
            machine_id="deadbeef",
        )
        cfg._client = mock_client

        cfg.check_api_version()
        cfg.check_api_version()
        assert mock_client.get.call_count == 1

    def test_health_check_failure_raises_server_error(self) -> None:
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.ConnectError("refused")

        cfg = KnowledgeHTTPConfig(
            server_url="http://localhost:9090",
            auth_token="tok",
            machine_id="deadbeef",
        )
        cfg._client = mock_client

        with pytest.raises(KnowledgeServerError, match="Health check failed"):
            cfg.check_api_version()
