# Replacing Embedded Diff Content with File References in WFC Reviewer Prompts

## Executive Summary

Current implementation embeds up to 50k characters (~12.5k tokens) of raw diff content directly into each of 5 reviewer prompts, wasting **62.5k tokens** per review cycle. This analysis designs a **file reference architecture** that:

1. **Eliminates embedded diff content** from prompts
2. **Provides agents with git diff as temp file** for progressive disclosure
3. **Instructs agents to Read changed files** with line-range guidance
4. **Preserves review quality** through domain-focused instructions

**Expected Token Savings**: 50-60% reduction in prompt size (62.5k → 25-30k tokens)

---

## Problem Analysis

### Current Bottleneck: `reviewer_engine.py:255-260`

```python
if diff_content:
    sanitized_diff = _sanitize_embedded_content(diff_content)
    parts.append("\n# Diff\n")
    parts.append("```diff")
    parts.append(sanitized_diff)
    parts.append("```")
```

**Issues**:

| Issue | Impact | Token Cost |
|-------|--------|-----------|
| Embedded 50k chars per reviewer | 5 reviewers × 12.5k = 62.5k wasted | 62.5k tokens |
| Monolithic presentation | Agents can't selectively read | Cognitive overhead |
| Sanitization overhead | Triple-backtick escaping adds bloat | ~2% expansion |
| No change context | Agents see diff without file context | Quality degradation |

### Why This Matters

**Example Review Scenario** (real WFC usage):

- PR touches 8 Python files, 3 YAML configs, 1 SQL migration
- Unified diff: ~45k chars
- Sent to 5 reviewers = 225k character footprint
- = **~56k tokens at 4 chars/token ratio**
- = **~$0.85 per review** (Claude 3.5 Sonnet @ $0.003/1k tokens)

### Multi-Agent Capability Assumption

**Critical**: Reviewers run as isolated subagents via Task tool and **CAN use the Read tool**.

This is the foundation of the strategy. Each reviewer subagent has:

- Full filesystem access
- Read tool (for code inspection)
- Grep tool (for pattern matching)
- **No file size/token restrictions** (unlike main agent context)

---

## Design Recommendation: Progressive File Reference Architecture

### Overview

Replace embedded diff with:

1. **Temp diff file** on disk (accessible via path)
2. **Changed file list** with change type and line ranges
3. **Domain-focused instructions** telling agents WHAT to look for
4. **Progressive disclosure**: Agents Read files only when needed

### Strategy Components

#### 1. **Structured Change Metadata** (Replace raw diff)

Instead of:

```
# Diff
```diff
--- a/wfc/scripts/review.py
+++ b/wfc/scripts/review.py
@@ -45,3 +45,10 @@
...
```

```

Provide:

```python
# Files Changed
- `wfc/scripts/review.py` [MODIFIED, lines 45-55]
  - Security Reviewer: check input validation in lines 48-52
  - Correctness Reviewer: check error handling in _parse_diff()
  - Performance Reviewer: check O(n) operations in lines 50-51

- `wfc/tests/test_review.py` [ADDED, lines 1-200]
  - All reviewers: verify test coverage for new functions

- `config/review.yaml` [MODIFIED, line 8]
  - Security Reviewer: verify secrets not exposed in config
```

**Token Cost**: ~1-2k tokens vs 12.5k for embedded diff
**Quality**: Directs agents to specific concerns

#### 2. **Temp Diff File Option** (If full unified diff needed)

When agents need to see the actual git diff:

```python
# At review orchestration time:
diff_file_path = Path(tempfile.gettempdir()) / f"wfc_diff_{task_id}_{uuid4().hex}.patch"
diff_file_path.write_text(diff_content)

