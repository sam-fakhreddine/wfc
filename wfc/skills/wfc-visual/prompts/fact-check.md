---
description: Verify the factual accuracy of a document against the actual codebase, correct inaccuracies in place
skill: wfc-visual
---
Verify the factual accuracy of a document that makes claims about a codebase. Read the file, extract every verifiable claim, check each against the actual code and git history, correct inaccuracies in place, and add a verification summary.

For HTML files: read `./references/css-patterns.md` to match the existing page's styling when inserting the verification summary.

**Target file** — determine what to verify from `$1`:
- Explicit path: verify that specific file
- No argument: verify the most recently modified `.html` file in `~/.agent/diagrams/`

Auto-detect the document type and adjust the verification strategy:
- **HTML review pages** (diff-review, plan-review, project-recap): verify against the git ref or plan file
- **Plan/spec documents** (markdown): verify file references, function/type names, behavior descriptions
- **Any other document**: extract and verify whatever factual claims about code it contains

**Phase 1: Extract claims.** Read the file. Extract every verifiable factual claim:
- **Quantitative**: line counts, file counts, function counts, metrics
- **Naming**: function names, type names, module names, file paths
- **Behavioral**: descriptions of what code does, before/after comparisons
- **Structural**: architecture claims, dependency relationships, import chains
- **Temporal**: git history claims, commit attributions, timeline entries

Skip subjective analysis (opinions, design judgments).

**Phase 2: Verify against source.** For each extracted claim:
- Re-read every file referenced in the document
- For git claims: re-run git commands and compare output
- For diff-reviews: read both ref and working tree versions
- For plan docs: verify files/functions/types exist as described

Classify each: **Confirmed**, **Corrected**, or **Unverifiable**.

**Phase 3: Correct in place.** Edit the file directly:
- Fix incorrect numbers, function names, file paths, behavior descriptions
- Preserve layout, CSS, animations, Mermaid diagrams (unless they contain errors)

**Phase 4: Add verification summary.**
- HTML: insert as a banner/section matching the page's styling
- Markdown: append a `## Verification Summary` section

Include: total claims checked, confirmed count, corrections list, unverifiable flags.

**Phase 5: Report.** Tell the user what was checked/corrected and open the file.

This is a fact-checker — it verifies data matches reality. It does not change structure, opinions, or design judgments.

Write corrections to the original file.

Ultrathink.

$@
