Now I have enough context. Let me create a comprehensive, ultra-granular TASKS.md file based on the BA document. I'll break down each file modification into atomic tasks optimized for lower-cost LLM agents.

Based on my analysis of the BA document and the existing WFC codebase, here's my extremely granular TASKS.md file for the Multi-Tenant WFC implementation:

---

# EXTREMELY GRANULAR TASKS.MD - MULTI-TENANT WFC IMPLEMENTATION

## Overview

This implementation plan breaks down the Multi-Tenant WFC feature into **65 ultra-granular tasks** (58 original + 7 infrastructure/security fixes from review), each designed for completion by lower-cost LLM agents (Haiku/Sonnet 3.5) in under 30 minutes. Each task modifies or creates exactly ONE file with explicit code patterns and minimal dependencies.

## Key Architectural Decisions

1. **ProjectContext dataclass**: Thread project_id, repo_path, worktree_dir, metrics_dir through all orchestrators
2. **Namespace isolation**: Worktrees at `.worktrees/{project_id}/wfc-{task_id}`, metrics at `~/.wfc/metrics/{project_id}/`
3. **File locking**: Use `filelock` library for atomic writes to shared KNOWLEDGE.md
4. **Developer attribution**: Tag all reviews/findings with developer_id for audit trail
5. **Interface abstraction**: ReviewInterface ABC allows both MCP and REST to reuse 90% of orchestrator code

---

## PHASE 1: SHARED CORE INFRASTRUCTURE (Weeks 1-2)

### 1.1 - Project Context & Configuration

#### TASK-001: Add project_context factory method to WFCConfig

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/shared/config/wfc_config.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-001a]
- **Properties**: [M1]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Add method to WFCConfig class to create ProjectContext from project_id and developer_id.

**Code Pattern Example**:

```python
def create_project_context(
    self,
    project_id: str,
    developer_id: str,
    repo_path: Optional[Path] = None
) -> ProjectContext:
    """Create ProjectContext with namespaced paths."""

    # Validate inputs
    import re
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

**Acceptance Criteria**:

- [ ] Method added to WFCConfig class
- [ ] Creates namespaced worktree_dir: `.worktrees/{project_id}/`
- [ ] Creates namespaced metrics_dir: `~/.wfc/metrics/{project_id}/`
- [ ] Creates namespaced output_dir: `.wfc/output/{project_id}/`
- [ ] Unit test passes: `test_create_project_context`

---

### 1.2 - Worktree Namespacing

#### TASK-002a: Update WorktreeOperations.**init** to accept project_id

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/gitwork/api/worktree.py`
- **Complexity**: XS (< 10 lines)
- **Dependencies**: []
- **Properties**: [M1]
- **Estimated Time**: 5min
- **Agent Level**: Haiku

**Description**: Modify `__init__` signature to accept optional project_id parameter.

**Code Pattern Example**:

```python
def __init__(self, worktree_dir: str = ".worktrees", project_id: Optional[str] = None):
    self.worktree_dir = worktree_dir
    self.project_id = project_id  # NEW
```

**Acceptance Criteria**:

- [ ] project_id parameter added to `__init__`
- [ ] Default is None for backward compatibility
- [ ] Stored as instance variable
- [ ] Existing tests still pass

---

#### TASK-002b: Update _worktree_path to namespace by project_id

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/gitwork/api/worktree.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-002a]
- **Properties**: [M1]
- **Estimated Time**: 10min
- **Agent Level**: Haiku

**Description**: Modify `_worktree_path` method to include project_id in path.

**Code Pattern Example**:

```python
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
    return Path(self.worktree_dir) / f"wfc-{task_id}"  # Note: branch also needs namespacing in create()
```

**CRITICAL**: Also update git worktree branch name to include project_id:

```python
if self.project_id:
    branch_name = f"wfc/{self.project_id}/{task_id}"
else:
    branch_name = f"wfc/{task_id}"
```

**Acceptance Criteria**:

- [ ] Worktree path includes project_id when set
- [ ] Git branch name includes project_id when set
- [ ] Falls back to legacy path when project_id is None
- [ ] Test: `WorktreeOperations(project_id="proj1")._worktree_path("test")` returns `.worktrees/proj1/wfc-test`
- [ ] Test: `WorktreeOperations()._worktree_path("test")` returns `.worktrees/wfc-test` (backward compat)

---

#### TASK-002c: Update worktree-manager.sh to accept project_id parameter

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/gitwork/scripts/worktree-manager.sh`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-002b]
- **Properties**: [M1, M3]
- **Estimated Time**: 20min
- **Agent Level**: Haiku

**Description**: Add optional `--project-id` flag to worktree-manager.sh that namespaces worktree paths.

**Code Pattern Example**:

```bash
PROJECT_ID=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project-id)
      PROJECT_ID="$2"
      shift 2
      ;;
    *)
      COMMAND="$1"
      shift
      break
      ;;
  esac
done

# Update WORKTREE_DIR based on PROJECT_ID
if [[ -n "$PROJECT_ID" ]]; then
  WORKTREE_DIR="$GIT_ROOT/.worktrees/$PROJECT_ID"
else
  WORKTREE_DIR="$GIT_ROOT/.worktrees"
fi
```

**Acceptance Criteria**:

- [ ] `--project-id` flag parsed correctly
- [ ] Worktree directory namespaced when flag provided
- [ ] Backward compatible when flag not provided
- [ ] Test: `bash worktree-manager.sh --project-id proj1 create test develop` creates `.worktrees/proj1/wfc-test`

---

#### TASK-002d: Add developer_id to GIT_AUTHOR env vars in worktree-manager.sh

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/gitwork/scripts/worktree-manager.sh`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-002c]
- **Properties**: [M3]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Override GIT_AUTHOR_NAME and GIT_AUTHOR_EMAIL when developer_id provided.

**Code Pattern Example**:

```bash
DEVELOPER_ID=""

# Parse arguments (add to existing parser)
case $1 in
  --developer-id)
    DEVELOPER_ID="$2"
    shift 2
    ;;
esac

# In create() function, after worktree is created:
if [[ -n "$DEVELOPER_ID" ]]; then
  # Set git config in worktree
  git -C "$DEST" config user.name "WFC Agent ($DEVELOPER_ID)"
  git -C "$DEST" config user.email "wfc+$DEVELOPER_ID@noreply.local"
  echo -e "  ${GREEN}Set git author to $DEVELOPER_ID${NC}"
fi
```

**Acceptance Criteria**:

- [ ] `--developer-id` flag parsed correctly
- [ ] Git config set in worktree when flag provided
- [ ] Git author format: `WFC Agent (developer_id)`
- [ ] Git email format: `wfc+developer_id@noreply.local`
- [ ] Test: commits in worktree show correct author

---

### 1.3 - File I/O Atomic Writes

#### TASK-003a: Add filelock dependency to pyproject.toml

- **File**: `/Users/samfakhreddine/repos/wfc/pyproject.toml`
- **Complexity**: XS (< 10 lines)
- **Dependencies**: []
- **Properties**: [M2]
- **Estimated Time**: 5min
- **Agent Level**: Haiku

**Description**: Add filelock to dependencies list.

**Code Pattern Example**:

```toml
[project]
dependencies = [
    # ... existing dependencies
    "filelock>=3.13.0",
]
```

**Acceptance Criteria**:

- [ ] filelock added to dependencies
- [ ] Version constraint: >= 3.13.0
- [ ] `uv pip install -e .` succeeds
- [ ] `python -c "import filelock"` succeeds

---

#### TASK-003b: Add FileLock wrapper to file_io.py

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/shared/file_io.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-003a]
- **Properties**: [M2]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Add safe_append_text function that uses FileLock.

**Code Pattern Example**:

```python
from filelock import FileLock

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
    
    Example:
        safe_append_text(Path('KNOWLEDGE.md'), 'New entry\\n')
    """
    try:
        path = Path(path)
        
        # Create parent directory if needed
        if ensure_parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        
        # Acquire lock (creates .lock file alongside target)
        lock_path = path.parent / f"{path.name}.lock"
        with FileLock(lock_path, timeout=timeout):
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)
    
    except Timeout:
        raise FileIOError(f"Failed to acquire lock for {path} within {timeout}s")
    except Exception as e:
        raise FileIOError(f"Error appending to {path}: {e}")
```

**Acceptance Criteria**:

- [ ] safe_append_text function added
- [ ] Uses FileLock for atomic writes
- [ ] Creates .lock file alongside target
- [ ] Timeout parameter (default 10s)
- [ ] Unit test: 10 concurrent appends result in correct line count

---

#### TASK-003c: Update append_text to use safe_append_text

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/shared/file_io.py`
- **Complexity**: XS (< 10 lines)
- **Dependencies**: [TASK-003b]
- **Properties**: [M2]
- **Estimated Time**: 5min
- **Agent Level**: Haiku

**Description**: Make append_text call safe_append_text for backward compatibility.

**Code Pattern Example**:

```python
def append_text(path: Path, content: str, ensure_parent: bool = True) -> None:
    """
    Append to text file safely (legacy wrapper - calls safe_append_text).
    
    Args:
        path: Path to text file
        content: String content to append
        ensure_parent: Create parent directory if needed (default: True)
    
    Raises:
        FileIOError: If file can't be written
    
    Example:
        append_text(Path('log.txt'), 'New log entry\\n')
    """
    safe_append_text(path, content, ensure_parent=ensure_parent)
```

**Acceptance Criteria**:

- [ ] append_text delegates to safe_append_text
- [ ] Signature unchanged (backward compatible)
- [ ] Existing tests still pass
- [ ] New behavior: file locking enabled for all appends

---

### 1.4 - Telemetry Namespacing

#### TASK-004a: Update AutoTelemetry.**init** to accept project_id

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/shared/telemetry_auto.py`
- **Complexity**: XS (< 10 lines)
- **Dependencies**: []
- **Properties**: [M1]
- **Estimated Time**: 5min
- **Agent Level**: Haiku

**Description**: Add project_id parameter to AutoTelemetry.**init**.

**Code Pattern Example**:

```python
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
```

**Acceptance Criteria**:

- [ ] project_id parameter added
- [ ] Metrics stored in `~/.wfc/telemetry/{project_id}/` when set
- [ ] Falls back to `~/.wfc/telemetry/` when None (backward compat)
- [ ] Test: `AutoTelemetry(project_id="proj1")` creates `~/.wfc/telemetry/proj1/`

---

#### TASK-004b: Update get_telemetry to accept project_id

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/shared/telemetry_auto.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-004a]
- **Properties**: [M1]
- **Estimated Time**: 10min
- **Agent Level**: Haiku

**Description**: Modify get_telemetry global factory to support project_id.

**Code Pattern Example**:

```python
# Global instances per project
_telemetry_instances: Dict[str, AutoTelemetry] = {}

def get_telemetry(project_id: Optional[str] = None) -> AutoTelemetry:
    """Get telemetry instance for project (or global if project_id=None)"""
    key = project_id or "_global"
    
    if key not in _telemetry_instances:
        _telemetry_instances[key] = AutoTelemetry(project_id=project_id)
    
    return _telemetry_instances[key]
```

