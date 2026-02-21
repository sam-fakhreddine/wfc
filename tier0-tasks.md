---
title: Multi-Tenant WFC - Tier 0 MVP (Validation-First)
status: active
created: 2026-02-21T10:30:00Z
updated: 2026-02-21T10:30:00Z
tasks_total: 7
tasks_completed: 0
complexity: M
---

# Tier 0 MVP: Project Isolation & Concurrency Safety

**Goal**: Validate demand by implementing ONLY the core isolation fixes that address the 6 critical race conditions. If this solves 80% of the problem, STOP HERE.

**Target**: 1 developer, 6 local projects, 0 collisions

**Timeline**: 1 week (7 tasks × 4 hours avg = 28 hours)

---

## TASK-001: Add ProjectContext to wfc_config.py

- **File**: `wfc/shared/config/wfc_config.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: []
- **Properties**: [M1-Project-Isolation]
- **Estimated Time**: 30min
- **Agent Level**: Haiku

### Description

Add ProjectContext dataclass and factory method to WFCConfig class. This is the foundation for all multi-tenant isolation.

### Code Pattern Example

```python
from dataclasses import dataclass
from pathlib import Path
import re

@dataclass
class ProjectContext:
    """Project isolation context for multi-tenant WFC."""
    project_id: str
    developer_id: str
    repo_path: Path
    worktree_dir: Path
    metrics_dir: Path
    output_dir: Path

    def __post_init__(self):
        """Ensure all paths are absolute."""
        self.repo_path = Path(self.repo_path).resolve()
        self.worktree_dir = Path(self.worktree_dir).resolve()
        self.metrics_dir = Path(self.metrics_dir).resolve()
        self.output_dir = Path(self.output_dir).resolve()

class WFCConfig:
    # ... existing methods ...

    def create_project_context(
        self,
        project_id: str,
        developer_id: str,
        repo_path: Optional[Path] = None
    ) -> ProjectContext:
        """Create ProjectContext with namespaced paths."""
        # Validate inputs
        if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', project_id):
            raise ValueError(f"Invalid project_id: {project_id}")
        if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', developer_id):
            raise ValueError(f"Invalid developer_id: {developer_id}")

        if repo_path is None:
            repo_path = self.project_root

        base_metrics_dir = Path(self.get("metrics.directory", str(Path.home() / ".wfc" / "metrics")))

        return ProjectContext(
            project_id=project_id,
            developer_id=developer_id,
            repo_path=Path(repo_path),
            worktree_dir=Path(repo_path) / ".worktrees" / project_id,
            metrics_dir=base_metrics_dir / project_id,
            output_dir=Path(repo_path) / ".wfc" / "output" / project_id,
        )
```

### Acceptance Criteria

- [ ] ProjectContext dataclass added after imports
- [ ] All 6 fields present (project_id, developer_id, repo_path, worktree_dir, metrics_dir, output_dir)
- [ ] `__post_init__` converts paths to absolute
- [ ] create_project_context factory method added to WFCConfig
- [ ] Input validation (regex) for project_id and developer_id
- [ ] Namespaced paths: `.worktrees/{project_id}/`, `~/.wfc/metrics/{project_id}/`
- [ ] Unit test passes: `test_create_project_context`

---

## TASK-002: Update WorktreeOperations for project namespacing

- **File**: `wfc/gitwork/api/worktree.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-001]
- **Properties**: [M1-Project-Isolation, PROP-S001]
- **Estimated Time**: 45min
- **Agent Level**: Haiku

### Description

Update WorktreeOperations class to accept project_id and namespace both worktree paths AND branch names.

### Code Pattern Example

```python
class WorktreeOperations:
    def __init__(self, worktree_dir: str = ".worktrees", project_id: Optional[str] = None):
        self.worktree_dir = worktree_dir
        self.project_id = project_id

    def _worktree_path(self, task_id: str) -> Path:
        """Return the absolute path for a task's worktree, anchored to repo root."""
        root = _repo_root()
        if root:
            if self.project_id:
                # Multi-tenant: .worktrees/{project_id}/wfc-{task_id}
                return Path(root) / self.worktree_dir / self.project_id / f"wfc-{task_id}"
            else:
                # Legacy: .worktrees/wfc-{task_id}
                return Path(root) / self.worktree_dir / f"wfc-{task_id}"

        # Fall back to relative path if git command fails
        if self.project_id:
            return Path(self.worktree_dir) / self.project_id / f"wfc-{task_id}"
        return Path(self.worktree_dir) / f"wfc-{task_id}"

    def create(self, task_id: str, base_ref: str = "develop") -> Dict:
        """Create a new worktree for the given task."""
        worktree_path = self._worktree_path(task_id)

        # Namespace branch name too
        if self.project_id:
            branch_name = f"wfc/{self.project_id}/{task_id}"
        else:
            branch_name = f"wfc/{task_id}"

        # ... rest of create logic
```

