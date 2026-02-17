"""RAG engine for knowledge retrieval.

Supports two vector store backends:
1. ChromaDB (persistent, local) -- preferred
2. JSON-based store with cosine similarity -- fallback
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from wfc.scripts.knowledge.chunker import KnowledgeChunk, KnowledgeChunker
from wfc.scripts.knowledge.embeddings import EmbeddingProvider, get_embedding_provider


@dataclass
class RetrievalResult:
    """A query result with similarity score."""

    chunk: KnowledgeChunk
    score: float


class _JsonVectorStore:
    """Simple JSON-backed vector store with cosine similarity.

    Used as a fallback when ChromaDB is not available.
    """

    def __init__(self, store_path: Path) -> None:
        self._path = store_path
        self._data: dict[str, dict] = {}
        if self._path.exists():
            self._data = json.loads(self._path.read_text(encoding="utf-8"))

    def upsert(
        self,
        collection: str,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        if collection not in self._data:
            self._data[collection] = {"ids": [], "embeddings": [], "metadatas": []}
        coll = self._data[collection]
        existing_ids = set(coll["ids"])
        for i, cid in enumerate(ids):
            if cid in existing_ids:
                idx = coll["ids"].index(cid)
                coll["embeddings"][idx] = embeddings[i]
                coll["metadatas"][idx] = metadatas[i]
            else:
                coll["ids"].append(cid)
                coll["embeddings"].append(embeddings[i])
                coll["metadatas"].append(metadatas[i])
        self._save()

    def query(
        self,
        collection: str,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[tuple[str, dict, float]]:
        if collection not in self._data:
            return []
        coll = self._data[collection]
        scored: list[tuple[str, dict, float]] = []
        for i, emb in enumerate(coll["embeddings"]):
            sim = self._cosine_similarity(query_embedding, emb)
            scored.append((coll["ids"][i], coll["metadatas"][i], sim))
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:top_k]

    def delete_collection(self, collection: str) -> None:
        self._data.pop(collection, None)
        self._save()

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data), encoding="utf-8")

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)


class _ChromaVectorStore:
    """ChromaDB-backed persistent vector store."""

    def __init__(self, store_dir: Path) -> None:
        import chromadb

        store_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(store_dir))

    def upsert(
        self,
        collection: str,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        coll = self._client.get_or_create_collection(
            name=collection, metadata={"hnsw:space": "cosine"}
        )
        coll.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas)

    def query(
        self,
        collection: str,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[tuple[str, dict, float]]:
        try:
            coll = self._client.get_collection(name=collection)
        except Exception:
            return []
        results = coll.query(query_embeddings=[query_embedding], n_results=top_k)
        out: list[tuple[str, dict, float]] = []
        if results and results["ids"]:
            ids = results["ids"][0]
            metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(ids)
            distances = results["distances"][0] if results["distances"] else [0.0] * len(ids)
            for i, cid in enumerate(ids):
                similarity = max(0.0, 1.0 - distances[i])
                out.append((cid, metadatas[i], similarity))
        return out

    def delete_collection(self, collection: str) -> None:
        try:
            self._client.delete_collection(name=collection)
        except Exception:
            pass


def _get_vector_store(store_dir: Path) -> _ChromaVectorStore | _JsonVectorStore:
    """Get the best available vector store backend."""
    try:
        return _ChromaVectorStore(store_dir / "chroma")
    except ImportError:
        return _JsonVectorStore(store_dir / "vectors.json")


class RAGEngine:
    """RAG engine for indexing and querying reviewer knowledge."""

    def __init__(
        self,
        store_dir: Path | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.store_dir = store_dir or Path(".development/knowledge-store")
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.provider = embedding_provider or get_embedding_provider()
        self._chunker = KnowledgeChunker()
        self._hashes: dict[str, str] = {}
        self._hash_file = self.store_dir / "file_hashes.json"
        self._load_hashes()
        self._store = _get_vector_store(self.store_dir)

    def index(self, reviewer_id: str, knowledge_path: Path) -> int:
        """Index a single reviewer's KNOWLEDGE.md.

        Args:
            reviewer_id: The reviewer identifier (e.g. 'security').
            knowledge_path: Path to the KNOWLEDGE.md file.

        Returns:
            Number of chunks indexed.
        """
        chunks = self._chunker.parse_file(knowledge_path, reviewer_id)
        if not chunks:
            return 0

        texts = [c.text for c in chunks]
        ids = [c.chunk_id for c in chunks]
        metadatas = [asdict(c) for c in chunks]

        embeddings = self.provider.embed(texts)
        collection_name = f"reviewer_{reviewer_id}"
        self._store.upsert(
            collection=collection_name,
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        file_hash = self._compute_file_hash(knowledge_path)
        self._hashes[reviewer_id] = file_hash
        self._save_hashes()

        return len(chunks)

    def index_all(self, reviewers_dir: Path | None = None) -> dict[str, int]:
        """Index all reviewers' KNOWLEDGE.md files.

        Args:
            reviewers_dir: Path to the reviewers directory.
                Defaults to wfc/reviewers/ relative to the project root.

        Returns:
            Dict mapping reviewer_id to number of chunks indexed.
        """
        if reviewers_dir is None:
            reviewers_dir = Path(__file__).resolve().parents[2] / "reviewers"

        results: dict[str, int] = {}
        if not reviewers_dir.is_dir():
            return results

        for reviewer_dir in sorted(reviewers_dir.iterdir()):
            knowledge_path = reviewer_dir / "KNOWLEDGE.md"
            if knowledge_path.is_file():
                reviewer_id = reviewer_dir.name
                count = self.index(reviewer_id, knowledge_path)
                results[reviewer_id] = count

        return results

    def needs_reindex(self, reviewer_id: str, knowledge_path: Path) -> bool:
        """Check if a KNOWLEDGE.md has changed since last indexing.

        Args:
            reviewer_id: The reviewer identifier.
            knowledge_path: Path to the KNOWLEDGE.md file.

        Returns:
            True if the file has changed or was never indexed.
        """
        current_hash = self._compute_file_hash(knowledge_path)
        stored_hash = self._hashes.get(reviewer_id)
        return stored_hash != current_hash

    def query(
        self,
        reviewer_id: str,
        query_text: str,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Query a reviewer's knowledge for relevant entries.

        Args:
            reviewer_id: The reviewer to query.
            query_text: The search query.
            top_k: Maximum number of results to return.

        Returns:
            List of RetrievalResult sorted by relevance (descending).
        """
        query_embedding = self.provider.embed_query(query_text)
        collection_name = f"reviewer_{reviewer_id}"
        raw_results = self._store.query(
            collection=collection_name,
            query_embedding=query_embedding,
            top_k=top_k,
        )

        results: list[RetrievalResult] = []
        for _cid, metadata, score in raw_results:
            chunk = KnowledgeChunk(
                text=metadata.get("text", query_text),
                reviewer_id=metadata.get("reviewer_id", reviewer_id),
                section=metadata.get("section", "unknown"),
                date=metadata.get("date", "unknown"),
                source=metadata.get("source", "unknown"),
                chunk_id=metadata.get("chunk_id", _cid),
            )
            results.append(RetrievalResult(chunk=chunk, score=score))

        return results

    @staticmethod
    def _compute_file_hash(path: Path) -> str:
        """SHA-256 hash of file contents."""
        content = path.read_bytes()
        return hashlib.sha256(content).hexdigest()

    def _load_hashes(self) -> None:
        if self._hash_file.exists():
            self._hashes = json.loads(self._hash_file.read_text(encoding="utf-8"))

    def _save_hashes(self) -> None:
        self._hash_file.write_text(json.dumps(self._hashes, indent=2), encoding="utf-8")