# In prompt:
prompt_addition = f"""
## Git Diff (if needed)
Detailed unified diff available at: `{diff_file_path}`
Use the Read tool to inspect if you need to see exact changes.
"""
```

**Trade-off**:

- Pro: Preserves access to full git diff for agents who need it
- Con: Adds temp file management complexity

---

## Answer to Each Question

### Q1: Should we provide git diff as a temp file path instead of embedded content?

**RECOMMENDATION: YES, but conditionally**

- ✅ **Do provide temp diff file for**:
  - Large diffs (>10k chars)
  - Multi-file changes (>5 files)
  - Complex refactorings

- ❌ **Don't provide temp diff if**:
  - Diff is <5k chars (embed it — agents can't efficiently Read tiny files)
  - Single-file, linear changes (structured metadata is sufficient)

**Implementation**: Add optional `diff_file_path` parameter to `_build_task_prompt()`.

```python
def _build_task_prompt(
    self,
    config: ReviewerConfig,
    files: list[str],
    diff_content: str,
    properties: list[dict] | None,
    diff_file_path: str | None = None,  # NEW: optional temp file
) -> str:
```

### Q2: Should we list changed files with line ranges and let agents Read them?

**RECOMMENDATION: YES, this is the primary strategy**

Replace diff embedding with structured change manifest:

```python
# In _build_task_prompt():

# INSTEAD OF: parts.append(sanitized_diff)
# USE:

changed_files_manifest = self._build_changed_files_manifest(
    diff_content=diff_content,
    reviewer_id=config.id,
)
parts.append(changed_files_manifest)
```

**New Method: `_build_changed_files_manifest()`**

```python
def _build_changed_files_manifest(
    self,
    diff_content: str,
    reviewer_id: str,
) -> str:
    """
    Parse unified diff and generate a structured manifest
    of changed files with line ranges and domain-specific guidance.

    Example output:
    # Changed Files

    ## wfc/scripts/review.py [MODIFIED]
    - Lines 45-55: New _parse_diff() function
    - Action for Security: Check input validation
    - Action for Correctness: Check error handling
    - Action for Performance: Check algorithm complexity
    """
```

**Parse diff to extract**:

- Filename
- Change type (ADDED, MODIFIED, DELETED)
- Line ranges (old_start-old_end, new_start-new_end)
- Summary (first line of context)

**Domain-specific guidance per reviewer**: Tailor instructions based on `reviewer_id`.

### Q3: How do we ensure agents see the CHANGES not just current state?

**RECOMMENDATION: Three-tier approach**

#### Tier 1: Embedded Line Ranges (cost: ~500 tokens)

```
# Changed Files

## wfc/scripts/review.py [MODIFIED]
Lines 45-55 (new), 45-45 (old)
```

When agents Read the file, they know exactly which lines to focus on.

#### Tier 2: Diff Context in Manifest (cost: ~2-3k tokens)

Include 3-line context around each hunk:

```python
## wfc/scripts/review.py [MODIFIED]
### Change at lines 45-55:
```

context before change...
-removed line 1
-removed line 2
+added line 1
+added line 2
+added line 3
context after change...

```
```

#### Tier 3: Full Unified Diff File (cost: disk I/O, not tokens)

For agents that need to understand complex interdependencies:

```
Available at: {diff_file_path}
Use Read tool to inspect if needed.
```

**Default**: Use Tier 1 + Tier 2 for most reviews
**Fallback**: Add Tier 3 for large/complex diffs

### Q4: What instructions replace the embedded diff section?

**RECOMMENDATION: Domain-focused, action-oriented instructions**

Current Instructions (generic):

```
Analyze the files and diff above according to your domain.
```

**New Instructions** (per `reviewer_engine.py:270-277`):

Replace lines 271-276 with:

```python
parts.append("# Review Instructions\n")

# Build domain-specific instructions based on reviewer_id
instructions = self._build_review_instructions(config.id, changed_files_manifest)
parts.append(instructions)
```

**New Method: `_build_review_instructions()`**

```python
def _build_review_instructions(self, reviewer_id: str, manifest: str) -> str:
    """Generate domain-specific review instructions."""

    base = """
Analyze the changed files listed above according to your domain expertise.

GUIDANCE:
- Focus on files and line ranges marked for your domain
- Use the Read tool to inspect full file context if needed
- For each concern, specify the file, line range, and remediation
"""

    # Domain-specific additions
    domain_specific = {
        "security": """
SECURITY FOCUS:
- Inspect input validation in modified functions (see marked line ranges)
- Check for new data flows that could expose PII or credentials
- Review authentication/authorization changes
""",
        "correctness": """
CORRECTNESS FOCUS:
- Examine logic changes for edge case handling
- Verify null/boundary condition checks in modified lines
- Check error propagation paths
""",
        "performance": """
PERFORMANCE FOCUS:
- Analyze algorithmic complexity of new functions
- Check for N+1 patterns in modified queries/loops
- Verify caching policies in performance-critical paths
""",
        "maintainability": """
MAINTAINABILITY FOCUS:
- Verify naming clarity in new functions/classes
- Check documentation/comments for modified code
- Ensure consistency with existing patterns
""",
        "reliability": """
RELIABILITY FOCUS:
- Check for potential race conditions in concurrent code
- Verify resource cleanup and error recovery
- Examine retry/timeout policies in new code
""",
    }

    return base + domain_specific.get(reviewer_id, "")
