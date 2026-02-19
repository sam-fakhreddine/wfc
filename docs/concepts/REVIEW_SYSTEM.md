# Five-Agent Consensus Review System

## What It Is

Every time you run `wfc review` or trigger a review through `wfc-build` or `wfc-lfg`, your code is analyzed by five independent specialist reviewers running in parallel. Each reviewer examines the code through a specific lens: Security, Correctness, Performance, Maintainability, and Reliability.

This is not a single AI giving you a generic opinion. It is five distinct agents with separate domain knowledge, each producing structured findings. Those findings are then deduplicated, scored mathematically, and combined into a single Consensus Score (CS) that drives the merge decision.

## The Five Reviewers

Each reviewer loads its instructions from a dedicated prompt file at `wfc/references/reviewers/{name}/PROMPT.md` and draws on accumulated domain knowledge from a paired `KNOWLEDGE.md` file.

- **Security**: OWASP/CWE taxonomy, injection flaws, authentication gaps, privilege escalation, secrets in code, and hostile threat modeling.
- **Correctness**: Edge cases, off-by-one errors, contract violations, type safety, and logic errors that tests might miss.
- **Performance**: Big-O complexity, N+1 query patterns, unnecessary allocations, and memory pressure under load.
- **Maintainability**: SOLID principles, DRY violations, tight coupling, naming clarity, and long-term readability.
- **Reliability**: Concurrency hazards, error handling gaps, resource leaks, chaos scenarios, and failure recovery paths.

## The Consensus Score Formula

After all five reviewers submit their findings, WFC computes a single Consensus Score:

```
CS = (0.5 × R̄) + (0.3 × R̄ × k/n) + (0.2 × R_max)
```

Where:

- `R_i = (severity × confidence) / 10` — the relevance score for each deduplicated finding. Severity and confidence are each on a 0–10 scale, so R_i is bounded between 0 and 10.
- `R̄` (R-bar) — the mean R_i across all findings. This is the baseline signal: how serious are the findings on average?
- `k` — the total number of reviewer agreements across all findings. A finding seen by three reviewers has k=3. This term rewards cross-reviewer agreement.
- `n` — always 5 (the fixed number of reviewers). The ratio k/n measures how much consensus exists.
- `R_max` — the single highest R_i across all findings. This term ensures one severe finding can anchor the score upward even if everything else is minor.

In plain English: the score is dominated by average severity, boosted when multiple reviewers agree on the same issue, and anchored by the worst finding found.

## Minority Protection Rule (MPR)

The standard formula relies on averages, which means a single catastrophic security finding could be mathematically diluted by a dozen low-severity style notes. The Minority Protection Rule prevents this.

If the maximum finding score (R_max) is 8.5 or higher **and** that finding comes from the Security or Reliability reviewer, the Consensus Score is elevated:

```
CS_final = max(CS, 0.7 × R_max + 2.0)
```

One reviewer cannot be outvoted on a critical security or reliability issue. This is intentional: these are the domains where being wrong has the highest real-world cost.

## Decision Tiers

The Consensus Score maps to one of four tiers, each with a defined response:

| CS Range | Tier | Action |
|---|---|---|
| CS < 4.0 | Informational | Logged only, merge proceeds |
| 4.0 <= CS < 7.0 | Moderate | Inline PR comment added |
| 7.0 <= CS < 9.0 | Important | Merge blocked until resolved |
| CS >= 9.0 | Critical | Merge blocked + escalation required |

## Finding Deduplication

When five reviewers analyze the same code, they will sometimes flag the same issue. Without deduplication, the same SQL injection on line 42 appearing in three reviewer outputs would be counted three times, inflating the score and burying the report in noise.

WFC deduplicates findings using a SHA-256 fingerprint computed from three fields: `{file}:{line_start // 3}:{category}`. The line number is bucketed in groups of three so that findings within three lines of each other in the same category are treated as the same issue. When duplicates are merged, the highest severity wins, all unique descriptions and remediations are preserved, and the reviewer count `k` is incremented — which feeds directly into the CS formula as a signal of cross-reviewer agreement.

## Emergency Bypass

When a review must be bypassed (e.g., a production incident requiring immediate deployment), WFC provides a 24-hour bypass with a mandatory reason. Every bypass is recorded to an append-only `BYPASS-AUDIT.json` file, including the CS at the time of bypass. This creates an accountability trail without blocking emergency response.
