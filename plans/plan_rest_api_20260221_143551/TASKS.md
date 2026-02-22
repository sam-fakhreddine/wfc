# REST API FOR MULTI-TENANT WFC - TASKS.MD

## Overview

This implementation plan breaks down the REST API feature into **42 ultra-granular tasks**, each designed for completion by lower-cost LLM agents (Haiku/Sonnet 3.5) in under 30 minutes. Each task modifies or creates exactly ONE file with explicit code patterns and minimal dependencies.

**Goal**: Production-ready FastAPI REST server for multi-tenant WFC with authentication, authorization, resource monitoring, and async review execution.

## Key Architectural Decisions

1. **FastAPI framework**: Async-first, OpenAPI docs, Pydantic validation, production-ready
2. **Authentication**: API key-based (project_id + api_key mapping in file-based store)
3. **Authorization**: Per-request project isolation via dependency injection
4. **Background tasks**: Long-running reviews execute via BackgroundTasks, status tracked in file-based store
5. **Resource monitoring**: Expose WorktreePool and TokenBucket status via GET endpoints
6. **Backward compatibility**: REST API reuses existing ReviewOrchestrator, ProjectContext, WorktreePool, TokenBucket
7. **Testing**: pytest-asyncio + httpx.AsyncClient for integration tests

---

## PHASE 0: PREREQUISITES (Week 1, Days 1-2)

### 0.1 - Dependencies & Project Structure

#### TASK-000: Add FastAPI dependencies to pyproject.toml

- **File**: `/Users/samfakhreddine/repos/wfc/pyproject.toml`
- **Complexity**: XS (< 10 lines)
- **Dependencies**: []
- **Properties**: []
- **Estimated Time**: 5min
- **Agent Level**: Haiku

**Description**: Add FastAPI, uvicorn, pydantic, httpx to dependencies.

**Code Pattern Example**:

```toml
[project.optional-dependencies]
api = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.9.0",
    "httpx>=0.27.0",
]
all = [
    # ... existing ...
    "wfc[api]",
]
```

**Acceptance Criteria**:

- [ ] FastAPI, uvicorn, pydantic, httpx added to `[project.optional-dependencies.api]`
- [ ] `api` included in `all` group
- [ ] `uv lock` completes without errors

---

#### TASK-001: Create wfc/servers/rest_api/ directory structure

- **File**: N/A (directory creation)
- **Complexity**: XS
- **Dependencies**: []
- **Properties**: []
- **Estimated Time**: 2min
- **Agent Level**: Haiku

**Description**: Create directory structure for REST API server.

**Bash Commands**:

```bash
mkdir -p /Users/samfakhreddine/repos/wfc/wfc/servers/rest_api
touch /Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/__init__.py
touch /Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/main.py
touch /Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/auth.py
touch /Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/models.py
touch /Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/routes.py
touch /Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/dependencies.py
touch /Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/background.py
```

**Acceptance Criteria**:

- [ ] All files created
- [ ] Directory imports cleanly: `python -c "import wfc.servers.rest_api"`

---

## PHASE 1: CORE DATA MODELS (Week 1, Days 2-3)

### 1.1 - Request/Response Models

#### TASK-002: Define Pydantic models for API requests and responses

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/models.py`
- **Complexity**: M (100-200 lines)
- **Dependencies**: [TASK-000]
- **Properties**: [S1, S2]
- **Estimated Time**: 20min
- **Agent Level**: Haiku

**Description**: Define all request/response models with validation.

**Code Pattern Example**:

```python
"""
Pydantic models for WFC REST API.

All request/response models with validation.
"""

from datetime import datetime
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

    @field_validator('files')
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
    project_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]{1,64}$')
    developer_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]{1,64}$')
    repo_path: str = Field(..., description="Absolute path to repository")

    @field_validator('repo_path')
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
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

**Acceptance Criteria**:

- [ ] All request/response models defined
- [ ] Pydantic validation works (pattern matching, field constraints)
- [ ] Models import cleanly
- [ ] Unit tests pass for model validation

---

## PHASE 2: AUTHENTICATION & AUTHORIZATION (Week 1, Days 3-4)

### 2.1 - API Key Authentication

#### TASK-003: Implement file-based API key store

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/auth.py`
- **Complexity**: M (100-200 lines)
- **Dependencies**: [TASK-002]
- **Properties**: [S1, S2, S3, I1]
- **Estimated Time**: 25min
- **Agent Level**: Sonnet

**Description**: Implement API key storage, generation, validation with file locking.

**Code Pattern Example**:

```python
"""
API key authentication for WFC REST API.

File-based storage at ~/.wfc/api_keys.json with filelock protection.
"""

import hashlib
import json
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

from filelock import FileLock