### Acceptance Criteria

- [ ] project_id parameter added to `__init__`
- [ ] Worktree path includes project_id when set: `.worktrees/{project_id}/wfc-{task_id}`
- [ ] Git branch name includes project_id when set: `wfc/{project_id}/{task_id}`
- [ ] Falls back to legacy path/branch when project_id is None (backward compat)
- [ ] Unit test: `WorktreeOperations(project_id="proj1")._worktree_path("test")` → `.worktrees/proj1/wfc-test`
- [ ] Unit test: `WorktreeOperations()._worktree_path("test")` → `.worktrees/wfc-test`
- [ ] Integration test: Two projects create same task_id → different paths AND branches

---

## TASK-003: Add FileLock to file_io.py

- **File**: `wfc/shared/file_io.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: []
- **Properties**: [M2-Concurrent-Access-Safety]
- **Estimated Time**: 30min
- **Agent Level**: Haiku

### Description

Add filelock dependency and implement safe_append_text function with atomic writes and path traversal prevention.

### Code Pattern Example

```python
from filelock import FileLock, Timeout
from pathlib import Path

def safe_append_text(path: Path, content: str, ensure_parent: bool = True, timeout: int = 10) -> None:
    """
    Append to text file safely with file locking for concurrent writes.

    Args:
        path: Path to text file
        content: String content to append
        ensure_parent: Create parent directory if needed (default: True)
        timeout: Lock timeout in seconds (default: 10)

    Raises:
        FileIOError: If file can't be written or lock times out
    """
    try:
        # Validate path (prevent traversal)
        path = Path(path).resolve()
        lock_path = path.parent / f"{path.name}.lock"
        lock_path = lock_path.resolve()

        # Ensure lock file is in same directory as target
        if lock_path.parent != path.parent:
            raise FileIOError(f"Lock file path traversal detected: {lock_path}")

        # Create parent directory if needed
        if ensure_parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        # Acquire lock (creates .lock file alongside target)
        with FileLock(lock_path, timeout=timeout):
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)

    except Timeout:
        raise FileIOError(f"Failed to acquire lock for {path} within {timeout}s")
    except Exception as e:
        raise FileIOError(f"Error appending to {path}: {e}")

def append_text(path: Path, content: str, ensure_parent: bool = True) -> None:
    """Append to text file safely (legacy wrapper - calls safe_append_text)."""
    safe_append_text(path, content, ensure_parent=ensure_parent)
```

### Acceptance Criteria

- [ ] filelock added to pyproject.toml dependencies (>=3.13.0)
- [ ] safe_append_text function added with FileLock
- [ ] Path traversal validation (rejects `../../etc/passwd`)
- [ ] Creates .lock file alongside target
- [ ] Timeout parameter (default 10s)
- [ ] append_text delegates to safe_append_text (backward compat)
- [ ] Unit test: 10 concurrent appends result in correct line count
- [ ] Unit test: Rejects paths with `..` or outside project root

---

## TASK-004: Add project_id to AutoTelemetry

- **File**: `wfc/shared/telemetry_auto.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-001]
- **Properties**: [M1-Project-Isolation]
- **Estimated Time**: 20min
- **Agent Level**: Haiku

### Description

Update AutoTelemetry to accept project_id and namespace metrics directory.

### Code Pattern Example

```python
class AutoTelemetry:
    def __init__(self, storage_dir: Optional[Path] = None, project_id: Optional[str] = None):
        """Initialize auto telemetry with storage directory and optional project_id"""
        if storage_dir is None:
            # Default: ~/.wfc/telemetry/ or ~/.wfc/telemetry/{project_id}/
            base_dir = Path.home() / ".wfc" / "telemetry"
            if project_id:
                storage_dir = base_dir / project_id
            else:
                storage_dir = base_dir

        self.project_id = project_id
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        # ... rest of __init__

# Global instances per project
_telemetry_instances: Dict[str, AutoTelemetry] = {}

def get_telemetry(project_id: Optional[str] = None) -> AutoTelemetry:
    """Get telemetry instance for project (or global if project_id=None)"""
    key = project_id or "_global"

    if key not in _telemetry_instances:
        _telemetry_instances[key] = AutoTelemetry(project_id=project_id)

    return _telemetry_instances[key]
```

