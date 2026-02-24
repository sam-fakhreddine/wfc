"""Tests for the Knowledge Server API routes."""

from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

TEST_TOKEN = "test-token-123456789012345678901234"


@pytest.fixture(autouse=True)
def _set_knowledge_token(tmp_path, monkeypatch):
    """Set the knowledge token env var and reset cached state for each test."""
    monkeypatch.setenv("WFC_KNOWLEDGE_TOKEN", TEST_TOKEN)

    from wfc.servers.rest_api.knowledge_dependencies import reset_knowledge_token

    reset_knowledge_token()

    from wfc.servers.rest_api.knowledge_routes import _reset_caches

    _reset_caches()

    import wfc.servers.rest_api.knowledge_routes as kr

    monkeypatch.setattr(kr, "DATA_DIR", tmp_path / "data")

    yield

    reset_knowledge_token()
    _reset_caches()


AUTH_HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}"}


@dataclass
class FakeChunk:
    text: str = "test chunk"
    chunk_id: str = "chunk-1"
    reviewer_id: str = "security"
    section: str = "patterns_found"
    date: str = "2026-01-01"
    source: str = "test"


@dataclass
class FakeRetrievalResult:
    chunk: FakeChunk
    score: float


@dataclass
class FakeDriftSignal:
    reviewer_id: str = "security"
    signal_type: str = "stale"
    severity: str = "medium"
    description: str = "Entry is 100 days old"
    file_path: str = "/tmp/test"
    line_range: tuple = (1, 1)


@dataclass
class FakeDriftReport:
    signals: list
    total_entries: int = 10
    stale_count: int = 1
    bloated_count: int = 0
    healthy_count: int = 4
    recommendation: str = "needs_pruning"


def _get_app():
    from wfc.servers.rest_api.main import app

    return app


@pytest.mark.asyncio
async def test_health_no_auth():
    """Health endpoint returns minimal info without auth."""
    app = _get_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/v1/knowledge/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["api_version"] == 1
        assert data["embedding_provider"] == ""
        assert data["chroma_status"] == ""
        assert resp.headers.get("X-WFC-Knowledge-Version") == "1"


@pytest.mark.asyncio
async def test_health_with_auth():
    """Health endpoint returns full diagnostic with auth."""
    app = _get_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/v1/knowledge/health", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["api_version"] == 1
        assert data["chroma_status"] in ("available", "unavailable")
        assert resp.headers.get("X-WFC-Knowledge-Version") == "1"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,path,body",
    [
        (
            "post",
            "/v1/knowledge/chunks/index",
            {"project": "p", "reviewer_id": "security", "knowledge_md": "# test"},
        ),
        (
            "post",
            "/v1/knowledge/chunks/query",
            {"project": "p", "reviewer_id": "security", "query_text": "test"},
        ),
        (
            "post",
            "/v1/knowledge/learnings/append",
            {
                "project": "p",
                "reviewer_id": "security",
                "entries": [{"text": "t", "section": "patterns_found", "source": "s"}],
            },
        ),
        (
            "post",
            "/v1/knowledge/learnings/promote",
            {
                "project": "p",
                "reviewer_id": "security",
                "entry_text": "t",
                "section": "patterns_found",
                "source": "s",
            },
        ),
        ("get", "/v1/knowledge/learnings/security?project=default", None),
        ("post", "/v1/knowledge/drift/analyze", {"project": "p"}),
        ("get", "/v1/knowledge/hash/proj/security", None),
    ],
)
async def test_endpoints_require_auth(method, path, body):
    """All data endpoints return 401 without valid auth."""
    app = _get_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        if method == "get":
            resp = await client.get(path)
        else:
            resp = await client.post(path, json=body)
        assert resp.status_code == 401, f"{method.upper()} {path} should require auth"


@pytest.mark.asyncio
async def test_index_chunks(tmp_path, monkeypatch):
    """Index endpoint indexes content and returns chunk count."""
    mock_engine = MagicMock()
    mock_engine.index.return_value = 5
    mock_engine._hashes = {}

    import wfc.servers.rest_api.knowledge_routes as kr

    monkeypatch.setattr(kr, "DATA_DIR", tmp_path / "data")

    with patch.object(kr, "_get_engine", return_value=mock_engine):
        app = _get_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/v1/knowledge/chunks/index",
                json={
                    "project": "myproj",
                    "reviewer_id": "security",
                    "knowledge_md": "# KNOWLEDGE.md\n\n## Patterns Found\n- test entry",
                },
                headers=AUTH_HEADERS,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["chunks_indexed"] == 5
        assert data["reviewer_id"] == "security"
        assert data["project"] == "myproj"
        assert resp.headers.get("X-WFC-Knowledge-Version") == "1"


