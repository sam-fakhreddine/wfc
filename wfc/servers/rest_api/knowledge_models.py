"""Pydantic v2 models for the WFC Knowledge Server API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, constr

ReviewerId = Literal["security", "correctness", "performance", "maintainability", "reliability"]

ProjectId = constr(pattern=r"^[a-zA-Z0-9_-]+$", min_length=1, max_length=128)

SectionId = Literal[
    "patterns_found",
    "false_positives",
    "incidents_prevented",
    "repo_rules",
    "codebase_context",
]


class ChunkResult(BaseModel):
    """A single chunk returned from a knowledge query."""

    text: str
    score: float = Field(ge=0.0, le=1.0)
    tier: str
    chunk_id: str
    reviewer_id: str
    section: str
    date: str
    source: str


class IndexRequest(BaseModel):
    """Request to index KNOWLEDGE.md content."""

    project: ProjectId
    reviewer_id: ReviewerId
    knowledge_md: str = Field(max_length=950_000)
    machine_id: str = ""


class IndexResponse(BaseModel):
    """Response after indexing."""

    chunks_indexed: int
    reviewer_id: str
    project: str


class QueryRequest(BaseModel):
    """Request to query knowledge chunks."""

    project: ProjectId
    reviewer_id: ReviewerId
    query_text: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)


class QueryResponse(BaseModel):
    """Response with query results."""

    results: list[ChunkResult]
    query_text: str
    reviewer_id: str


class LearningEntryModel(BaseModel):
    """A single learning entry for append operations."""

    text: str = Field(min_length=1)
    section: SectionId
    source: str = Field(min_length=1)
    developer_id: str = ""
    date: str = ""


class AppendRequest(BaseModel):
    """Request to append learning entries."""

    project: ProjectId
    reviewer_id: ReviewerId
    entries: list[LearningEntryModel] = Field(min_length=1)
    machine_id: str = ""


class AppendResponse(BaseModel):
    """Response after appending."""

    appended: int
    duplicates_skipped: int
    reviewer_id: str


class PromoteRequest(BaseModel):
    """Request to promote an entry from project to global tier."""

    project: ProjectId
    reviewer_id: ReviewerId
    entry_text: str = Field(min_length=1)
    section: SectionId
    source: str = Field(min_length=1)


class PromoteResponse(BaseModel):
    """Response after promotion attempt."""

    promoted: bool
    reviewer_id: str
    message: str


class DriftRequest(BaseModel):
    """Request to run drift analysis."""

    project: ProjectId


class DriftSignalModel(BaseModel):
    """A single drift signal."""

    reviewer_id: str
    signal_type: str
    severity: str
    description: str
    file_path: str
    line_range: tuple[int, int] | None = None


class DriftResponse(BaseModel):
    """Response with drift analysis results."""

    signals: list[DriftSignalModel]
    total_entries: int
    stale_count: int
    bloated_count: int
    healthy_count: int
    recommendation: str


class HashResponse(BaseModel):
    """Response with file hash info."""

    file_hash: str | None
    last_indexed: str | None
    reviewer_id: str
    project: str


class KnowledgeHealthResponse(BaseModel):
    """Health check response for knowledge server."""

    status: str
    api_version: int = 1
    embedding_provider: str = ""
    chroma_status: str = ""
    project_count: int = 0
    total_chunks: int = 0
