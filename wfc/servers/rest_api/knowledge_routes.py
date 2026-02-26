"""Knowledge Server API routes."""

import asyncio
import logging
from collections import OrderedDict
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi import Path as PathParam

from wfc.servers.rest_api.knowledge_dependencies import (
    optional_knowledge_token,
    verify_knowledge_token,
)
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
    PromoteRequest,
    PromoteResponse,
    QueryRequest,
    QueryResponse,
    ReviewerId,
)

logger = logging.getLogger(__name__)

KNOWLEDGE_API_VERSION = 1

DATA_DIR = Path("/data/wfc-knowledge")

_locks: OrderedDict[tuple[str, str], asyncio.Lock] = OrderedDict()
_index_semaphore = asyncio.Semaphore(2)

_MAX_CACHE_SIZE = 20
_engines: OrderedDict[str, object] = OrderedDict()
_writers: OrderedDict[str, object] = OrderedDict()


def _get_lock(project: str, reviewer_id: str) -> asyncio.Lock:
    """Get or create an asyncio.Lock for a (project, reviewer_id) pair, LRU-capped."""
    key = (project, reviewer_id)
    lock = _locks.get(key)
    if lock is not None:
        _locks.move_to_end(key)
        return lock

    lock = asyncio.Lock()
    _locks[key] = lock

    max_locks = _MAX_CACHE_SIZE * 5
    while len(_locks) > max_locks:
        _locks.popitem(last=False)

    return lock


def _get_engine(project: str):
    """Get or create a RAGEngine for a project, LRU-capped."""
    from wfc.scripts.knowledge.rag_engine import RAGEngine

    if project in _engines:
        _engines.move_to_end(project)
        return _engines[project]

    store_dir = DATA_DIR / project / "knowledge"
    store_dir.mkdir(parents=True, exist_ok=True)
    engine = RAGEngine(store_dir=store_dir)
    _engines[project] = engine

    while len(_engines) > _MAX_CACHE_SIZE:
        evicted_key, _ = _engines.popitem(last=False)
        logger.warning("Evicted RAGEngine for project: %s", evicted_key)

    return engine


def _get_writer(project: str):
    """Get or create a KnowledgeWriter for a project, LRU-capped."""
    from wfc.scripts.knowledge.knowledge_writer import KnowledgeWriter

    if project in _writers:
        _writers.move_to_end(project)
        return _writers[project]

    reviewers_dir = DATA_DIR / project / "reviewers"
    global_dir = DATA_DIR / "_global" / "reviewers"
    reviewers_dir.mkdir(parents=True, exist_ok=True)
    global_dir.mkdir(parents=True, exist_ok=True)
    writer = KnowledgeWriter(reviewers_dir=reviewers_dir, global_knowledge_dir=global_dir)
    _writers[project] = writer

    while len(_writers) > _MAX_CACHE_SIZE:
        evicted_key, _ = _writers.popitem(last=False)
        logger.warning("Evicted KnowledgeWriter for project: %s", evicted_key)

    return writer


def _reset_caches() -> None:
    """Reset all module-level caches (for testing)."""
    _engines.clear()
    _writers.clear()
    _locks.clear()


router = APIRouter(prefix="/v1/knowledge", tags=["knowledge"])

Auth = Annotated[bool, Depends(verify_knowledge_token)]
OptionalAuth = Annotated[bool, Depends(optional_knowledge_token)]


def _add_version_header(response: Response) -> None:
    """Add the knowledge API version header to a response."""
    response.headers["X-WFC-Knowledge-Version"] = str(KNOWLEDGE_API_VERSION)


@router.post("/chunks/index", response_model=IndexResponse)
async def index_chunks(req: IndexRequest, response: Response, _auth: Auth):
    """Index KNOWLEDGE.md content into vector store."""
    _add_version_header(response)

    try:
        engine = _get_engine(req.project)
        lock = _get_lock(req.project, req.reviewer_id)

        async with _index_semaphore:
            async with lock:
                knowledge_dir = DATA_DIR / req.project / "reviewers" / req.reviewer_id
                knowledge_dir.mkdir(parents=True, exist_ok=True)
                knowledge_path = knowledge_dir / "KNOWLEDGE.md"

                await asyncio.to_thread(knowledge_path.write_text, req.knowledge_md)
                count = await asyncio.to_thread(engine.index, req.reviewer_id, knowledge_path)
    except OSError as e:
        logger.exception("Index failed (I/O): project=%s reviewer=%s", req.project, req.reviewer_id)
        raise HTTPException(status_code=503, detail=f"Storage error: {type(e).__name__}") from e
    except Exception as e:
        logger.exception("Index failed: project=%s reviewer=%s", req.project, req.reviewer_id)
        raise HTTPException(status_code=500, detail="Indexing failed") from e

    return IndexResponse(chunks_indexed=count, reviewer_id=req.reviewer_id, project=req.project)


@router.post("/chunks/query", response_model=QueryResponse)
async def query_chunks(req: QueryRequest, response: Response, _auth: Auth):
    """Query knowledge chunks."""
    _add_version_header(response)

    try:
        engine = _get_engine(req.project)
        results = await asyncio.to_thread(engine.query, req.reviewer_id, req.query_text, req.top_k)
    except OSError as e:
        logger.exception("Query failed (I/O): project=%s", req.project)
        raise HTTPException(status_code=503, detail=f"Storage error: {type(e).__name__}") from e
    except Exception as e:
        logger.exception("Query failed: project=%s", req.project)
        raise HTTPException(status_code=500, detail="Query failed") from e

    chunks = [
        ChunkResult(
            text=r.chunk.text,
            score=r.score,
            tier="global",
            chunk_id=r.chunk.chunk_id,
            reviewer_id=r.chunk.reviewer_id,
            section=r.chunk.section,
            date=r.chunk.date,
            source=r.chunk.source,
        )
        for r in results
    ]

    return QueryResponse(results=chunks, query_text=req.query_text, reviewer_id=req.reviewer_id)