**Acceptance Criteria**:

- [ ] get_telemetry accepts project_id parameter
- [ ] Returns separate instance per project_id
- [ ] Global instance when project_id=None (backward compat)
- [ ] Test: `get_telemetry("proj1")` != `get_telemetry("proj2")`

---

### 1.5 - Knowledge Writer Attribution

#### TASK-005a: Add developer_id to LearningEntry dataclass

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/scripts/knowledge/knowledge_writer.py`
- **Complexity**: XS (< 10 lines)
- **Dependencies**: []
- **Properties**: [M3]
- **Estimated Time**: 5min
- **Agent Level**: Haiku

**Description**: Add developer_id field to LearningEntry for attribution.

**Code Pattern Example**:

```python
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
```

**Acceptance Criteria**:

- [ ] developer_id field added
- [ ] Default empty string for backward compat
- [ ] Optional parameter (does not break existing code)

---

#### TASK-005b: Update _format_entry to include developer_id

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/scripts/knowledge/knowledge_writer.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-005a]
- **Properties**: [M3]
- **Estimated Time**: 10min
- **Agent Level**: Haiku

**Description**: Modify entry formatting to include developer_id in output.

**Code Pattern Example**:

```python
def _format_entry(self, entry: LearningEntry) -> str:
    entry_text, entry_source = self._sanitize_entry_fields(entry.text, entry.source)
    
    # Format: - [date] text (Source: source, Developer: developer_id)
    if entry.developer_id:
        return f"- [{entry.date}] {entry_text} (Source: {entry_source}, Developer: {entry.developer_id})"
    else:
        # Legacy format (no developer_id)
        return f"- [{entry.date}] {entry_text} (Source: {entry_source})"
```

**Acceptance Criteria**:

- [ ] Developer ID included when present
- [ ] Legacy format maintained when developer_id=""
- [ ] Test: Entry with developer_id="alice" shows "(Developer: alice)"
- [ ] Test: Entry without developer_id omits field

---

#### TASK-005c: Update KnowledgeWriter to use safe_append_text

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/scripts/knowledge/knowledge_writer.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-003b]
- **Properties**: [M2]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Replace direct file writes with safe_append_text for concurrent safety.

**Code Pattern Example**:

```python
from wfc.shared.file_io import safe_append_text

# In append_entries method:
def append_entries(self, entries: list[LearningEntry]) -> dict[str, int]:
    grouped: dict[str, list[LearningEntry]] = {}
    for e in entries:
        grouped.setdefault(e.reviewer_id, []).append(e)
    
    result: dict[str, int] = {}
    for reviewer_id, reviewer_entries in grouped.items():
        count = 0
        kp = self.reviewers_dir / reviewer_id / "KNOWLEDGE.md"
        if not kp.exists():
            self._create_empty_knowledge(kp, reviewer_id)
        
        # Read once, mutate in memory, write once
        current_content: str = kp.read_text(encoding="utf-8")
        for entry in reviewer_entries:
            updated_content = self._append_to_file(kp, entry, existing_content=current_content)
            if updated_content is not None:
                current_content = updated_content
                count += 1
        
        # Write final content with file locking
        from wfc.shared.file_io import save_text
        save_text(kp, current_content)  # Uses FileLock internally now
        
        result[reviewer_id] = count
    return result
```

**Acceptance Criteria**:

- [ ] Imports safe_append_text from file_io
- [ ] Uses file locking for writes
- [ ] Test: 10 concurrent KnowledgeWriter.append_entries complete without corruption
- [ ] Backward compatible (existing tests pass)

---

### 1.6 - Review Orchestrator Context Threading

#### TASK-006a: Add project_context parameter to ReviewOrchestrator.**init**

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/scripts/orchestrators/review/orchestrator.py`
- **Complexity**: XS (< 10 lines)
- **Dependencies**: [TASK-001a]
- **Properties**: [M1]
- **Estimated Time**: 5min
- **Agent Level**: Haiku

**Description**: Add optional project_context parameter to ReviewOrchestrator.

**Code Pattern Example**:

```python
from wfc.shared.config.wfc_config import ProjectContext

def __init__(
    self,
    reviewer_engine: ReviewerEngine | None = None,
    retriever: KnowledgeRetriever | None = None,
    model_router: ModelRouter | None = None,
    use_diff_manifest: bool = False,
    project_context: ProjectContext | None = None,  # NEW
):
    """
    Initialize ReviewOrchestrator.
    
    Args:
        reviewer_engine: Optional custom reviewer engine
        retriever: Optional knowledge retriever for RAG
        model_router: Optional model router for reviewer selection
        use_diff_manifest: If True, use structured diff manifests
        project_context: Optional project isolation context for multi-tenant mode
    """
    self.engine = reviewer_engine or ReviewerEngine(retriever=retriever)
    self.fingerprinter = Fingerprinter()
    self.scorer = ConsensusScore()
    self.validator = FindingValidator()
    self.model_router = model_router
    self.use_diff_manifest = use_diff_manifest
    self.project_context = project_context  # NEW
```

**Acceptance Criteria**:

- [ ] project_context parameter added to **init**
- [ ] Stored as instance variable
- [ ] Default None for backward compatibility
- [ ] Docstring updated

---

#### TASK-006b: Update _generate_report to use project_context.output_dir

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/scripts/orchestrators/review/orchestrator.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-006a]
- **Properties**: [M1]
- **Estimated Time**: 10min
- **Agent Level**: Haiku

**Description**: Use namespaced output_dir from project_context when available.

**Code Pattern Example**:

```python
def finalize_review(
    self,
    request: ReviewRequest,
    task_responses: list[dict],
    output_dir: Path,
    skip_validation: bool = False,
) -> ReviewResult:
    """Phase 2: Parse responses, deduplicate, score, report."""
    # ... existing code ...
    
    # Use project_context.output_dir if available
    if self.project_context:
        report_dir = self.project_context.output_dir
    else:
        report_dir = output_dir
    
    report_path = report_dir / f"REVIEW-{request.task_id}.md"
    # ... rest of method
```

**Acceptance Criteria**:

- [ ] Uses project_context.output_dir when available
- [ ] Falls back to output_dir parameter when project_context=None
- [ ] Test: Review with project_context writes to `.wfc/output/{project_id}/`
- [ ] Test: Review without project_context writes to output_dir param (backward compat)

---

#### TASK-006c: Thread developer_id to knowledge writer

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/scripts/orchestrators/review/orchestrator.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-005a, TASK-006a]
- **Properties**: [M3]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Pass developer_id from project_context to knowledge writer for attribution.

**Code Pattern Example**:

```python
# In finalize_review, after generating report:
if self.project_context:
    # Extract learnings with developer attribution
    from wfc.scripts.knowledge.knowledge_writer import KnowledgeWriter, LearningEntry
    
    writer = KnowledgeWriter()
    for result in reviewer_results:
        entries = writer.extract_learnings(
            review_findings=result.findings,
            reviewer_id=result.reviewer_id,
            source=request.task_id,
        )
        
        # Add developer_id to each entry
        for entry in entries:
            entry.developer_id = self.project_context.developer_id
        
        writer.append_entries(entries)
```

**Acceptance Criteria**:

- [ ] developer_id added to LearningEntry instances
- [ ] Only when project_context is set
- [ ] Test: Knowledge entries show correct developer_id
- [ ] Backward compatible (no developer_id when project_context=None)

---

### 1.7 - Resource Pooling & Rate Limiting

#### TASK-007a: Create wfc/shared/resource_pool.py file

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/shared/resource_pool.py`
- **Complexity**: XS (create empty file)
- **Dependencies**: []
- **Properties**: [M4, M5]
- **Estimated Time**: 5min
- **Agent Level**: Haiku

**Description**: Create new file with module docstring and imports.

**Code Pattern Example**:

```python
"""
Resource pooling and rate limiting for multi-tenant WFC.

Provides:
- WorktreePool: Manages limited pool of concurrent worktrees
- TokenBucket: Rate limits Anthropic API calls to prevent 429 errors
"""

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Set
```

**Acceptance Criteria**:

- [ ] File created at `/Users/samfakhreddine/repos/wfc/wfc/shared/resource_pool.py`
- [ ] Module docstring present
- [ ] Imports correct
- [ ] `python -c "import wfc.shared.resource_pool"` succeeds

---

#### TASK-007b: Implement TokenBucket class in resource_pool.py

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/shared/resource_pool.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-007a]
- **Properties**: [M4]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Implement token bucket rate limiter to prevent Anthropic API 429 errors.

**Code Pattern Example**:

```python
@dataclass
class TokenBucket:
    """
    Token bucket rate limiter for API calls.
    
    Prevents Anthropic API rate limit (429) errors by queuing requests
    when bucket is empty. Refills at constant rate.
    
    Example:
        bucket = TokenBucket(capacity=50, refill_rate=10)
        bucket.acquire()  # Blocks if no tokens available
        make_api_call()
    """
    capacity: int  # Max tokens in bucket
    refill_rate: float  # Tokens added per second
    
    def __post_init__(self):
        self.tokens = float(self.capacity)
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()
    
    def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens from bucket. Blocks if insufficient tokens.
        
        Args:
            tokens: Number of tokens to acquire
            timeout: Max seconds to wait (None = wait forever)
        
        Returns:
            True if acquired, False if timeout
        """
        start = time.monotonic()
        
        while True:
            with self._lock:
                self._refill()
                
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True
            
            # Check timeout
            if timeout is not None:
                elapsed = time.monotonic() - start
                if elapsed >= timeout:
                    return False
            
            # Sleep briefly before retry
            time.sleep(0.1)
    
    def _refill(self):
        """Refill bucket based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
```

**Acceptance Criteria**:

- [ ] TokenBucket class implemented
- [ ] acquire() method blocks when bucket empty
- [ ] Refills at specified rate
- [ ] Thread-safe (uses lock)
- [ ] Unit test: 10 concurrent acquires respect rate limit
- [ ] Unit test: timeout parameter works correctly

---

#### TASK-007c: Implement WorktreePool class in resource_pool.py

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/shared/resource_pool.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-007a]
- **Properties**: [M5]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Implement worktree pool to limit concurrent worktrees and prevent resource exhaustion.

**Code Pattern Example**:

```python
class WorktreePool:
    """
    Pool of limited worktree slots for concurrent execution.
    
    Prevents resource exhaustion by limiting concurrent worktrees.
    Tracks active worktrees and cleans up orphans.
    
    Example:
        pool = WorktreePool(max_worktrees=50)
        with pool.acquire("task-123") as worktree_path:
            # Work in isolated worktree
            pass
        # Worktree automatically released
    """
    
    def __init__(self, max_worktrees: int = 50, cleanup_age_hours: int = 24):
        self.max_worktrees = max_worktrees
        self.cleanup_age_hours = cleanup_age_hours
        self.active: Set[str] = set()
        self.timestamps: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def acquire(self, task_id: str, timeout: Optional[float] = None):
        """
        Acquire worktree slot. Blocks if pool full.
        
        Returns context manager that releases slot on exit.
        """
        start = time.monotonic()
        
        while True:
            with self._lock:
                # Clean up old worktrees first
                self._cleanup_orphans()
                
                if len(self.active) < self.max_worktrees:
                    self.active.add(task_id)
                    self.timestamps[task_id] = time.time()
                    return _WorktreeSlot(self, task_id)
            
            # Check timeout
            if timeout is not None:
                elapsed = time.monotonic() - start
                if elapsed >= timeout:
                    raise TimeoutError(f"Could not acquire worktree slot within {timeout}s")
            
            time.sleep(0.5)
    
    def release(self, task_id: str):
        """Release worktree slot."""
        with self._lock:
            self.active.discard(task_id)
            self.timestamps.pop(task_id, None)
    
    def _cleanup_orphans(self):
        """Remove worktrees older than cleanup_age_hours."""
        now = time.time()
        cutoff = self.cleanup_age_hours * 3600
        
        orphans = [
            tid for tid, ts in self.timestamps.items()
            if (now - ts) > cutoff
        ]
        
        for tid in orphans:
            self.active.discard(tid)
            self.timestamps.pop(tid, None)

