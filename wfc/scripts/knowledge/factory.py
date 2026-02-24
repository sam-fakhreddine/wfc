"""Knowledge system factory — returns local or remote implementations based on environment.

Modes:
1. Remote: WFC_KNOWLEDGE_URL set, server reachable -> remote implementations
2. Local: WFC_KNOWLEDGE_URL not set -> local implementations
3. Local (same provider): URL set, server unreachable, same embedding provider -> full local
4. Degraded: URL set, server unreachable, embedding mismatch -> local with retrieval disabled
5. Local (no cache): URL set, server never reached, no cached health -> full local (NOT degraded)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeComponents:
    """Tuple of knowledge system components."""

    retriever: Any
    writer: Any
    rag_engine: Any
    mode: str


class DegradedRetriever:
    """Retriever that returns empty results — used when embedding providers don't match."""

    def retrieve(self, reviewer_id: str, diff_context: str, top_k: int | None = None) -> list:
        logger.warning("Knowledge retrieval disabled (embedding provider mismatch)")
        return []

    def format_knowledge_section(self, results: list, token_budget: int = 500) -> str:
        return ""

    def extract_diff_signals(self, diff_content: str) -> str:
        from wfc.scripts.knowledge.retriever import KnowledgeRetriever

        r = KnowledgeRetriever.__new__(KnowledgeRetriever)
        return KnowledgeRetriever.extract_diff_signals(r, diff_content)


class KnowledgeFactory:
    """Factory that returns the appropriate knowledge implementations."""

    _cached_health: dict | None = None

    @classmethod
    def create(
        cls,
        project: str = "default",
        server_url: str | None = None,
        auth_token: str | None = None,
        health_timeout: float | None = None,
    ) -> KnowledgeComponents:
        """Create knowledge components based on environment.

        Args:
            project: Project identifier
            server_url: Override WFC_KNOWLEDGE_URL env var
            auth_token: Override WFC_KNOWLEDGE_TOKEN env var
            health_timeout: Override WFC_KNOWLEDGE_TIMEOUT env var (default 2.0s)
        """
        url = server_url or os.environ.get("WFC_KNOWLEDGE_URL", "")
        token = auth_token or os.environ.get("WFC_KNOWLEDGE_TOKEN", "")
        timeout = health_timeout or float(os.environ.get("WFC_KNOWLEDGE_TIMEOUT", "2.0"))

        if not url:
            logger.info("knowledge: local (WFC_KNOWLEDGE_URL not set)")
            return cls._create_local(project)

        try:
            from wfc.scripts.knowledge.remote import KnowledgeHTTPConfig

            config = KnowledgeHTTPConfig(
                server_url=url,
                auth_token=token,
            )
            resp = config.client.get("/v1/knowledge/health", timeout=timeout)
            resp.raise_for_status()
            health_data = resp.json()
            cls._cached_health = health_data

            logger.info(f"knowledge: remote ({url})")
            return cls._create_remote(config, project)

        except Exception as e:
            logger.warning(f"Knowledge server unreachable: {e}")
            return cls._create_fallback(project, url)

    @classmethod
    def _create_remote(cls, config: Any, project: str) -> KnowledgeComponents:
        """Create remote implementations."""
        from wfc.scripts.knowledge.remote import (
            RemoteRAGEngine,
            RemoteRetriever,
            RemoteWriter,
        )

        return KnowledgeComponents(
            retriever=RemoteRetriever(config, project),
            writer=RemoteWriter(config, project),
            rag_engine=RemoteRAGEngine(config, project),
            mode="remote",
        )

    @classmethod
    def _create_local(cls, project: str) -> KnowledgeComponents:
        """Create local implementations."""
        from wfc.scripts.knowledge.knowledge_writer import KnowledgeWriter
        from wfc.scripts.knowledge.rag_engine import RAGEngine
        from wfc.scripts.knowledge.retriever import KnowledgeRetriever

        return KnowledgeComponents(
            retriever=KnowledgeRetriever(),
            writer=KnowledgeWriter(),
            rag_engine=RAGEngine(),
            mode="local",
        )

    @classmethod
    def _create_fallback(cls, project: str, url: str) -> KnowledgeComponents:
        """Create fallback — check embedding compatibility."""
        if cls._cached_health is None:
            logger.info("knowledge: local (server never reached, no cached health)")
            return cls._create_local(project)

        server_provider = cls._cached_health.get("embedding_provider", "")
        if not server_provider:
            logger.info("knowledge: local (no embedding info in cached health)")
            return cls._create_local(project)

        try:
            from wfc.scripts.knowledge.embeddings import get_embedding_provider

            local_provider = type(get_embedding_provider()).__name__
        except Exception:
            local_provider = "unknown"

        if local_provider == server_provider:
            logger.info(f"knowledge: local (same provider: {local_provider})")
            return cls._create_local(project)

        logger.error(
            f"knowledge: local (degraded — embedding mismatch: "
            f"server={server_provider}, local={local_provider})"
        )

        from wfc.scripts.knowledge.knowledge_writer import KnowledgeWriter
        from wfc.scripts.knowledge.rag_engine import RAGEngine

        return KnowledgeComponents(
            retriever=DegradedRetriever(),
            writer=KnowledgeWriter(),
            rag_engine=RAGEngine(),
            mode="degraded",
        )