class APIKeyStore:
    """
    File-based API key storage.

    Format: ~/.wfc/api_keys.json
    {
        "project1": {
            "api_key_hash": "sha256...",
            "developer_id": "alice",
            "created_at": "2026-02-21T14:00:00Z"
        }
    }
    """

    def __init__(self, store_path: Optional[Path] = None):
        """Initialize API key store."""
        self.store_path = store_path or (Path.home() / ".wfc" / "api_keys.json")
        self.lock_path = self.store_path.with_suffix(".json.lock")

        # Ensure directory exists
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize empty store if doesn't exist
        if not self.store_path.exists():
            self._write_store({})

    def generate_api_key(self) -> str:
        """Generate cryptographically secure API key."""
        return secrets.token_urlsafe(32)

    def hash_api_key(self, api_key: str) -> str:
        """Hash API key using SHA-256."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def create_api_key(self, project_id: str, developer_id: str) -> str:
        """
        Create new API key for project.

        Args:
            project_id: Project identifier
            developer_id: Developer identifier

        Returns:
            Generated API key (plaintext, return to user)

        Raises:
            ValueError: If project already has API key
        """
        with FileLock(self.lock_path, timeout=10):
            store = self._read_store()

            if project_id in store:
                raise ValueError(f"Project {project_id} already has API key")

            api_key = self.generate_api_key()
            api_key_hash = self.hash_api_key(api_key)

            store[project_id] = {
                "api_key_hash": api_key_hash,
                "developer_id": developer_id,
                "created_at": datetime.utcnow().isoformat()
            }

            self._write_store(store)

            return api_key

    def validate_api_key(self, project_id: str, api_key: str) -> bool:
        """
        Validate API key for project.

        Args:
            project_id: Project identifier
            api_key: API key to validate

        Returns:
            True if valid, False otherwise
        """
        with FileLock(self.lock_path, timeout=10):
            store = self._read_store()

            if project_id not in store:
                return False

            expected_hash = store[project_id]["api_key_hash"]
            actual_hash = self.hash_api_key(api_key)

            return secrets.compare_digest(expected_hash, actual_hash)

    def get_developer_id(self, project_id: str) -> Optional[str]:
        """Get developer_id for project."""
        with FileLock(self.lock_path, timeout=10):
            store = self._read_store()
            return store.get(project_id, {}).get("developer_id")

    def list_projects(self) -> Dict[str, dict]:
        """List all projects."""
        with FileLock(self.lock_path, timeout=10):
            return self._read_store()

    def revoke_api_key(self, project_id: str) -> None:
        """Revoke API key for project."""
        with FileLock(self.lock_path, timeout=10):
            store = self._read_store()
            if project_id in store:
                del store[project_id]
                self._write_store(store)

    def _read_store(self) -> Dict[str, dict]:
        """Read API key store from disk."""
        if not self.store_path.exists():
            return {}

        with open(self.store_path, "r") as f:
            return json.load(f)

    def _write_store(self, store: Dict[str, dict]) -> None:
        """Write API key store to disk."""
        with open(self.store_path, "w") as f:
            json.dump(store, f, indent=2)
```

**Acceptance Criteria**:

- [ ] API keys generated with 32 bytes entropy
- [ ] API keys hashed with SHA-256 before storage
- [ ] File locking prevents concurrent write corruption
- [ ] `validate_api_key()` uses constant-time comparison
- [ ] Unit tests pass for create, validate, revoke operations

---

#### TASK-004: Implement FastAPI dependency for authentication

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/dependencies.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-003]
- **Properties**: [S1, S2]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Create FastAPI dependency to extract and validate API key from Authorization header.

**Code Pattern Example**:

```python
"""
FastAPI dependencies for authentication and authorization.
"""

from fastapi import Header, HTTPException, status
from wfc.servers.rest_api.auth import APIKeyStore
from wfc.shared.config.wfc_config import ProjectContext, WFCConfig


# Global APIKeyStore instance (singleton)
_api_key_store = APIKeyStore()


async def get_project_context(
    x_project_id: str = Header(..., description="Project ID"),
    authorization: str = Header(..., description="Bearer <api_key>")
) -> ProjectContext:
    """
    Dependency to authenticate request and return ProjectContext.

    Args:
        x_project_id: Project ID from X-Project-ID header
        authorization: API key from Authorization header (Bearer <key>)

    Returns:
        ProjectContext for authenticated project

    Raises:
        HTTPException: 401 if authentication fails
    """
    # Extract API key from "Bearer <key>" format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: Bearer <api_key>"
        )

    api_key = authorization[7:]  # Strip "Bearer "

    # Validate API key
    if not _api_key_store.validate_api_key(x_project_id, api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or project ID"
        )

    # Get developer_id from store
    developer_id = _api_key_store.get_developer_id(x_project_id)
    if not developer_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Project not found"
        )

    # Create ProjectContext
    config = WFCConfig()
    return config.create_project_context(x_project_id, developer_id)
```

**Acceptance Criteria**:

- [ ] Dependency extracts project_id and API key from headers
- [ ] Returns 401 if authentication fails
- [ ] Returns ProjectContext on success
- [ ] Unit tests pass for valid/invalid credentials

---

## PHASE 3: REVIEW EXECUTION & STATUS TRACKING (Week 1, Days 4-5)

### 3.1 - Review Status Store

#### TASK-005: Implement file-based review status store

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/background.py`
- **Complexity**: L (200-500 lines)
- **Dependencies**: [TASK-002, TASK-003]
- **Properties**: [L1, L2, I1, P1]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet

**Description**: Implement review status tracking with file-based storage at ~/.wfc/reviews/{review_id}.json.

**Code Pattern Example**:

```python
"""
Background task execution and review status tracking for WFC REST API.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from filelock import FileLock

from wfc.scripts.orchestrators.review.orchestrator import ReviewOrchestrator
from wfc.shared.config.wfc_config import ProjectContext
from wfc.servers.rest_api.models import ReviewStatus, ReviewStatusResponse, ReviewFinding


logger = logging.getLogger(__name__)


