"""Tests for the RAG indexing pipeline.

Covers: chunker parsing, embedding providers, RAG engine indexing and querying.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from wfc.scripts.knowledge.chunker import KnowledgeChunk, KnowledgeChunker
from wfc.scripts.knowledge.embeddings import TfidfEmbeddings, get_embedding_provider
from wfc.scripts.knowledge.rag_engine import RAGEngine

REVIEWERS_DIR = Path(__file__).resolve().parents[1] / "wfc" / "reviewers"

SAMPLE_KNOWLEDGE_MD = """\
# KNOWLEDGE.md -- Test Reviewer

## Patterns Found

- [2026-02-16] Use of subprocess in hook infrastructure -- verify inputs are sanitized (Source: initial-seed)
- [2026-02-16] Security patterns loaded from JSON files (Source: PR-10)

## False Positives to Avoid

- [2026-02-16] eval() in regex pattern definition -> not executable eval (Source: initial-seed)

## Incidents Prevented

- [2026-02-16] No incidents recorded yet (Source: initial-seed)

## Repository-Specific Rules

- [2026-02-16] Security checks run as Phase 1 in PreToolUse hook (Source: initial-seed)

## Codebase Context

- [2026-02-16] WFC uses two-phase hook dispatch (Source: initial-seed)
"""

EMPTY_SECTIONS_MD = """\
# KNOWLEDGE.md -- Empty Reviewer

## Patterns Found

## False Positives to Avoid

## Incidents Prevented

## Repository-Specific Rules

## Codebase Context

