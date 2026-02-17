# KNOWLEDGE.md Schema

## Purpose

Each reviewer has a KNOWLEDGE.md that serves as its institutional memory -- human-readable, git-controlled, and RAG-indexed. Over time, reviewers accumulate domain-specific knowledge about the codebase they review, making each successive review more accurate and context-aware.

## File Location

```
wfc/reviewers/<domain>/KNOWLEDGE.md
```

Where `<domain>` is one of: `security`, `correctness`, `performance`, `maintainability`, `reliability`.

## Sections

### Patterns Found

Recurring code patterns specific to this codebase that the reviewer has learned to watch for.

**Format:**
```
- [YYYY-MM-DD] <pattern description> (Source: <review/PR reference>)
```

**Example:**
```
- [2026-02-16] WFC uses subprocess calls in hook infrastructure -- verify all subprocess inputs are sanitized (Source: initial-seed)
```

### False Positives to Avoid

Things that look like issues in this domain but are not problems in the context of this specific project. Prevents the reviewer from repeatedly flagging known-safe patterns.

**Format:**
```
- [YYYY-MM-DD] <what looks wrong> -> <why it's actually fine> (Source: <reference>)
```

**Example:**
```
- [2026-02-16] eval() appears in security pattern regex -> it is a string literal inside a JSON pattern definition, not executable code (Source: initial-seed)
```

### Incidents Prevented

High-value catches from past reviews -- findings that prevented real bugs or security issues. This section captures the reviewer's track record and reinforces vigilance for similar patterns.

**Format:**
```
- [YYYY-MM-DD] <what was caught> -> <what would have happened> (Source: <reference>)
```

**Example:**
```
- [2026-02-16] Caught unsanitized user input in subprocess call -> could have allowed command injection (Source: PR-45)
```

### Repository-Specific Rules

Project conventions and architectural decisions that affect this reviewer's domain. These are rules that cannot be inferred from the code alone and must be explicitly documented.

**Format:**
```
- [YYYY-MM-DD] <rule description> (Source: <reference>)
```

**Example:**
```
- [2026-02-16] All Python code must pass ruff and pyright checks before merge (Source: initial-seed)
```

### Codebase Context

Key architectural facts relevant to this reviewer's domain. Provides the background knowledge needed to make informed review decisions.

**Format:**
```
- [YYYY-MM-DD] <architectural fact> (Source: <reference>)
```

**Example:**
```
- [2026-02-16] Hook infrastructure uses a two-phase dispatch: security patterns first, then custom rules (Source: initial-seed)
```

## Entry Rules

1. Each entry is a single, self-contained fact (atomic entries for clean RAG chunking)
2. Entries MUST have a date in `[YYYY-MM-DD]` format
3. Entries SHOULD have a source attribution in `(Source: <reference>)` format
4. Entries are parseable by a RAG chunker without loss of meaning
5. No multi-fact entries -- split compound facts into separate lines
6. Use `->` to indicate cause-effect or "looks like X but is actually Y" relationships
7. Use `--` (double dash) for inline clarifications within a single fact

## Machine Parsing

Each entry can be parsed with a simple regex:

```
^\- \[(\d{4}-\d{2}-\d{2})\] (.+?) \(Source: (.+?)\)$
```

Capturing groups:
1. Date (YYYY-MM-DD)
2. Content (the fact itself)
3. Source attribution

## Lifecycle

1. **Seeded** at reviewer creation with initial codebase observations
2. **Updated** after each review cycle with new learnings
3. **Pruned** periodically to remove stale or superseded entries
4. **Version-controlled** via git for full audit trail