@router.post("/learnings/append", response_model=AppendResponse)
async def append_learnings(req: AppendRequest, response: Response, _auth: Auth):
    """Append learning entries to KNOWLEDGE.md."""
    _add_version_header(response)

    from wfc.scripts.knowledge.knowledge_writer import LearningEntry

    writer = _get_writer(req.project)
    lock = _get_lock(req.project, req.reviewer_id)

    entries = [
        LearningEntry(
            text=e.text,
            section=e.section,
            reviewer_id=req.reviewer_id,
            source=e.source,
            developer_id=e.developer_id,
            date=e.date,
        )
        for e in req.entries
    ]

    try:
        async with lock:
            result = await asyncio.to_thread(writer.append_entries, entries)
    except OSError as e:
        logger.exception("Append failed (I/O): project=%s", req.project)
        raise HTTPException(status_code=503, detail=f"Storage error: {type(e).__name__}") from e
    except Exception as e:
        logger.exception("Append failed: project=%s", req.project)
        raise HTTPException(status_code=500, detail="Append failed") from e

    appended = sum(result.values())
    duplicates = max(0, len(entries) - appended)

    return AppendResponse(
        appended=appended, duplicates_skipped=duplicates, reviewer_id=req.reviewer_id
    )


@router.post("/learnings/promote", response_model=PromoteResponse)
async def promote_learning(req: PromoteRequest, response: Response, _auth: Auth):
    """Promote a learning entry from project to global tier."""
    _add_version_header(response)

    from wfc.scripts.knowledge.knowledge_writer import LearningEntry

    writer = _get_writer(req.project)
    entry = LearningEntry(
        text=req.entry_text,
        section=req.section,
        reviewer_id=req.reviewer_id,
        source=req.source,
    )

    promoted = await asyncio.to_thread(writer.promote_to_global, entry, req.project)
    msg = "Promoted to global tier" if promoted else "Promotion failed or already exists"

    return PromoteResponse(promoted=promoted, reviewer_id=req.reviewer_id, message=msg)


@router.get("/learnings/{reviewer_id}")
async def get_learnings(
    reviewer_id: ReviewerId,
    response: Response,
    _auth: Auth,
    project: Annotated[str, Query(pattern=r"^[a-zA-Z0-9_-]+$", max_length=128)] = "default",
):
    """Get raw KNOWLEDGE.md content for a reviewer."""
    _add_version_header(response)

    knowledge_path = DATA_DIR / project / "reviewers" / reviewer_id / "KNOWLEDGE.md"
    if not knowledge_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge file not found"
        )

    content = await asyncio.to_thread(knowledge_path.read_text)
    return {"reviewer_id": reviewer_id, "project": project, "content": content}


@router.post("/drift/analyze", response_model=DriftResponse)
async def analyze_drift(req: DriftRequest, response: Response, _auth: Auth):
    """Run drift detection analysis."""
    _add_version_header(response)

    from wfc.scripts.knowledge.drift_detector import DriftDetector

    reviewers_dir = DATA_DIR / req.project / "reviewers"
    global_dir = DATA_DIR / "_global" / "reviewers"

    detector = DriftDetector(reviewers_dir=reviewers_dir, global_knowledge_dir=global_dir)
    report = await asyncio.to_thread(detector.analyze)

    signals = [
        DriftSignalModel(
            reviewer_id=s.reviewer_id,
            signal_type=s.signal_type,
            severity=s.severity,
            description=s.description,
            file_path=s.file_path,
            line_range=s.line_range,
        )
        for s in report.signals
    ]

    return DriftResponse(
        signals=signals,
        total_entries=report.total_entries,
        stale_count=report.stale_count,
        bloated_count=report.bloated_count,
        healthy_count=report.healthy_count,
        recommendation=report.recommendation,
    )


@router.get("/hash/{project}/{reviewer_id}", response_model=HashResponse)
async def get_hash(
    project: Annotated[str, PathParam(pattern=r"^[a-zA-Z0-9_-]+$", max_length=128)],
    reviewer_id: ReviewerId,
    response: Response,
    _auth: Auth,
):
    """Get stored file hash and last-indexed timestamp for a reviewer."""
    _add_version_header(response)

    engine = _get_engine(project)
    file_hash = engine._hashes.get(reviewer_id)

    return HashResponse(
        file_hash=file_hash,
        last_indexed=None,
        reviewer_id=reviewer_id,
        project=project,
    )


@router.get("/health", response_model=KnowledgeHealthResponse)
async def knowledge_health(response: Response, authenticated: OptionalAuth):
    """Health check -- minimal without auth, full diagnostic with auth."""
    _add_version_header(response)

    if not authenticated:
        return KnowledgeHealthResponse(status="ok", api_version=KNOWLEDGE_API_VERSION)

    chroma_status = "unknown"
    try:
        import chromadb  # noqa: F401

        chroma_status = "available"
    except ImportError:
        chroma_status = "unavailable"

    provider_name = "unavailable"
    try:
        from wfc.scripts.knowledge.embeddings import get_embedding_provider

        provider = get_embedding_provider()
        provider_name = type(provider).__name__
    except Exception:
        pass

    return KnowledgeHealthResponse(
        status="ok",
        api_version=KNOWLEDGE_API_VERSION,
        embedding_provider=provider_name,
        chroma_status=chroma_status,
        project_count=len(_engines),
        total_chunks=0,
    )