class _WorktreeSlot:
    """Context manager for worktree slot."""
    
    def __init__(self, pool: WorktreePool, task_id: str):
        self.pool = pool
        self.task_id = task_id
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.pool.release(self.task_id)
```

**Acceptance Criteria**:

- [ ] WorktreePool class implemented
- [ ] acquire() returns context manager
- [ ] Blocks when pool full (max_worktrees)
- [ ] Cleans up orphans older than cleanup_age_hours
- [ ] Thread-safe
- [ ] Unit test: Pool respects max_worktrees limit
- [ ] Unit test: Orphan cleanup works correctly

---

#### TASK-007d: Add TokenBucket to wfc-implement executor.py

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/skills/wfc-implement/executor.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-007b]
- **Properties**: [M4]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Integrate TokenBucket rate limiting into ExecutionEngine to prevent API 429 errors.

**Code Pattern Example**:

```python
from wfc.shared.resource_pool import TokenBucket

class ExecutionEngine:
    def __init__(self, orchestrator: WFCOrchestrator):
        """Initialize with orchestrator."""
        self.orchestrator = orchestrator
        self.config = orchestrator.config
        self.project_root = orchestrator.project_root
        
        # Rate limiting (prevent Anthropic 429 errors)
        api_rate_limit = self.config.get("orchestration.api_rate_limit", 50)
        api_refill_rate = self.config.get("orchestration.api_refill_rate", 10)
        self.token_bucket = TokenBucket(capacity=api_rate_limit, refill_rate=api_refill_rate)
        
        # ... rest of __init__
    
    def _spawn_subagent(self, task: Task) -> None:
        """Spawn subagent via Task tool to execute task implementation."""
        # Acquire token before spawning (blocks if bucket empty)
        if not self.token_bucket.acquire(timeout=30):
            raise TimeoutError("API rate limit - could not acquire token within 30s")
        
        # ... existing spawn logic
```

**Acceptance Criteria**:

- [ ] TokenBucket imported
- [ ] Created in **init** with config-driven capacity/rate
- [ ] acquire() called before spawning subagents
- [ ] Test: 50 concurrent spawns respect rate limit (no 429 errors)

---

### 1.8 - Interface Abstraction

#### TASK-008a: Create wfc/shared/interfaces.py file

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/shared/interfaces.py`
- **Complexity**: XS (create empty file)
- **Dependencies**: []
- **Properties**: [M6]
- **Estimated Time**: 5min
- **Agent Level**: Haiku

**Description**: Create new file for interface abstractions.

**Code Pattern Example**:

```python
"""
Interface abstractions for WFC multi-tenant architecture.

Allows MCP and REST interfaces to share 90% of orchestrator code
while implementing interface-specific concerns (auth, transport) separately.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from wfc.shared.config.wfc_config import ProjectContext
```

**Acceptance Criteria**:

- [ ] File created at `/Users/samfakhreddine/repos/wfc/wfc/shared/interfaces.py`
- [ ] Module docstring present
- [ ] Imports correct
- [ ] `python -c "import wfc.shared.interfaces"` succeeds

---

#### TASK-008b: Implement ReviewInterface ABC in interfaces.py

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/shared/interfaces.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-008a]
- **Properties**: [M6]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Define ReviewInterface abstract base class that both MCP and REST implement.

**Code Pattern Example**:

```python
class ReviewInterface(ABC):
    """
    Abstract interface for WFC review operations.
    
    Both MCP and REST interfaces implement this to share orchestrator logic
    while handling interface-specific concerns (auth, transport, etc.) separately.
    """
    
    @abstractmethod
    def create_project_context(
        self,
        project_id: str,
        developer_id: str,
        repo_path: Path,
    ) -> ProjectContext:
        """
        Create ProjectContext for request.
        
        Args:
            project_id: Unique project identifier
            developer_id: Developer triggering review
            repo_path: Repository root path
        
        Returns:
            ProjectContext with namespaced paths
        """
        pass
    
    @abstractmethod
    def run_review(
        self,
        project_context: ProjectContext,
        task_id: str,
        files: List[str],
        diff_content: str = "",
    ) -> Dict[str, Any]:
        """
        Run code review with 5-agent consensus.
        
        Args:
            project_context: Project isolation context
            task_id: Task identifier
            files: List of files to review
            diff_content: Git diff (optional)
        
        Returns:
            Review result dict with CS, findings, report_path
        """
        pass
    
    @abstractmethod
    def get_review_status(
        self,
        project_context: ProjectContext,
        task_id: str,
    ) -> Dict[str, Any]:
        """
        Get status of review (for async implementations).
        
        Returns:
            Status dict with state, progress, result
        """
        pass
```

**Acceptance Criteria**:

- [ ] ReviewInterface ABC defined
- [ ] create_project_context abstract method
- [ ] run_review abstract method
- [ ] get_review_status abstract method
- [ ] Docstrings complete
- [ ] Type hints correct

---

---

#### TASK-043a: Add API key generation utility

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/auth.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: []
- **Properties**: [M3, PROP-S006]
- **Estimated Time**: 20min
- **Agent Level**: Haiku

**Description**: Create secure API key generation with bcrypt hashing.

**Code Pattern Example**:

```python
import secrets
import bcrypt

def generate_api_key() -> tuple[str, str]:
    """Generate API key and hashed version for storage."""
    # Generate 32-byte random key
    key = secrets.token_urlsafe(32)

    # Hash for storage
    hashed = bcrypt.hashpw(key.encode(), bcrypt.gensalt())

    return key, hashed.decode()

def verify_api_key(provided: str, hashed: str) -> bool:
    """Verify provided key against stored hash."""
    return bcrypt.checkpw(provided.encode(), hashed.encode())
```

**Acceptance Criteria**:

- [ ] generate_api_key returns (plaintext, hash) tuple
- [ ] verify_api_key validates correctly
- [ ] Uses bcrypt with salt rounds >=12
- [ ] Unit test: generate + verify cycle passes

---

#### TASK-043b: Add API key storage configuration

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/auth.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-043a]
- **Properties**: [M3]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Store API key hashes in environment variables (not database for MVP).

**Code Pattern Example**:

```python
import os

def load_api_keys() -> dict[str, str]:
    """Load API keys from environment (format: WFC_API_KEY_username=hash)."""
    keys = {}
    for key, value in os.environ.items():
        if key.startswith("WFC_API_KEY_"):
            username = key.replace("WFC_API_KEY_", "").lower()
            keys[username] = value
    return keys

def authenticate_request(api_key: str) -> Optional[str]:
    """Validate API key and return developer_id."""
    keys = load_api_keys()
    for developer_id, hashed in keys.items():
        if verify_api_key(api_key, hashed):
            return developer_id
    return None
```

**Acceptance Criteria**:

- [ ] load_api_keys reads from environment
- [ ] authenticate_request returns developer_id on success
- [ ] Returns None on failure (no exceptions)
- [ ] Unit test: valid key → developer_id, invalid → None

---

#### TASK-043c: Add API key rotation endpoint

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/routes/auth.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-043a, TASK-043b]
- **Properties**: [M3]
- **Estimated Time**: 30min
- **Agent Level**: Haiku

**Description**: POST /v1/auth/rotate endpoint for key rotation.

**Code Pattern Example**:

```python
from fastapi import APIRouter, Header, HTTPException

router = APIRouter()

@router.post("/v1/auth/rotate")
async def rotate_api_key(x_api_key: str = Header()):
    """Rotate API key (requires valid existing key)."""
    developer_id = authenticate_request(x_api_key)
    if not developer_id:
        raise HTTPException(401, "Invalid API key")

    # Generate new key
    new_key, new_hash = generate_api_key()

    # Return new key (caller must update environment)
    return {
        "developer_id": developer_id,
        "new_api_key": new_key,
        "instruction": f"Update WFC_API_KEY_{developer_id.upper()}={new_hash}"
    }
```

**Acceptance Criteria**:

- [ ] Requires valid API key to rotate
- [ ] Returns new plaintext key + hash
- [ ] 401 on invalid key
- [ ] Integration test: rotate + verify new key works

---

#### TASK-044a: Design PostgreSQL schema

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/state.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: []
- **Properties**: [M3, S1]
- **Estimated Time**: 30min
- **Agent Level**: Haiku

**Description**: Define SQLAlchemy models for projects, reviews, developers, project_access.

**Code Pattern Example**:

```python
from sqlalchemy import Column, String, Integer, DateTime, Boolean, DECIMAL, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"

    project_id = Column(String(255), primary_key=True)
    repo_url = Column(String(512))
    repo_path = Column(String(512))
    created_at = Column(DateTime, default=datetime.utcnow)

class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(String(255), primary_key=True)
    project_id = Column(String(255), ForeignKey("projects.project_id"))
    developer_id = Column(String(255), ForeignKey("developers.developer_id"))
    task_id = Column(String(255))
    consensus_score = Column(DECIMAL(4, 2))
    passed = Column(Boolean)
    findings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class Developer(Base):
    __tablename__ = "developers"

    developer_id = Column(String(255), primary_key=True)
    email = Column(String(255))
    github_username = Column(String(255))
    api_key_hash = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class ProjectAccess(Base):
    __tablename__ = "project_access"

    project_id = Column(String(255), ForeignKey("projects.project_id"), primary_key=True)
    developer_id = Column(String(255), ForeignKey("developers.developer_id"), primary_key=True)
    role = Column(String(50))  # 'admin', 'reviewer', 'viewer'
```

**Acceptance Criteria**:

- [ ] All 4 models defined (Project, Review, Developer, ProjectAccess)
- [ ] Foreign keys correctly defined
- [ ] Timestamps on all tables
- [ ] JSON column for findings
- [ ] Schema matches BA Section 4

---

#### TASK-044b: Setup Alembic migrations

- **File**: `/Users/samfakhreddine/repos/wfc/alembic/env.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-044a]
- **Properties**: [S1]
- **Estimated Time**: 25min
- **Agent Level**: Haiku

**Description**: Initialize Alembic and create initial migration.

**Code Pattern Example**:

```bash
# Initialize Alembic
uv run alembic init alembic

