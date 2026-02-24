"""Remote knowledge clients — drop-in replacements for local implementations.

Each class matches the public interface of its local counterpart (Liskov substitution).
Uses httpx.Client for HTTP communication with the knowledge server.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from wfc.shared.machine import machine_id

logger = logging.getLogger(__name__)

EXPECTED_API_VERSION = 1


class KnowledgeServerError(Exception):
    """Raised when the knowledge server returns an error."""


class KnowledgeVersionError(Exception):
    """Raised when API version is incompatible."""


@dataclass
class KnowledgeHTTPConfig:
    """Shared HTTP configuration for all remote knowledge clients.

    Composition over inheritance — each remote class takes this as a constructor arg.
    Owns a single shared httpx.Client (one connection pool for all 3 clients).
    """

    server_url: str
    auth_token: str
    query_timeout: float = 30.0
    index_timeout: float = 60.0
    machine_id: str = field(default_factory=machine_id)
    _client: httpx.Client | None = field(default=None, init=False, repr=False)
    _api_version_checked: bool = field(default=False, init=False, repr=False)

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.server_url,
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json",
                },
                timeout=self.query_timeout,
            )
        return self._client

    def check_api_version(self) -> dict:
        """Check server health and API version. Raises on mismatch."""
        if self._api_version_checked:
            return {}
        try:
            resp = self.client.get("/v1/knowledge/health", timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
            version = data.get("api_version", 1)
            if version != EXPECTED_API_VERSION:
                raise KnowledgeVersionError(
                    f"Server API version {version} != expected {EXPECTED_API_VERSION}"
                )
            self._api_version_checked = True
            return data
        except httpx.HTTPError as e:
            raise KnowledgeServerError(f"Health check failed: {e}") from e

    def close(self) -> None:
        """Clean teardown of shared client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def _post(self, path: str, data: dict, timeout: float | None = None) -> dict:
        """POST helper with error handling."""
        try:
            resp = self.client.post(path, json=data, timeout=timeout or self.query_timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.TimeoutException as e:
            raise KnowledgeServerError(f"Request timed out: {path}") from e
        except httpx.HTTPStatusError as e:
            raise KnowledgeServerError(f"Server error {e.response.status_code}: {path}") from e
        except httpx.HTTPError as e:
            raise KnowledgeServerError(f"HTTP error: {path}: {e}") from e

    def _get(self, path: str, timeout: float | None = None) -> dict:
        """GET helper with error handling."""
        try:
            resp = self.client.get(path, timeout=timeout or self.query_timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.TimeoutException as e:
            raise KnowledgeServerError(f"Request timed out: {path}") from e
        except httpx.HTTPStatusError as e:
            raise KnowledgeServerError(f"Server error {e.response.status_code}: {path}") from e
        except httpx.HTTPError as e:
            raise KnowledgeServerError(f"HTTP error: {path}: {e}") from e


class RemoteRetriever:
    """Drop-in replacement for KnowledgeRetriever.

    Matches all 3 public methods: retrieve, format_knowledge_section, extract_diff_signals.
    """

    def __init__(self, config: KnowledgeHTTPConfig, project: str = "default"):
        self.config = config
        self.project = project
        try:
            health = config.check_api_version()
            server_provider = health.get("embedding_provider", "")
            if server_provider:
                from wfc.scripts.knowledge.embeddings import get_embedding_provider

                try:
                    local_provider = type(get_embedding_provider()).__name__
                    if local_provider != server_provider:
                        logger.warning(
                            "Embedding provider mismatch: server=%s, local=%s",
                            server_provider,
                            local_provider,
                        )
                except Exception:
                    pass
        except KnowledgeServerError:
            pass

    def retrieve(
        self,
        reviewer_id: str,
        diff_context: str,
        top_k: int | None = None,
    ) -> list:
        """Query knowledge server for relevant chunks."""
        from wfc.scripts.knowledge.chunker import KnowledgeChunk
        from wfc.scripts.knowledge.retriever import TaggedResult

        signals = self.extract_diff_signals(diff_context)
        data = self.config._post(
            "/v1/knowledge/chunks/query",
            {
                "project": self.project,
                "reviewer_id": reviewer_id,
                "query_text": signals,
                "top_k": top_k or 5,
            },
        )

        results = []
        for r in data.get("results", []):
            chunk = KnowledgeChunk(
                text=r["text"],
                reviewer_id=r.get("reviewer_id", reviewer_id),
                section=r.get("section", ""),
                date=r.get("date", ""),
                source=r.get("source", ""),
                chunk_id=r.get("chunk_id", ""),
            )
            results.append(
                TaggedResult(chunk=chunk, score=r["score"], source_tier=r.get("tier", "global"))
            )
        return results

    def format_knowledge_section(
        self,
        results: list,
        token_budget: int = 500,
    ) -> str:
        """Format results as markdown section — local operation."""
        from wfc.scripts.knowledge.retriever import KnowledgeRetriever

        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        return KnowledgeRetriever.format_knowledge_section(retriever, results, token_budget)

    def extract_diff_signals(self, diff_content: str) -> str:
        """Extract diff signals — local operation (no HTTP)."""
        from wfc.scripts.knowledge.retriever import KnowledgeRetriever

        retriever = KnowledgeRetriever.__new__(KnowledgeRetriever)
        return KnowledgeRetriever.extract_diff_signals(retriever, diff_content)


class RemoteWriter:
    """Drop-in replacement for KnowledgeWriter.

    Matches all 5 public methods: append_entries, promote_to_global,
    extract_learnings, prune_old_entries, check_promotion_eligibility.
    """

    def __init__(self, config: KnowledgeHTTPConfig, project: str = "default"):
        self.config = config
        self.project = project

    def append_entries(self, entries: list) -> dict[str, int]:
        """Append learning entries via server."""
        entry_dicts = [
            {
                "text": e.text,
                "section": e.section,
                "source": e.source,
                "developer_id": getattr(e, "developer_id", ""),
                "date": getattr(e, "date", ""),
            }
            for e in entries
        ]

        by_reviewer: dict[str, list] = {}
        for e, d in zip(entries, entry_dicts):
            by_reviewer.setdefault(e.reviewer_id, []).append(d)

        result = {}
        for reviewer_id, reviewer_entries in by_reviewer.items():
            data = self.config._post(
                "/v1/knowledge/learnings/append",
                {
                    "project": self.project,
                    "reviewer_id": reviewer_id,
                    "entries": reviewer_entries,
                    "machine_id": self.config.machine_id,
                },
            )
            result[reviewer_id] = data.get("appended", 0)
        return result

    def promote_to_global(self, entry, project_name: str) -> bool:
        """Promote entry to global tier via server."""
        data = self.config._post(
            "/v1/knowledge/learnings/promote",
            {
                "project": self.project,
                "reviewer_id": entry.reviewer_id,
                "entry_text": entry.text,
                "section": entry.section,
                "source": entry.source,
            },
        )
        return data.get("promoted", False)

    def extract_learnings(
        self,
        review_findings: list[dict],
        reviewer_id: str,
        source: str,
    ) -> list:
        """Extract learnings from review — local operation (text parsing)."""
        from wfc.scripts.knowledge.knowledge_writer import KnowledgeWriter

        writer = KnowledgeWriter.__new__(KnowledgeWriter)
        writer.reviewers_dir = Path("/tmp")
        writer.global_knowledge_dir = Path("/tmp")
        return KnowledgeWriter.extract_learnings(writer, review_findings, reviewer_id, source)

    def prune_old_entries(self, reviewer_id: str, max_age_days: int = 180) -> int:
        """Prune old entries — delegates to local implementation."""
        from wfc.scripts.knowledge.knowledge_writer import KnowledgeWriter

        writer = KnowledgeWriter.__new__(KnowledgeWriter)
        writer.reviewers_dir = Path("/tmp")
        writer.global_knowledge_dir = Path("/tmp")
        return KnowledgeWriter.prune_old_entries(writer, reviewer_id, max_age_days)

    def check_promotion_eligibility(
        self, entry_text: str, reviewer_id: str, min_projects: int = 2
    ) -> bool:
        """Check promotion eligibility — delegates to local implementation."""
        from wfc.scripts.knowledge.knowledge_writer import KnowledgeWriter

        writer = KnowledgeWriter.__new__(KnowledgeWriter)
        writer.reviewers_dir = Path("/tmp")
        writer.global_knowledge_dir = Path("/tmp")
        return KnowledgeWriter.check_promotion_eligibility(
            writer, entry_text, reviewer_id, min_projects
        )


class RemoteRAGEngine:
    """Drop-in replacement for RAGEngine.

    Matches all 4 public methods: index, index_all, query, needs_reindex.
    """

    def __init__(self, config: KnowledgeHTTPConfig, project: str = "default"):
        self.config = config
        self.project = project

    def index(self, reviewer_id: str, knowledge_path: Path) -> int:
        """Read file locally, POST content to server for indexing."""
        content = knowledge_path.read_text()
        data = self.config._post(
            "/v1/knowledge/chunks/index",
            {
                "project": self.project,
                "reviewer_id": reviewer_id,
                "knowledge_md": content,
                "machine_id": self.config.machine_id,
            },
            timeout=self.config.index_timeout,
        )
        return data.get("chunks_indexed", 0)

    def index_all(self, reviewers_dir: Path | None = None) -> dict[str, int]:
        """Iterate locally over reviewers_dir, call index() per reviewer."""
        if reviewers_dir is None:
            return {}
        result = {}
        for reviewer_dir in sorted(reviewers_dir.iterdir()):
            if not reviewer_dir.is_dir():
                continue
            knowledge_path = reviewer_dir / "KNOWLEDGE.md"
            if knowledge_path.exists():
                reviewer_id = reviewer_dir.name
                result[reviewer_id] = self.index(reviewer_id, knowledge_path)
        return result

    def query(
        self,
        reviewer_id: str,
        query_text: str,
        top_k: int = 5,
    ) -> list:
        """Query via server."""
        from wfc.scripts.knowledge.chunker import KnowledgeChunk
        from wfc.scripts.knowledge.rag_engine import RetrievalResult

        data = self.config._post(
            "/v1/knowledge/chunks/query",
            {
                "project": self.project,
                "reviewer_id": reviewer_id,
                "query_text": query_text,
                "top_k": top_k,
            },
        )

        results = []
        for r in data.get("results", []):
            chunk = KnowledgeChunk(
                text=r["text"],
                reviewer_id=r.get("reviewer_id", reviewer_id),
                section=r.get("section", ""),
                date=r.get("date", ""),
                source=r.get("source", ""),
                chunk_id=r.get("chunk_id", ""),
            )
            results.append(RetrievalResult(chunk=chunk, score=r["score"]))
        return results

    def needs_reindex(self, reviewer_id: str, knowledge_path: Path) -> bool:
        """Compare local file hash against server's stored hash."""
        local_hash = hashlib.sha256(knowledge_path.read_bytes()).hexdigest()
        try:
            data = self.config._get(f"/v1/knowledge/hash/{self.project}/{reviewer_id}")
            server_hash = data.get("file_hash")
            return local_hash != server_hash
        except KnowledgeServerError:
            return True