### Acceptance Criteria

- [ ] project_id parameter added to `__init__`
- [ ] Metrics stored in `~/.wfc/telemetry/{project_id}/` when set
- [ ] Falls back to `~/.wfc/telemetry/` when None (backward compat)
- [ ] get_telemetry factory accepts project_id
- [ ] Returns separate instance per project_id
- [ ] Unit test: `get_telemetry("proj1")` != `get_telemetry("proj2")`

---

## TASK-005: Add developer_id to knowledge_writer.py

- **File**: `wfc/scripts/knowledge/knowledge_writer.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-003]
- **Properties**: [M3-Developer-Attribution, M2-Concurrent-Access-Safety]
- **Estimated Time**: 30min
- **Agent Level**: Haiku

### Description

Add developer_id field to LearningEntry and update knowledge writing to use FileLock for atomic read-modify-write.

### Code Pattern Example

```python
from filelock import FileLock

@dataclass
class LearningEntry:
    """A new knowledge entry to append."""
    text: str
    section: str
    reviewer_id: str
    source: str
    developer_id: str = ""  # NEW: Developer who triggered review
    date: str = ""

    def __post_init__(self) -> None:
        if not self.date:
            self.date = date.today().isoformat()

def append_entry(entry: LearningEntry) -> None:
    """Append knowledge entry with atomic read-modify-write under lock."""
    knowledge_file = get_knowledge_path(entry.reviewer_id)
    lock_file = knowledge_file.with_suffix('.lock')

    with FileLock(lock_file, timeout=10):
        # Read existing content
        if knowledge_file.exists():
            with open(knowledge_file) as f:
                existing = f.read()
        else:
            existing = ""

        # Format new entry (now includes developer_id)
        formatted = _format_entry(entry)

        # Write atomically (lock held throughout)
        with open(knowledge_file, 'w') as f:
            f.write(existing + formatted)

def _format_entry(entry: LearningEntry) -> str:
    """Format entry including developer attribution."""
    header = f"## {entry.section} ({entry.date})"
    if entry.developer_id:
        header += f" - by {entry.developer_id}"

    return f"{header}\n\n{entry.text}\n\n"
```

### Acceptance Criteria

- [ ] developer_id field added to LearningEntry
- [ ] Default empty string for backward compat
- [ ] _format_entry includes developer_id in header
- [ ] append_entry uses FileLock for full read-modify-write
- [ ] Lock held for entire operation (read + format + write)
- [ ] Unit test: Concurrent appends don't corrupt file
- [ ] Unit test: Entry includes developer attribution

---

## TASK-006: Update worktree-manager.sh for developer attribution

- **File**: `wfc/gitwork/scripts/worktree-manager.sh`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-002]
- **Properties**: [M3-Developer-Attribution]
- **Estimated Time**: 20min
- **Agent Level**: Haiku

### Description

Add --developer-id flag and override GIT_AUTHOR_* env vars in created worktrees.

### Code Pattern Example

```bash
PROJECT_ID=""
DEVELOPER_ID=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project-id)
      PROJECT_ID="$2"
      shift 2
      ;;
    --developer-id)
      DEVELOPER_ID="$2"
      shift 2
      ;;
    *)
      COMMAND="$1"
      shift
      break
      ;;
  esac
done

# In create() function, after worktree is created:
if [[ -n "$DEVELOPER_ID" ]]; then
  # Set git config in worktree
  git -C "$DEST" config user.name "WFC Agent ($DEVELOPER_ID)"
  git -C "$DEST" config user.email "wfc+$DEVELOPER_ID@noreply.local"
  echo -e "  ${GREEN}Set git author to $DEVELOPER_ID${NC}"
fi
```

### Acceptance Criteria

- [ ] --project-id flag parsed correctly
- [ ] --developer-id flag parsed correctly
- [ ] Git config set in worktree when developer_id provided
- [ ] Git author format: `WFC Agent (developer_id)`
- [ ] Git email format: `wfc+developer_id@noreply.local`
- [ ] Test: commits in worktree show correct author

---

## TASK-007: Acceptance test for Tier 0 MVP

- **File**: `tests/tier0/test_concurrent_reviews.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-001, TASK-002, TASK-003, TASK-004, TASK-005, TASK-006]
- **Properties**: [M1, M2, M3]
- **Estimated Time**: 45min
- **Agent Level**: Sonnet

### Description

Integration test that validates all 6 race conditions are fixed. This is the STOP/GO gate for Tier 0.