class ReviewStatusStore:
    """
    File-based review status storage.

    Each review stored at: ~/.wfc/reviews/{review_id}.json
    Format:
    {
        "review_id": "uuid",
        "project_id": "proj1",
        "developer_id": "alice",
        "status": "pending|in_progress|completed|failed",
        "submitted_at": "ISO8601",
        "completed_at": "ISO8601|null",
        "consensus_score": 8.5,
        "passed": true,
        "findings": [...],
        "error_message": null
    }
    """

    def __init__(self, reviews_dir: Optional[Path] = None):
        """Initialize review status store."""
        self.reviews_dir = reviews_dir or (Path.home() / ".wfc" / "reviews")
        self.reviews_dir.mkdir(parents=True, exist_ok=True)

    def create_review(self, project_id: str, developer_id: str) -> str:
        """
        Create new review entry.

        Args:
            project_id: Project identifier
            developer_id: Developer identifier

        Returns:
            Review ID (UUID)
        """
        review_id = str(uuid.uuid4())
        review_path = self.reviews_dir / f"{review_id}.json"
        lock_path = review_path.with_suffix(".json.lock")

        review_data = {
            "review_id": review_id,
            "project_id": project_id,
            "developer_id": developer_id,
            "status": ReviewStatus.PENDING.value,
            "submitted_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "consensus_score": None,
            "passed": None,
            "findings": [],
            "error_message": None
        }

        with FileLock(lock_path, timeout=10):
            with open(review_path, "w") as f:
                json.dump(review_data, f, indent=2)

        return review_id

    def get_review(self, review_id: str) -> Optional[ReviewStatusResponse]:
        """
        Get review status.

        Args:
            review_id: Review identifier

        Returns:
            ReviewStatusResponse or None if not found
        """
        review_path = self.reviews_dir / f"{review_id}.json"

        if not review_path.exists():
            return None

        lock_path = review_path.with_suffix(".json.lock")

        with FileLock(lock_path, timeout=10):
            with open(review_path, "r") as f:
                data = json.load(f)

        # Convert to Pydantic model
        return ReviewStatusResponse(
            review_id=data["review_id"],
            status=ReviewStatus(data["status"]),
            project_id=data["project_id"],
            developer_id=data["developer_id"],
            submitted_at=datetime.fromisoformat(data["submitted_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None,
            consensus_score=data["consensus_score"],
            passed=data["passed"],
            findings=[ReviewFinding(**f) for f in data["findings"]],
            error_message=data["error_message"]
        )

    def update_status(self, review_id: str, status: ReviewStatus) -> None:
        """Update review status."""
        review_path = self.reviews_dir / f"{review_id}.json"
        lock_path = review_path.with_suffix(".json.lock")

        with FileLock(lock_path, timeout=10):
            with open(review_path, "r") as f:
                data = json.load(f)

            data["status"] = status.value

            with open(review_path, "w") as f:
                json.dump(data, f, indent=2)

    def complete_review(
        self,
        review_id: str,
        consensus_score: float,
        passed: bool,
        findings: list
    ) -> None:
        """Mark review as completed with results."""
        review_path = self.reviews_dir / f"{review_id}.json"
        lock_path = review_path.with_suffix(".json.lock")

        with FileLock(lock_path, timeout=10):
            with open(review_path, "r") as f:
                data = json.load(f)

            data["status"] = ReviewStatus.COMPLETED.value
            data["completed_at"] = datetime.utcnow().isoformat()
            data["consensus_score"] = consensus_score
            data["passed"] = passed
            data["findings"] = findings

            with open(review_path, "w") as f:
                json.dump(data, f, indent=2)

    def fail_review(self, review_id: str, error_message: str) -> None:
        """Mark review as failed with error."""
        review_path = self.reviews_dir / f"{review_id}.json"
        lock_path = review_path.with_suffix(".json.lock")

        with FileLock(lock_path, timeout=10):
            with open(review_path, "r") as f:
                data = json.load(f)

            data["status"] = ReviewStatus.FAILED.value
            data["completed_at"] = datetime.utcnow().isoformat()
            data["error_message"] = error_message

            with open(review_path, "w") as f:
                json.dump(data, f, indent=2)


async def execute_review_task(
    review_id: str,
    project_context: ProjectContext,
    diff_content: str,
    files: list,
    review_store: ReviewStatusStore
) -> None:
    """
    Execute review in background.

    Args:
        review_id: Review identifier
        project_context: Project context
        diff_content: Git diff content
        files: List of changed files
        review_store: Review status store
    """
    try:
        # Update status to IN_PROGRESS
        review_store.update_status(review_id, ReviewStatus.IN_PROGRESS)

        # Execute review
        orchestrator = ReviewOrchestrator(project_context=project_context)

        # TODO: ReviewOrchestrator needs async support
        # For now, run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            orchestrator.run_review,
            diff_content,
            files
        )

        # Parse result and update status
        consensus_score = result.get("consensus_score", 0.0)
        passed = result.get("passed", False)
        findings = result.get("findings", [])

        # Convert findings to dict format for storage
        findings_data = [
            {
                "reviewer": f.get("reviewer", ""),
                "severity": f.get("severity", ""),
                "category": f.get("category", ""),
                "description": f.get("description", ""),
                "file_path": f.get("file_path"),
                "line_number": f.get("line_number"),
                "confidence": f.get("confidence", 50)
            }
            for f in findings
        ]

        review_store.complete_review(review_id, consensus_score, passed, findings_data)

    except Exception as e:
        logger.error(f"Review {review_id} failed: {e}", exc_info=True)
        review_store.fail_review(review_id, str(e))
```

**Acceptance Criteria**:

- [ ] Review status stored at ~/.wfc/reviews/{review_id}.json
- [ ] File locking prevents concurrent corruption
- [ ] Status transitions: PENDING → IN_PROGRESS → COMPLETED/FAILED
- [ ] Background task executes ReviewOrchestrator
- [ ] Unit tests pass for status transitions

---

## PHASE 4: API ROUTES (Week 2, Days 1-3)

### 4.1 - Review Endpoints

#### TASK-006: Implement POST /v1/reviews endpoint

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/routes.py`
- **Complexity**: M (100-200 lines)
- **Dependencies**: [TASK-004, TASK-005]
- **Properties**: [S1, S2, L1, P1]
- **Estimated Time**: 20min
- **Agent Level**: Sonnet

**Description**: Implement endpoint to submit code review requests.

**Code Pattern Example**:

```python
"""
API routes for WFC REST server.
"""

import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from wfc.servers.rest_api.models import (
    ReviewSubmitRequest,
    ReviewSubmitResponse,
    ReviewStatusResponse,
    ReviewStatus,
)
from wfc.servers.rest_api.dependencies import get_project_context
from wfc.servers.rest_api.background import ReviewStatusStore, execute_review_task
from wfc.shared.config.wfc_config import ProjectContext
from wfc.shared.resource_pool import TokenBucket


logger = logging.getLogger(__name__)

# Router for review endpoints
review_router = APIRouter(prefix="/v1/reviews", tags=["reviews"])

# Global singletons
_review_store = ReviewStatusStore()
_rate_limiter = TokenBucket(capacity=10, refill_rate=10.0)


@review_router.post(
    "/",
    response_model=ReviewSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit code for review",
    description="Submit code changes for 5-agent consensus review. Returns immediately with review_id. Use GET /v1/reviews/{review_id} to check status."
)
async def submit_review(
    request: ReviewSubmitRequest,
    background_tasks: BackgroundTasks,
    project_context: ProjectContext = Depends(get_project_context)
) -> ReviewSubmitResponse:
    """
    Submit code for review.

    Returns review_id immediately. Review executes in background.
    """
    # Rate limiting
    if not _rate_limiter.acquire(tokens=1, timeout=0.0):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )

    # Create review entry
    review_id = _review_store.create_review(
        project_id=project_context.project_id,
        developer_id=project_context.developer_id
    )

    # Schedule background task
    background_tasks.add_task(
        execute_review_task,
        review_id,
        project_context,
        request.diff_content,
        request.files,
        _review_store
    )

    logger.info(f"Review {review_id} submitted for project {project_context.project_id}")

    from datetime import datetime
    return ReviewSubmitResponse(
        review_id=review_id,
        status=ReviewStatus.PENDING,
        submitted_at=datetime.utcnow(),
        project_id=project_context.project_id
    )


@review_router.get(
    "/{review_id}",
    response_model=ReviewStatusResponse,
    summary="Get review status",
    description="Get status and results of a review task."
)
async def get_review_status(
    review_id: str,
    project_context: ProjectContext = Depends(get_project_context)
) -> ReviewStatusResponse:
    """Get review status and results."""
    review = _review_store.get_review(review_id)

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review {review_id} not found"
        )

    # Project isolation: ensure requester owns this review
    if review.project_id != project_context.project_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: review belongs to different project"
        )

    return review
```

**Acceptance Criteria**:

- [ ] POST /v1/reviews accepts ReviewSubmitRequest
- [ ] Returns 202 Accepted with review_id
- [ ] Background task scheduled for review execution
- [ ] Rate limiting enforced (429 if exceeded)
- [ ] GET /v1/reviews/{review_id} returns status
- [ ] Project isolation enforced (403 if accessing other project's review)
- [ ] Integration tests pass

---

### 4.2 - Project Management Endpoints

#### TASK-007: Implement POST /v1/projects endpoint

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/routes.py` (append)
- **Complexity**: S (50-100 lines)
- **Dependencies**: [TASK-003, TASK-006]
- **Properties**: [S1, S2, I1]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Implement endpoint to create new projects and generate API keys.

**Code Pattern Example**:

```python
# Add to routes.py

from wfc.servers.rest_api.models import ProjectCreateRequest, ProjectCreateResponse, ProjectListResponse
from wfc.servers.rest_api.auth import APIKeyStore


# Router for project endpoints
project_router = APIRouter(prefix="/v1/projects", tags=["projects"])

# Global APIKeyStore
_api_key_store = APIKeyStore()


@project_router.post(
    "/",
    response_model=ProjectCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new project",
    description="Create new project and generate API key. IMPORTANT: Store the API key securely - it cannot be retrieved later."
)
async def create_project(request: ProjectCreateRequest) -> ProjectCreateResponse:
    """Create new project and generate API key."""
    try:
        api_key = _api_key_store.create_api_key(
            request.project_id,
            request.developer_id
        )

        from datetime import datetime
        return ProjectCreateResponse(
            project_id=request.project_id,
            api_key=api_key,
            created_at=datetime.utcnow()
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@project_router.get(
    "/",
    response_model=ProjectListResponse,
    summary="List all projects",
    description="List all registered projects (does not require authentication)."
)
async def list_projects() -> ProjectListResponse:
    """List all projects."""
    projects_data = _api_key_store.list_projects()

    # Strip sensitive data (api_key_hash)
    projects = [
        {
            "project_id": project_id,
            "developer_id": data["developer_id"],
            "created_at": data["created_at"]
        }
        for project_id, data in projects_data.items()
    ]

    return ProjectListResponse(projects=projects)
```

**Acceptance Criteria**:

- [ ] POST /v1/projects creates project and returns API key
- [ ] Returns 409 if project already exists
- [ ] GET /v1/projects lists all projects (without API keys)
- [ ] Integration tests pass

---

### 4.3 - Resource Monitoring Endpoints

#### TASK-008: Implement GET /v1/resources/pool endpoint

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/routes.py` (append)
- **Complexity**: S (50-100 lines)
- **Dependencies**: [TASK-006]
- **Properties**: [P2]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Implement endpoint to query worktree pool status.

**Code Pattern Example**:

```python
# Add to routes.py

from wfc.servers.rest_api.models import PoolStatusResponse, RateLimitStatusResponse
from wfc.shared.resource_pool import WorktreePool
from pathlib import Path


# Router for resource monitoring
resource_router = APIRouter(prefix="/v1/resources", tags=["resources"])

# Global WorktreePool
_worktree_pool = WorktreePool(pool_dir=Path.home() / ".wfc" / "worktrees", max_worktrees=10)


@resource_router.get(
    "/pool",
    response_model=PoolStatusResponse,
    summary="Get worktree pool status",
    description="Get current status of the worktree resource pool."
)
async def get_pool_status(
    project_context: ProjectContext = Depends(get_project_context)
) -> PoolStatusResponse:
    """Get worktree pool status."""
    # Count active worktrees
    active = _worktree_pool._count_worktrees()

    # Run orphan cleanup to get accurate count
    orphaned = _worktree_pool._cleanup_orphans()

    return PoolStatusResponse(
        max_worktrees=_worktree_pool.max_worktrees,
        active_worktrees=active,
        available_capacity=max(0, _worktree_pool.max_worktrees - active),
        orphaned_worktrees=orphaned
    )


@resource_router.get(
    "/rate-limit",
    response_model=RateLimitStatusResponse,
    summary="Get rate limit status",
    description="Get current rate limiting status for review requests."
)
async def get_rate_limit_status(
    project_context: ProjectContext = Depends(get_project_context)
) -> RateLimitStatusResponse:
    """Get rate limit status."""
    available = _rate_limiter.get_available_tokens()

    return RateLimitStatusResponse(
        capacity=_rate_limiter.capacity,
        refill_rate=_rate_limiter.refill_rate,
        available_tokens=available,
        tokens_used=_rate_limiter.capacity - available
    )
```

**Acceptance Criteria**:

- [ ] GET /v1/resources/pool returns pool status
- [ ] GET /v1/resources/rate-limit returns rate limit status
- [ ] Both endpoints require authentication
- [ ] Integration tests pass

---

## PHASE 5: FASTAPI APPLICATION (Week 2, Day 3)

### 5.1 - Main Application

#### TASK-009: Implement FastAPI application with routers and middleware

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/main.py`
- **Complexity**: M (100-200 lines)
- **Dependencies**: [TASK-006, TASK-007, TASK-008]
- **Properties**: [S1, P1, P2]
- **Estimated Time**: 20min
- **Agent Level**: Sonnet

**Description**: Create main FastAPI app with all routers, middleware, error handling.

**Code Pattern Example**:

```python
"""
WFC REST API Server - Main application.

FastAPI application with authentication, authorization, and resource monitoring.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from wfc.servers.rest_api.routes import review_router, project_router, resource_router
from wfc.servers.rest_api.models import ErrorResponse


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Lifespan context manager for startup/shutdown."""
    logger.info("WFC REST API server starting up")
    yield
    logger.info("WFC REST API server shutting down")


# Create FastAPI app
app = FastAPI(
    title="WFC REST API",
    description="Multi-tenant code review and project management API for WFC",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware (configure based on deployment needs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(review_router)
app.include_router(project_router)
app.include_router(resource_router)


@app.get("/", summary="Health check", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "wfc-rest-api", "version": "1.0.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    error_response = ErrorResponse(
        error="Internal server error",
        detail=str(exc)
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "wfc.servers.rest_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

**Acceptance Criteria**:

- [ ] FastAPI app created with all routers
- [ ] CORS middleware configured
- [ ] Global exception handler installed
- [ ] Health check endpoint at GET /
- [ ] OpenAPI docs at /docs
- [ ] Server runs with `python -m wfc.servers.rest_api.main`

---

#### TASK-010: Add **init**.py exports for REST API module

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/__init__.py`
- **Complexity**: XS (< 10 lines)
- **Dependencies**: [TASK-009]
- **Properties**: []
- **Estimated Time**: 2min
- **Agent Level**: Haiku

**Description**: Export main FastAPI app and key classes.

**Code Pattern Example**:

```python
"""
WFC REST API Server.

Multi-tenant code review API with authentication and resource monitoring.
"""

from wfc.servers.rest_api.main import app
from wfc.servers.rest_api.auth import APIKeyStore
from wfc.servers.rest_api.background import ReviewStatusStore

__all__ = ["app", "APIKeyStore", "ReviewStatusStore"]
```

**Acceptance Criteria**:

- [ ] Module imports cleanly
- [ ] App accessible via `from wfc.servers.rest_api import app`

---

## PHASE 6: TESTING (Week 2, Days 4-5)

### 6.1 - Unit Tests

#### TASK-011: Write unit tests for Pydantic models

- **File**: `/Users/samfakhreddine/repos/wfc/tests/rest_api/test_models.py`
- **Complexity**: M (100-200 lines)
- **Dependencies**: [TASK-002]
- **Properties**: [S1, S2]
- **Estimated Time**: 20min
- **Agent Level**: Haiku

**Description**: Test all Pydantic model validation.

**Code Pattern Example**:

```python
"""
Unit tests for REST API Pydantic models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from wfc.servers.rest_api.models import (
    ReviewSubmitRequest,
    ReviewSubmitResponse,
    ReviewStatus,
    ProjectCreateRequest,
    ReviewFinding,
)


class TestReviewSubmitRequest:
    """Test ReviewSubmitRequest validation."""

    def test_valid_request(self):
        """Valid request should pass validation."""
        request = ReviewSubmitRequest(
            diff_content="diff content",
            files=["file1.py", "file2.py"]
        )
        assert request.diff_content == "diff content"
        assert len(request.files) == 2

    def test_empty_diff_content_fails(self):
        """Empty diff_content should fail validation."""
        with pytest.raises(ValidationError):
            ReviewSubmitRequest(diff_content="", files=[])

    def test_empty_files_allowed(self):
        """Empty files list should be allowed."""
        request = ReviewSubmitRequest(diff_content="diff", files=[])
        assert request.files == []

    def test_non_string_files_fail(self):
        """Non-string files should fail validation."""
        with pytest.raises(ValidationError):
            ReviewSubmitRequest(diff_content="diff", files=[123, 456])


class TestProjectCreateRequest:
    """Test ProjectCreateRequest validation."""

    def test_valid_project_id(self):
        """Valid project_id should pass."""
        request = ProjectCreateRequest(
            project_id="my-project-123",
            developer_id="alice",
            repo_path="/absolute/path"
        )
        assert request.project_id == "my-project-123"

    def test_invalid_project_id_characters(self):
        """Invalid characters in project_id should fail."""
        with pytest.raises(ValidationError):
            ProjectCreateRequest(
                project_id="invalid@project!",
                developer_id="alice",
                repo_path="/absolute/path"
            )

    def test_relative_repo_path_fails(self):
        """Relative repo_path should fail."""
        with pytest.raises(ValidationError):
            ProjectCreateRequest(
                project_id="proj1",
                developer_id="alice",
                repo_path="relative/path"
            )


class TestReviewFinding:
    """Test ReviewFinding validation."""

    def test_confidence_in_range(self):
        """Confidence must be 0-100."""
        finding = ReviewFinding(
            reviewer="Security",
            severity="HIGH",
            category="XSS",
            description="Potential XSS",
            confidence=85
        )
        assert finding.confidence == 85

    def test_confidence_out_of_range_fails(self):
        """Confidence >100 should fail."""
        with pytest.raises(ValidationError):
            ReviewFinding(
                reviewer="Security",
                severity="HIGH",
                category="XSS",
                description="Potential XSS",
                confidence=150
            )
```

**Acceptance Criteria**:

- [ ] All model validation paths tested
- [ ] Edge cases covered (empty strings, out of range, invalid patterns)
- [ ] Tests pass with pytest

---

#### TASK-012: Write unit tests for APIKeyStore

- **File**: `/Users/samfakhreddine/repos/wfc/tests/rest_api/test_auth.py`
- **Complexity**: M (100-200 lines)
- **Dependencies**: [TASK-003]
- **Properties**: [S1, S2, S3, I1]
- **Estimated Time**: 25min
- **Agent Level**: Sonnet

**Description**: Test API key generation, validation, storage, revocation.

**Code Pattern Example**:

```python
"""
Unit tests for API key authentication.
"""

import pytest
from pathlib import Path

from wfc.servers.rest_api.auth import APIKeyStore


class TestAPIKeyStore:
    """Test APIKeyStore functionality."""

    @pytest.fixture
    def tmp_store(self, tmp_path):
        """Create temporary API key store."""
        store_path = tmp_path / "api_keys.json"
        return APIKeyStore(store_path=store_path)

    def test_create_api_key_generates_unique_key(self, tmp_store):
        """Each API key should be unique."""
        key1 = tmp_store.create_api_key("proj1", "alice")
        key2 = tmp_store.create_api_key("proj2", "bob")

        assert key1 != key2
        assert len(key1) > 30  # Should be long and secure

    def test_validate_api_key_accepts_valid_key(self, tmp_store):
        """Valid API key should be accepted."""
        api_key = tmp_store.create_api_key("proj1", "alice")

        assert tmp_store.validate_api_key("proj1", api_key) is True

    def test_validate_api_key_rejects_invalid_key(self, tmp_store):
        """Invalid API key should be rejected."""
        tmp_store.create_api_key("proj1", "alice")

        assert tmp_store.validate_api_key("proj1", "wrong-key") is False

    def test_validate_api_key_rejects_nonexistent_project(self, tmp_store):
        """Non-existent project should be rejected."""
        assert tmp_store.validate_api_key("nonexistent", "any-key") is False

    def test_create_duplicate_project_fails(self, tmp_store):
        """Creating duplicate project should raise ValueError."""
        tmp_store.create_api_key("proj1", "alice")

        with pytest.raises(ValueError, match="already has API key"):
            tmp_store.create_api_key("proj1", "bob")

    def test_get_developer_id_returns_correct_id(self, tmp_store):
        """get_developer_id should return correct developer."""
        tmp_store.create_api_key("proj1", "alice")

        assert tmp_store.get_developer_id("proj1") == "alice"

    def test_revoke_api_key_invalidates_key(self, tmp_store):
        """Revoked API key should no longer validate."""
        api_key = tmp_store.create_api_key("proj1", "alice")

        tmp_store.revoke_api_key("proj1")

        assert tmp_store.validate_api_key("proj1", api_key) is False

    def test_list_projects_returns_all_projects(self, tmp_store):
        """list_projects should return all created projects."""
        tmp_store.create_api_key("proj1", "alice")
        tmp_store.create_api_key("proj2", "bob")

        projects = tmp_store.list_projects()

        assert "proj1" in projects
        assert "proj2" in projects
        assert projects["proj1"]["developer_id"] == "alice"
```

**Acceptance Criteria**:

- [ ] All APIKeyStore methods tested
- [ ] Concurrent access tested (file locking)
- [ ] Security properties verified (constant-time comparison, hashing)
- [ ] Tests pass

---

#### TASK-013: Write unit tests for ReviewStatusStore

- **File**: `/Users/samfakhreddine/repos/wfc/tests/rest_api/test_background.py`
- **Complexity**: M (100-200 lines)
- **Dependencies**: [TASK-005]
- **Properties**: [L1, L2, I1]
- **Estimated Time**: 25min
- **Agent Level**: Sonnet

**Description**: Test review status creation, updates, completion, failure.

**Code Pattern Example**:

```python
"""
Unit tests for review status tracking.
"""

import pytest
from pathlib import Path

from wfc.servers.rest_api.background import ReviewStatusStore
from wfc.servers.rest_api.models import ReviewStatus


class TestReviewStatusStore:
    """Test ReviewStatusStore functionality."""

    @pytest.fixture
    def tmp_store(self, tmp_path):
        """Create temporary review status store."""
        reviews_dir = tmp_path / "reviews"
        return ReviewStatusStore(reviews_dir=reviews_dir)

    def test_create_review_generates_uuid(self, tmp_store):
        """create_review should generate unique UUID."""
        review_id = tmp_store.create_review("proj1", "alice")

        assert len(review_id) == 36  # UUID format
        assert "-" in review_id

    def test_get_review_returns_pending_status(self, tmp_store):
        """Newly created review should have PENDING status."""
        review_id = tmp_store.create_review("proj1", "alice")

        review = tmp_store.get_review(review_id)

        assert review is not None
        assert review.status == ReviewStatus.PENDING
        assert review.project_id == "proj1"
        assert review.developer_id == "alice"

    def test_update_status_changes_status(self, tmp_store):
        """update_status should change review status."""
        review_id = tmp_store.create_review("proj1", "alice")

        tmp_store.update_status(review_id, ReviewStatus.IN_PROGRESS)

        review = tmp_store.get_review(review_id)
        assert review.status == ReviewStatus.IN_PROGRESS

    def test_complete_review_sets_results(self, tmp_store):
        """complete_review should set results and COMPLETED status."""
        review_id = tmp_store.create_review("proj1", "alice")

        findings = [
            {
                "reviewer": "Security",
                "severity": "HIGH",
                "category": "XSS",
                "description": "Potential XSS",
                "file_path": "test.py",
                "line_number": 42,
                "confidence": 85
            }
        ]

        tmp_store.complete_review(review_id, 8.5, True, findings)

        review = tmp_store.get_review(review_id)
        assert review.status == ReviewStatus.COMPLETED
        assert review.consensus_score == 8.5
        assert review.passed is True
        assert len(review.findings) == 1
        assert review.completed_at is not None

    def test_fail_review_sets_error(self, tmp_store):
        """fail_review should set error message and FAILED status."""
        review_id = tmp_store.create_review("proj1", "alice")

        tmp_store.fail_review(review_id, "Something went wrong")

        review = tmp_store.get_review(review_id)
        assert review.status == ReviewStatus.FAILED
        assert review.error_message == "Something went wrong"
        assert review.completed_at is not None

    def test_get_nonexistent_review_returns_none(self, tmp_store):
        """get_review with invalid ID should return None."""
        review = tmp_store.get_review("nonexistent-uuid")

        assert review is None
```

**Acceptance Criteria**:

- [ ] All ReviewStatusStore methods tested
- [ ] Status transitions validated
- [ ] File persistence verified
- [ ] Tests pass

---

### 6.2 - Integration Tests

#### TASK-014: Write integration tests for review endpoints

- **File**: `/Users/samfakhreddine/repos/wfc/tests/rest_api/test_review_endpoints.py`
- **Complexity**: L (200-500 lines)
- **Dependencies**: [TASK-009, TASK-012, TASK-013]
- **Properties**: [S1, S2, L1, P1]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet

**Description**: End-to-end tests for review submission and status querying.

**Code Pattern Example**:

```python
"""
Integration tests for review endpoints.
"""

import pytest
import asyncio
from httpx import AsyncClient

from wfc.servers.rest_api.main import app
from wfc.servers.rest_api.auth import APIKeyStore
from wfc.servers.rest_api.background import ReviewStatusStore


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def setup_project(tmp_path):
    """Set up test project with API key."""
    # Override default paths for testing
    api_key_store = APIKeyStore(store_path=tmp_path / "api_keys.json")
    review_store = ReviewStatusStore(reviews_dir=tmp_path / "reviews")

    # Create test project
    api_key = api_key_store.create_api_key("test-proj", "alice")

    return {
        "project_id": "test-proj",
        "developer_id": "alice",
        "api_key": api_key
    }


@pytest.mark.asyncio
class TestReviewEndpoints:
    """Integration tests for review endpoints."""

    async def test_submit_review_returns_202_with_review_id(self, client, setup_project):
        """POST /v1/reviews should return 202 with review_id."""
        headers = {
            "X-Project-ID": setup_project["project_id"],
            "Authorization": f"Bearer {setup_project['api_key']}"
        }

        response = await client.post(
            "/v1/reviews/",
            json={
                "diff_content": "sample diff content",
                "files": ["test.py"]
            },
            headers=headers
        )

        assert response.status_code == 202
        data = response.json()
        assert "review_id" in data
        assert data["status"] == "pending"
        assert data["project_id"] == "test-proj"

    async def test_submit_review_without_auth_returns_401(self, client):
        """POST /v1/reviews without auth should return 401."""
        response = await client.post(
            "/v1/reviews/",
            json={"diff_content": "diff", "files": []}
        )

        assert response.status_code == 401

    async def test_submit_review_with_invalid_api_key_returns_401(self, client, setup_project):
        """POST /v1/reviews with invalid API key should return 401."""
        headers = {
            "X-Project-ID": setup_project["project_id"],
            "Authorization": "Bearer invalid-key"
        }

        response = await client.post(
            "/v1/reviews/",
            json={"diff_content": "diff", "files": []},
            headers=headers
        )

        assert response.status_code == 401

    async def test_get_review_status_returns_pending(self, client, setup_project):
        """GET /v1/reviews/{id} should return review status."""
        headers = {
            "X-Project-ID": setup_project["project_id"],
            "Authorization": f"Bearer {setup_project['api_key']}"
        }

        # Submit review
        submit_response = await client.post(
            "/v1/reviews/",
            json={"diff_content": "diff", "files": ["test.py"]},
            headers=headers
        )
        review_id = submit_response.json()["review_id"]

        # Get status
        status_response = await client.get(
            f"/v1/reviews/{review_id}",
            headers=headers
        )

        assert status_response.status_code == 200
        data = status_response.json()
        assert data["review_id"] == review_id
        assert data["status"] in ["pending", "in_progress", "completed"]

    async def test_get_review_status_other_project_returns_403(self, client, setup_project, tmp_path):
        """GET /v1/reviews/{id} from different project should return 403."""
        # Create second project
        api_key_store = APIKeyStore(store_path=tmp_path / "api_keys.json")
        api_key2 = api_key_store.create_api_key("proj2", "bob")

        headers1 = {
            "X-Project-ID": setup_project["project_id"],
            "Authorization": f"Bearer {setup_project['api_key']}"
        }

        # Submit review with proj1
        submit_response = await client.post(
            "/v1/reviews/",
            json={"diff_content": "diff", "files": []},
            headers=headers1
        )
        review_id = submit_response.json()["review_id"]

        # Try to access with proj2
        headers2 = {
            "X-Project-ID": "proj2",
            "Authorization": f"Bearer {api_key2}"
        }

        status_response = await client.get(
            f"/v1/reviews/{review_id}",
            headers=headers2
        )

        assert status_response.status_code == 403

    async def test_rate_limiting_enforced(self, client, setup_project):
        """Submitting too many reviews should trigger rate limiting."""
        headers = {
            "X-Project-ID": setup_project["project_id"],
            "Authorization": f"Bearer {setup_project['api_key']}"
        }

        # Submit 11 reviews rapidly (capacity is 10)
        responses = []
        for i in range(11):
            response = await client.post(
                "/v1/reviews/",
                json={"diff_content": f"diff {i}", "files": []},
                headers=headers
            )
            responses.append(response)

        # At least one should be rate limited
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes
```

**Acceptance Criteria**:

- [ ] All review endpoints tested end-to-end
- [ ] Authentication/authorization tested
- [ ] Rate limiting tested
- [ ] Project isolation tested
- [ ] Tests pass

---

#### TASK-015: Write integration tests for project endpoints

- **File**: `/Users/samfakhreddine/repos/wfc/tests/rest_api/test_project_endpoints.py`
- **Complexity**: M (100-200 lines)
- **Dependencies**: [TASK-007, TASK-012]
- **Properties**: [S1, S2, I1]
- **Estimated Time**: 20min
- **Agent Level**: Haiku

**Description**: Test project creation and listing.

**Code Pattern Example**:

```python
"""
Integration tests for project endpoints.
"""

import pytest
from httpx import AsyncClient

from wfc.servers.rest_api.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestProjectEndpoints:
    """Integration tests for project endpoints."""

    async def test_create_project_returns_201_with_api_key(self, client):
        """POST /v1/projects should create project and return API key."""
        response = await client.post(
            "/v1/projects/",
            json={
                "project_id": "new-proj",
                "developer_id": "alice",
                "repo_path": "/absolute/path"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == "new-proj"
        assert "api_key" in data
        assert len(data["api_key"]) > 30

    async def test_create_duplicate_project_returns_409(self, client):
        """Creating duplicate project should return 409."""
        payload = {
            "project_id": "dup-proj",
            "developer_id": "alice",
            "repo_path": "/absolute/path"
        }

        # Create first time
        await client.post("/v1/projects/", json=payload)

        # Try to create again
        response = await client.post("/v1/projects/", json=payload)

        assert response.status_code == 409

    async def test_list_projects_returns_all_projects(self, client):
        """GET /v1/projects should list all projects."""
        # Create two projects
        await client.post(
            "/v1/projects/",
            json={"project_id": "proj1", "developer_id": "alice", "repo_path": "/path1"}
        )
        await client.post(
            "/v1/projects/",
            json={"project_id": "proj2", "developer_id": "bob", "repo_path": "/path2"}
        )

        # List projects
        response = await client.get("/v1/projects/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["projects"]) >= 2
        project_ids = [p["project_id"] for p in data["projects"]]
        assert "proj1" in project_ids
        assert "proj2" in project_ids
```

**Acceptance Criteria**:

- [ ] Project creation tested
- [ ] Duplicate project rejection tested
- [ ] Project listing tested
- [ ] Tests pass

---

#### TASK-016: Write integration tests for resource monitoring endpoints

- **File**: `/Users/samfakhreddine/repos/wfc/tests/rest_api/test_resource_endpoints.py`
- **Complexity**: S (50-100 lines)
- **Dependencies**: [TASK-008, TASK-012]
- **Properties**: [P2]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Test pool and rate limit status endpoints.

**Code Pattern Example**:

```python
"""
Integration tests for resource monitoring endpoints.
"""

import pytest
from httpx import AsyncClient

from wfc.servers.rest_api.main import app
from wfc.servers.rest_api.auth import APIKeyStore


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def setup_project(tmp_path):
    """Set up test project."""
    api_key_store = APIKeyStore(store_path=tmp_path / "api_keys.json")
    api_key = api_key_store.create_api_key("test-proj", "alice")

    return {
        "project_id": "test-proj",
        "api_key": api_key
    }


@pytest.mark.asyncio
class TestResourceEndpoints:
    """Integration tests for resource endpoints."""

    async def test_get_pool_status_returns_metrics(self, client, setup_project):
        """GET /v1/resources/pool should return pool metrics."""
        headers = {
            "X-Project-ID": setup_project["project_id"],
            "Authorization": f"Bearer {setup_project['api_key']}"
        }

        response = await client.get("/v1/resources/pool", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "max_worktrees" in data
        assert "active_worktrees" in data
        assert "available_capacity" in data
        assert data["max_worktrees"] == 10

    async def test_get_rate_limit_status_returns_metrics(self, client, setup_project):
        """GET /v1/resources/rate-limit should return rate limit metrics."""
        headers = {
            "X-Project-ID": setup_project["project_id"],
            "Authorization": f"Bearer {setup_project['api_key']}"
        }

        response = await client.get("/v1/resources/rate-limit", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "capacity" in data
        assert "refill_rate" in data
        assert "available_tokens" in data
        assert data["capacity"] == 10

    async def test_resource_endpoints_require_auth(self, client):
        """Resource endpoints should require authentication."""
        pool_response = await client.get("/v1/resources/pool")
        rate_response = await client.get("/v1/resources/rate-limit")

        assert pool_response.status_code == 401
        assert rate_response.status_code == 401
```

**Acceptance Criteria**:

- [ ] Pool status endpoint tested
- [ ] Rate limit status endpoint tested
- [ ] Authentication required
- [ ] Tests pass

---

## PHASE 7: DOCUMENTATION & DEPLOYMENT (Week 2, Day 5)

### 7.1 - Documentation

#### TASK-017: Write REST API usage documentation

- **File**: `/Users/samfakhreddine/repos/wfc/docs/REST_API.md`
- **Complexity**: M (100-200 lines)
- **Dependencies**: [TASK-009]
- **Properties**: []
- **Estimated Time**: 25min
- **Agent Level**: Haiku

**Description**: Comprehensive API documentation with examples.

**Content Pattern**:

```markdown
# WFC REST API

Multi-tenant code review and project management API.

## Quick Start

### 1. Create Project

```bash
curl -X POST http://localhost:8000/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "my-project",
    "developer_id": "alice",
    "repo_path": "/absolute/path/to/repo"
  }'
```

Response:

```json
{
  "project_id": "my-project",
  "api_key": "generated-api-key-here",
  "created_at": "2026-02-21T14:00:00Z"
}
```

**IMPORTANT**: Store the API key securely. It cannot be retrieved later.

### 2. Submit Code Review

```bash
curl -X POST http://localhost:8000/v1/reviews/ \
  -H "Content-Type: application/json" \
  -H "X-Project-ID: my-project" \
  -H "Authorization: Bearer <api-key>" \
  -d '{
    "diff_content": "diff content here",
    "files": ["file1.py", "file2.py"]
  }'
```

Response (202 Accepted):

```json
{
  "review_id": "uuid-here",
  "status": "pending",
  "submitted_at": "2026-02-21T14:00:00Z",
  "project_id": "my-project"
}
```

### 3. Check Review Status

```bash
curl -X GET http://localhost:8000/v1/reviews/<review-id> \
  -H "X-Project-ID: my-project" \
  -H "Authorization: Bearer <api-key>"
```

Response:

```json
{
  "review_id": "uuid",
  "status": "completed",
  "project_id": "my-project",
  "developer_id": "alice",
  "submitted_at": "2026-02-21T14:00:00Z",
  "completed_at": "2026-02-21T14:05:00Z",
  "consensus_score": 8.5,
  "passed": true,
  "findings": [...]
}
```

## Endpoints

### Projects

- `POST /v1/projects/` - Create new project
- `GET /v1/projects/` - List all projects

### Reviews

- `POST /v1/reviews/` - Submit code for review
- `GET /v1/reviews/{review_id}` - Get review status

### Resources

- `GET /v1/resources/pool` - Worktree pool status
- `GET /v1/resources/rate-limit` - Rate limit status

### Health

- `GET /` - Health check

## Authentication

All endpoints except `POST /v1/projects/` and `GET /v1/projects/` require:

- `X-Project-ID` header: Your project ID
- `Authorization` header: `Bearer <api-key>`

## Rate Limiting

- Capacity: 10 requests/project
- Refill rate: 10 tokens/second
- Returns 429 when exceeded

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message",
  "detail": "Additional details",
  "timestamp": "2026-02-21T14:00:00Z"
}
```

Common status codes:

- 401 Unauthorized: Invalid/missing API key
- 403 Forbidden: Accessing other project's resources
- 404 Not Found: Resource not found
- 409 Conflict: Duplicate project
- 429 Too Many Requests: Rate limit exceeded
- 500 Internal Server Error: Server error

```

**Acceptance Criteria**:

- [ ] All endpoints documented
- [ ] curl examples provided
- [ ] Authentication explained
- [ ] Error responses documented

---

#### TASK-018: Add REST API section to main README

- **File**: `/Users/samfakhreddine/repos/wfc/README.md` (append)
- **Complexity**: XS (< 10 lines)
- **Dependencies**: [TASK-017]
- **Properties**: []
- **Estimated Time**: 5min
- **Agent Level**: Haiku

**Description**: Add REST API section to README with link to docs.

**Code Pattern Example**:

```markdown
## REST API

WFC provides a production-ready REST API for multi-tenant code review:

```bash
# Start server
uv run python -m wfc.servers.rest_api.main

# Create project
curl -X POST http://localhost:8000/v1/projects/ ...

# Submit review
curl -X POST http://localhost:8000/v1/reviews/ ...
```

See [REST API Documentation](docs/REST_API.md) for full details.

```

**Acceptance Criteria**:

- [ ] README updated
- [ ] Link to full documentation added

---

### 7.2 - Deployment Configuration

#### TASK-019: Add Dockerfile for REST API server

- **File**: `/Users/samfakhreddine/repos/wfc/Dockerfile.rest_api`
- **Complexity**: S (50-100 lines)
- **Dependencies**: [TASK-009]
- **Properties**: []
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Production Dockerfile for containerized deployment.

**Code Pattern Example**:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY wfc/ ./wfc/

# Install dependencies
RUN uv pip install --system -e ".[api]"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Run server
CMD ["uvicorn", "wfc.servers.rest_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Acceptance Criteria**:

- [ ] Dockerfile builds successfully
- [ ] Container runs and responds to health checks
- [ ] Port 8000 exposed

---

#### TASK-020: Add docker-compose.yml for local development

- **File**: `/Users/samfakhreddine/repos/wfc/docker-compose.yml`
- **Complexity**: S (50-100 lines)
- **Dependencies**: [TASK-019]
- **Properties**: []
- **Estimated Time**: 10min
- **Agent Level**: Haiku

**Description**: Docker Compose setup for local testing.

**Code Pattern Example**:

```yaml
version: '3.8'

services:
  wfc-rest-api:
    build:
      context: .
      dockerfile: Dockerfile.rest_api
    ports:
      - "8000:8000"
    volumes:
      - ./wfc:/app/wfc:ro  # Mount source for development
      - wfc-data:/root/.wfc  # Persist API keys and reviews
    environment:
      - LOG_LEVEL=info
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

volumes:
  wfc-data:
```

**Acceptance Criteria**:

- [ ] docker-compose up starts server
- [ ] API accessible at <http://localhost:8000>
- [ ] Data persisted in volume

---

## PHASE 8: SECURITY HARDENING (Week 3, Day 1)

### 8.1 - Security Enhancements

#### TASK-021: Add request logging middleware

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/main.py` (append)
- **Complexity**: S (50-100 lines)
- **Dependencies**: [TASK-009]
- **Properties**: [S4]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Log all requests with sanitized headers (no API keys in logs).

**Code Pattern Example**:

```python
# Add to main.py

import time
from fastapi import Request


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with sanitized headers."""
    start_time = time.time()

    # Sanitize authorization header
    headers = dict(request.headers)
    if "authorization" in headers:
        headers["authorization"] = "Bearer ***"

    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"from {request.client.host}"
    )

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(
        f"Response: {response.status_code} "
        f"({duration:.3f}s)"
    )

    return response
```

**Acceptance Criteria**:

- [ ] All requests logged
- [ ] API keys sanitized in logs
- [ ] Request duration logged

---

#### TASK-022: Add input validation middleware

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/main.py` (append)
- **Complexity**: S (50-100 lines)
- **Dependencies**: [TASK-021]
- **Properties**: [S1, S4]
- **Estimated Time**: 15min
- **Agent Level**: Sonnet

**Description**: Validate all inputs for size limits and suspicious patterns.

**Code Pattern Example**:

```python
# Add to main.py

MAX_DIFF_SIZE = 1_000_000  # 1MB


@app.middleware("http")
async def validate_request_size(request: Request, call_next):
    """Validate request body size."""
    if request.method in ["POST", "PUT", "PATCH"]:
        content_length = request.headers.get("content-length")

        if content_length and int(content_length) > MAX_DIFF_SIZE:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"error": f"Request too large. Max {MAX_DIFF_SIZE} bytes."}
            )

    return await call_next(request)
```

**Acceptance Criteria**:

- [ ] Request size validated
- [ ] Returns 413 for oversized requests
- [ ] Tests pass

---

## PHASE 9: PERFORMANCE OPTIMIZATION (Week 3, Day 2)

### 9.1 - Async Review Execution

#### TASK-023: Make ReviewOrchestrator async-compatible

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/scripts/orchestrators/review/orchestrator.py`
- **Complexity**: M (100-200 lines)
- **Dependencies**: []
- **Properties**: [P1]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet

**Description**: Add async wrapper methods to ReviewOrchestrator for non-blocking execution.

**Code Pattern Example**:

```python
# Add to ReviewOrchestrator class

import asyncio
from typing import Dict, Any


async def run_review_async(
    self,
    diff_content: str,
    files: list
) -> Dict[str, Any]:
    """
    Run review asynchronously (non-blocking).

    Args:
        diff_content: Git diff content
        files: List of changed files

    Returns:
        Review result dict
    """
    loop = asyncio.get_event_loop()

    # Run sync review in thread pool
    return await loop.run_in_executor(
        None,
        self.run_review,
        diff_content,
        files
    )
```

**Acceptance Criteria**:

- [ ] async wrapper added
- [ ] Non-blocking execution verified
- [ ] Backward compatible with sync callers
- [ ] Tests pass

---

### 9.2 - Connection Pooling

#### TASK-024: Add connection pool configuration

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/main.py` (append)
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-009]
- **Properties**: [P3]
- **Estimated Time**: 10min
- **Agent Level**: Haiku

**Description**: Configure uvicorn for production-ready connection pooling.

**Code Pattern Example**:

```python
# Update __main__ block

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "wfc.servers.rest_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable in production
        log_level="info",
        workers=4,  # Multi-process workers
        limit_concurrency=100,  # Max concurrent connections
        timeout_keep_alive=5,  # Keep-alive timeout
    )
```

**Acceptance Criteria**:

- [ ] Worker count configured
- [ ] Connection limits set
- [ ] Keep-alive timeout configured

---

## PHASE 10: MONITORING & OBSERVABILITY (Week 3, Day 3)

### 10.1 - Metrics Endpoint

#### TASK-025: Add Prometheus metrics endpoint

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/servers/rest_api/metrics.py`
- **Complexity**: M (100-200 lines)
- **Dependencies**: [TASK-009]
- **Properties**: [P4]
- **Estimated Time**: 25min
- **Agent Level**: Sonnet

**Description**: Expose Prometheus metrics for monitoring.

**Code Pattern Example**:

```python
"""
Prometheus metrics for WFC REST API.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response


# Metrics
review_requests_total = Counter(
    "wfc_review_requests_total",
    "Total review requests",
    ["project_id", "status"]
)

review_duration_seconds = Histogram(
    "wfc_review_duration_seconds",
    "Review execution duration",
    ["project_id"]
)

active_reviews = Gauge(
    "wfc_active_reviews",
    "Number of reviews in progress"
)

worktree_pool_size = Gauge(
    "wfc_worktree_pool_size",
    "Number of active worktrees"
)


def get_metrics() -> Response:
    """Return Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

**Acceptance Criteria**:

- [ ] Metrics defined for key operations
- [ ] GET /metrics endpoint added
- [ ] Metrics update on events

---

## SUMMARY

**Total Tasks**: 25 (core implementation) + 17 (testing/docs/deployment) = 42 tasks

**Estimated Timeline**:

- Week 1: Core implementation (PHASE 0-3)
- Week 2: Routes, testing, docs (PHASE 4-7)
- Week 3: Security, performance, monitoring (PHASE 8-10)

**Key Deliverables**:

1. Production-ready FastAPI REST server
2. Multi-tenant authentication/authorization
3. Async review execution with status tracking
4. Comprehensive test suite (95%+ coverage)
5. Docker deployment configuration
6. Prometheus metrics for observability

**Dependencies**:

- FastAPI 0.115+
- uvicorn 0.32+
- pydantic 2.9+
- httpx 0.27+ (testing)
- pytest-asyncio (testing)
- filelock (already used)

**Backward Compatibility**:

- Reuses existing ReviewOrchestrator, ProjectContext, WorktreePool, TokenBucket
- MCP server continues to work independently
- No breaking changes to existing code
