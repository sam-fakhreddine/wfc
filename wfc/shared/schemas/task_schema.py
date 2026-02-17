"""
WFC Task Schema - ELEGANT & SIMPLE

Defines the structure for tasks in TASKS.md (from wfc-plan, consumed by wfc-implement)

Design: Simple dataclasses, clear validation, no over-engineering.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskComplexity(Enum):
    """Task complexity levels for model selection."""

    S = "S"  # Small: 1-2 hours, simple changes, haiku
    M = "M"  # Medium: half-day, moderate complexity, sonnet
    L = "L"  # Large: 1-2 days, complex changes, opus
    XL = "XL"  # Extra Large: 2+ days, very complex, opus


class TaskStatus(Enum):
    """Task execution states."""

    QUEUED = "QUEUED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    REVIEW_RETRY = "REVIEW_RETRY"
    MERGING = "MERGING"
    MERGED = "MERGED"
    INTEGRATION_TEST = "INTEGRATION_TEST"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    PLAN_GENERATED = "PLAN_GENERATED"


@dataclass
class Task:
    """
    A single implementation task.

    Used by: wfc-plan (creates), wfc-implement (executes), wfc-architecture (informs)
    """

    id: str  # e.g., "TASK-001"
    title: str  # Short title
    description: str  # What to implement
    acceptance_criteria: List[str]  # How to know it's done
    complexity: TaskComplexity  # S, M, L, XL

    # Dependencies and relationships
    dependencies: List[str] = field(default_factory=list)  # Other TASK-XXX IDs
    properties_satisfied: List[str] = field(default_factory=list)  # PROP-XXX IDs
    requirements: List[str] = field(default_factory=list)  # FR-XXX, NFR-XXX

    # Implementation hints
    files_likely_affected: List[str] = field(default_factory=list)
    test_requirements: List[str] = field(default_factory=list)

    # Execution state (populated during wfc-implement)
    status: TaskStatus = TaskStatus.QUEUED
    assigned_agent: Optional[str] = None
    worktree_path: Optional[str] = None
    branch_name: Optional[str] = None

    # Metadata
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate task on creation."""
        if not self.id.startswith("TASK-"):
            raise ValueError(f"Task ID must start with 'TASK-': {self.id}")

        if not self.title.strip():
            raise ValueError(f"Task {self.id} must have a non-empty title")

        if not self.description.strip():
            raise ValueError(f"Task {self.id} must have a non-empty description")

        if not self.acceptance_criteria:
            raise ValueError(f"Task {self.id} must have acceptance criteria")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "complexity": self.complexity.value,
            "dependencies": self.dependencies,
            "properties_satisfied": self.properties_satisfied,
            "requirements": self.requirements,
            "files_likely_affected": self.files_likely_affected,
            "test_requirements": self.test_requirements,
            "status": self.status.value,
            "assigned_agent": self.assigned_agent,
            "worktree_path": self.worktree_path,
            "branch_name": self.branch_name,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create Task from dictionary."""
        data = data.copy()
        data["complexity"] = TaskComplexity(data["complexity"])
        data["status"] = TaskStatus(data.get("status", "QUEUED"))
        return cls(**data)


@dataclass
class TaskGraph:
    """
    A dependency graph of tasks.

    Used by: wfc-implement (orchestration), wfc-architecture (visualization)
    """

    tasks: List[Task] = field(default_factory=list)

    def add(self, task: Task) -> None:
        """Add a task to the graph."""
        if any(t.id == task.id for t in self.tasks):
            raise ValueError(f"Task {task.id} already exists")
        self.tasks.append(task)

    def get(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return next((t for t in self.tasks if t.id == task_id), None)

    def validate_dag(self) -> bool:
        """
        Validate that the task graph is a DAG (Directed Acyclic Graph).

        Returns:
            True if valid DAG, False if cycles detected
        """
        # Simple DFS cycle detection
        visited = set()
        rec_stack = set()

        def has_cycle(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)

            task = self.get(task_id)
            if task:
                for dep_id in task.dependencies:
                    if dep_id not in visited:
                        if has_cycle(dep_id):
                            return True
                    elif dep_id in rec_stack:
                        return True

            rec_stack.remove(task_id)
            return False

        for task in self.tasks:
            if task.id not in visited:
                if has_cycle(task.id):
                    return False

        return True

    def get_dependency_levels(self) -> Dict[str, int]:
        """
        Compute dependency levels (0 = no deps, 1 = depends on level 0, etc.)

        Returns:
            Dict mapping task_id to level
        """
        levels = {}

        def compute_level(task_id: str) -> int:
            if task_id in levels:
                return levels[task_id]

            task = self.get(task_id)
            if not task or not task.dependencies:
                levels[task_id] = 0
                return 0

            max_dep_level = max(compute_level(dep) for dep in task.dependencies)
            levels[task_id] = max_dep_level + 1
            return levels[task_id]

        for task in self.tasks:
            compute_level(task.id)

        return levels

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {"tasks": [t.to_dict() for t in self.tasks]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskGraph":
        """Create TaskGraph from dictionary."""
        tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return cls(tasks=tasks)


# Example usage
if __name__ == "__main__":
    # Create tasks
    task1 = Task(
        id="TASK-001",
        title="Implement auth middleware",
        description="Create authentication middleware for protected routes",
        acceptance_criteria=[
            "Middleware validates JWT tokens",
            "Invalid tokens are rejected with 401",
            "Valid tokens pass through to handler",
        ],
        complexity=TaskComplexity.M,
        properties_satisfied=["PROP-001"],
        files_likely_affected=["middleware/auth.py", "tests/test_auth.py"],
    )

    task2 = Task(
        id="TASK-002",
        title="Add auth to user routes",
        description="Apply auth middleware to user management routes",
        acceptance_criteria=["All user routes require authentication"],
        complexity=TaskComplexity.S,
        dependencies=["TASK-001"],  # Depends on auth middleware
        files_likely_affected=["routes/users.py"],
    )

    # Create graph
    graph = TaskGraph()
    graph.add(task1)
    graph.add(task2)

    print(f"Valid DAG: {graph.validate_dag()}")
    print(f"Dependency levels: {graph.get_dependency_levels()}")
