"""
Pydantic models for WFC REST API.

All request/response models with validation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ReviewStatus(str, Enum):
    """Review task status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewSubmitRequest(BaseModel):
    """Request to submit code for review."""

    diff_content: str = Field(..., min_length=1, description="Git diff content")
    files: List[str] = Field(default_factory=list, description="List of changed files")

    @field_validator("files")
    @classmethod
    def validate_files(cls, v):
        """Ensure files is a list of non-empty strings."""
        if not all(isinstance(f, str) and f.strip() for f in v):
            raise ValueError("All files must be non-empty strings")
        return v


class ReviewSubmitResponse(BaseModel):
    """Response after submitting review request."""

    review_id: str = Field(..., description="Unique review identifier")
    status: ReviewStatus = Field(..., description="Initial status (pending)")
    submitted_at: datetime = Field(..., description="Submission timestamp")
    project_id: str = Field(..., description="Project identifier")


class ReviewFinding(BaseModel):
    """Individual review finding."""

    reviewer: str = Field(..., description="Reviewer name (e.g., Security)")
    severity: str = Field(..., description="HIGH, MEDIUM, LOW")
    category: str = Field(..., description="Finding category")
    description: str = Field(..., description="Finding description")
    file_path: Optional[str] = Field(None, description="Affected file")
    line_number: Optional[int] = Field(None, description="Line number")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score 0-100")


class ReviewStatusResponse(BaseModel):
    """Response for review status query."""

    review_id: str
    status: ReviewStatus
    project_id: str
    developer_id: str
    submitted_at: datetime
    completed_at: Optional[datetime] = None
    consensus_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    passed: Optional[bool] = None
    findings: List[ReviewFinding] = Field(default_factory=list)
    error_message: Optional[str] = None


class ProjectCreateRequest(BaseModel):
    """Request to create a new project."""

    project_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    developer_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    repo_path: str = Field(..., description="Absolute path to repository")

    @field_validator("repo_path")
    @classmethod
    def validate_repo_path(cls, v):
        """Ensure repo_path is absolute."""
        from pathlib import Path

        if not Path(v).is_absolute():
            raise ValueError("repo_path must be absolute")
        return v


class ProjectCreateResponse(BaseModel):
    """Response after creating project."""

    project_id: str
    api_key: str = Field(..., description="Generated API key (store securely)")
    created_at: datetime


class ProjectListResponse(BaseModel):
    """Response listing all projects."""

    projects: List[dict] = Field(..., description="List of projects")


class PoolStatusResponse(BaseModel):
    """Worktree pool status."""

    max_worktrees: int
    active_worktrees: int
    available_capacity: int
    orphaned_worktrees: int


class RateLimitStatusResponse(BaseModel):
    """Rate limit status."""

    capacity: int
    refill_rate: float
    available_tokens: float
    tokens_used: float


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional details")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