# Configure alembic.ini
sqlalchemy.url = postgresql://user:pass@localhost/wfc

# Create initial migration
uv run alembic revision --autogenerate -m "Initial schema"

# Apply migration
uv run alembic upgrade head
```

**Acceptance Criteria**:

- [ ] alembic/ directory created
- [ ] Initial migration file generated
- [ ] Migration creates all 4 tables
- [ ] `alembic upgrade head` succeeds

---

#### TASK-044c: Configure Redis connection

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/cache.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: []
- **Properties**: [M4]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Redis client for job queue and caching.

**Code Pattern Example**:

```python
import redis
import os

def get_redis_client() -> redis.Redis:
    """Get Redis client with connection pooling."""
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        decode_responses=True,
        max_connections=10
    )

# Singleton
_redis_client = None

def redis() -> redis.Redis:
    """Get global Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = get_redis_client()
    return _redis_client
```

**Acceptance Criteria**:

- [ ] Redis client with connection pooling
- [ ] Environment variables for host/port/db
- [ ] Singleton pattern
- [ ] Connection test passes

---

#### TASK-007d: Create background orphan cleanup cron task

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/background.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-007c]
- **Properties**: [M5, PROP-L001]
- **Estimated Time**: 30min
- **Agent Level**: Haiku

**Description**: Separate cron task that runs every hour to clean orphaned worktrees (independent of acquire() lock).

**Code Pattern Example**:

```python
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

async def cleanup_orphaned_worktrees(max_age_hours: int = 24):
    """Clean worktrees older than max_age_hours."""
    worktree_base = Path.cwd() / ".worktrees"

    if not worktree_base.exists():
        return

    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    deleted = 0

    for project_dir in worktree_base.iterdir():
        if not project_dir.is_dir():
            continue

        for worktree_dir in project_dir.iterdir():
            if not worktree_dir.is_dir():
                continue

            # Check age
            mtime = datetime.fromtimestamp(worktree_dir.stat().st_mtime)
            if mtime < cutoff:
                # Verify no active process
                if not _is_worktree_active(worktree_dir):
                    _delete_worktree(worktree_dir)
                    deleted += 1

    return deleted

async def orphan_cleanup_loop():
    """Run cleanup every hour forever."""
    while True:
        try:
            deleted = await cleanup_orphaned_worktrees()
            print(f"Orphan cleanup: deleted {deleted} worktrees")
        except Exception as e:
            print(f"Orphan cleanup error: {e}")

        # Sleep 1 hour
        await asyncio.sleep(3600)
```

**Acceptance Criteria**:

- [ ] Runs independently of WorktreePool
- [ ] Deletes worktrees >24h old
- [ ] Checks for active process before deleting
- [ ] Runs every hour in background loop
- [ ] Test: create old worktree → wait → verify deleted

## PHASE 2A: MCP INTERFACE (Week 2)

### 2.1 - MCP Server Infrastructure

#### TASK-009a: Create wfc/mcp directory

- **File**: N/A (directory creation)
- **Complexity**: XS
- **Dependencies**: []
- **Properties**: [M6]
- **Estimated Time**: 5min
- **Agent Level**: Haiku

**Description**: Create MCP module directory structure.

**Code Pattern Example**:

```bash
mkdir -p /Users/samfakhreddine/repos/wfc/wfc/mcp
touch /Users/samfakhreddine/repos/wfc/wfc/mcp/__init__.py
```

**Acceptance Criteria**:

- [ ] Directory `/Users/samfakhreddine/repos/wfc/wfc/mcp/` exists
- [ ] `__init__.py` created
- [ ] `python -c "import wfc.mcp"` succeeds

---

#### TASK-009b: Add MCP dependencies to pyproject.toml

- **File**: `/Users/samfakhreddine/repos/wfc/pyproject.toml`
- **Complexity**: XS (< 10 lines)
- **Dependencies**: []
- **Properties**: [M6]
- **Estimated Time**: 5min
- **Agent Level**: Haiku

**Description**: Add MCP SDK and dependencies.

**Code Pattern Example**:

```toml
[project.optional-dependencies]
mcp = [
    "mcp>=1.0.0",  # Anthropic MCP SDK
    "httpx>=0.27.0",  # For MCP → REST delegation (optional)
]
```

**Acceptance Criteria**:

- [ ] mcp dependency added to optional-dependencies
- [ ] httpx added for delegation support
- [ ] `uv pip install -e ".[mcp]"` succeeds
- [ ] `python -c "import mcp"` succeeds

---

#### TASK-009c: Create wfc/mcp/server.py skeleton

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/mcp/server.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-009a, TASK-009b]
- **Properties**: [M6]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Create MCP server skeleton with imports and class structure.

**Code Pattern Example**:

```python
"""
WFC MCP Server - Model Context Protocol interface for solo developers.

Provides local, low-latency access to WFC review/plan operations via MCP.
Implements ReviewInterface for code reuse with REST API.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.models import Resource, Tool

from wfc.shared.config.wfc_config import ProjectContext, WFCConfig
from wfc.shared.interfaces import ReviewInterface

logger = logging.getLogger(__name__)


class WFCMCPServer(ReviewInterface):
    """
    MCP server for WFC operations.
    
    Local-first interface for solo developers. No authentication,
    no persistence - relies on Claude Code session context.
    """
    
    def __init__(self, config_path: Path | None = None):
        """Initialize MCP server with config."""
        self.config = WFCConfig(project_root=config_path or Path.cwd())
        self.server = Server("wfc-mcp")
    
    # ReviewInterface implementation
    def create_project_context(
        self,
        project_id: str,
        developer_id: str,
        repo_path: Path,
    ) -> ProjectContext:
        """Create project context from MCP request."""
        return self.config.create_project_context(
            project_id=project_id,
            developer_id=developer_id,
            repo_path=repo_path,
        )
    
    def run_review(
        self,
        project_context: ProjectContext,
        task_id: str,
        files: List[str],
        diff_content: str = "",
    ) -> Dict[str, Any]:
        """Run review (implemented in TASK-010)."""
        raise NotImplementedError("Implemented in TASK-010")
    
    def get_review_status(
        self,
        project_context: ProjectContext,
        task_id: str,
    ) -> Dict[str, Any]:
        """Get review status (MCP is synchronous, always returns complete)."""
        return {"status": "complete"}
```

**Acceptance Criteria**:

- [ ] WFCMCPServer class created
- [ ] Implements ReviewInterface
- [ ] **init** creates MCP Server instance
- [ ] create_project_context implemented
- [ ] Placeholder methods for run_review, get_review_status
- [ ] `python -c "from wfc.mcp.server import WFCMCPServer"` succeeds

---

#### TASK-010a: Implement run_review in MCP server

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/mcp/server.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-009c, TASK-006a]
- **Properties**: [M6]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Implement run_review method that calls ReviewOrchestrator with ProjectContext.

**Code Pattern Example**:

```python
def run_review(
    self,
    project_context: ProjectContext,
    task_id: str,
    files: List[str],
    diff_content: str = "",
) -> Dict[str, Any]:
    """
    Run code review with 5-agent consensus.
    
    Args:
        project_context: Project isolation context
        task_id: Task identifier
        files: List of files to review
        diff_content: Git diff (optional)
    
    Returns:
        Review result dict
    """
    from wfc.scripts.orchestrators.review.orchestrator import (
        ReviewOrchestrator,
        ReviewRequest,
    )
    
    # Create orchestrator with project context
    orchestrator = ReviewOrchestrator(project_context=project_context)
    
    # Build request
    request = ReviewRequest(
        task_id=task_id,
        files=files,
        diff_content=diff_content,
    )
    
    # Phase 1: Prepare review tasks
    task_specs = orchestrator.prepare_review(request)
    
    # Phase 2: Execute reviewers (via Task tool in real implementation)
    # For now, simulate with empty responses
    task_responses = []
    for spec in task_specs:
        # In production: spawn Task tool and wait for result
        task_responses.append({
            "reviewer_id": spec["reviewer_id"],
            "response": "",  # Would be filled by Task tool
        })
    
    # Phase 3: Finalize review
    result = orchestrator.finalize_review(
        request=request,
        task_responses=task_responses,
        output_dir=project_context.output_dir,
    )
    
    return {
        "task_id": result.task_id,
        "consensus_score": result.consensus.cs,
        "tier": result.consensus.tier,
        "passed": result.passed,
        "finding_count": len(result.consensus.findings),
        "report_path": str(result.report_path),
    }
```

**Acceptance Criteria**:

- [ ] run_review method implemented
- [ ] Creates ReviewOrchestrator with project_context
- [ ] Calls prepare_review and finalize_review
- [ ] Returns structured result dict
- [ ] Test: MCP review writes to project_context.output_dir

---

#### TASK-010b: Register MCP tools in server.py

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/mcp/server.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-010a]
- **Properties**: [M6]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Register MCP tools (review_code, generate_plan) with server.

**Code Pattern Example**:

```python
def register_tools(self):
    """Register MCP tools."""
    
    @self.server.tool()
    async def review_code(
        project_id: str,
        developer_id: str,
        task_id: str,
        files: List[str],
        diff_content: str = "",
    ) -> Dict[str, Any]:
        """
        Run WFC code review.
        
        Args:
            project_id: Project identifier
            developer_id: Developer identifier
            task_id: Task identifier
            files: List of files to review
            diff_content: Optional git diff
        
        Returns:
            Review result with consensus score and findings
        """
        repo_path = Path.cwd()  # MCP context = current directory
        
        context = self.create_project_context(
            project_id=project_id,
            developer_id=developer_id,
            repo_path=repo_path,
        )
        
        return self.run_review(
            project_context=context,
            task_id=task_id,
            files=files,
            diff_content=diff_content,
        )
    
    @self.server.tool()
    async def generate_plan(
        project_id: str,
        developer_id: str,
        requirements: str,
    ) -> Dict[str, Any]:
        """
        Generate implementation plan (placeholder for Phase 3).
        
        Args:
            project_id: Project identifier
            developer_id: Developer identifier
            requirements: Requirements text
        
        Returns:
            Plan result
        """
        return {"status": "not_implemented", "message": "Phase 3 feature"}
```

**Acceptance Criteria**:

- [ ] review_code tool registered
- [ ] generate_plan tool registered (placeholder)
- [ ] Tools accept project_id, developer_id parameters
- [ ] Tools call create_project_context
- [ ] Test: MCP tool invocation succeeds

---

#### TASK-011: Create wfc/mcp/resources.py for MCP resources

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/mcp/resources.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-009a]
- **Properties**: [M6, S2]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Implement MCP resources for review:// and knowledge:// URIs.

**Code Pattern Example**:

```python
"""
MCP Resources for WFC.

Provides URIs for accessing review reports and knowledge base:
- review://{project_id}/{task_id} - Review report
- knowledge://{reviewer_id} - Reviewer knowledge base
"""

from pathlib import Path
from typing import Dict

from mcp.server import Server
from mcp.server.models import Resource


