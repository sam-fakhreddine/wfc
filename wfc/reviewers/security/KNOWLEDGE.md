# KNOWLEDGE.md -- Security Reviewer

## Patterns Found

- [2026-02-16] WFC uses subprocess calls in hook infrastructure (pretooluse_hook.py, file_checker.py, _checkers/python.py) -- verify all subprocess inputs are sanitized and shell=True is never used (Source: initial-seed)
- [2026-02-16] Security patterns are loaded from JSON files in wfc/scripts/hooks/patterns/ and matched via compiled regexes with @lru_cache -- new patterns must be added to these JSON files, not hardcoded (Source: initial-seed)
- [2026-02-16] The security_hook.py silently passes on any internal exception (returns {}) to avoid blocking user workflow -- this fail-open behavior is intentional but means hook bugs could silently disable security checks (Source: initial-seed)
- [2026-02-16] Regex patterns in security checks use a 1-second SIGALRM timeout via regex_timeout() context manager to prevent ReDoS -- all new regex patterns should be tested for catastrophic backtracking (Source: initial-seed)
- [2026-02-16] The PreToolUse hook reads raw JSON from stdin and parses it -- malformed JSON is silently ignored (exits 0), which is the correct fail-open behavior per Claude Code hook protocol (Source: initial-seed)

## False Positives to Avoid

- [2026-02-16] eval() appears as a string literal in security.json pattern definitions ("\\beval\\s*\\(") -> this is a regex pattern for detection, not executable eval() usage (Source: initial-seed)
- [2026-02-16] subprocess.run() calls in _checkers/python.py and _util.py use capture_output=True without shell=True -> these are safe invocations of known binaries (ruff, pyright, git) with no user-controlled input (Source: initial-seed)
- [2026-02-16] os.system pattern in security.json is a detection regex, not actual os.system() usage in the codebase -> do not flag the pattern file itself (Source: initial-seed)

## Incidents Prevented

- [2026-02-16] No incidents recorded yet -- this section will be populated as the reviewer catches real issues in reviews (Source: initial-seed)

## Repository-Specific Rules

- [2026-02-16] Security checks run as Phase 1 (highest priority) in the PreToolUse hook dispatch, before custom rule evaluation (Source: initial-seed)
- [2026-02-16] The security hook uses a global _bypass_count to track how many times it has failed open due to exceptions -- this counter should be monitored for anomalies (Source: initial-seed)
- [2026-02-16] Blocking patterns (action: "block") cause exit code 2 and halt the tool use; warning patterns (action: "warn") emit to stderr but allow the operation to proceed (Source: initial-seed)
- [2026-02-16] Security patterns support language-scoped and file-pattern-scoped matching -- a pattern with "languages": ["python"] will only match Python files (Source: initial-seed)

## Codebase Context

- [2026-02-16] WFC hook infrastructure uses a two-phase dispatch in pretooluse_hook.py: Phase 1 is security_hook.check() for pattern matching, Phase 2 is rule_engine.evaluate() for user-defined rules (Source: initial-seed)
- [2026-02-16] The project uses Python 3.12+ with UV as the package manager -- never use pip or bare python commands (Source: initial-seed)
- [2026-02-16] FILE_WRITE_TOOLS (Write, Edit, NotebookEdit) and BASH_TOOLS (Bash) are the two categories of tool inputs checked by the security hook (Source: initial-seed)
- [2026-02-16] Known blocked patterns include: eval(), os.system(), subprocess with shell=True, new Function(), rm -rf on system/home paths, and hardcoded secrets (Source: initial-seed)
- [2026-02-16] The HookState class provides deduplication of warnings so the same pattern match on the same file is only warned once per session (Source: initial-seed)