@pytest.mark.asyncio
async def test_query_chunks():
    """Query endpoint returns matching chunks."""
    fake_results = [
        FakeRetrievalResult(chunk=FakeChunk(), score=0.95),
    ]

    import wfc.servers.rest_api.knowledge_routes as kr

    mock_engine = MagicMock()
    mock_engine.query.return_value = fake_results

    with patch.object(kr, "_get_engine", return_value=mock_engine):
        app = _get_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/v1/knowledge/chunks/query",
                json={
                    "project": "myproj",
                    "reviewer_id": "security",
                    "query_text": "SQL injection",
                    "top_k": 3,
                },
                headers=AUTH_HEADERS,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["text"] == "test chunk"
        assert data["results"][0]["score"] == 0.95
        assert data["query_text"] == "SQL injection"


@pytest.mark.asyncio
async def test_append_learnings():
    """Append endpoint appends entries and reports counts."""
    import wfc.servers.rest_api.knowledge_routes as kr

    mock_writer = MagicMock()
    mock_writer.append_entries.return_value = {"security": 2}

    with patch.object(kr, "_get_writer", return_value=mock_writer):
        app = _get_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/v1/knowledge/learnings/append",
                json={
                    "project": "myproj",
                    "reviewer_id": "security",
                    "entries": [
                        {"text": "entry 1", "section": "patterns_found", "source": "review-1"},
                        {"text": "entry 2", "section": "false_positives", "source": "review-1"},
                        {"text": "entry 3", "section": "patterns_found", "source": "review-2"},
                    ],
                },
                headers=AUTH_HEADERS,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["appended"] == 2
        assert data["duplicates_skipped"] == 1
        assert data["reviewer_id"] == "security"


@pytest.mark.asyncio
async def test_promote_learning():
    """Promote endpoint promotes entry to global tier."""
    import wfc.servers.rest_api.knowledge_routes as kr

    mock_writer = MagicMock()
    mock_writer.promote_to_global.return_value = True

    with patch.object(kr, "_get_writer", return_value=mock_writer):
        app = _get_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/v1/knowledge/learnings/promote",
                json={
                    "project": "myproj",
                    "reviewer_id": "security",
                    "entry_text": "Always check for SQL injection in ORM queries",
                    "section": "patterns_found",
                    "source": "review-42",
                },
                headers=AUTH_HEADERS,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["promoted"] is True
        assert data["reviewer_id"] == "security"
        assert "global" in data["message"].lower()


@pytest.mark.asyncio
async def test_drift_analyze():
    """Drift endpoint returns analysis report."""
    fake_report = FakeDriftReport(signals=[FakeDriftSignal()])

    with patch("wfc.scripts.knowledge.drift_detector.DriftDetector") as MockDetector:
        mock_instance = MagicMock()
        mock_instance.analyze.return_value = fake_report
        MockDetector.return_value = mock_instance

        app = _get_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/v1/knowledge/drift/analyze",
                json={"project": "myproj"},
                headers=AUTH_HEADERS,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["signals"]) == 1
        assert data["signals"][0]["signal_type"] == "stale"
        assert data["total_entries"] == 10
        assert data["recommendation"] == "needs_pruning"


@pytest.mark.asyncio
async def test_get_hash():
    """Hash endpoint returns stored file hash."""
    import wfc.servers.rest_api.knowledge_routes as kr

    mock_engine = MagicMock()
    mock_engine._hashes = {"security": "abc123def456"}

    with patch.object(kr, "_get_engine", return_value=mock_engine):
        app = _get_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/v1/knowledge/hash/myproj/security", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["file_hash"] == "abc123def456"
        assert data["reviewer_id"] == "security"
        assert data["project"] == "myproj"


@pytest.mark.asyncio
async def test_get_learnings(tmp_path, monkeypatch):
    """GET learnings returns raw KNOWLEDGE.md content."""
    import wfc.servers.rest_api.knowledge_routes as kr

    data_dir = tmp_path / "data"
    monkeypatch.setattr(kr, "DATA_DIR", data_dir)

    knowledge_dir = data_dir / "testproj" / "reviewers" / "security"
    knowledge_dir.mkdir(parents=True)
    knowledge_file = knowledge_dir / "KNOWLEDGE.md"
    knowledge_file.write_text("# Test Knowledge\n\n## Patterns Found\n- entry 1\n")

    app = _get_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/v1/knowledge/learnings/security?project=testproj", headers=AUTH_HEADERS
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["reviewer_id"] == "security"
    assert data["project"] == "testproj"
    assert "Patterns Found" in data["content"]


@pytest.mark.asyncio
async def test_get_learnings_not_found():
    """GET learnings returns 404 when file does not exist."""
    app = _get_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/v1/knowledge/learnings/security?project=nonexistent", headers=AUTH_HEADERS
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_invalid_reviewer_id_rejected():
    """Invalid reviewer_id values are rejected by the Literal type."""
    app = _get_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/v1/knowledge/learnings/hacker?project=test", headers=AUTH_HEADERS)
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_reviewer_id_in_hash():
    """Invalid reviewer_id in hash endpoint is rejected."""
    app = _get_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/v1/knowledge/hash/proj/notareviewer", headers=AUTH_HEADERS)
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_wrong_token_rejected():
    """Requests with wrong token are rejected."""
    app = _get_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/v1/knowledge/learnings/security?project=test",
            headers={"Authorization": "Bearer wrong-token"},
        )
    assert resp.status_code == 401