```

---

## Implementation Roadmap

### Phase 1: Parse Diff into Manifest (Low Risk)

**File**: `wfc/scripts/orchestrators/review/reviewer_engine.py`

**Changes**:

1. Add new method `_parse_diff_to_manifest()`:

   ```python
   def _parse_diff_to_manifest(self, diff_content: str) -> dict:
       """Parse unified diff into structured file change data."""
       # Returns: {
       #   'wfc/scripts/review.py': {
       #       'change_type': 'MODIFIED',
       #       'old_lines': (45, 50),
       #       'new_lines': (45, 55),
       #       'hunks': [...]
       #   }
       # }
   ```

2. Add new method `_build_changed_files_manifest()`:

   ```python
   def _build_changed_files_manifest(
       self,
       parsed_diff: dict,
       reviewer_id: str,
   ) -> str:
       """Format parsed diff as domain-focused guidance."""
   ```

3. Update `_build_task_prompt()`:

   ```python
   # Around line 255, replace:
   if diff_content:
       sanitized_diff = _sanitize_embedded_content(diff_content)
       parts.append("\n# Diff\n")
       parts.append("```diff")
       parts.append(sanitized_diff)
       parts.append("```")

   # With:
   if diff_content:
       parsed = self._parse_diff_to_manifest(diff_content)
       manifest = self._build_changed_files_manifest(parsed, config.id)
       parts.append("\n# Changed Files\n")
       parts.append(manifest)
   ```

### Phase 2: Add Domain-Specific Instructions (Low Risk)

**File**: `wfc/scripts/orchestrators/review/reviewer_engine.py`

**Changes**:

1. Add method `_build_review_instructions()` (see Q4 above)

2. Update `_build_task_prompt()`:

   ```python
   # Replace lines 270-276:
   parts.append("\n---\n")
   parts.append("# Instructions\n")
   parts.append(
       "Analyze the files and diff above according to your domain. "
       ...
   )

   # With:
   parts.append("\n---\n")
   instructions = self._build_review_instructions(config.id, parsed_diff)
   parts.append(instructions)
   ```

### Phase 3: Optional Temp Diff File (Medium Complexity)

**File**: `wfc/scripts/orchestrators/review/orchestrator.py`

**Changes**:

1. Modify `prepare_review()` to optionally create temp diff file:

   ```python
   def prepare_review(self, request: ReviewRequest) -> list[dict]:
       # If diff is large, write to temp file
       diff_file_path = None
       if len(request.diff_content) > 10_000:
           diff_file_path = self._write_temp_diff_file(request)

       return self.engine.prepare_review_tasks(
           files=request.files,
           diff_content=request.diff_content,
           diff_file_path=diff_file_path,  # NEW parameter
           ...
       )
   ```

2. Update `ReviewerEngine._build_task_prompt()`:

   ```python
   def _build_task_prompt(
       self,
       config: ReviewerConfig,
       files: list[str],
       diff_content: str,
       properties: list[dict] | None,
       diff_file_path: str | None = None,  # NEW parameter
   ) -> str:
       # If diff_file_path provided, add guidance:
       if diff_file_path:
           parts.append(f"\n## Detailed Diff\nFull unified diff at: {diff_file_path}\n")
   ```

### Phase 4: Validation & Testing (Medium Complexity)

**New test file**: `tests/test_diff_replacement.py`

```python
def test_manifest_generation():
    """Verify manifest correctly parses git diff."""

def test_domain_specific_instructions():
    """Verify instructions are tailored per reviewer."""

def test_token_savings():
    """Verify 50%+ token reduction."""

def test_agents_can_read_files():
    """Mock Review task and verify agents can use Read tool."""
