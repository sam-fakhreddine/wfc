---
name: wfc-skill-fixer
description: >
  Diagnose and fix Claude Skills at scale using 6-agent pipeline: Cataloger (filesystem inventory),
  Analyst (rubric-based diagnosis), Fixer (LLM rewriting), Structural QA (validation with retry),
  Functional QA (optional execution testing), Reporter (deliverable generation). Detects 16 skill antipatterns,
  validates against triggering/instruction/operational rubric, preserves scripts (never modifies), handles
  cross-reference integrity, frontmatter validation, and skills-ref integration with graceful fallback.
---

# Skill Fixer

6-agent pipeline for diagnosing and fixing Claude Skills at scale.

## Quick Reference

```bash
# Fix single skill
/wfc-skill-fixer ~/.claude/skills/wfc-build

# With functional QA (slow)
/wfc-skill-fixer --functional-qa ~/.claude/skills/wfc-build
```

## Core Workflow

1. **Cataloger** - Local filesystem inventory (no LLM)
2. **Analyst** - Diagnose against skill rubric (LLM or fallback)
3. **Fixer** - Rewrite to fix issues (LLM or fallback)
4. **Structural QA** - Validate with retry support
5. **Functional QA** - Optional skill execution testing
6. **Reporter** - Generate deliverable summary

## Rubric Dimensions

**Triggering** (critical for skill loading):

- TRIGGER_COVERAGE: Does description cover all user phrasings?
- TRIGGER_ASSERTIVENESS: Pushy enough to overcome undertriggering?
- TRIGGER_SPECIFICITY: Clear boundaries to avoid overtriggering?
- TRIGGER_FORMAT: Valid YAML, under 1024 chars, no angle brackets?

**Instruction Quality**:

- PROGRESSIVE_DISCLOSURE: Uses 3-level loading effectively?
- STRUCTURE_PATTERN: Appropriate pattern (workflow/task-based/reference)?
- ACTIONABILITY: Concrete commands vs vague suggestions?
- EXAMPLE_QUALITY: Present when needed, demonstrates right patterns?
- SCOPE_BOUNDARIES: Clear negative scope?
- ANTI_BLOAT: Free of README-style content (under 700 lines)?

**Operational Integrity**:

- FILE_INTEGRITY: Cross-references resolve?
- SCRIPT_QUALITY: Executable, has shebang, basic error handling?
- REFERENCE_ORGANIZATION: ToCs for long files, selective reading?

## Antipatterns Detected

See `references/antipatterns.json` for full list (SK-01 through SK-16).

Critical:

- SK-01: Empty/TODO description
- SK-03: Overbroad description
- SK-08: Phantom file references

Major:

- SK-02: Timid description
- SK-10: Non-executable scripts
- SK-11: README in disguise (>700 lines)

## Constraints

**NEVER modifies scripts** - only flags issues for human review
Preserves original intent while fixing diagnosed issues
Uses skills-ref validate when available, graceful fallback otherwise

## Output

Report includes:

- Grade change (A-F)
- Triggering changes
- Structural changes (max 5)
- Script issues (human action required)
- Unresolved items
- Rewritten files (ready to deploy)
