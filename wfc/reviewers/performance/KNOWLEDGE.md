# KNOWLEDGE.md -- Performance Reviewer

## Patterns Found

- [2026-02-16] WFC uses @lru_cache extensively for expensive operations: regex compilation in_util.py (maxsize=256), pattern loading in security_hook.py (maxsize=1), and model resolution -- verify cache sizes are appropriate for the working set (Source: initial-seed)
- [2026-02-16] The security hook compiles and caches regex patterns via compile_regex() with a 256-entry LRU cache -- pattern files are loaded once and cached with_load_patterns(maxsize=1) (Source: initial-seed)
- [2026-02-16] PersonaRegistry builds multiple in-memory indexes (by_tag, by_tech_stack, by_panel, by_complexity, by_property) at initialization for O(1) lookup during persona selection (Source: initial-seed)
- [2026-02-16] Token budget allocation reserves 92% of the total budget (138k of 150k tokens) for actual code files, with only 1k for system prompts -- this aggressive allocation is key to the 99% token reduction claim (Source: initial-seed)
- [2026-02-16] subprocess calls in _checkers/python.py run ruff twice (once for --fix, once for format) then again for lint checking -- this is three ruff invocations per Python file save (Source: initial-seed)

## False Positives to Avoid

- [2026-02-16] _load_patterns() uses str(PATTERNS_DIR) as the cache key instead of a Path object -> this is required because @lru_cache needs hashable arguments, not a performance anti-pattern (Source: initial-seed)
- [2026-02-16] PersonaRegistry loads all persona JSON files at init rather than lazily -> this is intentional because index building requires all personas upfront, and the dataset is small (56 personas) (Source: initial-seed)
- [2026-02-16] The regex_timeout() context manager uses SIGALRM on Unix which has 1-second granularity -> this is acceptable for a safety mechanism, sub-second precision is not needed (Source: initial-seed)

## Incidents Prevented

- [2026-02-16] No incidents recorded yet -- this section will be populated as the reviewer catches real issues in reviews (Source: initial-seed)

## Repository-Specific Rules

- [2026-02-16] Token budgets are tiered by task size: S=200, M=1K, L=2.5K, XL=5K tokens -- exceeding a budget requires explicit justification (Source: initial-seed)
- [2026-02-16] File length warnings trigger at 300 lines (FILE_LENGTH_WARN) and critical alerts at 500 lines (FILE_LENGTH_CRITICAL) -- these thresholds are enforced by the PostToolUse file checker (Source: initial-seed)
- [2026-02-16] The project targets 99% token reduction as a key performance metric -- any change that significantly increases token usage must be justified with benchmarks (make benchmark) (Source: initial-seed)

## Codebase Context

- [2026-02-16] WFC's performance-critical path is the PreToolUse hook dispatch which runs on every tool invocation -- it must complete quickly to avoid blocking the user's workflow (Source: initial-seed)
- [2026-02-16] The consensus algorithm computes weighted scores across all reviewer agents -- in persona mode with relevance-based weights, scores are normalized so total relevance sums to 1.0 (Source: initial-seed)
- [2026-02-16] The PostToolUse file_checker dispatches to language-specific checkers (Python, TypeScript, Go) based on file extension -- each checker may invoke external tools (ruff, eslint, gofmt) as subprocesses (Source: initial-seed)
- [2026-02-16] Ultra-minimal prompts (200 tokens per persona vs. legacy 3000 tokens) are the primary mechanism for token reduction -- the system trusts the LLM to be an expert without verbose backstories (Source: initial-seed)
