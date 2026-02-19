# Documentation Maintenance

How to keep WFC docs current as the system evolves.

---

## 1. Updating a Skill Doc

When `~/.claude/skills/wfc-{name}/SKILL.md` changes, update `docs/skills/wfc-{name}.md` in the same PR.

**Steps:**

1. Read the changed `SKILL.md`
2. Update `docs/skills/wfc-{name}.md` — focus on "What It Does", "Usage", and "Integration" sections
3. Verify word count stays ≤750 words: `wc -w docs/skills/wfc-{name}.md`
4. Update `docs/skills/README.md` selection matrix if the skill's purpose changed

---

## 2. Detecting Drift

Run this to see which skill docs may be stale (doc older than its source SKILL.md):

```bash
for skill in ~/.claude/skills/wfc-*/; do
  name=$(basename "$skill")
  skill_md="$skill/SKILL.md"
  doc="docs/skills/${name}.md"
  if [ -f "$skill_md" ] && [ -f "$doc" ]; then
    if [ "$skill_md" -nt "$doc" ]; then
      echo "STALE: $doc (SKILL.md is newer)"
    fi
  elif [ -f "$skill_md" ] && [ ! -f "$doc" ]; then
    echo "MISSING: $doc"
  fi
done
```

This runs as a CI warning (not block) via `.github/workflows/docs-drift.yml` (when implemented).

---

## 3. Adding a New Skill Doc

When a new skill is installed to `~/.claude/skills/wfc-{name}/`:

1. Read `~/.claude/skills/wfc-{name}/SKILL.md`
2. Create `docs/skills/wfc-{name}.md` using the template:

   ```markdown
   # wfc-{name}

   ## What It Does
   ## When to Use It
   ## Usage
   ## Example
   ## Options
   ## Integration
   ```

3. Add to `docs/skills/README.md` selection matrix
4. Add to `docs/README.md` skills table
5. Update PROP-002 count in any relevant plan docs

---

## 4. Archive Policy

When a doc becomes stale:

1. `git mv docs/{section}/{FILE}.md docs/archive/{FILE}_V{N}.md`
2. Add redirect entry in `docs/archive/README.md`
3. Create replacement doc at original or new path
4. Update any links in `docs/README.md`, `CLAUDE.md`, `QUICKSTART.md`, `CONTRIBUTING.md`

**Rule:** Never delete from `docs/archive/`. Increment version suffix if a second archive is needed (`_V2`, `_V3`).

---

## 5. Registry Sync

After any docs change, regenerate the registry:

```bash
# Manual: update docs/reference/REGISTRY.md
# List all docs with section, filename, description, status

# Validate no dead links in docs/
find docs/ -name "*.md" | xargs grep -l "\[.*\](\..*)" | \
  xargs -I{} sh -c 'echo "Checking {}..." && grep -oP "\(\..*?\)" {} | sed "s/(\|)//g"'

# Verify skill count matches installed
installed=$(ls ~/.claude/skills/ | grep ^wfc- | wc -l | tr -d ' ')
documented=$(ls docs/skills/wfc-*.md 2>/dev/null | wc -l | tr -d ' ')
echo "Installed: $installed | Documented: $documented"
[ "$installed" = "$documented" ] && echo "OK" || echo "MISMATCH — update docs/skills/"
```

---

## Path Portability Note

The skill drift detection script uses `~/.claude/skills/`. On different machines, devcontainers, or CI, this path may differ. Always verify the path before running automated checks:

```bash
ls ~/.claude/skills/wfc-build/ 2>/dev/null || echo "Skills not at expected path — check installation"
```

---

## Current Skill Count

**30 skills installed** (verified 2026-02-18):

wfc-agentic, wfc-architecture, wfc-ba, wfc-build, wfc-code-standards, wfc-compound, wfc-deepen, wfc-export, wfc-gh-debug, wfc-housekeeping, wfc-implement, wfc-init, wfc-isthissmart, wfc-lfg, wfc-newskill, wfc-observe, wfc-plan, wfc-playground, wfc-pr-comments, wfc-python, wfc-retro, wfc-review, wfc-rules, wfc-safeclaude, wfc-safeguard, wfc-security, wfc-sync, wfc-test, wfc-validate, wfc-vibe

If this number changes, update: `docs/reference/AGENT_SKILLS_COMPLIANCE.md`, `docs/reference/COMMANDS.md`, `docs/README.md`, and this file.
