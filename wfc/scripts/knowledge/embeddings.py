"""Generate embeddings for knowledge chunks.

Provides a unified interface with two backends:
1. sentence-transformers (semantic embeddings, preferred)
2. scikit-learn TF-IDF (keyword-based fallback)
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract embedding interface."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts into vectors."""
        ...

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """Embed a single query text into a vector."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimensionality of the embedding vectors."""
        ...


class SentenceTransformerEmbeddings(EmbeddingProvider):
    """Uses sentence-transformers for semantic embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [vec.tolist() for vec in embeddings]

    def embed_query(self, query: str) -> list[float]:
        return self.embed([query])[0]

    @property
    def dimension(self) -> int:
        return self._dimension


class TfidfEmbeddings(EmbeddingProvider):
    """TF-IDF fallback when sentence-transformers is unavailable."""

    def __init__(self, max_features: int = 384) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._max_features = max_features
        self.vectorizer = TfidfVectorizer(max_features=max_features)
        self._fitted = False
        self._corpus: list[str] = []

    def fit(self, texts: list[str]) -> None:
        """Fit the vectorizer on a corpus of texts."""
        self._corpus = list(texts)
        self.vectorizer.fit(self._corpus)
        self._fitted = True

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self._fitted:
            self.fit(texts)
        matrix = self.vectorizer.transform(texts)
        return [row.toarray().flatten().tolist() for row in matrix]

    def embed_query(self, query: str) -> list[float]:
        if not self._fitted:
            raise RuntimeError("TF-IDF vectorizer not fitted. Call embed() or fit() first.")
        matrix = self.vectorizer.transform([query])
        return matrix.toarray().flatten().tolist()

    @property
    def dimension(self) -> int:
        if self._fitted:
            return len(self.vectorizer.get_feature_names_out())
        return self._max_features


def get_embedding_provider() -> EmbeddingProvider:
    """Get the best available embedding provider.

    Tries sentence-transformers first, falls back to TF-IDF.

    Returns:
        An EmbeddingProvider instance.

    Raises:
        RuntimeError: If no embedding backend is available.
    """
    try:
        return SentenceTransformerEmbeddings()
    except ImportError:
        pass

    try:
        return TfidfEmbeddings()
    except ImportError:
        pass

    raise RuntimeError(
        "No embedding provider available. Install sentence-transformers or scikit-learn."
    )