"""




class TestChunker:
    def setup_method(self) -> None:
        self.chunker = KnowledgeChunker()

    def test_chunker_parses_knowledge_md(self) -> None:
        """Parse sample KNOWLEDGE.md and verify chunk count."""
        chunks = self.chunker.parse(SAMPLE_KNOWLEDGE_MD, "test")
        assert len(chunks) == 6
        assert all(isinstance(c, KnowledgeChunk) for c in chunks)

    def test_chunker_extracts_dates(self) -> None:
        """Date extraction from [YYYY-MM-DD] format."""
        chunks = self.chunker.parse(SAMPLE_KNOWLEDGE_MD, "test")
        for chunk in chunks:
            assert chunk.date == "2026-02-16"

    def test_chunker_extracts_sources(self) -> None:
        """Source extraction from (Source: ...) suffix."""
        chunks = self.chunker.parse(SAMPLE_KNOWLEDGE_MD, "test")
        sources = {c.source for c in chunks}
        assert "initial-seed" in sources
        assert "PR-10" in sources

    def test_chunker_handles_empty_sections(self) -> None:
        """Empty sections produce no chunks."""
        chunks = self.chunker.parse(EMPTY_SECTIONS_MD, "empty")
        assert len(chunks) == 0

    def test_chunker_assigns_sections(self) -> None:
        """Each chunk is assigned to the correct section."""
        chunks = self.chunker.parse(SAMPLE_KNOWLEDGE_MD, "test")
        sections = {c.section for c in chunks}
        assert "patterns_found" in sections
        assert "false_positives" in sections
        assert "incidents_prevented" in sections
        assert "repo_rules" in sections
        assert "codebase_context" in sections

    def test_chunker_generates_unique_ids(self) -> None:
        """Each chunk gets a unique deterministic chunk_id."""
        chunks = self.chunker.parse(SAMPLE_KNOWLEDGE_MD, "test")
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids)), "chunk_ids must be unique"

    def test_chunker_parses_real_knowledge_md(self) -> None:
        """Parse the real security KNOWLEDGE.md to verify against actual format."""
        security_path = REVIEWERS_DIR / "security" / "KNOWLEDGE.md"
        if not security_path.exists():
            pytest.skip("Security KNOWLEDGE.md not found")
        chunks = self.chunker.parse_file(security_path, "security")
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.reviewer_id == "security"
            assert chunk.date
            assert chunk.source

    def test_chunker_deterministic_ids(self) -> None:
        """Same content always produces the same chunk_id."""
        chunks_a = self.chunker.parse(SAMPLE_KNOWLEDGE_MD, "test")
        chunks_b = self.chunker.parse(SAMPLE_KNOWLEDGE_MD, "test")
        for a, b in zip(chunks_a, chunks_b):
            assert a.chunk_id == b.chunk_id




class TestEmbeddings:
    def test_embedding_provider_available(self) -> None:
        """At least one embedding provider loads successfully."""
        provider = get_embedding_provider()
        assert provider is not None

    def test_tfidf_fallback_works(self) -> None:
        """TF-IDF produces vectors of the expected shape."""
        provider = TfidfEmbeddings(max_features=50)
        texts = [
            "subprocess calls must be sanitized",
            "eval is a security risk",
            "token budget optimization",
        ]
        embeddings = provider.embed(texts)
        assert len(embeddings) == 3
        assert all(isinstance(v, list) for v in embeddings)
        assert all(len(v) > 0 for v in embeddings)

    def test_tfidf_query_after_fit(self) -> None:
        """TF-IDF can embed a query after fitting."""
        provider = TfidfEmbeddings(max_features=50)
        provider.fit(["security patterns", "subprocess calls", "regex timeout"])
        vec = provider.embed_query("security")
        assert isinstance(vec, list)
        assert len(vec) > 0

    def test_tfidf_query_before_fit_raises(self) -> None:
        """TF-IDF embed_query raises if not fitted."""
        provider = TfidfEmbeddings()
        with pytest.raises(RuntimeError, match="not fitted"):
            provider.embed_query("test")

    def test_tfidf_dimension(self) -> None:
        """TF-IDF dimension reflects fitted vocabulary size."""
        provider = TfidfEmbeddings(max_features=50)
        provider.fit(["hello world", "foo bar baz"])
        assert provider.dimension > 0
        assert provider.dimension <= 50




class TestRAGEngine:
    def test_rag_index_creates_store(self) -> None:
        """Indexing creates a persistent store directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            provider = TfidfEmbeddings(max_features=50)
            engine = RAGEngine(store_dir=store_dir, embedding_provider=provider)

            knowledge_path = Path(tmpdir) / "KNOWLEDGE.md"
            knowledge_path.write_text(SAMPLE_KNOWLEDGE_MD, encoding="utf-8")

            count = engine.index("test", knowledge_path)
            assert count == 6
            assert store_dir.exists()

    def test_rag_needs_reindex_detects_changes(self) -> None:
        """Hash comparison detects file changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            provider = TfidfEmbeddings(max_features=50)
            engine = RAGEngine(store_dir=store_dir, embedding_provider=provider)

            knowledge_path = Path(tmpdir) / "KNOWLEDGE.md"
            knowledge_path.write_text(SAMPLE_KNOWLEDGE_MD, encoding="utf-8")

            assert engine.needs_reindex("test", knowledge_path) is True

            engine.index("test", knowledge_path)
            assert engine.needs_reindex("test", knowledge_path) is False

            knowledge_path.write_text(
                SAMPLE_KNOWLEDGE_MD + "\n- [2026-02-17] New entry (Source: test)\n",
                encoding="utf-8",
            )
            assert engine.needs_reindex("test", knowledge_path) is True

    def test_rag_query_returns_relevant(self) -> None:
        """Query returns scored results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            provider = TfidfEmbeddings(max_features=100)
            engine = RAGEngine(store_dir=store_dir, embedding_provider=provider)

            knowledge_path = Path(tmpdir) / "KNOWLEDGE.md"
            knowledge_path.write_text(SAMPLE_KNOWLEDGE_MD, encoding="utf-8")
            engine.index("test", knowledge_path)

            results = engine.query("test", "subprocess sanitize", top_k=3)
            assert len(results) > 0
            assert all(hasattr(r, "score") for r in results)
            assert all(hasattr(r, "chunk") for r in results)
            for r in results:
                assert 0.0 <= r.score <= 1.0 + 1e-6

    def test_rag_query_empty_collection(self) -> None:
        """Querying a non-existent reviewer returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            provider = TfidfEmbeddings(max_features=50)
            engine = RAGEngine(store_dir=store_dir, embedding_provider=provider)

            provider.fit(["dummy text for fitting"])
            results = engine.query("nonexistent", "test query", top_k=5)
            assert results == []

    def test_rag_index_all_indexes_5_reviewers(self) -> None:
        """Index all 5 reviewers from the real reviewers directory."""
        if not REVIEWERS_DIR.is_dir():
            pytest.skip("Reviewers directory not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            provider = TfidfEmbeddings(max_features=100)
            engine = RAGEngine(store_dir=store_dir, embedding_provider=provider)

            results = engine.index_all(REVIEWERS_DIR)
            assert len(results) == 5
            expected = {"security", "correctness", "performance", "maintainability", "reliability"}
            assert set(results.keys()) == expected
            for reviewer_id, count in results.items():
                assert count > 0, f"{reviewer_id} should have chunks"

    def test_rag_hash_persistence(self) -> None:
        """File hashes persist across RAGEngine instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            knowledge_path = Path(tmpdir) / "KNOWLEDGE.md"
            knowledge_path.write_text(SAMPLE_KNOWLEDGE_MD, encoding="utf-8")

            provider = TfidfEmbeddings(max_features=50)
            engine1 = RAGEngine(store_dir=store_dir, embedding_provider=provider)
            engine1.index("test", knowledge_path)

            engine2 = RAGEngine(store_dir=store_dir, embedding_provider=provider)
            assert engine2.needs_reindex("test", knowledge_path) is False
