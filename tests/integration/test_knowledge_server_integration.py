"""Integration tests for the Central WFC Knowledge Server (TASK-007).

These tests require a running Docker Compose stack with the knowledge server
and ChromaDB. They are marked with @pytest.mark.integration and are skipped
during normal test runs (`make test`).

Run with:
    uv run pytest tests/integration/test_knowledge_server_integration.py -v -m integration

Prerequisites:
    WFC_KNOWLEDGE_TOKEN=<min-32-chars> docker compose -f wfc/servers/rest_api/docker-compose.knowledge.yml up -d
"""

import os

import pytest

pytestmark = pytest.mark.integration

SERVER_URL = os.environ.get("WFC_KNOWLEDGE_URL", "http://localhost:8420")
AUTH_TOKEN = os.environ.get("WFC_KNOWLEDGE_TOKEN", "test-integration-token-at-least-32-chars-long")
HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json",
}

SAMPLE_KNOWLEDGE_MD = """# Knowledge Base — Security Reviewer

## Patterns Found

- [2026-02-01] (review-001) Always use parameterized queries to prevent SQL injection
- [2026-02-02] (review-002) Validate all user input at system boundaries
- [2026-02-03] (review-003) Use constant-time comparison for secret tokens

## False Positives to Avoid

- [2026-02-01] (review-001) logging.info() with sanitized data is not a security issue

## Incidents Prevented

- [2026-02-02] (review-002) Caught hardcoded API key in config.py before merge
"""


@pytest.fixture
def client():
    """Create httpx client for integration tests."""
    import httpx

    with httpx.Client(base_url=SERVER_URL, headers=HEADERS, timeout=30.0) as c:
        yield c


@pytest.fixture
def unauthed_client():
    """Create httpx client without auth headers."""
    import httpx

    with httpx.Client(base_url=SERVER_URL, timeout=10.0) as c:
        yield c


