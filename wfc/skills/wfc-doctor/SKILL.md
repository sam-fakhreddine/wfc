---
name: wfc-doctor
description: WFC system health checker that validates Agent Skills compliance, prompt quality, settings.json configuration, hook installation, and pre-commit setup. Auto-fixes safe issues (settings format, file permissions) and reports findings for manual review. Delegates to wfc-prompt-fixer for prompt quality checks. Generates comprehensive health report in .development/wfc-doctor-report.md with pass/fail status for each check category.
license: MIT
---

# wfc-doctor

Comprehensive WFC installation health checker and auto-fixer.

## ⚠️ Status: EXPERIMENTAL (Stub Implementation)

**Current Implementation:** All checks return PASS unconditionally (no actual validation performed)

This skill provides the **integration framework and architecture** for health checking, but check modules are placeholder stubs. Use for:

- Testing health check orchestration
- Understanding the health check workflow
- Reference implementation for future development

**Production use:** Not recommended until check implementations complete (tracked in [#50](https://github.com/sam-fakhreddine/wfc/issues/50))

---

## What It Will Do (When Complete)

Runs 5 health checks and auto-fixes safe issues:

1. **Agent Skills Compliance** - Validates all 30 wfc-* skills pass `skills-ref validate` ⚠️ *stub*
2. **Prompt Quality** - Delegates to `wfc-prompt-fixer --batch --wfc` for all skill/reviewer prompts ⚠️ *stub*
3. **Settings.json** - Validates hook matchers, permission modes, detects common misconfigurations ⚠️ *stub*
4. **Hook Installation** - Verifies hook scripts exist and are executable ⚠️ *partial*
5. **Pre-commit** - Runs `uv run pre-commit run --all-files` and reports failures ✅ *implemented*

## When to Use

Use `/wfc-doctor` when:

- After fresh WFC installation
- Before starting work (session health check)
- After updating WFC or skills
- Debugging why skills/hooks aren't working
- CI failures that suggest configuration issues

## Workflow

```bash
/wfc-doctor              # Run all checks
/wfc-doctor --fix        # Run checks + auto-fix safe issues
/wfc-doctor --check-only # Report only, no fixes
```

## Health Checks

### 1. Agent Skills Compliance

- Runs `skills-ref validate` (if installed)
- Counts skills in `~/.claude/skills/wfc-*` (should be 30)
- Validates YAML frontmatter format
- Checks for deprecated fields

**Auto-fix:** Removes deprecated frontmatter fields

### 2. Prompt Quality

- Delegates to `wfc-prompt-fixer --batch --wfc wfc/skills/*/SKILL.md`
- Checks all reviewer PROMPT.md files
- Reports grade distribution (A/B/C/D/F)

**Auto-fix:** Can auto-apply fixes if `--fix` flag passed

### 3. Settings.json Validation

- Checks `~/.claude/settings.json` exists
- Validates hook matchers (common issue: `Task` in context_monitor)
- Checks permission modes
- Validates JSON syntax

**Auto-fix:** Corrects common matcher errors, fixes JSON syntax

### 4. Hook Installation

- Verifies `wfc/scripts/hooks/` files exist
- Checks file permissions (executable)
- Validates hook registration in settings

**Auto-fix:** Sets correct permissions on hook scripts

### 5. Pre-commit

- Runs `uv run pre-commit run --all-files`
- Reports failures by category (trailing-whitespace, ruff, black, etc.)
- Shows file paths for failures

**Auto-fix:** Runs `uv run pre-commit run --all-files --fix` for auto-fixable issues

## Outputs

**Report:** `.development/wfc-doctor-report.md`

```markdown
# WFC Health Check Report

**Timestamp:** 2026-02-19 14:30:00
**Status:** PASS | FAIL

---

## Summary

| Check | Status | Issues |
|-------|--------|--------|
| Agent Skills | ✅ PASS | 0 |
| Prompt Quality | ⚠️  WARN | 3 prompts grade B |
| Settings | ✅ PASS | 0 |
| Hooks | ✅ PASS | 0 |
| Pre-commit | ❌ FAIL | 2 files |

---

## Details

### Agent Skills Compliance
✅ All 30 skills installed
✅ skills-ref validate passed
✅ No deprecated frontmatter fields

### Prompt Quality
⚠️  3 prompts rated B (minor issues):
- wfc-build/SKILL.md: B (missing verification step)
- wfc-review/SKILL.md: B (vague output spec)
- wfc-security/SKILL.md: B (missing XML tags)

### Settings.json
✅ Valid JSON
✅ Hook matchers correct
✅ Permission modes valid

### Hook Installation
✅ All hook scripts present
✅ All scripts executable

### Pre-commit
❌ 2 files failed checks:
- wfc/skills/wfc-build/cli.py: ruff (F401 unused import)
- tests/test_build.py: trailing-whitespace

---

## Auto-Fixes Applied

{If --fix was used:}
1. Removed `user-invocable` from wfc-ba/SKILL.md
2. Fixed settings.json context_monitor matcher (removed Task)
3. Set executable permission on pretooluse_hook.py
4. Ran black on 5 files

{If --check-only:}
No auto-fixes applied (use --fix to apply safe fixes)

---

## Recommendations

1. Fix pre-commit failures: `uv run pre-commit run --all-files`
2. Improve prompt grades: `/wfc-prompt-fixer --batch wfc/skills/{build,review,security}/SKILL.md`
3. Review settings.json for custom configurations

---

## Next Steps

{If STATUS is PASS:}
✅ WFC installation is healthy. No action needed.

{If STATUS is WARN:}
⚠️  Minor issues detected. Recommended actions listed above.

{If STATUS is FAIL:}
❌ Critical issues detected. Fix failures before proceeding.
```

## Integration

**Session start checklist:**

```bash
/wfc-doctor --fix  # Auto-fix safe issues
```

**CI integration:**

```yaml
# .github/workflows/health-check.yml
- name: WFC Health Check
  run: uv run python -m wfc.skills.wfc_doctor.cli --check-only
```

**Pre-commit hook:**

```bash
# Run doctor before commit (optional)
wfc-doctor --check-only || echo "⚠️  WFC health issues detected"
```

## Examples

**Quick health check:**

```bash
/wfc-doctor
```

**Fix everything automatically:**

```bash
/wfc-doctor --fix
```

**Check-only (CI mode):**

```bash
/wfc-doctor --check-only
```

## Exit Codes

- `0`: All checks passed
- `1`: Warnings (non-critical issues)
- `2`: Failures (critical issues)
