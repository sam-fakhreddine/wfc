"""Tests for the two-tier knowledge retriever.

Covers:
- Diff signal extraction (file paths, function names, imports)
- Two-tier retrieval (global + project stores)
- Result formatting with source tier tags
- Token budget enforcement
- ReviewerEngine integration with KnowledgeRetriever
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from wfc.scripts.knowledge.chunker import KnowledgeChunk
from wfc.scripts.knowledge.rag_engine import RAGEngine
from wfc.scripts.knowledge.retriever import (
    KnowledgeRetriever,
    RetrievalConfig,
    TaggedResult,
)

SAMPLE_KNOWLEDGE_MD = """\
# KNOWLEDGE.md -- Test Reviewer

## Patterns Found

- [2026-02-16] Use of subprocess in hook infrastructure -- verify inputs are sanitized (Source: initial-seed)
- [2026-02-16] Security patterns loaded from JSON files (Source: PR-10)

## False Positives to Avoid

- [2026-02-16] eval() in regex pattern definition -> not executable eval (Source: initial-seed)

## Repository-Specific Rules

- [2026-02-16] Security checks run as Phase 1 in PreToolUse hook (Source: initial-seed)

## Codebase Context

- [2026-02-16] WFC uses two-phase hook dispatch (Source: initial-seed)
"""


def _make_chunk(
    text: str,
    reviewer_id: str = "security",
    chunk_id: str | None = None,
    section: str = "patterns_found",
) -> KnowledgeChunk:
    """Helper to create a KnowledgeChunk."""
    return KnowledgeChunk(
        text=text,
        reviewer_id=reviewer_id,
        section=section,
        date="2026-02-16",
        source="test",
        chunk_id=chunk_id or f"chunk_{text[:8]}",
    )


def _make_tagged(
    text: str,
    score: float = 0.8,
    source_tier: str = "global",
    chunk_id: str | None = None,
) -> TaggedResult:
    """Helper to create a TaggedResult."""
    chunk = _make_chunk(text, chunk_id=chunk_id)
    return TaggedResult(chunk=chunk, score=score, source_tier=source_tier)


@pytest.fixture()
def config_with_stores(tmp_path: Path) -> RetrievalConfig:
    """Config pointing at real temp directories."""
    global_dir = tmp_path / "global"
    project_dir = tmp_path / "project"
    global_dir.mkdir()
    project_dir.mkdir()
    return RetrievalConfig(
        global_store_dir=global_dir,
        project_store_dir=project_dir,
        token_budget=500,
        top_k=5,
        min_score=0.3,
    )




class TestDiffSignalExtraction:
    """Test extraction of signals from git diffs."""

    def test_extract_file_paths_from_diff_headers(self) -> None:
        """Extract file paths from --- a/file and +++ b/file lines."""
        diff = textwrap.dedent("""\
            --- a/src/main.py
            +++ b/src/main.py
            @@ -1,3 +1,5 @@
            +import os
        """)
        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        signals = retriever.extract_diff_signals(diff)
        assert "src/main.py" in signals

    def test_extract_function_names_python(self) -> None:
        """Extract Python function/class names from def/class lines."""
        diff = textwrap.dedent("""\
            +++ b/app.py
            @@ -10,0 +11,3 @@
            +def validate_input(data):
            +    pass
            +class UserService:
        """)
        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        signals = retriever.extract_diff_signals(diff)
        assert "validate_input" in signals
        assert "UserService" in signals

    def test_extract_function_names_javascript(self) -> None:
        """Extract JS function names from function keyword lines."""
        diff = textwrap.dedent("""\
            +++ b/index.js
            +function handleRequest(req, res) {
        """)
        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        signals = retriever.extract_diff_signals(diff)
        assert "handleRequest" in signals

    def test_extract_import_statements(self) -> None:
        """Extract import module names."""
        diff = textwrap.dedent("""\
            +++ b/app.py
            +import subprocess
            +from pathlib import Path
        """)
        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        signals = retriever.extract_diff_signals(diff)
        assert "subprocess" in signals
        assert "pathlib" in signals

    def test_empty_diff_returns_empty_signals(self) -> None:
        """Empty diff produces empty signal string."""
        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        signals = retriever.extract_diff_signals("")
        assert signals == ""

    def test_diff_with_no_recognizable_patterns(self) -> None:
        """Diff with only plain text changes still extracts changed lines."""
        diff = textwrap.dedent("""\
            +++ b/readme.txt
            +This is a documentation update.
        """)
        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        signals = retriever.extract_diff_signals(diff)
        assert "readme.txt" in signals




class TestTwoTierRetrieval:
    """Test the two-tier merge logic of KnowledgeRetriever."""

    def test_global_only_when_no_project_store(self, tmp_path: Path) -> None:
        """Returns global results when project store dir does not exist."""
        from wfc.scripts.knowledge.embeddings import TfidfEmbeddings

        global_dir = tmp_path / "global"
        project_dir = tmp_path / "project_nonexistent"
        global_dir.mkdir()

        config = RetrievalConfig(
            global_store_dir=global_dir,
            project_store_dir=project_dir,
            token_budget=500,
            top_k=5,
            min_score=0.0,
        )

        provider = TfidfEmbeddings(max_features=50)
        engine = RAGEngine(store_dir=global_dir, embedding_provider=provider)
        knowledge_path = tmp_path / "KNOWLEDGE.md"
        knowledge_path.write_text(SAMPLE_KNOWLEDGE_MD, encoding="utf-8")
        engine.index("security", knowledge_path)

        retriever = KnowledgeRetriever(config=config, embedding_provider=provider)
        results = retriever.retrieve("security", "subprocess sanitize", top_k=3)

        assert len(results) > 0
        assert all(r.source_tier == "global" for r in results)

    def test_project_only_when_no_global_store(self, tmp_path: Path) -> None:
        """Returns project results when global store dir does not exist."""
        from wfc.scripts.knowledge.embeddings import TfidfEmbeddings

        global_dir = tmp_path / "global_nonexistent"
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        config = RetrievalConfig(
            global_store_dir=global_dir,
            project_store_dir=project_dir,
            token_budget=500,
            top_k=5,
            min_score=0.0,
        )

        provider = TfidfEmbeddings(max_features=50)
        engine = RAGEngine(store_dir=project_dir, embedding_provider=provider)
        knowledge_path = tmp_path / "KNOWLEDGE.md"
        knowledge_path.write_text(SAMPLE_KNOWLEDGE_MD, encoding="utf-8")
        engine.index("security", knowledge_path)

        retriever = KnowledgeRetriever(config=config, embedding_provider=provider)
        results = retriever.retrieve("security", "subprocess sanitize", top_k=3)

        assert len(results) > 0
        assert all(r.source_tier == "project" for r in results)

    def test_merged_results_from_both_tiers(self, tmp_path: Path) -> None:
        """Results from both tiers are merged and sorted by score."""
        from wfc.scripts.knowledge.embeddings import TfidfEmbeddings

        global_dir = tmp_path / "global"
        project_dir = tmp_path / "project"
        global_dir.mkdir()
        project_dir.mkdir()

        config = RetrievalConfig(
            global_store_dir=global_dir,
            project_store_dir=project_dir,
            token_budget=500,
            top_k=10,
            min_score=0.0,
        )

        provider = TfidfEmbeddings(max_features=50)

        global_engine = RAGEngine(store_dir=global_dir, embedding_provider=provider)
        knowledge_path = tmp_path / "KNOWLEDGE.md"
        knowledge_path.write_text(SAMPLE_KNOWLEDGE_MD, encoding="utf-8")
        global_engine.index("security", knowledge_path)

        project_knowledge = """\
# KNOWLEDGE.md -- Project Security

## Patterns Found

- [2026-02-16] Project uses subprocess.run with shell=True in deploy scripts (Source: project-audit)
- [2026-02-16] Custom authentication middleware validates JWT tokens (Source: project-audit)

## Codebase Context

- [2026-02-16] Project deploys via custom shell scripts in scripts/ directory (Source: project-audit)
"""
        project_engine = RAGEngine(
            store_dir=project_dir, embedding_provider=provider
        )
        knowledge_path2 = tmp_path / "KNOWLEDGE2.md"
        knowledge_path2.write_text(project_knowledge, encoding="utf-8")
        project_engine.index("security", knowledge_path2)

        retriever = KnowledgeRetriever(config=config, embedding_provider=provider)
        results = retriever.retrieve("security", "subprocess sanitize", top_k=10)

        tiers = {r.source_tier for r in results}
        assert "global" in tiers
        assert "project" in tiers
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_deduplication_keeps_highest_score(self, tmp_path: Path) -> None:
        """Same chunk_id from both tiers keeps the higher-scored entry."""
        from wfc.scripts.knowledge.embeddings import TfidfEmbeddings

        global_dir = tmp_path / "global"
        project_dir = tmp_path / "project"
        global_dir.mkdir()
        project_dir.mkdir()

        config = RetrievalConfig(
            global_store_dir=global_dir,
            project_store_dir=project_dir,
            token_budget=500,
            top_k=10,
            min_score=0.0,
        )

        provider = TfidfEmbeddings(max_features=50)

        knowledge_path = tmp_path / "KNOWLEDGE.md"
        knowledge_path.write_text(SAMPLE_KNOWLEDGE_MD, encoding="utf-8")

        engine_g = RAGEngine(store_dir=global_dir, embedding_provider=provider)
        engine_g.index("security", knowledge_path)

        engine_p = RAGEngine(store_dir=project_dir, embedding_provider=provider)
        engine_p.index("security", knowledge_path)

        retriever = KnowledgeRetriever(config=config, embedding_provider=provider)
        results = retriever.retrieve("security", "subprocess sanitize", top_k=10)

        chunk_ids = [r.chunk.chunk_id for r in results]
        assert len(chunk_ids) == len(set(chunk_ids)), "Duplicate chunk_ids found after dedup"

    def test_min_score_filtering(self, tmp_path: Path) -> None:
        """Results below min_score are filtered out."""
        from wfc.scripts.knowledge.embeddings import TfidfEmbeddings

        global_dir = tmp_path / "global"
        global_dir.mkdir()
        project_dir = tmp_path / "project_none"

        config = RetrievalConfig(
            global_store_dir=global_dir,
            project_store_dir=project_dir,
            token_budget=500,
            top_k=5,
            min_score=0.99,
        )

        provider = TfidfEmbeddings(max_features=50)
        engine = RAGEngine(store_dir=global_dir, embedding_provider=provider)
        knowledge_path = tmp_path / "KNOWLEDGE.md"
        knowledge_path.write_text(SAMPLE_KNOWLEDGE_MD, encoding="utf-8")
        engine.index("security", knowledge_path)

        retriever = KnowledgeRetriever(config=config, embedding_provider=provider)
        results = retriever.retrieve("security", "unrelated query about bananas", top_k=5)

        for r in results:
            assert r.score >= 0.99




class TestFormatKnowledgeSection:
    """Test formatting of retrieval results into markdown."""

    def test_formats_with_source_tier_tags(self) -> None:
        """Each entry is tagged with [global] or [project]."""
        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        results = [
            _make_tagged("Sanitize subprocess inputs", score=0.9, source_tier="global"),
            _make_tagged("Use parameterized queries", score=0.8, source_tier="project"),
        ]
        output = retriever.format_knowledge_section(results, token_budget=500)
        assert "[global]" in output
        assert "[project]" in output
        assert "Sanitize subprocess inputs" in output
        assert "Use parameterized queries" in output

    def test_respects_token_budget(self) -> None:
        """Output is truncated when entries exceed token budget."""
        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        results = [
            _make_tagged("A" * 200, score=0.9, source_tier="global"),
            _make_tagged("B" * 200, score=0.8, source_tier="project"),
            _make_tagged("C" * 200, score=0.7, source_tier="global"),
        ]
        output = retriever.format_knowledge_section(results, token_budget=100)
        char_count = len(output)
        assert char_count <= 500

    def test_empty_results_returns_empty_string(self) -> None:
        """No results produces empty output."""
        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        output = retriever.format_knowledge_section([], token_budget=500)
        assert output == ""

    def test_markdown_section_header(self) -> None:
        """Output starts with a '## Relevant Knowledge' header."""
        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        results = [_make_tagged("Test entry", score=0.9, source_tier="global")]
        output = retriever.format_knowledge_section(results, token_budget=500)
        assert output.startswith("## Relevant Knowledge")




class TestTokenBudget:
    """Test token budget enforcement."""

    def test_stays_within_budget(self) -> None:
        """Total output stays within the configured token budget."""
        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        results = [
            _make_tagged(f"Entry number {i} with some context about security", score=0.9 - i * 0.05)
            for i in range(10)
        ]
        budget = 200
        output = retriever.format_knowledge_section(results, token_budget=budget)
        approx_tokens = len(output) / 4
        assert approx_tokens <= budget + 20

    def test_includes_entries_that_fit(self) -> None:
        """Includes as many entries as fit within the budget."""
        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        results = [
            _make_tagged(f"Short entry {i}", score=0.9 - i * 0.05, source_tier="global")
            for i in range(5)
        ]
        output = retriever.format_knowledge_section(results, token_budget=500)
        assert "Short entry 0" in output
        assert "Short entry 1" in output

    def test_zero_budget_returns_empty(self) -> None:
        """Budget of 0 returns empty string."""
        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        results = [_make_tagged("Some content", score=0.9)]
        output = retriever.format_knowledge_section(results, token_budget=0)
        assert output == ""




class TestReviewerEngineIntegration:
    """Test ReviewerEngine integration with KnowledgeRetriever."""

    @pytest.fixture()
    def reviewers_dir(self, tmp_path: Path) -> Path:
        """Create a temporary reviewers directory with all 5 reviewers."""
        from wfc.scripts.skills.review.reviewer_loader import REVIEWER_IDS

        for reviewer_id in REVIEWER_IDS:
            d = tmp_path / reviewer_id
            d.mkdir()
            prompt = textwrap.dedent(f"""\
                # {reviewer_id.title()} Reviewer Agent

                ## Identity

                You are the {reviewer_id} reviewer.

                ## Temperature

                0.4

                ## Output Format

                ```json
                {{"severity": "<1-10>", "description": "<what>"}}
                ```
            """)
            (d / "PROMPT.md").write_text(prompt, encoding="utf-8")
            knowledge = f"# KNOWLEDGE.md -- {reviewer_id.title()}\n\n- Known pattern.\n"
            (d / "KNOWLEDGE.md").write_text(knowledge, encoding="utf-8")
        return tmp_path

    def test_engine_with_retriever_uses_rag_knowledge(
        self, reviewers_dir: Path
    ) -> None:
        """ReviewerEngine with retriever injects RAG-based knowledge section."""
        from wfc.scripts.skills.review.reviewer_engine import ReviewerEngine
        from wfc.scripts.skills.review.reviewer_loader import ReviewerLoader

        loader = ReviewerLoader(reviewers_dir=reviewers_dir)

        mock_retriever = MagicMock(spec=KnowledgeRetriever)
        mock_retriever.config = RetrievalConfig()
        mock_retriever.retrieve.return_value = [
            _make_tagged("Always sanitize subprocess inputs", score=0.95, source_tier="global"),
        ]
        mock_retriever.format_knowledge_section.return_value = (
            "## Relevant Knowledge\n\n- [global] Always sanitize subprocess inputs\n"
        )

        engine = ReviewerEngine(loader=loader, retriever=mock_retriever)
        tasks = engine.prepare_review_tasks(
            files=["app.py"],
            diff_content="+ import subprocess",
        )

        assert mock_retriever.retrieve.called

        security_task = next(t for t in tasks if t["reviewer_id"] == "security")
        assert "Relevant Knowledge" in security_task["prompt"]
        assert "sanitize subprocess" in security_task["prompt"]

    def test_engine_without_retriever_uses_raw_knowledge(
        self, reviewers_dir: Path
    ) -> None:
        """ReviewerEngine without retriever falls back to raw KNOWLEDGE.md."""
        from wfc.scripts.skills.review.reviewer_engine import ReviewerEngine
        from wfc.scripts.skills.review.reviewer_loader import ReviewerLoader

        loader = ReviewerLoader(reviewers_dir=reviewers_dir)
        engine = ReviewerEngine(loader=loader)

        tasks = engine.prepare_review_tasks(
            files=["app.py"],
            diff_content="+ import os",
        )

        security_task = next(t for t in tasks if t["reviewer_id"] == "security")
        assert "Repository Knowledge" in security_task["prompt"]
        assert "Known pattern" in security_task["prompt"]

    def test_engine_retriever_backward_compatible(
        self, reviewers_dir: Path
    ) -> None:
        """Existing code that creates ReviewerEngine(loader=...) still works."""
        from wfc.scripts.skills.review.reviewer_engine import ReviewerEngine
        from wfc.scripts.skills.review.reviewer_loader import ReviewerLoader

        loader = ReviewerLoader(reviewers_dir=reviewers_dir)
        engine = ReviewerEngine(loader=loader)

        tasks = engine.prepare_review_tasks(files=["app.py"])
        assert len(tasks) == 5
        for task in tasks:
            assert "reviewer_id" in task
            assert "prompt" in task