### Code Pattern Example

```python
import pytest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def test_six_concurrent_reviews_zero_collisions():
    """
    Tier 0 MVP acceptance test (from BA Section 11, Test 1).

    If this passes, Tier 0 solves the problem. STOP HERE.
    If this fails, continue to Phase 1 (full MCP/REST).
    """
    # Setup: 6 projects
    projects = [f"proj{i}" for i in range(1, 7)]

    # Run 6 concurrent reviews
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [
            executor.submit(run_review, project_id, "test-task")
            for project_id in projects
        ]
        results = [f.result() for f in futures]

    # Acceptance criteria (from BA):
    # ✅ All 6 complete successfully
    assert all(r.success for r in results), "Some reviews failed"

    # ✅ No worktree collisions
    worktree_paths = [r.worktree_path for r in results]
    assert len(set(worktree_paths)) == 6, "Worktree path collision detected"

    # ✅ 6 separate reports: REVIEW-proj{1-6}-test-task.md
    report_paths = [r.report_path for r in results]
    assert len(set(report_paths)) == 6, "Report path collision detected"
    for i, path in enumerate(report_paths, 1):
        assert f"proj{i}" in str(path), f"Report path doesn't include project_id: {path}"

    # ✅ KNOWLEDGE.md not corrupted
    knowledge_file = Path.home() / ".wfc" / "knowledge" / "global" / "reviewers" / "security" / "KNOWLEDGE.md"
    if knowledge_file.exists():
        content = knowledge_file.read_text()
        # Should be valid markdown (not garbled from concurrent writes)
        assert "##" in content or content == "", "KNOWLEDGE.md appears corrupted"

def test_no_branch_name_collisions():
    """Test that branch names are namespaced (TASK-002 fix)."""
    from wfc.gitwork.api.worktree import WorktreeOperations

    ops1 = WorktreeOperations(project_id="proj1")
    ops2 = WorktreeOperations(project_id="proj2")

    # Both create same task_id
    path1 = ops1._worktree_path("feature-001")
    path2 = ops2._worktree_path("feature-001")

    # Paths must be different
    assert path1 != path2
    assert "proj1" in str(path1)
    assert "proj2" in str(path2)

def test_knowledge_concurrent_writes():
    """Test that FileLock prevents knowledge corruption (TASK-003, TASK-005)."""
    from wfc.scripts.knowledge.knowledge_writer import append_entry, LearningEntry
    import tempfile
    import shutil

    # 10 concurrent writes
    entries = [
        LearningEntry(
            text=f"Finding {i}",
            section="Test",
            reviewer_id="test",
            source="test",
            developer_id=f"dev{i}"
        )
        for i in range(10)
    ]

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(append_entry, e) for e in entries]
        [f.result() for f in futures]

    # Knowledge file should have exactly 10 entries
    # (no corruption from concurrent writes)
    knowledge_file = get_knowledge_path("test")
    content = knowledge_file.read_text()

    # Count section headers
    section_count = content.count("## Test")
    assert section_count == 10, f"Expected 10 entries, found {section_count}"
```

### Acceptance Criteria

- [ ] test_six_concurrent_reviews_zero_collisions passes
- [ ] test_no_branch_name_collisions passes
- [ ] test_knowledge_concurrent_writes passes
- [ ] All 6 race conditions from BA Section 2 are fixed
- [ ] **DECISION GATE**: If all pass → Tier 0 SUCCESS, evaluate if Phase 1 needed

---

## Success Criteria (Tier 0 MVP)

If these 7 tasks complete successfully:

1. ✅ **0% worktree collision rate** (TEST-007 validates)
2. ✅ **0% knowledge corruption** (TEST-007 validates)
3. ✅ **Project isolation working** (namespaced paths)
4. ✅ **Developer attribution working** (git author set)
5. ✅ **File locking prevents races** (concurrent writes safe)

**DECISION**: Does this solve 80% of your multi-project use case?

- **YES** → STOP HERE. Tier 0 is sufficient.
- **NO** → Proceed to Phase 1 (full 65-task plan)

---

## What This DOESN'T Include (Full Plan Has)

- MCP interface (12 tasks)
- REST API (20 tasks)
- PostgreSQL/Redis infrastructure (3 tasks)
- API key management (3 tasks)
- Token bucket rate limiting (5 tasks)
- Orphan cleanup cron (1 task)
- WebSocket progress streaming
- RBAC

**Tier 0 is validation-first**: Prove the core multi-tenant fixes work before building the full hybrid architecture.