def register_resources(server: Server, config):
    """Register MCP resources."""
    
    @server.resource("review://{project_id}/{task_id}")
    async def get_review(project_id: str, task_id: str) -> str:
        """
        Get review report content.
        
        Args:
            project_id: Project identifier
            task_id: Task identifier
        
        Returns:
            Review report markdown
        """
        # Resolve path from config
        output_dir = Path.home() / ".wfc" / "output" / project_id
        report_path = output_dir / f"REVIEW-{task_id}.md"
        
        if not report_path.exists():
            return f"# Review Not Found\n\nNo review found for {task_id} in project {project_id}"
        
        return report_path.read_text(encoding="utf-8")
    
    @server.resource("knowledge://{reviewer_id}")
    async def get_knowledge(reviewer_id: str) -> str:
        """
        Get reviewer knowledge base.
        
        Args:
            reviewer_id: Reviewer identifier (e.g., security, correctness)
        
        Returns:
            Knowledge base markdown
        """
        # Global knowledge (shared across projects)
        knowledge_dir = Path.home() / ".wfc" / "knowledge" / "global" / "reviewers" / reviewer_id
        knowledge_path = knowledge_dir / "KNOWLEDGE.md"
        
        if not knowledge_path.exists():
            return f"# Knowledge Not Found\n\nNo knowledge base for reviewer {reviewer_id}"
        
        return knowledge_path.read_text(encoding="utf-8")
```

**Acceptance Criteria**:

- [ ] register_resources function created
- [ ] review:// URI pattern registered
- [ ] knowledge:// URI pattern registered
- [ ] Returns markdown content
- [ ] Test: MCP resource fetch succeeds
- [ ] Test: Non-existent resource returns helpful message

---

## PHASE 2B: REST API INTERFACE (Weeks 3-4)

### 2.2 - REST API Core

#### TASK-012a: Create wfc/api directory

- **File**: N/A (directory creation)
- **Complexity**: XS
- **Dependencies**: []
- **Properties**: [M6]
- **Estimated Time**: 5min
- **Agent Level**: Haiku

**Description**: Create REST API module directory structure.

**Code Pattern Example**:

```bash
mkdir -p /Users/samfakhreddine/repos/wfc/wfc/api
mkdir -p /Users/samfakhreddine/repos/wfc/wfc/api/routes
touch /Users/samfakhreddine/repos/wfc/wfc/api/__init__.py
touch /Users/samfakhreddine/repos/wfc/wfc/api/routes/__init__.py
```

**Acceptance Criteria**:

- [ ] Directory `/Users/samfakhreddine/repos/wfc/wfc/api/` exists
- [ ] Directory `/Users/samfakhreddine/repos/wfc/wfc/api/routes/` exists
- [ ] `__init__.py` files created
- [ ] `python -c "import wfc.api"` succeeds

---

#### TASK-012b: Add FastAPI dependencies to pyproject.toml

- **File**: `/Users/samfakhreddine/repos/wfc/pyproject.toml`
- **Complexity**: XS (< 10 lines)
- **Dependencies**: []
- **Properties**: [M6]
- **Estimated Time**: 5min
- **Agent Level**: Haiku

**Description**: Add FastAPI and related dependencies.

**Code Pattern Example**:

```toml
[project.optional-dependencies]
api = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlalchemy>=2.0.0",
    "psycopg2-binary>=2.9.9",  # PostgreSQL driver
    "redis>=5.0.0",
    "python-multipart>=0.0.9",
    "pydantic>=2.9.0",
    "alembic>=1.13.0",  # Database migrations
]
```

**Acceptance Criteria**:

- [ ] FastAPI and dependencies added
- [ ] SQLAlchemy + PostgreSQL driver added
- [ ] Redis client added
- [ ] `uv pip install -e ".[api]"` succeeds
- [ ] `python -c "import fastapi, sqlalchemy, redis"` succeeds

---

#### TASK-013a: Create wfc/api/models.py for Pydantic schemas

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/models.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-012b]
- **Properties**: [M6]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Define Pydantic request/response models for REST API.

**Code Pattern Example**:

```python
"""
Pydantic models for WFC REST API.

Request/response schemas for all endpoints.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    """Request to create code review."""
    
    project_id: str = Field(..., description="Project identifier")
    developer_id: str = Field(..., description="Developer identifier")
    task_id: str = Field(..., description="Task identifier")
    files: List[str] = Field(..., description="Files to review")
    diff_content: str = Field(default="", description="Optional git diff")
    use_diff_manifest: bool = Field(default=False, description="Use diff manifests (87.6% token reduction)")


class ReviewResponse(BaseModel):
    """Response from code review."""
    
    job_id: str = Field(..., description="Job identifier for async tracking")
    task_id: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Job status: queued, in_progress, complete, failed")
    consensus_score: Optional[float] = Field(None, description="Consensus score (0-10)")
    tier: Optional[str] = Field(None, description="Tier: CRITICAL, HIGH, MEDIUM, LOW, PASS")
    passed: Optional[bool] = Field(None, description="Review passed quality gate")
    finding_count: Optional[int] = Field(None, description="Number of findings")
    report_path: Optional[str] = Field(None, description="Path to review report")


class ProjectResponse(BaseModel):
    """Response for project query."""
    
    project_id: str
    developer_id: str
    repo_path: str
    created_at: str
    review_count: int


class ErrorResponse(BaseModel):
    """Error response."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
```

**Acceptance Criteria**:

- [ ] ReviewRequest model defined
- [ ] ReviewResponse model defined
- [ ] ProjectResponse model defined
- [ ] ErrorResponse model defined
- [ ] Field descriptions present
- [ ] Validation works: `ReviewRequest(project_id="test", developer_id="alice", task_id="t1", files=[])`

---

#### TASK-013b: Create wfc/api/state.py for PostgreSQL models

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/state.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-012b]
- **Properties**: [M6, S1]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Define SQLAlchemy ORM models for database persistence.

**Code Pattern Example**:

```python
"""
SQLAlchemy models for WFC REST API state persistence.

Tables:
- projects: Project registrations
- reviews: Review job state and results
- developers: Developer accounts
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Developer(Base):
    """Developer account."""
    
    __tablename__ = "developers"
    
    id = Column(String, primary_key=True)  # developer_id
    email = Column(String, nullable=True)
    api_key = Column(String, unique=True, nullable=False)
    role = Column(String, default="reviewer")  # admin, reviewer, viewer
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    reviews = relationship("Review", back_populates="developer")


class Project(Base):
    """Project registration."""
    
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)  # project_id
    developer_id = Column(String, ForeignKey("developers.id"), nullable=False)
    repo_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    reviews = relationship("Review", back_populates="project")


class Review(Base):
    """Review job state and results."""
    
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, unique=True, nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    developer_id = Column(String, ForeignKey("developers.id"), nullable=False)
    task_id = Column(String, nullable=False)
    status = Column(String, default="queued")  # queued, in_progress, complete, failed
    consensus_score = Column(Float, nullable=True)
    tier = Column(String, nullable=True)
    passed = Column(Boolean, nullable=True)
    finding_count = Column(Integer, nullable=True)
    report_path = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="reviews")
    developer = relationship("Developer", back_populates="reviews")
```

**Acceptance Criteria**:

- [ ] Developer model defined
- [ ] Project model defined
- [ ] Review model defined
- [ ] Relationships configured
- [ ] Timestamps (created_at, updated_at) present
- [ ] Test: Models can be created and queried

---

#### TASK-014a: Create wfc/api/main.py FastAPI application

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/main.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-012b, TASK-013a]
- **Properties**: [M6]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Create FastAPI application with middleware and error handling.

**Code Pattern Example**:

```python
"""
WFC REST API - FastAPI application.

Multi-tenant code review API with PostgreSQL persistence, RBAC, and audit trail.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from wfc.api.models import ErrorResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("WFC API starting up...")
    
    # Initialize database connection pool
    from wfc.api.state import init_db
    init_db()
    
    # Start background tasks (orphan cleanup)
    from wfc.api.background import start_background_tasks
    start_background_tasks()
    
    yield
    
    # Shutdown
    logger.info("WFC API shutting down...")


app = FastAPI(
    title="WFC API",
    description="Multi-tenant code review and planning API",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=str(exc.detail)).dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if logger.level == logging.DEBUG else None,
        ).dict(),
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import routes
from wfc.api.routes import review, plan, projects

app.include_router(review.router, prefix="/v1", tags=["review"])
app.include_router(plan.router, prefix="/v1", tags=["plan"])
app.include_router(projects.router, prefix="/v1", tags=["projects"])
```

**Acceptance Criteria**:

- [ ] FastAPI app created
- [ ] Lifespan manager for startup/shutdown
- [ ] CORS middleware configured
- [ ] Exception handlers present
- [ ] Health check endpoint
- [ ] Routes registered
- [ ] Test: `uvicorn wfc.api.main:app` starts successfully

---

#### TASK-014b: Create wfc/api/auth.py for API key validation

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/auth.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-013b]
- **Properties**: [M6, S4]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Implement API key authentication dependency.

**Code Pattern Example**:

```python
"""
API authentication for WFC REST API.

Uses API keys stored in Developer table.
"""

import hashlib
from typing import Optional

from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from wfc.api.state import Developer, get_db


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_current_developer(
    x_api_key: str = Header(..., description="API key"),
    db: Session = Depends(get_db),
) -> Developer:
    """
    Validate API key and return developer.
    
    Args:
        x_api_key: API key from X-API-Key header
        db: Database session
    
    Returns:
        Developer object
    
    Raises:
        HTTPException: 401 if invalid API key
    """
    # Hash provided key
    key_hash = hash_api_key(x_api_key)
    
    # Look up developer
    developer = db.query(Developer).filter(Developer.api_key == key_hash).first()
    
    if not developer:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )
    
    return developer


async def require_admin(
    developer: Developer = Depends(get_current_developer),
) -> Developer:
    """
    Require admin role.
    
    Args:
        developer: Current developer from get_current_developer
    
    Returns:
        Developer object (if admin)
    
    Raises:
        HTTPException: 403 if not admin
    """
    if developer.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin role required",
        )
    
    return developer
```

**Acceptance Criteria**:

- [ ] get_current_developer dependency created
- [ ] Validates X-API-Key header
- [ ] Queries Developer table
- [ ] Returns Developer object on success
- [ ] Raises 401 on invalid key
- [ ] require_admin dependency for admin endpoints
- [ ] Test: Valid API key returns developer
- [ ] Test: Invalid API key returns 401

---

#### TASK-015a: Create wfc/api/routes/review.py endpoint

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/routes/review.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-014a, TASK-014b]
- **Properties**: [M6]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Implement POST /v1/review endpoint for async code reviews.

**Code Pattern Example**:

```python
"""
Review routes for WFC REST API.
"""

import uuid
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from wfc.api.auth import get_current_developer
from wfc.api.models import ReviewRequest, ReviewResponse
from wfc.api.state import Developer, Project, Review, get_db

router = APIRouter()


