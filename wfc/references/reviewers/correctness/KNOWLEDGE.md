# KNOWLEDGE.md -- Correctness Reviewer

## Patterns Found

- [2026-02-16] WFC modules use try/except ImportError blocks to handle optional dependencies gracefully (e.g., tiktoken in token_manager.py, relative imports in consensus.py) -- verify fallback behavior is correct in each case (Source: initial-seed)
- [2026-02-16] The consensus algorithm requires ALL agents to pass (score >= 7) AND no critical comments AND overall score >= 7.0 -- a single failing agent vetoes the entire review (Source: initial-seed)
- [2026-02-16] The rule_engine.py uses virtual field mapping (TOOL_FIELD_MAP) to translate abstract field names to tool-specific input keys -- new tools must be added to this mapping or their fields will not be checked (Source: initial-seed)
- [2026-02-16] PersonaRegistry loads personas from JSON files in panels/ subdirectories and has a fallback path resolution if the primary panels_dir does not exist (Source: initial-seed)
- [2026-02-16] The file_checker.py PostToolUse hook returns exit code 0 for unsupported languages or on any exception -- linting failures use exit code 2 as non-blocking notifications (Source: initial-seed)

## False Positives to Avoid

- [2026-02-16] consensus.py returns None for consensus_areas, unique_insights, and divergent_views when there are 4 or fewer reviewers -> this is intentional, not a missing-data bug; these fields are only computed in persona mode (>4 reviewers) (Source: initial-seed)
- [2026-02-16] check_python() in _checkers/python.py returns (2, "") on success -> exit code 2 with empty reason means "checks passed, notify Claude" not "error occurred" (Source: initial-seed)
- [2026-02-16] The _bypass_count global variables in security_hook.py, rule_engine.py, and pretooluse_hook.py are module-level mutable state -> this is intentional for lightweight telemetry, not a thread-safety bug in this single-threaded hook context (Source: initial-seed)

## Incidents Prevented

- [2026-02-16] No incidents recorded yet -- this section will be populated as the reviewer catches real issues in reviews (Source: initial-seed)

## Repository-Specific Rules

- [2026-02-16] All Python code targets Python 3.12+ (configured in pyproject.toml) -- do not use compatibility shims for older Python versions (Source: initial-seed)
- [2026-02-16] The project uses hatchling as the build backend with "wfc" as the sole package directory (Source: initial-seed)
- [2026-02-16] Test files are located in tests/ and follow the test_*.py naming convention as configured in pyproject.toml pytest settings (Source: initial-seed)
- [2026-02-16] The consensus algorithm uses fixed weights in legacy 4-agent mode (SEC:35%, CR:30%, PERF:20%, COMP:15%) and relevance-based weights in persona mode (Source: initial-seed)

## Codebase Context

- [2026-02-16] WFC is a multi-agent consensus review system where 5 expert personas independently review code and their scores are combined via weighted consensus (Source: initial-seed)
- [2026-02-16] The PersonaOrchestrator selects 5 relevant experts from 56 available personas using semantic matching on file types, properties, and task context with diversity scoring to ensure varied perspectives (Source: initial-seed)
- [2026-02-16] Token management achieves a 99% reduction (150k -> 1.5k tokens) by using file references instead of full content and ultra-minimal 200-token persona prompts (Source: initial-seed)
- [2026-02-16] The hook system follows Claude Code's protocol: stdin receives JSON with tool_name and tool_input, exit code 0 means allow, exit code 2 means block (Source: initial-seed)
