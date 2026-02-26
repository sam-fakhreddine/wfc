"""Tests for knowledge API models (TASK-002)."""

import pytest
from pydantic import ValidationError

from wfc.servers.rest_api.knowledge_models import (
    AppendRequest,
    AppendResponse,
    ChunkResult,
    DriftRequest,
    DriftResponse,
    DriftSignalModel,
    HashResponse,
    IndexRequest,
    IndexResponse,
    KnowledgeHealthResponse,
    LearningEntryModel,
    PromoteRequest,
    PromoteResponse,
    QueryRequest,
    QueryResponse,
)


class TestValidPayloads:
    """TEST-005: Valid payloads round-trip correctly."""

    def test_index_request_round_trip(self):
        req = IndexRequest(
            project="my-project",
            reviewer_id="security",
            knowledge_md="# Knowledge\n## Patterns Found\n- Use parameterized queries",
            machine_id="abcd1234",
        )
        data = req.model_dump()
        restored = IndexRequest(**data)
        assert restored == req

    def test_index_response_round_trip(self):
        resp = IndexResponse(chunks_indexed=5, reviewer_id="security", project="my-project")
        assert IndexResponse(**resp.model_dump()) == resp

    def test_query_request_round_trip(self):
        req = QueryRequest(
            project="my-project",
            reviewer_id="correctness",
            query_text="SQL injection prevention",
            top_k=10,
        )
        assert QueryRequest(**req.model_dump()) == req

    def test_query_response_round_trip(self):
        resp = QueryResponse(
            results=[
                ChunkResult(
                    text="Use parameterized queries",
                    score=0.85,
                    tier="global",
                    chunk_id="abc123",
                    reviewer_id="security",
                    section="patterns_found",
                    date="2026-02-20",
                    source="review-123",
                )
            ],
            query_text="SQL injection",
            reviewer_id="security",
        )
        assert QueryResponse(**resp.model_dump()) == resp

    def test_append_request_round_trip(self):
        req = AppendRequest(
            project="my-project",
            reviewer_id="performance",
            entries=[
                LearningEntryModel(
                    text="Cache database results",
                    section="patterns_found",
                    source="review-456",
                )
            ],
            machine_id="ef567890",
        )
        assert AppendRequest(**req.model_dump()) == req

    def test_append_response_round_trip(self):
        resp = AppendResponse(appended=3, duplicates_skipped=1, reviewer_id="performance")
        assert AppendResponse(**resp.model_dump()) == resp

    def test_promote_request_round_trip(self):
        req = PromoteRequest(
            project="my-project",
            reviewer_id="reliability",
            entry_text="Always use connection pooling",
            section="patterns_found",
            source="review-789",
        )
        assert PromoteRequest(**req.model_dump()) == req

    def test_promote_response_round_trip(self):
        resp = PromoteResponse(
            promoted=True, reviewer_id="reliability", message="Promoted successfully"
        )
        assert PromoteResponse(**resp.model_dump()) == resp

    def test_drift_request_round_trip(self):
        req = DriftRequest(project="my-project")
        assert DriftRequest(**req.model_dump()) == req

    def test_drift_response_round_trip(self):
        resp = DriftResponse(
            signals=[
                DriftSignalModel(
                    reviewer_id="security",
                    signal_type="stale",
                    severity="medium",
                    description="Entry is 120 days old",
                    file_path="/knowledge/security/KNOWLEDGE.md",
                    line_range=(10, 15),
                )
            ],
            total_entries=50,
            stale_count=3,
            bloated_count=0,
            healthy_count=47,
            recommendation="needs_pruning",
        )
        assert DriftResponse(**resp.model_dump()) == resp

    def test_hash_response_round_trip(self):
        resp = HashResponse(
            file_hash="abc123def456",
            last_indexed="2026-02-20T10:00:00Z",
            reviewer_id="security",
            project="my-project",
        )
        assert HashResponse(**resp.model_dump()) == resp

    def test_health_response_round_trip(self):
        resp = KnowledgeHealthResponse(
            status="ok",
            api_version=1,
            embedding_provider="sentence-transformers",
            chroma_status="connected",
            project_count=5,
            total_chunks=1200,
        )
        assert KnowledgeHealthResponse(**resp.model_dump()) == resp


class TestInvalidPayloads:
    """TEST-006: Invalid payloads raise ValidationError."""

    def test_index_request_empty_project(self):
        with pytest.raises(ValidationError):
            IndexRequest(project="", reviewer_id="security", knowledge_md="content")

    def test_query_request_top_k_zero(self):
        with pytest.raises(ValidationError):
            QueryRequest(project="proj", reviewer_id="security", query_text="test", top_k=0)

    def test_query_request_top_k_too_high(self):
        with pytest.raises(ValidationError):
            QueryRequest(project="proj", reviewer_id="security", query_text="test", top_k=51)

    def test_append_request_invalid_reviewer(self):
        with pytest.raises(ValidationError):
            AppendRequest(
                project="proj",
                reviewer_id="../../etc/passwd",
                entries=[LearningEntryModel(text="x", section="patterns_found", source="s")],
            )

    def test_index_request_path_traversal_project(self):
        with pytest.raises(ValidationError):
            IndexRequest(project="../../../root", reviewer_id="security", knowledge_md="x")

    def test_project_with_slashes(self):
        with pytest.raises(ValidationError):
            IndexRequest(project="foo/bar", reviewer_id="security", knowledge_md="x")

    def test_project_with_dots(self):
        with pytest.raises(ValidationError):
            IndexRequest(project="foo.bar", reviewer_id="security", knowledge_md="x")

    def test_invalid_section(self):
        with pytest.raises(ValidationError):
            LearningEntryModel(text="x", section="invalid_section", source="s")

    def test_empty_entries_list(self):
        with pytest.raises(ValidationError):
            AppendRequest(project="proj", reviewer_id="security", entries=[])

    def test_empty_query_text(self):
        with pytest.raises(ValidationError):
            QueryRequest(project="proj", reviewer_id="security", query_text="", top_k=5)


class TestPayloadLimits:
    """TEST-006b: 950KB payload rejection."""

    def test_knowledge_md_at_limit(self):
        """950,000 chars should be accepted."""
        content = "x" * 950_000
        req = IndexRequest(project="proj", reviewer_id="security", knowledge_md=content)
        assert len(req.knowledge_md) == 950_000

    def test_knowledge_md_over_limit(self):
        """950,001 chars should be rejected."""
        content = "x" * 950_001
        with pytest.raises(ValidationError):
            IndexRequest(project="proj", reviewer_id="security", knowledge_md=content)

    def test_knowledge_md_well_under_limit(self):
        """Normal content should work fine."""
        req = IndexRequest(
            project="proj",
            reviewer_id="security",
            knowledge_md="# Knowledge\nSome content",
        )
        assert req.knowledge_md == "# Knowledge\nSome content"