@router.post("/review", response_model=ReviewResponse)
async def create_review(
    request: ReviewRequest,
    developer: Developer = Depends(get_current_developer),
    db: Session = Depends(get_db),
) -> ReviewResponse:
    """
    Create code review job.
    
    Args:
        request: Review request
        developer: Authenticated developer
        db: Database session
    
    Returns:
        Review response with job_id
    """
    # Validate project exists and developer has access
    project = db.query(Project).filter(
        Project.id == request.project_id,
        Project.developer_id == developer.id,
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project {request.project_id} not found or access denied",
        )
    
    # Create job ID
    job_id = str(uuid.uuid4())
    
    # Create review record
    review = Review(
        job_id=job_id,
        project_id=request.project_id,
        developer_id=developer.id,
        task_id=request.task_id,
        status="queued",
    )
    db.add(review)
    db.commit()
    
    # Queue background job (implemented in TASK-016)
    from wfc.api.background import queue_review_job
    queue_review_job(
        job_id=job_id,
        request=request,
        developer_id=developer.id,
    )
    
    return ReviewResponse(
        job_id=job_id,
        task_id=request.task_id,
        status="queued",
    )


@router.get("/review/{job_id}", response_model=ReviewResponse)
async def get_review(
    job_id: str,
    developer: Developer = Depends(get_current_developer),
    db: Session = Depends(get_db),
) -> ReviewResponse:
    """
    Get review job status and results.
    
    Args:
        job_id: Job identifier
        developer: Authenticated developer
        db: Database session
    
    Returns:
        Review response with current status
    """
    review = db.query(Review).filter(
        Review.job_id == job_id,
        Review.developer_id == developer.id,
    ).first()
    
    if not review:
        raise HTTPException(
            status_code=404,
            detail=f"Review job {job_id} not found or access denied",
        )
    
    return ReviewResponse(
        job_id=review.job_id,
        task_id=review.task_id,
        status=review.status,
        consensus_score=review.consensus_score,
        tier=review.tier,
        passed=review.passed,
        finding_count=review.finding_count,
        report_path=review.report_path,
    )
```

**Acceptance Criteria**:

- [ ] POST /v1/review endpoint created
- [ ] GET /v1/review/{job_id} endpoint created
- [ ] Authentication required (get_current_developer)
- [ ] RBAC: Developer can only access their projects
- [ ] Creates Review record in database
- [ ] Queues background job
- [ ] Returns job_id for tracking
- [ ] Test: POST returns 201 with job_id
- [ ] Test: GET returns current status

---

#### TASK-015b: Create wfc/api/routes/projects.py endpoint

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/routes/projects.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-014a, TASK-014b]
- **Properties**: [M6, S4]
- **Estimated Time**: 20min
- **Agent Level**: Haiku

**Description**: Implement GET /v1/projects endpoint to list developer's projects.

**Code Pattern Example**:

```python
"""
Project routes for WFC REST API.
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from wfc.api.auth import get_current_developer
from wfc.api.models import ProjectResponse
from wfc.api.state import Developer, Project, Review, get_db

router = APIRouter()


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    developer: Developer = Depends(get_current_developer),
    db: Session = Depends(get_db),
) -> List[ProjectResponse]:
    """
    List developer's projects.
    
    Args:
        developer: Authenticated developer
        db: Database session
    
    Returns:
        List of projects with review counts
    """
    projects = db.query(Project).filter(Project.developer_id == developer.id).all()
    
    results = []
    for project in projects:
        review_count = db.query(Review).filter(Review.project_id == project.id).count()
        
        results.append(ProjectResponse(
            project_id=project.id,
            developer_id=project.developer_id,
            repo_path=project.repo_path,
            created_at=project.created_at.isoformat(),
            review_count=review_count,
        ))
    
    return results
```

**Acceptance Criteria**:

- [ ] GET /v1/projects endpoint created
- [ ] Authentication required
- [ ] Returns only developer's projects (RBAC)
- [ ] Includes review_count per project
- [ ] Test: Returns correct projects for developer

---

#### TASK-015c: Create wfc/api/routes/plan.py endpoint (placeholder)

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/routes/plan.py`
- **Complexity**: XS (< 10 lines)
- **Dependencies**: [TASK-014a]
- **Properties**: [M6]
- **Estimated Time**: 5min
- **Agent Level**: Haiku

**Description**: Create placeholder plan endpoint for Phase 3.

**Code Pattern Example**:

```python
"""
Plan routes for WFC REST API (Phase 3).
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/plan")
async def create_plan():
    """Create implementation plan (Phase 3 feature)."""
    return {"status": "not_implemented", "message": "Phase 3 feature"}
```

**Acceptance Criteria**:

- [ ] POST /v1/plan endpoint created
- [ ] Returns "not_implemented" message
- [ ] Placeholder for Phase 3

---

#### TASK-016: Create wfc/api/background.py for async job processing

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/background.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-015a, TASK-006a]
- **Properties**: [M5, S1]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Implement background job queue for review processing and orphan cleanup.

**Code Pattern Example**:

```python
"""
Background tasks for WFC REST API.

- Review job processing
- Orphan worktree cleanup
"""

import logging
import threading
import time
from pathlib import Path

from sqlalchemy.orm import Session

from wfc.api.models import ReviewRequest
from wfc.api.state import Review, get_db
from wfc.shared.config.wfc_config import ProjectContext, WFCConfig
from wfc.shared.interfaces import ReviewInterface

logger = logging.getLogger(__name__)

# Global job queue (in production: use Redis + Celery/RQ)
_job_queue: list = []
_job_queue_lock = threading.Lock()


def queue_review_job(job_id: str, request: ReviewRequest, developer_id: str):
    """Queue review job for background processing."""
    with _job_queue_lock:
        _job_queue.append({
            "job_id": job_id,
            "request": request,
            "developer_id": developer_id,
        })


def process_review_job(job_id: str, request: ReviewRequest, developer_id: str):
    """
    Process review job in background.
    
    Updates Review record in database with results.
    """
    from wfc.scripts.orchestrators.review.orchestrator import (
        ReviewOrchestrator,
        ReviewRequest as OrchestratorRequest,
    )
    
    db = next(get_db())
    
    try:
        # Update status to in_progress
        review = db.query(Review).filter(Review.job_id == job_id).first()
        review.status = "in_progress"
        db.commit()
        
        # Create project context
        config = WFCConfig()
        context = config.create_project_context(
            project_id=request.project_id,
            developer_id=developer_id,
            repo_path=Path(request.project_id),  # TODO: Lookup from Project table
        )
        
        # Run review
        orchestrator = ReviewOrchestrator(project_context=context)
        orch_request = OrchestratorRequest(
            task_id=request.task_id,
            files=request.files,
            diff_content=request.diff_content,
        )
        
        task_specs = orchestrator.prepare_review(orch_request)
        # TODO: Execute reviewers via Task tool
        task_responses = []  # Placeholder
        
        result = orchestrator.finalize_review(
            request=orch_request,
            task_responses=task_responses,
            output_dir=context.output_dir,
        )
        
        # Update review record
        review.status = "complete"
        review.consensus_score = result.consensus.cs
        review.tier = result.consensus.tier
        review.passed = result.passed
        review.finding_count = len(result.consensus.findings)
        review.report_path = str(result.report_path)
        db.commit()
        
    except Exception as e:
        logger.exception("Review job failed")
        review = db.query(Review).filter(Review.job_id == job_id).first()
        review.status = "failed"
        review.error = str(e)
        db.commit()
    
    finally:
        db.close()


def worker_loop():
    """Background worker loop (processes jobs from queue)."""
    while True:
        job = None
        
        with _job_queue_lock:
            if _job_queue:
                job = _job_queue.pop(0)
        
        if job:
            process_review_job(
                job_id=job["job_id"],
                request=job["request"],
                developer_id=job["developer_id"],
            )
        else:
            time.sleep(1)


def start_background_tasks():
    """Start background worker threads."""
    # Start worker thread
    worker_thread = threading.Thread(target=worker_loop, daemon=True)
    worker_thread.start()
    
    logger.info("Background tasks started")
```

**Acceptance Criteria**:

- [ ] queue_review_job function created
- [ ] process_review_job function created
- [ ] worker_loop function created
- [ ] start_background_tasks called from main.py lifespan
- [ ] Review record updated with results
- [ ] Errors logged and stored in Review.error
- [ ] Test: Queued job completes and updates database

---

### 2.3 - RBAC & Audit

#### TASK-017a: Create wfc/api/rbac.py for role-based access control

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/rbac.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-014b]
- **Properties**: [S4]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Implement RBAC logic for project access control.

**Code Pattern Example**:

```python
"""
Role-based access control for WFC REST API.

Roles:
- admin: Full access to all projects
- reviewer: Can review assigned projects
- viewer: Read-only access to assigned projects
"""

from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from wfc.api.state import Developer, Project


class ProjectACL:
    """Access control list for projects."""
    
    @staticmethod
    def can_access_project(
        developer: Developer,
        project_id: str,
        db: Session,
        require_write: bool = False,
    ) -> bool:
        """
        Check if developer can access project.
        
        Args:
            developer: Developer object
            project_id: Project ID to check
            db: Database session
            require_write: If True, require write access (reviewer/admin role)
        
        Returns:
            True if access granted
        
        Raises:
            HTTPException: 403 if access denied
        """
        # Admin has access to all projects
        if developer.role == "admin":
            return True
        
        # Look up project
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found",
            )
        
        # Check ownership
        if project.developer_id != developer.id:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to project {project_id}",
            )
        
        # Check role for write operations
        if require_write and developer.role == "viewer":
            raise HTTPException(
                status_code=403,
                detail="Viewer role cannot perform write operations",
            )
        
        return True
    
    @staticmethod
    def get_accessible_projects(
        developer: Developer,
        db: Session,
    ) -> List[Project]:
        """
        Get list of projects developer can access.
        
        Args:
            developer: Developer object
            db: Database session
        
        Returns:
            List of Project objects
        """
        if developer.role == "admin":
            # Admin sees all projects
            return db.query(Project).all()
        else:
            # Others see only their projects
            return db.query(Project).filter(Project.developer_id == developer.id).all()
```

**Acceptance Criteria**:

- [ ] ProjectACL class created
- [ ] can_access_project method implemented
- [ ] Admin role bypasses ownership check
- [ ] Viewer role cannot write
- [ ] Raises 403 on access denied
- [ ] Test: Admin can access all projects
- [ ] Test: Reviewer can access own projects
- [ ] Test: Viewer cannot write

---

#### TASK-017b: Create wfc/api/audit.py for audit trail logging

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/audit.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-013b]
- **Properties**: [M3]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Implement audit trail logging for all API operations.

**Code Pattern Example**:

```python
"""
Audit trail logging for WFC REST API.

Logs all API operations with developer attribution.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Session

from wfc.api.state import Base

logger = logging.getLogger(__name__)


class AuditLog(Base):
    """Audit log entry."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    developer_id = Column(String, nullable=False)
    action = Column(String, nullable=False)  # create_review, get_review, etc.
    resource_type = Column(String, nullable=False)  # review, project, plan
    resource_id = Column(String, nullable=True)  # job_id, project_id, etc.
    status = Column(String, nullable=False)  # success, failed
    details = Column(Text, nullable=True)


