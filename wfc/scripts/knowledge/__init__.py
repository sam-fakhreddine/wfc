"""Knowledge indexing pipeline for RAG-powered reviewer memory."""

from wfc.scripts.knowledge.chunker import KnowledgeChunk, KnowledgeChunker
from wfc.scripts.knowledge.drift_detector import (
    DriftDetector,
    DriftReport,
    DriftSignal,
)
from wfc.scripts.knowledge.embeddings import (
    EmbeddingProvider,
    TfidfEmbeddings,
    get_embedding_provider,
)
from wfc.scripts.knowledge.knowledge_writer import (
    SECTION_HEADERS,
    KnowledgeWriter,
    LearningEntry,
)
from wfc.scripts.knowledge.rag_engine import RAGEngine, RetrievalResult
from wfc.scripts.knowledge.retriever import (
    KnowledgeRetriever,
    RetrievalConfig,
    TaggedResult,
)

__all__ = [
    "SECTION_HEADERS",
    "DriftDetector",
    "DriftReport",
    "DriftSignal",
    "EmbeddingProvider",
    "KnowledgeChunk",
    "KnowledgeChunker",
    "KnowledgeRetriever",
    "KnowledgeWriter",
    "LearningEntry",
    "RAGEngine",
    "RetrievalConfig",
    "RetrievalResult",
    "TaggedResult",
    "TfidfEmbeddings",
    "get_embedding_provider",
]
