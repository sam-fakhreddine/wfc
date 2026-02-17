"""Two-tier knowledge retrieval with global and project-local stores.

Merges results from a global knowledge store (~/.wfc/knowledge/global/)
and a project-local store (.development/knowledge/), deduplicates by
chunk_id, respects token budgets, and formats results for prompt injection.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from wfc.scripts.knowledge.chunker import KnowledgeChunk
from wfc.scripts.knowledge.embeddings import EmbeddingProvider
from wfc.scripts.knowledge.rag_engine import RAGEngine

logger = logging.getLogger(__name__)


@dataclass
class RetrievalConfig:
    """Configuration for knowledge retrieval."""

    global_store_dir: Path = field(
        default_factory=lambda: Path.home() / ".wfc" / "knowledge" / "global"
    )
    project_store_dir: Path = field(default_factory=lambda: Path(".development") / "knowledge")
    token_budget: int = 500
    top_k: int = 5
    min_score: float = 0.3


@dataclass
class TaggedResult:
    """A retrieval result tagged with its source tier."""

    chunk: KnowledgeChunk
    score: float
    source_tier: str


_FILE_PATH_PATTERN = re.compile(r"^(?:---|\+\+\+)\s+[ab]/(.+)$", re.MULTILINE)
_PYTHON_DEF_PATTERN = re.compile(r"^\+.*(?:def|class)\s+(\w+)", re.MULTILINE)
_JS_FUNC_PATTERN = re.compile(r"^\+.*function\s+(\w+)", re.MULTILINE)
_IMPORT_PATTERN = re.compile(r"^\+\s*(?:import\s+(\w+)|from\s+(\w+))", re.MULTILINE)


class KnowledgeRetriever:
    """Two-tier retrieval engine merging global and project-local knowledge."""

    def __init__(
        self,
        config: RetrievalConfig | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        """Initialize with config. Creates RAGEngine instances for each tier.

        Args:
            config: Retrieval configuration. Uses defaults if None.
            embedding_provider: Optional embedding provider shared by both tiers.
                When None, each RAGEngine picks the best available provider.
        """
        self.config = config or RetrievalConfig()
        self._global_engine: RAGEngine | None = None
        self._project_engine: RAGEngine | None = None

        if self.config.global_store_dir.is_dir():
            self._global_engine = RAGEngine(
                store_dir=self.config.global_store_dir,
                embedding_provider=embedding_provider,
            )

        if self.config.project_store_dir.is_dir():
            self._project_engine = RAGEngine(
                store_dir=self.config.project_store_dir,
                embedding_provider=embedding_provider,
            )

    def retrieve(
        self,
        reviewer_id: str,
        diff_context: str,
        top_k: int | None = None,
    ) -> list[TaggedResult]:
        """Query both tiers and merge results by relevance.

        1. Extract signals from diff_context (file paths, imports, function names)
        2. Query global store
        3. Query project store
        4. Merge by score, deduplicate by chunk_id
        5. Filter by min_score threshold
        6. Return top-k sorted by score descending

        Args:
            reviewer_id: The reviewer to query knowledge for.
            diff_context: Git diff or descriptive text to derive a query from.
            top_k: Maximum results to return. Defaults to config.top_k.

        Returns:
            List of TaggedResult sorted by score descending.
        """
        effective_top_k = top_k if top_k is not None else self.config.top_k
        query = self.extract_diff_signals(diff_context)
        if not query:
            query = diff_context

        if not query.strip():
            return []

        candidates: list[TaggedResult] = []

        if self._global_engine is not None:
            global_results = self._global_engine.query(reviewer_id, query, top_k=effective_top_k)
            for r in global_results:
                candidates.append(TaggedResult(chunk=r.chunk, score=r.score, source_tier="global"))

        if self._project_engine is not None:
            project_results = self._project_engine.query(reviewer_id, query, top_k=effective_top_k)
            for r in project_results:
                candidates.append(TaggedResult(chunk=r.chunk, score=r.score, source_tier="project"))

        seen: dict[str, TaggedResult] = {}
        for c in candidates:
            cid = c.chunk.chunk_id
            if cid not in seen or c.score > seen[cid].score:
                seen[cid] = c
        deduped = list(seen.values())

        filtered = [r for r in deduped if r.score >= self.config.min_score]

        filtered.sort(key=lambda r: r.score, reverse=True)
        return filtered[:effective_top_k]

    def format_knowledge_section(
        self,
        results: list[TaggedResult],
        token_budget: int = 500,
    ) -> str:
        """Format retrieval results as a markdown section for prompt injection.

        Returns a "## Relevant Knowledge" section with entries tagged
        [global] or [project]. Respects token budget (1 token ~ 4 chars).

        Args:
            results: List of TaggedResult to format.
            token_budget: Maximum tokens for the entire section.

        Returns:
            Markdown string, or empty string if no results or zero budget.
        """
        if not results or token_budget <= 0:
            return ""

        char_budget = token_budget * 4
        header = "## Relevant Knowledge\n\n"
        output = header
        remaining = char_budget - len(header)

        for r in results:
            entry = f"- [{r.source_tier}] {r.chunk.text}\n"
            if len(entry) > remaining:
                break
            output += entry
            remaining -= len(entry)

        return output

    def extract_diff_signals(self, diff_content: str) -> str:
        """Extract key signals from a diff for use as a RAG query.

        Extracts: file paths, function/class names, import statements.
        Returns a compact query string.

        Args:
            diff_content: Raw git diff text.

        Returns:
            Space-separated signal string, or empty string if no signals found.
        """
        if not diff_content.strip():
            return ""

        signals: list[str] = []

        for match in _FILE_PATH_PATTERN.finditer(diff_content):
            signals.append(match.group(1))

        for match in _PYTHON_DEF_PATTERN.finditer(diff_content):
            signals.append(match.group(1))

        for match in _JS_FUNC_PATTERN.finditer(diff_content):
            signals.append(match.group(1))

        for match in _IMPORT_PATTERN.finditer(diff_content):
            module = match.group(1) or match.group(2)
            if module:
                signals.append(module)

        return " ".join(signals)
