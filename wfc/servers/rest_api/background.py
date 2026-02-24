"""
Background task execution and review status tracking for WFC REST API.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from filelock import FileLock

from wfc.servers.rest_api.models import (
    ReviewFinding,
    ReviewStatus,
    ReviewStatusResponse,
)

if TYPE_CHECKING:
    from wfc.shared.config.wfc_config import ProjectContext

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
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "consensus_score": None,
            "passed": None,
            "findings": [],
            "error_message": None,
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

        return ReviewStatusResponse(
            review_id=data["review_id"],
            status=ReviewStatus(data["status"]),
            project_id=data["project_id"],
            developer_id=data["developer_id"],
            submitted_at=datetime.fromisoformat(data["submitted_at"]),
            completed_at=(
                datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None
            ),
            consensus_score=data["consensus_score"],
            passed=data["passed"],
            findings=[ReviewFinding(**f) for f in data["findings"]],
            error_message=data["error_message"],
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
        findings: list,
    ) -> None:
        """Mark review as completed with results."""
        review_path = self.reviews_dir / f"{review_id}.json"
        lock_path = review_path.with_suffix(".json.lock")

        with FileLock(lock_path, timeout=10):
            with open(review_path, "r") as f:
                data = json.load(f)

            data["status"] = ReviewStatus.COMPLETED.value
            data["completed_at"] = datetime.now(timezone.utc).isoformat()
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
            data["completed_at"] = datetime.now(timezone.utc).isoformat()
            data["error_message"] = error_message

            with open(review_path, "w") as f:
                json.dump(data, f, indent=2)

    def list_reviews(self, project_id: str) -> List[ReviewStatusResponse]:
        """
        List all reviews for a project.

        Args:
            project_id: Project identifier

        Returns:
            List of ReviewStatusResponse for the project
        """
        reviews = []
        for review_path in self.reviews_dir.glob("*.json"):
            if review_path.name.endswith(".lock"):
                continue

            lock_path = review_path.with_suffix(".json.lock")
            with FileLock(lock_path, timeout=10):
                with open(review_path, "r") as f:
                    data = json.load(f)

            if data["project_id"] == project_id:
                reviews.append(
                    ReviewStatusResponse(
                        review_id=data["review_id"],
                        status=ReviewStatus(data["status"]),
                        project_id=data["project_id"],
                        developer_id=data["developer_id"],
                        submitted_at=datetime.fromisoformat(data["submitted_at"]),
                        completed_at=(
                            datetime.fromisoformat(data["completed_at"])
                            if data["completed_at"]
                            else None
                        ),
                        consensus_score=data["consensus_score"],
                        passed=data["passed"],
                        findings=[ReviewFinding(**f) for f in data["findings"]],
                        error_message=data["error_message"],
                    )
                )

        return reviews


async def execute_review_task(
    review_id: str,
    project_context: "ProjectContext",
    diff_content: str,
    files: list,
    review_store: ReviewStatusStore,
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
        review_store.update_status(review_id, ReviewStatus.IN_PROGRESS)

        from wfc.scripts.orchestrators.review.orchestrator import ReviewOrchestrator

        orchestrator = ReviewOrchestrator(project_context=project_context)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            orchestrator.run_review,
            diff_content,
            files,
        )

        consensus_score = result.get("consensus_score", 0.0)
        passed = result.get("passed", False)
        findings = result.get("findings", [])

        findings_data = [
            {
                "reviewer": f.get("reviewer", ""),
                "severity": f.get("severity", ""),
                "category": f.get("category", ""),
                "description": f.get("description", ""),
                "file_path": f.get("file_path"),
                "line_number": f.get("line_number"),
                "confidence": f.get("confidence", 50),
            }
            for f in findings
        ]

        review_store.complete_review(review_id, consensus_score, passed, findings_data)

    except Exception as e:
        logger.error(f"Review {review_id} failed: {e}", exc_info=True)
        review_store.fail_review(review_id, str(e))
