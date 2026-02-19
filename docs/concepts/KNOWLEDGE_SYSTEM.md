# Knowledge System

## What It Is

Each of WFC's five reviewers has a dedicated `KNOWLEDGE.md` file that grows over time. After every review, findings that meet quality thresholds are automatically written back to the relevant reviewer's knowledge file. The next time that reviewer runs, it retrieves relevant entries from this file and uses them to inform its analysis.

The result is a review system that gets better the more it is used. A security pattern flagged in your codebase today becomes part of the security reviewer's context for every future review on that project.

Knowledge files live at:

```
wfc/references/reviewers/
  security/KNOWLEDGE.md
  correctness/KNOWLEDGE.md
  performance/KNOWLEDGE.md
  maintainability/KNOWLEDGE.md
  reliability/KNOWLEDGE.md
```

## RAG Pipeline: Two-Tier Retrieval

When a review task is prepared, the knowledge retriever performs a two-tier lookup against the relevant reviewer's knowledge file.

**Tier 1 — Embedding-based retrieval**: The query (derived from the diff or file being reviewed) is embedded using the configured embedding provider. Stored knowledge entries are compared by cosine similarity, and the top matches are retrieved. This tier captures semantic similarity — a new SQL query pattern can match against a knowledge entry about parameterized queries even if no keywords overlap.

**Tier 2 — Keyword fallback**: If the embedding tier returns no results above the confidence threshold (e.g., because the embedding model is unavailable or no entries are indexed yet), the retriever falls back to keyword matching against the raw text of the knowledge file. This ensures the system degrades gracefully rather than failing silently.

The two-tier design means knowledge retrieval works correctly even in minimal environments without embedding infrastructure, and becomes more precise as the embedding index is populated.

## Auto-Append After Reviews

After a review completes, `wfc/scripts/knowledge/knowledge_writer.py` examines the findings and extracts learnings based on severity and outcome:

- Findings with severity >= 9.0 are written to the **Incidents Prevented** section.
- Findings with severity >= 7.0 and confidence >= 8.0 are written to the **Patterns Found** section.
- Findings that were dismissed as false positives are written to the **False Positives to Avoid** section.

Each entry is date-stamped and tagged with its source. Duplicate entries (matched case-insensitively) are skipped to prevent the file from accumulating redundant information.

This append process is idempotent: running it multiple times on the same findings does not create duplicate entries.

## Drift Detection

As knowledge files accumulate entries over time, they can become stale, bloated, contradictory, or orphaned. The drift detector (`wfc/scripts/knowledge/drift_detector.py`) analyzes all reviewer knowledge files and surfaces four types of signals:

**Stale** (threshold: 90 days): Entries whose date stamp is older than 90 days. These may reflect patterns that no longer apply to the current codebase or have been resolved.

**Bloated** (threshold: 50 entries): Knowledge files with more than 50 total entries. A bloated file slows retrieval and suggests the pruning workflow should be run.

**Contradictory**: Entries where the same file or pattern appears in both the Patterns Found section and the False Positives to Avoid section. This indicates the reviewer has conflicting signals about whether a pattern is real or noise.

**Orphaned**: Entries that reference specific file paths that no longer exist in the project. These entries are still syntactically valid but no longer point to real code, which reduces their utility in retrieval.

When drift is detected, the recommendation is either `needs_pruning` (for stale or bloated signals) or `needs_review` (for contradictions). Running `wfc-compound` after resolving a non-trivial problem is the recommended way to add high-quality, well-contextualized entries rather than relying solely on the auto-append pipeline.

## Global Knowledge Promotion

Learnings that prove relevant across multiple projects can be promoted to a global knowledge store at `~/.wfc/knowledge/global/reviewers/`. This allows patterns discovered in one repository to inform reviews in others, building a cross-project knowledge base that reflects your organization's actual codebase patterns and past incidents.
