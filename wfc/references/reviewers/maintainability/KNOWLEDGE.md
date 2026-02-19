# KNOWLEDGE.md -- Maintainability Reviewer

## Patterns Found

- [2026-02-16] WFC follows a progressive disclosure pattern: SKILL.md files are kept under 500 lines, reference docs are loaded on demand, and scripts execute only when needed (Source: initial-seed)
- [2026-02-16] The hooks subsystem uses a consistent three-layer structure: public entry point (check/evaluate) wraps _impl function wraps per-item logic -- this pattern appears in security_hook.py, rule_engine.py, and pretooluse_hook.py (Source: initial-seed)
- [2026-02-16] Dataclasses are used consistently for structured data: PatternMatch, CheckResult, TokenBudget, Persona, PersonaSelectionContext, SelectedPersona, ConsensusResult -- prefer dataclasses over raw dicts for new structures (Source: initial-seed)
- [2026-02-16] The codebase uses __future__ annotations imports for forward reference support in type hints across all hook modules (Source: initial-seed)
- [2026-02-16] Module-level docstrings follow a consistent pattern: purpose statement, architecture notes, and design principles (e.g., token_manager.py has ARCHITECTURE and DESIGN PRINCIPLES sections) (Source: initial-seed)

## False Positives to Avoid

- [2026-02-16] sys.path.insert(0, ...) appears in multiple files (file_checker.py, consensus.py, persona_orchestrator.py) -> this is needed to support both package imports and standalone execution, not a code smell (Source: initial-seed)
- [2026-02-16] Global mutable state (_bypass_count) exists in several hook modules -> this is intentional lightweight telemetry for monitoring hook health, acceptable in the single-threaded hook context (Source: initial-seed)
- [2026-02-16] The EXTENSION_TO_LANGUAGE mapping is duplicated between security_hook.py and persona_orchestrator.py with slight differences -> each module needs its own mapping for its specific use case (security vs. tech stack detection) (Source: initial-seed)

## Incidents Prevented

- [2026-02-16] No incidents recorded yet -- this section will be populated as the reviewer catches real issues in reviews (Source: initial-seed)

## Repository-Specific Rules

- [2026-02-16] Line length limit is 100 characters, enforced by both black and ruff as configured in pyproject.toml (Source: initial-seed)
- [2026-02-16] Files should not exceed 300 lines (warning) or 500 lines (critical) -- split into focused modules when approaching these limits (Source: initial-seed)
- [2026-02-16] The project uses ruff for linting and import sorting, black for formatting -- run make format before committing (Source: initial-seed)
- [2026-02-16] Development artifacts (summaries, plans, scratch notes) must go in .development/ which is gitignored -- never commit these to the repository (Source: initial-seed)

## Codebase Context

- [2026-02-16] WFC is organized as: wfc/ (main package), wfc/scripts/ (executable code), wfc/references/ (progressive disclosure docs), wfc/assets/ (templates), tests/ (test suite), docs/ (documentation by topic) (Source: initial-seed)
- [2026-02-16] Skills are installed to ~/.claude/skills/wfc-*/ and follow Agent Skills compliance: valid frontmatter (name, description, license only), hyphenated names, XML prompt generation (Source: initial-seed)
- [2026-02-16] The hook infrastructure separates concerns: pretooluse_hook.py is the dispatcher, security_hook.py handles pattern matching, rule_engine.py handles user rules,_util.py provides shared utilities (Source: initial-seed)
- [2026-02-16] The persona system separates orchestration (persona_orchestrator.py selects who reviews) from execution (persona_executor.py prepares what they review) from prompting (ultra_minimal_prompts.py defines how they review) (Source: initial-seed)
