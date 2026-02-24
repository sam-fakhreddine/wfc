"""
API routes for WFC REST server.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from wfc.servers.rest_api.auth import APIKeyStore
from wfc.servers.rest_api.background import ReviewStatusStore, execute_review_task
from wfc.servers.rest_api.dependencies import get_api_key_store, get_project_context
from wfc.servers.rest_api.models import (
    PoolStatusResponse,
    ProjectCreateRequest,
    ProjectCreateResponse,
    ProjectListResponse,
    RateLimitStatusResponse,
    ReviewStatus,
    ReviewStatusResponse,
    ReviewSubmitRequest,
    ReviewSubmitResponse,
)
from wfc.shared.config.wfc_config import ProjectContext
from wfc.shared.resource_pool import TokenBucket, WorktreePool

logger = logging.getLogger(__name__)


review_router = APIRouter(prefix="/v1/reviews", tags=["reviews"])

_review_store = ReviewStatusStore()
_rate_limiter = TokenBucket(capacity=10, refill_rate=10.0)


def get_review_store() -> ReviewStatusStore:
    """Get the global ReviewStatusStore (testable via dependency_overrides)."""
    return _review_store


def get_rate_limiter() -> TokenBucket:
    """Get the global rate limiter (testable via dependency_overrides)."""
    return _rate_limiter


@review_router.post(
    "/",
    response_model=ReviewSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit code for review",
    description=(
        "Submit code changes for 5-agent consensus review. "
        "Returns immediately with review_id. "
        "Use GET /v1/reviews/{review_id} to check status."
    ),
)
async def submit_review(
    request: ReviewSubmitRequest,
    background_tasks: BackgroundTasks,
    project_context: ProjectContext = Depends(get_project_context),
    review_store: ReviewStatusStore = Depends(get_review_store),
    rate_limiter: TokenBucket = Depends(get_rate_limiter),
) -> ReviewSubmitResponse:
    """Submit code for review. Returns review_id immediately."""
    if not rate_limiter.acquire(tokens=1, timeout=0.0):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )

    review_id = review_store.create_review(
        project_id=project_context.project_id,
        developer_id=project_context.developer_id,
    )

    background_tasks.add_task(
        execute_review_task,
        review_id,
        project_context,
        request.diff_content,
        request.files,
        review_store,
    )

    logger.info(f"Review {review_id} submitted for project {project_context.project_id}")

    return ReviewSubmitResponse(
        review_id=review_id,
        status=ReviewStatus.PENDING,
        submitted_at=datetime.now(timezone.utc),
        project_id=project_context.project_id,
    )


@review_router.get(
    "/{review_id}",
    response_model=ReviewStatusResponse,
    summary="Get review status",
    description="Get status and results of a review task.",
)
async def get_review_status(
    review_id: str,
    project_context: ProjectContext = Depends(get_project_context),
    review_store: ReviewStatusStore = Depends(get_review_store),
) -> ReviewStatusResponse:
    """Get review status and results."""
    review = review_store.get_review(review_id)

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review {review_id} not found",
        )

    if review.project_id != project_context.project_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: review belongs to different project",
        )

    return review


project_router = APIRouter(prefix="/v1/projects", tags=["projects"])


@project_router.post(
    "/",
    response_model=ProjectCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new project",
    description=(
        "Create new project and generate API key. "
        "IMPORTANT: Store the API key securely - it cannot be retrieved later."
    ),
)
async def create_project(
    request: ProjectCreateRequest,
    api_key_store: APIKeyStore = Depends(get_api_key_store),
) -> ProjectCreateResponse:
    """Create new project and generate API key."""
    try:
        api_key = api_key_store.create_api_key(
            request.project_id,
            request.developer_id,
        )

        return ProjectCreateResponse(
            project_id=request.project_id,
            api_key=api_key,
            created_at=datetime.now(timezone.utc),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@project_router.get(
    "/",
    response_model=ProjectListResponse,
    summary="List all projects",
    description="List all registered projects (does not require authentication).",
)
async def list_projects(
    api_key_store: APIKeyStore = Depends(get_api_key_store),
) -> ProjectListResponse:
    """List all projects."""
    projects_data = api_key_store.list_projects()

    projects = [
        {
            "project_id": project_id,
            "developer_id": data["developer_id"],
            "created_at": data["created_at"],
        }
        for project_id, data in projects_data.items()
    ]

    return ProjectListResponse(projects=projects)


resource_router = APIRouter(prefix="/v1/resources", tags=["resources"])

_worktree_pool = WorktreePool(
    pool_dir=Path.home() / ".wfc" / "worktrees",
    max_worktrees=10,
)


def get_worktree_pool() -> WorktreePool:
    """Get the global WorktreePool (testable via dependency_overrides)."""
    return _worktree_pool


@resource_router.get(
    "/pool",
    response_model=PoolStatusResponse,
    summary="Get worktree pool status",
    description="Get current status of the worktree resource pool.",
)
async def get_pool_status(
    project_context: ProjectContext = Depends(get_project_context),
    worktree_pool: WorktreePool = Depends(get_worktree_pool),
) -> PoolStatusResponse:
    """Get worktree pool status."""
    active = worktree_pool._count_worktrees()
    orphaned = worktree_pool._cleanup_orphans()

    return PoolStatusResponse(
        max_worktrees=worktree_pool.max_worktrees,
        active_worktrees=active,
        available_capacity=max(0, worktree_pool.max_worktrees - active),
        orphaned_worktrees=orphaned,
    )


@resource_router.get(
    "/rate-limit",
    response_model=RateLimitStatusResponse,
    summary="Get rate limit status",
    description="Get current rate limiting status for review requests.",
)
async def get_rate_limit_status(
    project_context: ProjectContext = Depends(get_project_context),
    rate_limiter: TokenBucket = Depends(get_rate_limiter),
) -> RateLimitStatusResponse:
    """Get rate limit status."""
    available = rate_limiter.get_available_tokens()

    return RateLimitStatusResponse(
        capacity=rate_limiter.capacity,
        refill_rate=rate_limiter.refill_rate,
        available_tokens=available,
        tokens_used=rate_limiter.capacity - available,
    )