class TestHealthEndpoint:
    """Health check endpoint tests."""

    def test_health_no_auth_returns_minimal(self, unauthed_client):
        resp = unauthed_client.get("/v1/knowledge/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["api_version"] == 1

    def test_health_with_auth_returns_full(self, client):
        resp = client.get("/v1/knowledge/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["api_version"] == 1
        assert "embedding_provider" in data
        assert data["embedding_provider"] != ""


class TestIndexQueryRoundTrip:
    """TEST-018: Full index → query round-trip."""

    def test_index_and_query(self, client):
        index_resp = client.post(
            "/v1/knowledge/chunks/index",
            json={
                "project": "integration-test",
                "reviewer_id": "security",
                "knowledge_md": SAMPLE_KNOWLEDGE_MD,
                "machine_id": "inttest1",
            },
        )
        assert index_resp.status_code == 200
        index_data = index_resp.json()
        assert index_data["chunks_indexed"] > 0

        query_resp = client.post(
            "/v1/knowledge/chunks/query",
            json={
                "project": "integration-test",
                "reviewer_id": "security",
                "query_text": "SQL injection parameterized queries",
                "top_k": 5,
            },
        )
        assert query_resp.status_code == 200
        query_data = query_resp.json()
        assert len(query_data["results"]) > 0
        assert any("parameterized" in r["text"].lower() for r in query_data["results"])


class TestMultiMachineDeduplication:
    """TEST-019: Two machines index same content, chunks stored once."""

    def test_dedup_across_machines(self, client):
        client.post(
            "/v1/knowledge/chunks/index",
            json={
                "project": "dedup-test",
                "reviewer_id": "security",
                "knowledge_md": SAMPLE_KNOWLEDGE_MD,
                "machine_id": "aaaa1111",
            },
        )

        client.post(
            "/v1/knowledge/chunks/index",
            json={
                "project": "dedup-test",
                "reviewer_id": "security",
                "knowledge_md": SAMPLE_KNOWLEDGE_MD,
                "machine_id": "bbbb2222",
            },
        )

        resp = client.post(
            "/v1/knowledge/chunks/query",
            json={
                "project": "dedup-test",
                "reviewer_id": "security",
                "query_text": "parameterized queries SQL injection",
                "top_k": 10,
            },
        )
        assert resp.status_code == 200
        results = resp.json()["results"]

        chunk_ids = [r["chunk_id"] for r in results]
        assert len(chunk_ids) == len(set(chunk_ids)), "Duplicate chunks detected"


class TestAppendLearnings:
    """TEST-009: Append and dedup learning entries."""

    def test_append_entries(self, client):
        resp = client.post(
            "/v1/knowledge/learnings/append",
            json={
                "project": "append-test",
                "reviewer_id": "correctness",
                "entries": [
                    {
                        "text": "Always check return values from I/O operations",
                        "section": "patterns_found",
                        "source": "integration-test",
                    },
                    {
                        "text": "Use structured logging for better observability",
                        "section": "patterns_found",
                        "source": "integration-test",
                    },
                ],
                "machine_id": "inttest1",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["appended"] >= 1


class TestPromoteToGlobal:
    """Promote entry from project to global tier."""

    def test_promote_entry(self, client):
        client.post(
            "/v1/knowledge/learnings/append",
            json={
                "project": "promote-test",
                "reviewer_id": "performance",
                "entries": [
                    {
                        "text": "Use connection pooling for database access",
                        "section": "patterns_found",
                        "source": "integration-test",
                    }
                ],
                "machine_id": "inttest1",
            },
        )

        resp = client.post(
            "/v1/knowledge/learnings/promote",
            json={
                "project": "promote-test",
                "reviewer_id": "performance",
                "entry_text": "Use connection pooling for database access",
                "section": "patterns_found",
                "source": "integration-test",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["reviewer_id"] == "performance"


class TestDriftAnalysis:
    """Drift detection with seeded data."""

    def test_drift_analyze(self, client):
        resp = client.post(
            "/v1/knowledge/drift/analyze",
            json={"project": "integration-test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "signals" in data
        assert "recommendation" in data
        assert data["recommendation"] in ("healthy", "needs_pruning", "needs_review")


class TestAuthEnforcement:
    """Verify auth is required on all data endpoints."""

    def test_index_requires_auth(self, unauthed_client):
        resp = unauthed_client.post(
            "/v1/knowledge/chunks/index",
            json={
                "project": "test",
                "reviewer_id": "security",
                "knowledge_md": "test",
            },
        )
        assert resp.status_code == 401

    def test_query_requires_auth(self, unauthed_client):
        resp = unauthed_client.post(
            "/v1/knowledge/chunks/query",
            json={
                "project": "test",
                "reviewer_id": "security",
                "query_text": "test",
                "top_k": 5,
            },
        )
        assert resp.status_code == 401


class TestOfflineFallback:
    """TEST-021: Factory falls back when server stops."""

    def test_factory_fallback_to_local(self):
        """Verify factory falls back to local when server is unreachable."""
        from wfc.scripts.knowledge.factory import KnowledgeFactory

        KnowledgeFactory._cached_health = None

        components = KnowledgeFactory.create(
            project="fallback-test",
            server_url="http://localhost:59999",
            auth_token="dummy-token-at-least-32-characters-long",
            health_timeout=1.0,
        )

        assert components.mode == "local"

        results = components.retriever.retrieve("security", "test diff context")
        assert isinstance(results, list)


class TestHashEndpoint:
    """Hash endpoint for change detection."""

    def test_get_hash(self, client):
        client.post(
            "/v1/knowledge/chunks/index",
            json={
                "project": "hash-test",
                "reviewer_id": "security",
                "knowledge_md": SAMPLE_KNOWLEDGE_MD,
                "machine_id": "inttest1",
            },
        )

        resp = client.get("/v1/knowledge/hash/hash-test/security")
        assert resp.status_code == 200
        data = resp.json()
        assert data["reviewer_id"] == "security"
        assert data["project"] == "hash-test"


class TestPathTraversal:
    """Verify path traversal is blocked."""

    def test_invalid_reviewer_in_learnings(self, client):
        resp = client.get("/v1/knowledge/learnings/../../etc/passwd")
        assert resp.status_code in (404, 422)

    def test_invalid_project_in_hash(self, client):
        resp = client.get("/v1/knowledge/hash/../../../root/security")
        assert resp.status_code in (404, 422)