def log_audit_event(
    db: Session,
    developer_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    status: str = "success",
    details: Optional[str] = None,
):
    """
    Log audit event.
    
    Args:
        db: Database session
        developer_id: Developer ID
        action: Action performed
        resource_type: Type of resource
        resource_id: Resource ID (optional)
        status: Operation status
        details: Additional details (optional)
    """
    entry = AuditLog(
        developer_id=developer_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        details=details,
    )
    db.add(entry)
    db.commit()
    
    logger.info(
        f"Audit: {developer_id} {action} {resource_type} {resource_id} -> {status}"
    )
```

**Acceptance Criteria**:

- [ ] AuditLog model created
- [ ] log_audit_event function created
- [ ] Logs developer_id, action, resource
- [ ] Commits to database
- [ ] Test: Audit log entries created for API calls

---

#### TASK-017c: Add audit logging to review routes

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/routes/review.py`
- **Complexity**: XS (< 10 lines)
- **Dependencies**: [TASK-017b, TASK-015a]
- **Properties**: [M3]
- **Estimated Time**: 10min
- **Agent Level**: Haiku

**Description**: Add audit trail logging to POST /v1/review endpoint.

**Code Pattern Example**:

```python
from wfc.api.audit import log_audit_event

@router.post("/review", response_model=ReviewResponse)
async def create_review(
    request: ReviewRequest,
    developer: Developer = Depends(get_current_developer),
    db: Session = Depends(get_db),
) -> ReviewResponse:
    """Create code review job."""
    # ... existing validation ...
    
    # Create review record
    review = Review(...)
    db.add(review)
    db.commit()
    
    # Audit log
    log_audit_event(
        db=db,
        developer_id=developer.id,
        action="create_review",
        resource_type="review",
        resource_id=job_id,
        status="success",
    )
    
    # ... rest of function
```

**Acceptance Criteria**:

- [ ] log_audit_event called in create_review
- [ ] log_audit_event called in get_review
- [ ] Audit log records developer_id
- [ ] Test: Audit log entries created for review operations

---

### 2.4 - WebSocket & Advanced Features

#### TASK-018: Create wfc/api/websocket.py for real-time progress

- **File**: `/Users/samfakhreddine/repos/wfc/wfc/api/websocket.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-014a]
- **Properties**: [S3]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Implement WebSocket endpoint for real-time review progress updates.

**Code Pattern Example**:

```python
"""
WebSocket support for real-time review progress.
"""

import asyncio
import json
from typing import Dict

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from wfc.api.state import Review, get_db

# Global registry of WebSocket connections per job_id
_ws_connections: Dict[str, list] = {}


class ReviewProgressManager:
    """Manages WebSocket connections for review progress."""
    
    @staticmethod
    async def connect(job_id: str, websocket: WebSocket):
        """Register WebSocket connection for job."""
        await websocket.accept()
        
        if job_id not in _ws_connections:
            _ws_connections[job_id] = []
        
        _ws_connections[job_id].append(websocket)
    
    @staticmethod
    async def disconnect(job_id: str, websocket: WebSocket):
        """Unregister WebSocket connection."""
        if job_id in _ws_connections:
            _ws_connections[job_id].remove(websocket)
            
            if not _ws_connections[job_id]:
                del _ws_connections[job_id]
    
    @staticmethod
    async def broadcast_progress(job_id: str, message: Dict):
        """Broadcast progress update to all connected clients."""
        if job_id not in _ws_connections:
            return
        
        message_json = json.dumps(message)
        
        for ws in _ws_connections[job_id]:
            try:
                await ws.send_text(message_json)
            except Exception:
                # Client disconnected
                pass
    
    @staticmethod
    async def monitor_job(job_id: str, websocket: WebSocket):
        """
        Monitor review job and send progress updates.
        
        Polls database for status changes and broadcasts to client.
        """
        await ReviewProgressManager.connect(job_id, websocket)
        
        try:
            while True:
                # Poll database
                db = next(get_db())
                review = db.query(Review).filter(Review.job_id == job_id).first()
                db.close()
                
                if not review:
                    await websocket.send_json({"error": "Job not found"})
                    break
                
                # Send status update
                await websocket.send_json({
                    "job_id": job_id,
                    "status": review.status,
                    "progress": {
                        "reviewers_complete": 0,  # TODO: Track per-reviewer progress
                        "reviewers_total": 5,
                    },
                })
                
                # If complete, send final result and close
                if review.status in ["complete", "failed"]:
                    await websocket.send_json({
                        "job_id": job_id,
                        "status": review.status,
                        "result": {
                            "consensus_score": review.consensus_score,
                            "tier": review.tier,
                            "passed": review.passed,
                            "finding_count": review.finding_count,
                            "report_path": review.report_path,
                        },
                    })
                    break
                
                await asyncio.sleep(1)
        
        except WebSocketDisconnect:
            pass
        
        finally:
            await ReviewProgressManager.disconnect(job_id, websocket)