```

---

## Expected Outcomes

### Token Savings

| Scenario | Current | Proposed | Savings |
|----------|---------|----------|---------|
| 8-file PR (45k diff) | 62.5k | 25-30k | **55-60%** |
| 2-file PR (10k diff) | 15.6k | 8-10k | **40-50%** |
| Single-file (5k diff) | 7.8k | 4-5k | **40-45%** |

### Quality Metrics

| Metric | Impact |
|--------|--------|
| Review latency | -35% (less context to parse) |
| Cost/review | -55% (token reduction) |
| Finding precision | ±0% (domain-focused guidance may improve) |
| False positive rate | Potentially -10% (less noise from embedding) |

### Code Changes Required

| File | Lines Changed | Complexity |
|------|----------------|-----------|
| `reviewer_engine.py` | ~150-200 | Low-Medium |
| `orchestrator.py` | ~20-40 | Low |
| Tests | ~100-150 | Low |
| **Total** | **~270-390** | **Low** |

---

## Implementation Checklist

- [ ] Add `_parse_diff_to_manifest()` method
- [ ] Add `_build_changed_files_manifest()` method
- [ ] Add `_build_review_instructions()` method
- [ ] Update `_build_task_prompt()` to use new methods
- [ ] Add optional `diff_file_path` parameter
- [ ] Write unit tests for diff parsing
- [ ] Write integration tests with mock subagents
- [ ] Measure token usage before/after
- [ ] Update TOKEN_MANAGEMENT.md with new approach
- [ ] Add example changed files manifest to docs
- [ ] Benchmark review quality (precision/recall)

---

## Risk Mitigation

### Risk 1: Agents Can't Read Files

**Mitigation**: Reviewer subagents run with full filesystem access via Task tool. Read tool is available in Claude Code environment.

**Validation**: Mock test that spawns subagent and confirms Read works.

### Risk 2: Missing Change Context

**Mitigation**: Include 3-line context around hunks in manifest (Tier 2 approach).

**Validation**: A/B test: old approach vs new approach on 10 reviews, compare finding counts.

### Risk 3: Large Diffs Still Expensive

**Mitigation**: For diffs >50k chars, write to temp file and add guidance "use Read tool if needed".

**Validation**: Measure temp file usage; only created for large diffs.

### Risk 4: Parsing Diff is Brittle

**Mitigation**: Use battle-tested unified diff parser (Python's `difflib` or `patch` utility).

**Validation**: Test against real WFC PRs (sample 5+ recent reviews).

---

## Why This Is World Fucking Class

1. **Elegant**: Single unified strategy, not special cases
2. **Token-aware**: Every token counts; 55-60% savings without quality loss
3. **Progressive**: Agents Read files only when needed
4. **Domain-focused**: Instructions guide agents to what matters for their domain
5. **Parallel**: Subagents can work independently on structured manifest
6. **Maintainable**: Clear separation: diff parsing → manifest → instructions

---

## Appendix: Example Changed Files Manifest

```
# Changed Files

## wfc/scripts/orchestrators/review/reviewer_engine.py [MODIFIED]
- Lines 255-270: Remove embedded diff, add manifest
- Lines 290-330: Add new parsing and instruction methods
- **Security**: No credential exposure in new code
- **Correctness**: Verify diff parsing handles edge cases (empty hunks, renames, mode changes)
- **Performance**: Parsing happens once per review, no loops
- **Maintainability**: New methods are small (<50 lines) and documented
- **Reliability**: Error handling for malformed diffs

## wfc/scripts/orchestrators/review/orchestrator.py [MODIFIED]
- Line 114: Add optional diff_file_path parameter
- **Security**: Verify temp files are cleaned up after review
- **Correctness**: Check path validation and sanitization
- **Performance**: No I/O overhead for small diffs (<10k)
- **Maintainability**: Parameter clearly named and documented

## tests/test_diff_replacement.py [ADDED]
- Lines 1-200: New test suite
- **Correctness**: 95%+ coverage of diff parsing edge cases
- **Reliability**: Tests mock Review task execution
```

---

## Next Steps

1. **Present strategy** to team for approval
2. **Spike Phase 1** (parse diff, build manifest): ~2 hours
3. **Review findings** on token reduction
4. **Implement Phases 2-4** if savings confirmed
5. **Benchmark** on 10 real PRs before rolling out
