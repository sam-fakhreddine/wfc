# Five-Agent Consensus Review v2.0

## Overview

The review system uses 5 fixed specialist reviewers to analyze code changes. Each reviewer has a dedicated domain, a PROMPT.md defining its analysis scope, and a KNOWLEDGE.md that accumulates learnings via RAG. Findings are deduplicated across reviewers and scored using the Consensus Score (CS) algorithm.

## Architecture

```
ReviewOrchestrator (orchestrator.py)
  ├── prepare_review(request) → 5 task specs
  │     └── ReviewerEngine.prepare_review_tasks()
  │           └── ReviewerLoader (loads wfc/references/reviewers/{name}/PROMPT.md)
  │                 └── KnowledgeRetriever (optional, two-tier RAG)
  │
  └── finalize_review(request, responses, output_dir) → ReviewResult
        ├── ReviewerEngine.parse_results() → ReviewerResult per reviewer
        ├── Fingerprinter.deduplicate() → DeduplicatedFinding list
        ├── ConsensusScore.calculate() → ConsensusScoreResult with MPR
        └── Generate REVIEW-{task_id}.md report

CLI (cli.py)
  ├── wfc review --files ... --diff ... --format text|json
  └── --emergency-bypass --bypass-reason "..." --bypassed-by "..."

EmergencyBypass → BYPASS-AUDIT.json (24h expiry, append-only)

ReviewBenchmark → dataset.json (21 labeled test cases, precision/recall/F1)
```

## The 5 Reviewers

Each reviewer lives at `wfc/references/reviewers/{id}/` with two files:

| Reviewer | Domain | Focus Areas |
|----------|--------|-------------|
| **Security** | Vulnerabilities, auth, crypto | OWASP/CWE taxonomy, injection, hardcoded secrets, auth bypass |
| **Correctness** | Logic, contracts, types | Edge cases, null handling, off-by-one, contract violations |
| **Performance** | Efficiency, scalability | Big-O, N+1 queries, memory leaks, unnecessary allocations |
| **Maintainability** | Readability, design | SOLID principles, DRY, coupling/cohesion, complexity |
| **Reliability** | Resilience, failure handling | Concurrency, error propagation, resource leaks, timeouts |

### PROMPT.md

Defines the reviewer's identity, analysis checklist, output format (JSON schema), and severity mapping. Under 500 tokens each.

### KNOWLEDGE.md

Accumulates repository-specific learnings:

- **Patterns Found**: Recurring issues seen in this codebase
- **False Positives to Avoid**: Things that look like issues but aren't
- **Codebase Conventions**: Project-specific patterns to respect

## Consensus Score (CS) Algorithm

### Formula

```
CS = (0.5 * R_bar) + (0.3 * R_bar * (k/n)) + (0.2 * R_max)
```

Where:

- **R_i** = `(severity * confidence) / 10` for each deduplicated finding
- **R_bar** = mean of all R_i values
- **k** = total reviewer agreements (sum of DeduplicatedFinding.k across all findings)
- **n** = 5 (total reviewers)
- **R_max** = max(R_i) across all findings

### Decision Tiers

| Tier | CS Range | Action |
|------|----------|--------|
| Informational | CS < 4.0 | Log only |
| Moderate | 4.0 <= CS < 7.0 | Inline comment |
| Important | 7.0 <= CS < 9.0 | Block merge |
| Critical | CS >= 9.0 | Block + escalate |

Review **passes** if tier is informational or moderate (CS < 7.0).

### Minority Protection Rule (MPR)

Prevents a single critical security/reliability finding from being diluted by clean reports from other reviewers.

**Trigger**: R_max >= 8.5 AND the finding is from a security or reliability reviewer.

**Effect**: `CS_final = max(CS, 0.7 * R_max + 2.0)`

This ensures a 9.5-severity security finding with 9.5-confidence always blocks, even if all other reviewers report clean.

## Finding Deduplication

When multiple reviewers flag the same issue, findings are merged rather than counted separately.

### Fingerprinting

Each finding gets a SHA-256 fingerprint: `sha256("{file}:{normalized_line}:{category}")`

Line normalization uses `(line_start // 3) * 3` to create +/-3 line tolerance buckets.

### Merge Rules

When findings share a fingerprint:

- **Severity**: Highest wins
- **Confidence**: Highest wins
- **Descriptions**: All unique descriptions preserved
- **Remediations**: All unique remediations preserved
- **k**: Count of unique reviewer IDs (used in CS formula for agreement bonus)

## Knowledge System (RAG)

### Two-Tier Retrieval

1. **Embedding search**: Vector similarity against KNOWLEDGE.md chunks
2. **Keyword fallback**: BM25 matching when embeddings aren't available

### Auto-Append (knowledge_writer.py)

After each review, new findings are appended to the relevant reviewer's KNOWLEDGE.md with:

- Date stamp `[YYYY-MM-DD]`
- Category and severity
- File path reference
- Description

### Drift Detection (drift_detector.py)

Periodically checks KNOWLEDGE.md health:

- **Staleness**: Entries older than 90 days
- **Bloat**: Files with >50 entries
- **Contradictions**: Same file path in both "Patterns Found" and "False Positives"
- **Orphaned References**: File paths that no longer exist in the project

Produces a `DriftReport` with recommendation: "healthy", "needs_pruning", or "needs_review".

## Emergency Bypass

For production hotfixes that can't wait for review fixes:

```bash
wfc review --files app/hotfix.py --emergency-bypass \
  --bypass-reason "P0 production outage" \
  --bypassed-by "oncall@example.com"
```

### Constraints

- Reason must be non-empty
- Creates immutable record in `BYPASS-AUDIT.json`
- Records CS at time of bypass
- 24-hour expiry (bypass must be re-issued after 24h)
- Append-only audit trail (records are never deleted)

## CLI Interface

```bash
# Standard review
wfc review --files app/auth.py app/models.py --diff "$(git diff)" --format text

# JSON output (for CI integration)
wfc review --files app/auth.py --format json

# With emergency bypass
wfc review --files app/hotfix.py --emergency-bypass \
  --bypass-reason "Production P0" --bypassed-by "dev@co.com"
```

### Exit Codes

- `0`: Review passed (informational or moderate tier)
- `1`: Review failed (important or critical tier), or validation error

## Benchmark Dataset

21 labeled test cases at `wfc/scripts/benchmark/dataset.json` covering all 5 reviewer domains with true positives and true negatives. Used to measure precision, recall, and F1 score of the review system.

## Key Design Decisions

1. **5 fixed reviewers** (not dynamic selection): Deterministic, debuggable, no selection algorithm overhead
2. **PROMPT.md + KNOWLEDGE.md** (not JSON configs): Human-readable, version-controllable, progressive disclosure
3. **CS formula** (not weighted voting): Mathematical rigor, reproducible scores, clear thresholds
4. **MPR** (not simple majority): Prevents critical security findings from being outvoted by 4 clean reviewers
5. **Fingerprint dedup** (not exact match): Tolerates ±3 line offset across reviewers
6. **24h bypass expiry** (not permanent): Forces re-evaluation after initial emergency passes