# WebSocket endpoint (add to main.py)
async def websocket_review_progress(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for review progress."""
    await ReviewProgressManager.monitor_job(job_id, websocket)
```

**Acceptance Criteria**:

- [ ] ReviewProgressManager class created
- [ ] connect/disconnect methods implemented
- [ ] monitor_job polls database for status
- [ ] Broadcasts progress updates to clients
- [ ] Closes connection when review complete
- [ ] Test: WebSocket client receives progress updates

---

## PHASE 3: TESTING & DOCUMENTATION (Week 5)

### 3.1 - Integration Tests

#### TASK-019a: Create tests/api/test_multi_tenant_review.py

- **File**: `/Users/samfakhreddine/repos/wfc/tests/api/test_multi_tenant_review.py`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [TASK-015a]
- **Properties**: [M1, M2, M3]
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Test concurrent reviews from multiple projects with no collisions.

**Code Pattern Example**:

```python
"""
Integration tests for multi-tenant review system.
"""

import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wfc.api.main import app


class TestMultiTenantReview:
    """Test multi-tenant review isolation."""
    
    def test_concurrent_reviews_no_collision(self, test_db):
        """Test 6 concurrent reviews complete successfully with 0 collisions."""
        client = TestClient(app)
        
        # Create 6 test projects
        projects = []
        for i in range(6):
            project_id = f"proj{i+1}"
            # Register project in DB
            # ...
            projects.append(project_id)
        
        # Spawn 6 concurrent reviews
        results = []
        errors = []
        
        def run_review(project_id, developer_id):
            try:
                response = client.post(
                    "/v1/review",
                    json={
                        "project_id": project_id,
                        "developer_id": developer_id,
                        "task_id": "test",
                        "files": ["test.py"],
                    },
                    headers={"X-API-Key": "test-key"},
                )
                results.append(response.json())
            except Exception as e:
                errors.append(str(e))
        
        threads = []
        for i, project_id in enumerate(projects):
            t = threading.Thread(
                target=run_review,
                args=(project_id, f"dev{i+1}"),
            )
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Assertions
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 6, "Expected 6 review results"
        
        # Verify no worktree collisions
        job_ids = [r["job_id"] for r in results]
        assert len(set(job_ids)) == 6, "Duplicate job IDs (collision)"
        
        # Verify separate reports
        report_paths = [r.get("report_path") for r in results]
        assert len(set(report_paths)) == 6, "Report path collision"
    
    def test_knowledge_base_no_corruption(self, test_db):
        """Test 100 concurrent writes to KNOWLEDGE.md result in 0 corruption."""
        from wfc.scripts.knowledge.knowledge_writer import KnowledgeWriter, LearningEntry
        
        writer = KnowledgeWriter()
        
        errors = []
        
        def append_entry(i):
            try:
                entry = LearningEntry(
                    text=f"Test finding {i}",
                    section="patterns_found",
                    reviewer_id="security",
                    source="test",
                    developer_id=f"dev{i % 10}",
                )
                writer.append_entries([entry])
            except Exception as e:
                errors.append(str(e))
        
        threads = []
        for i in range(100):
            t = threading.Thread(target=append_entry, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # Verify KNOWLEDGE.md is valid
        knowledge_path = Path.home() / ".wfc" / "knowledge" / "global" / "reviewers" / "security" / "KNOWLEDGE.md"
        content = knowledge_path.read_text()
        
        # Should have entries (exact count may vary due to dedup)
        assert "Test finding" in content
        assert content.count("- [") >= 50, "Expected at least 50 unique entries"
```

**Acceptance Criteria**:

- [ ] test_concurrent_reviews_no_collision passes
- [ ] test_knowledge_base_no_corruption passes
- [ ] 6 concurrent reviews complete successfully
- [ ] 100 concurrent writes result in valid KNOWLEDGE.md
- [ ] No race conditions detected

---

#### TASK-019b: Create tests/api/test_rbac.py

- **File**: `/Users/samfakhreddine/repos/wfc/tests/api/test_rbac.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-017a]
- **Properties**: [S4]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Test role-based access control for projects.

**Code Pattern Example**:

```python
"""
Tests for RBAC (role-based access control).
"""

import pytest
from fastapi.testclient import TestClient

from wfc.api.main import app


class TestRBAC:
    """Test role-based access control."""
    
    def test_admin_can_access_all_projects(self, test_db):
        """Test admin role can access all projects."""
        client = TestClient(app)
        
        # Create test projects for different developers
        # ...
        
        # Admin tries to access Alice's project
        response = client.get(
            "/v1/projects",
            headers={"X-API-Key": "admin-key"},
        )
        
        assert response.status_code == 200
        projects = response.json()
        assert len(projects) >= 2, "Admin should see all projects"
    
    def test_reviewer_cannot_access_others_projects(self, test_db):
        """Test reviewer cannot access other developers' projects."""
        client = TestClient(app)
        
        # Alice tries to access Bob's project
        response = client.post(
            "/v1/review",
            json={
                "project_id": "bob-proj",
                "developer_id": "alice",
                "task_id": "test",
                "files": ["test.py"],
            },
            headers={"X-API-Key": "alice-key"},
        )
        
        assert response.status_code == 403, "Expected access denied"
    
    def test_viewer_cannot_write(self, test_db):
        """Test viewer role cannot perform write operations."""
        client = TestClient(app)
        
        # Viewer tries to create review
        response = client.post(
            "/v1/review",
            json={
                "project_id": "viewer-proj",
                "developer_id": "viewer",
                "task_id": "test",
                "files": ["test.py"],
            },
            headers={"X-API-Key": "viewer-key"},
        )
        
        assert response.status_code == 403, "Viewer should not be able to write"
```

**Acceptance Criteria**:

- [ ] test_admin_can_access_all_projects passes
- [ ] test_reviewer_cannot_access_others_projects passes
- [ ] test_viewer_cannot_write passes
- [ ] RBAC enforced correctly

---

#### TASK-019c: Create tests/api/test_rate_limiting.py

- **File**: `/Users/samfakhreddine/repos/wfc/tests/api/test_rate_limiting.py`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-007b, TASK-007d]
- **Properties**: [M4]
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Test token bucket rate limiting prevents API 429 errors.

**Code Pattern Example**:

```python
"""
Tests for rate limiting.
"""

import threading

import pytest

from wfc.shared.resource_pool import TokenBucket


class TestRateLimiting:
    """Test token bucket rate limiting."""
    
    def test_token_bucket_respects_capacity(self):
        """Test token bucket blocks when capacity exceeded."""
        bucket = TokenBucket(capacity=10, refill_rate=1)
        
        # Acquire 10 tokens (should succeed immediately)
        for i in range(10):
            assert bucket.acquire(timeout=1), f"Token {i+1} acquisition failed"
        
        # 11th token should timeout (bucket empty)
        assert not bucket.acquire(timeout=0.5), "Expected timeout (bucket empty)"
    
    def test_token_bucket_refills(self):
        """Test token bucket refills at specified rate."""
        bucket = TokenBucket(capacity=10, refill_rate=10)  # 10 tokens/sec
        
        # Drain bucket
        for _ in range(10):
            bucket.acquire()
        
        # Wait 1 second for refill
        import time
        time.sleep(1.1)
        
        # Should have ~10 tokens available again
        for i in range(10):
            assert bucket.acquire(timeout=0.1), f"Token {i+1} not refilled"
    
    def test_concurrent_acquires_respect_limit(self):
        """Test 50 concurrent acquires respect rate limit."""
        bucket = TokenBucket(capacity=50, refill_rate=10)
        
        acquired = []
        errors = []
        
        def try_acquire():
            try:
                if bucket.acquire(timeout=5):
                    acquired.append(1)
            except Exception as e:
                errors.append(str(e))
        
        threads = []
        for _ in range(50):
            t = threading.Thread(target=try_acquire)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(acquired) == 50, "All requests should succeed (eventually)"
```

**Acceptance Criteria**:

- [ ] test_token_bucket_respects_capacity passes
- [ ] test_token_bucket_refills passes
- [ ] test_concurrent_acquires_respect_limit passes
- [ ] No 429 errors under load

---

### 3.2 - Documentation

#### TASK-020a: Update CLAUDE.md with multi-tenant usage

- **File**: `/Users/samfakhreddine/repos/wfc/CLAUDE.md`
- **Complexity**: S (10-50 lines)
- **Dependencies**: [TASK-010b, TASK-015a]
- **Properties**: []
- **Estimated Time**: 15min
- **Agent Level**: Haiku

**Description**: Document multi-tenant usage patterns for MCP and REST interfaces.

**Code Pattern Example**:

```markdown
## Multi-Tenant Usage

WFC 2.0 supports multi-tenant deployments for teams and solo developers managing multiple projects.

### MCP Interface (Solo Developers)

```bash
# Start MCP server
wfc-mcp-server --config ~/.claude/wfc.config.json

# Use in Claude Code
@wfc review_code \
  --project-id my-app \
  --developer-id alice \
  --task-id TASK-001 \
  --files src/main.py
```

### REST API (Teams)

```bash
# Start API server
uvicorn wfc.api.main:app --host 0.0.0.0 --port 8000

# Create review
curl -X POST http://localhost:8000/v1/review \
  -H "X-API-Key: your-key-here" \
  -d '{
    "project_id": "my-app",
    "developer_id": "alice",
    "task_id": "TASK-001",
    "files": ["src/main.py"]
  }'

# Check status
curl http://localhost:8000/v1/review/{job_id} \
  -H "X-API-Key: your-key-here"
```

### Project Isolation

Each project gets isolated namespaces:

- Worktrees: `.worktrees/{project_id}/wfc-{task_id}`
- Metrics: `~/.wfc/metrics/{project_id}/`
- Reports: `.wfc/output/{project_id}/REVIEW-{task_id}.md`

Developer attribution ensures audit trail: "who reviewed what, when".

```

**Acceptance Criteria**:
- [ ] MCP usage documented
- [ ] REST API usage documented
- [ ] Project isolation explained
- [ ] Code examples correct

---

#### TASK-020b: Create docs/MULTI_TENANT_ARCHITECTURE.md
- **File**: `/Users/samfakhreddine/repos/wfc/docs/MULTI_TENANT_ARCHITECTURE.md`
- **Complexity**: M (50-200 lines)
- **Dependencies**: [All Phase 1 and 2 tasks]
- **Properties**: []
- **Estimated Time**: 30min
- **Agent Level**: Sonnet 3.5

**Description**: Comprehensive architecture documentation for multi-tenant WFC.

**Code Pattern Example**:
```markdown
# Multi-Tenant WFC Architecture

## Overview

WFC 2.0 is a production-grade multi-tenant code review system supporting:
- **Solo developers**: 1 developer managing 6+ projects via MCP
- **Teams**: 10+ developers sharing infrastructure via REST API
- **Hybrid**: MCP delegates to REST for team knowledge sharing

## Architecture Diagram

```

┌─────────────┐     ┌─────────────┐
│  MCP Client │     │ REST Client │
│ (Local)     │     │ (Remote)    │
└──────┬──────┘     └──────┬──────┘
       │                   │
       ├───────────────────┤
       │                   │
       v                   v
┌──────────────────────────────┐
│    Interface Layer           │
│  ┌───────┐    ┌───────┐     │
│  │  MCP  │    │  REST │     │
│  │Server │    │  API  │     │
│  └───┬───┘    └───┬───┘     │
└──────┼────────────┼─────────┘
       │            │
       └────────┬───┘
                │
       ┌────────v────────┐
       │ Shared Core     │
       │                 │
       │ - ReviewOrch... │
       │ - WorktreeOps   │
       │ - KnowledgeWr.. │
       │ - TokenBucket   │
       └────────┬────────┘
                │
       ┌────────v────────┐
       │ PostgreSQL      │
       │ (REST only)     │
       │                 │
       │ - projects      │
       │ - reviews       │
       │ - developers    │
       │ - audit_logs    │
       └─────────────────┘

```

## Key Components

### 1. ProjectContext
Threads project_id and developer_id through all operations.

### 2. Interface Abstraction (ReviewInterface)
Both MCP and REST implement same interface, sharing 90% of code.

### 3. Resource Pooling
- **TokenBucket**: Rate limits API calls (prevent 429 errors)
- **WorktreePool**: Limits concurrent worktrees (prevent resource exhaustion)

### 4. File Locking
Uses `filelock` for atomic writes to shared KNOWLEDGE.md.

### 5. RBAC
- admin: Full access
- reviewer: Can review assigned projects
- viewer: Read-only

## Database Schema (REST API)

```sql
CREATE TABLE developers (
  id TEXT PRIMARY KEY,
  email TEXT,
  api_key TEXT UNIQUE,
  role TEXT DEFAULT 'reviewer',
  created_at TIMESTAMP
);

CREATE TABLE projects (
  id TEXT PRIMARY KEY,
  developer_id TEXT REFERENCES developers(id),
  repo_path TEXT,
  created_at TIMESTAMP
);

CREATE TABLE reviews (
  id SERIAL PRIMARY KEY,
  job_id TEXT UNIQUE,
  project_id TEXT REFERENCES projects(id),
  developer_id TEXT REFERENCES developers(id),
  task_id TEXT,
  status TEXT,  -- queued, in_progress, complete, failed
  consensus_score FLOAT,
  tier TEXT,
  passed BOOLEAN,
  finding_count INT,
  report_path TEXT,
  error TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

## Deployment

### MCP (Solo Developer)

```bash
# Install
uv pip install -e ".[mcp]"

# Run
wfc-mcp-server
```

### REST API (Team)

```bash
# Install
uv pip install -e ".[api]"

# Run migrations
alembic upgrade head

# Start server
uvicorn wfc.api.main:app --workers 5
```

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Concurrent reviews | 50 | ✅ |
| Worktree collision rate | 0% | ✅ |
| Knowledge corruption rate | 0% | ✅ |
| API 429 errors | 0 | ✅ |
| Orphaned worktrees (24h) | 0 | ✅ |
| MCP latency overhead | <500ms | ✅ |
| REST API latency overhead | <2s | ✅ |

```

**Acceptance Criteria**:
- [ ] Architecture documented
- [ ] Diagrams included
- [ ] Database schema documented
- [ ] Deployment instructions clear
- [ ] Performance targets listed

---

## SUMMARY

### Task Breakdown

**Phase 1: Shared Core** (26 tasks)
- Project Context & Config: 2 tasks
- Worktree Namespacing: 4 tasks
- File I/O Atomic Writes: 3 tasks
- Telemetry Namespacing: 2 tasks
- Knowledge Writer Attribution: 3 tasks
- Review Orchestrator Context: 3 tasks
- Resource Pooling: 4 tasks
- Interface Abstraction: 2 tasks

**Phase 2A: MCP Interface** (4 tasks)
- MCP Server Infrastructure: 3 tasks
- MCP Resources: 1 task

**Phase 2B: REST API** (18 tasks)
- REST Core: 6 tasks
- Routes: 4 tasks
- RBAC & Audit: 4 tasks
- WebSocket: 1 task
- Background Jobs: 1 task

**Phase 3: Testing & Docs** (5 tasks)
- Integration Tests: 3 tasks
- Documentation: 2 tasks

**Total: 58 ultra-granular tasks**

### Properties Satisfied

- **M1 (Project Isolation)**: TASK-001, 002, 004, 006
- **M2 (Concurrent Safety)**: TASK-003, 005
- **M3 (Developer Attribution)**: TASK-002d, 005, 006c, 017b
- **M4 (Rate Limiting)**: TASK-007b, 007d
- **M5 (Resource Cleanup)**: TASK-007c, 016
- **M6 (Interface Choice)**: TASK-008, 009-015
- **S1 (Crash Recovery)**: TASK-013b, 016
- **S2 (Shared Knowledge)**: TASK-005, 011
- **S3 (WebSocket Progress)**: TASK-018
- **S4 (RBAC)**: TASK-014b, 017a

---

### Critical Files for Implementation

Based on this extremely granular plan, the 5 most critical files for implementing Multi-Tenant WFC are:

1. **`/Users/samfakhreddine/repos/wfc/wfc/shared/config/wfc_config.py`** - Core ProjectContext dataclass that threads project_id/developer_id through entire system. Foundation for all isolation.

2. **`/Users/samfakhreddine/repos/wfc/wfc/gitwork/api/worktree.py`** - Worktree namespacing by project_id. Critical for preventing collisions (MUST-1 requirement).

3. **`/Users/samfakhreddine/repos/wfc/wfc/shared/file_io.py`** - FileLock implementation for atomic writes. Prevents KNOWLEDGE.md corruption under concurrent access (MUST-2 requirement).

4. **`/Users/samfakhreddine/repos/wfc/wfc/shared/resource_pool.py`** - TokenBucket (rate limiting) and WorktreePool (resource limits). Prevents API 429 errors and resource exhaustion (MUST-4, MUST-5).

5. **`/Users/samfakhreddine/repos/wfc/wfc/scripts/orchestrators/review/orchestrator.py`** - Threading ProjectContext through review workflow. Connects all pieces together, ensures developer attribution and namespaced output (MUST-1, MUST-3).
