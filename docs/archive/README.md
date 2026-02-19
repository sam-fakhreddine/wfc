# docs/archive/

Historical documents preserved for reference. These were valid at the time of writing but have been superseded by v2.0 system changes or have been replaced by updated docs.

**Never delete from this directory.** If a doc needs further updates, create a new version with an incremented `_V{N}` suffix.

---

## Redirect Table

If you followed a link here from an old bookmark or external reference, use this table to find the current equivalent.

| Archived Document | Reason | Current Equivalent |
|------------------|--------|--------------------|
| `PERSONAS_V1.md` | System replaced 56-persona dynamic selection with 5 fixed specialist reviewers in v2.0 (2026-02-10) | [docs/concepts/REVIEW_SYSTEM.md](../concepts/REVIEW_SYSTEM.md) |
| `ARCHITECTURE_V1.md` | Described old persona library, pre-restructure paths (`wfc/scripts/skills/`, `wfc/reviewers/`) | [docs/architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md) |
| `PLANNING_V1.md` | Contained v1.0 design principles + 56-persona architecture decisions | [docs/architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md) |
| `BA-KODUS-INSPIRED-ENHANCEMENTS.md` | Strategic analysis draft — features not yet implemented | N/A (aspirational) |
| `BA-LOKI-MODE.md` | Dashboard/observability proposal — not yet implemented | N/A (aspirational) |
| `LOKI-MODE-ANALYSIS.md` | Deep-dive on Loki observability features — not yet implemented | N/A (aspirational) |
| `ROADMAP-DASHBOARD-OBSERVABILITY.md` | Dashboard plugin system roadmap — future initiative | N/A (aspirational) |

---

## What Changed in v2.0 (2026-02-10)

The major change archived here: **56-persona dynamic selection → 5 fixed specialist reviewers**.

**Before (v1.0):**

- 56 expert personas across 9 panels
- Dynamic selection at review time based on code characteristics
- Persona prompts were large (3000 tokens each)

**After (v2.0):**

- 5 fixed reviewers: Security, Correctness, Performance, Maintainability, Reliability
- Always the same 5 run (with conditional tier activation for L/XL tasks)
- Reviewer prompts are minimal (200 tokens) + per-reviewer KNOWLEDGE.md (RAG-powered)
- Consensus Score (CS) algorithm with Minority Protection Rule

See [docs/concepts/REVIEW_SYSTEM.md](../concepts/REVIEW_SYSTEM.md) for the current system.

---

## Post-Restructure Path Changes (2026-02-18)

If you see references to old paths in archived docs, use this mapping:

| Old Path | New Path |
|----------|----------|
| `wfc/reviewers/` | `wfc/references/reviewers/` |
| `wfc/scripts/skills/review/` | `wfc/scripts/orchestrators/review/` |
| `wfc/wfc_tools/gitwork/` | `wfc/gitwork/` |
| `wfc/wfc-tools/` | deleted (was legacy dead code) |
