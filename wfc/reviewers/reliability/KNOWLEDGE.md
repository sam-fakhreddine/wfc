# KNOWLEDGE.md -- Reliability Reviewer

## Patterns Found

- [2026-02-16] All WFC hook entry points use a fail-open pattern: exceptions in the hook never block the user's workflow (exit 0 on error) -- this is enforced in pretooluse_hook.py, security_hook.py, rule_engine.py, and file_checker.py (Source: initial-seed)
- [2026-02-16] The regex_timeout() context manager uses SIGALRM to prevent regex catastrophic backtracking, but degrades gracefully on Windows or non-main threads where SIGALRM is unavailable (Source: initial-seed)
- [2026-02-16] PersonaRegistry._load_personas() catches JSONDecodeError, KeyError, and FileNotFoundError individually per persona file -- a corrupt single persona file does not prevent loading the remaining 55 personas (Source: initial-seed)
- [2026-02-16] The _extract_content() function in security_hook.py handles multiple fallback fields (content, new_string, new_source) to account for different tool input formats (Write, Edit, NotebookEdit) (Source: initial-seed)
- [2026-02-16] Import errors for security_hook and rule_engine are caught in pretooluse_hook.py with a silent exit(0) -- this prevents broken imports from disabling the entire hook system (Source: initial-seed)

## False Positives to Avoid

- [2026-02-16] pretooluse_hook.py exits with code 0 when stdin is empty or contains invalid JSON -> this is correct fail-open behavior, not missing error handling (Source: initial-seed)
- [2026-02-16] file_checker.py main() returns 0 on any exception via a bare except -> this is intentional fail-open to prevent PostToolUse hook failures from blocking file writes (Source: initial-seed)
- [2026-02-16] The consensus algorithm returns passed=False even if overall_score >= 7.0 when any single agent fails -> this is the intended "any agent vetoes" design, not a logic error (Source: initial-seed)

## Incidents Prevented

- [2026-02-16] No incidents recorded yet -- this section will be populated as the reviewer catches real issues in reviews (Source: initial-seed)

## Repository-Specific Rules

- [2026-02-16] Hooks must NEVER block the user's workflow due to internal bugs -- the fail-open pattern (catch-all exception -> exit 0) is mandatory for all hook entry points (Source: initial-seed)
- [2026-02-16] The _bypass_count telemetry must be incremented on every caught exception in hook modules to enable monitoring of hook health degradation (Source: initial-seed)
- [2026-02-16] Regex operations in hooks must use the regex_timeout() context manager with a 1-second timeout to prevent hangs from malicious or malformed patterns (Source: initial-seed)
- [2026-02-16] Critical severity findings in the consensus algorithm bypass confidence filtering -- a critical finding is always surfaced regardless of its confidence score (Source: initial-seed)

## Codebase Context

- [2026-02-16] WFC hooks run synchronously in the Claude Code tool execution path -- any hang or crash in a hook directly impacts the user experience (Source: initial-seed)
- [2026-02-16] The hook dispatch follows a strict priority order: security patterns (Phase 1, can block) then custom rules (Phase 2, can block) -- a security block takes precedence and skips rule evaluation (Source: initial-seed)
- [2026-02-16] The HookState class provides session-scoped deduplication of warnings, preventing the same issue from being warned about repeatedly during a single session (Source: initial-seed)
- [2026-02-16] tiktoken is an optional dependency (installed via wfc[tokens]) -- the token_manager degrades to estimation when tiktoken is unavailable, with a logged warning (Source: initial-seed)
- [2026-02-16] The PersonaSelector enforces panel diversity (max 2 per panel) to prevent a single domain from dominating the review -- if diversity reduces the pool below the target count, the constraint is relaxed (Source: initial-seed)
