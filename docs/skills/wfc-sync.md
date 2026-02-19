# wfc-sync

## What It Does

`wfc-sync` keeps your project's rules and skill documentation aligned with how the codebase actually works. It reads all existing `.claude/rules/*.md` files and custom skills, explores the live codebase to discover current patterns and conventions, compares the two, and produces updated or new rule files that reflect reality. The result is a `project.md` context file, updated skills, and newly documented tribal knowledge that would otherwise exist only in developers' heads.

## When to Use It

- After a major refactor or architecture change that may have made existing rules stale
- When onboarding a new project to WFC for the first time
- After adding new languages, frameworks, or build tools to the project
- Periodically (e.g., monthly) to capture conventions that have emerged organically
- When rules feel out of date and you're not sure what's drifted

## Usage

```bash
/wfc-sync
```

## Example

Running `/wfc-sync` on a project that has grown beyond its documented rules:

```
## Phase 1: Reading existing rules...
  Found: .claude/rules/project.md, .claude/rules/api-responses.md
  Found skills: my-deploy-workflow

## Phase 2: Exploring codebase...
  Detected: Python (34 files), TypeScript (21 files)
  Found: FastAPI response envelope pattern (used in 12 endpoints)
  Found: New /services/ directory not in project.md
  Found: Zod validation pattern emerging in frontend (8 files)

## Phase 3: Comparing...
  project.md: tech stack outdated (missing TypeScript), commands stale
  api-responses.md: still accurate
  New pattern: Zod schema validation not yet documented

I found 3 gaps. How do you want to proceed?
  [A] Update all   [R] Review each   [S] Skip updates
> A

## Phase 4: Updating project.md...
  ✅ Updated tech stack (added TypeScript, updated commands)
  ✅ Added /services/ to directory structure

## Phase 5: Updating skills...
  ✅ my-deploy-workflow: Updated deploy path for new monorepo layout

## Phase 6: New rules...
  Creating: .claude/rules/zod-validation.md (Zod schema pattern)

## Sync Complete
  Rules updated: project.md
  New rules: zod-validation.md
  Skills updated: my-deploy-workflow
```

## Options

No flags required — `wfc-sync` runs interactively with guided prompts at each phase. It uses `AskUserQuestion` to confirm before applying changes, so nothing is modified without your approval.

The sync is idempotent: running it multiple times on the same codebase produces the same result.

## Integration

**Produces:**

- Updated `.claude/rules/project.md` with current tech stack, directory structure, and dev commands
- Updated `.claude/rules/*.md` files reflecting current conventions
- New rule files for undocumented patterns discovered in the codebase
- Updated custom skill files where referenced scripts or workflows have changed

**Consumes:**

- Existing `.claude/rules/*.md` and `.claude/skills/*/SKILL.md` files
- Live codebase (scanned via Grep, Glob, and file reads)
- Config files: `package.json`, `pyproject.toml`, `tsconfig.json`, `go.mod`, `Cargo.toml`

**Next step:** After syncing, use `/wfc-rules` to verify newly created rule files are enforcing the right patterns, or `/wfc-housekeeping` to remove artifacts that the sync identified as stale.
