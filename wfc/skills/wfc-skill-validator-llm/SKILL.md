---
name: wfc-skill-validator-llm
description: >-
  LLM-based discovery validator for WFC Agent Skills. Uses adversarial prompting to find routing
  gaps and ambiguity in skill descriptions. Triggers on "validate skill routing",
  "check skill descriptions", "test if my skill triggers correctly", "find routing gaps in my
  skill", "does my skill description work", or explicit /wfc-skill-validator-llm. Validates that
  agents will load the right skill for a given user message by simulating the agent decision.
  Not for: structural checks (use make validate), fixing skill formatting, logic validation (Phase 2).
license: MIT
---

# wfc-skill-validator-llm

LLM-based discovery validator that stress-tests skill descriptions using adversarial prompting.

## What It Does

Sends each skill's name and description to an LLM with an adversarial prompt that instructs it to
find routing gaps, generate confusing near-miss prompts, and suggest rewrites. Results are written
to a timestamped report and appended to a persistent corpus for trend tracking.

This is **Phase 1 (Discovery)** validation only. It answers: "Will agents load this skill when they
should, and avoid it when they shouldn't?"

## Usage

```bash
# Validate a single skill by name
/wfc-skill-validator-llm wfc-review

# Validate all installed skills
/wfc-skill-validator-llm --all

# Run only the discovery stage
/wfc-skill-validator-llm wfc-build --stage discovery

# Dry run — print what would be sent, do not call LLM
/wfc-skill-validator-llm wfc-review --dry-run

# Skip confirmation prompts (non-interactive / CI use)
/wfc-skill-validator-llm --all --yes
```

## Workflow

1. **Argument parsing** — `cli.py` parses skill name or `--all`, plus stage/dry-run/yes flags.
2. **Skill reading** — Read `SKILL.md` from the skill directory; extract `name` and `description`
   fields from the YAML frontmatter via file I/O (no imports).
3. **Corpus load** — Load `skill-validation-corpus.json` from the corpus path if it exists.
4. **Discovery prompt construction** — Load `assets/templates/discovery-prompt.txt` at runtime
   (JiT), substitute `{skill_name}` and `{description}`, send to LLM.
5. **LLM call** — Call LLM with the adversarial prompt. Capture the full response.
6. **Report writing** — Write a Markdown report using the format from
   `assets/templates/validation-report.md` (JiT loading) to the output path.
7. **Corpus append** — Append a structured entry (skill name, timestamp, routing gaps found,
   summary) to `skill-validation-corpus.json`.
8. **Summary** — Print a one-line result per skill: PASS / GAPS FOUND / ERROR.

## Corpus Repo Identification

The corpus is stored per-repo. The repo name is resolved in this order:

1. **`WFC_CORPUS_REPO` env var** — if set, use its value as the repo name.
2. **`git rev-parse --show-toplevel`** — take `basename` of the result.
3. **Fallback `"wfc"`** — if git command fails, use the string `"wfc"` and log a WARNING.

```
WARNING: could not determine repo name via git; defaulting to "wfc".
         Set WFC_CORPUS_REPO env var to override.
```

This logic is implemented in `cli.py`.

## Discovery Prompt (Adversarial Framing)

The prompt below is loaded from `assets/templates/discovery-prompt.txt` at runtime.
`{skill_name}` and `{description}` are substituted before the LLM call.

```
I am building an Agent Skill based on the agentskills.io spec.
Agents will decide whether to load this skill based entirely on the YAML metadata below.

name: {skill_name}
description: {description}

Your job is to find faults, routing gaps, and ambiguity. Based strictly on this description:
1. Generate 3 realistic user prompts you are 100% confident SHOULD trigger this skill.
2. Generate 3 user prompts that sound similar but SHOULD NOT trigger this skill.
3. Critique the description: Is it too broad? Too narrow? Ambiguous? Does it overlap with similar skills?
   Suggest an optimized rewrite that eliminates routing gaps.
```

## Output

### Report path

```
~/.wfc/projects/{repo}/branches/{branch}/docs/skill-validation/{timestamp}/
```

One Markdown file per skill: `{skill_name}-discovery.md`.
Report format is defined in `assets/templates/validation-report.md` (loaded JiT).

### Corpus path

```
~/.wfc/projects/{repo}/skill-validation-corpus.json
```

The corpus is **branch-independent** — it accumulates results across all branches for the repo.
Each entry contains: `skill`, `timestamp`, `branch`, `routing_gaps_found` (bool), `summary`.

## Flags Reference

| Flag | Description |
|------|-------------|
| `--all` | Validate every skill found in `~/.claude/skills/wfc-*/SKILL.md` |
| `--stage discovery` | Run only the discovery stage (default; future stages: logic, edge-case) |
| `--dry-run` | Print the constructed prompt without calling the LLM or writing files |
| `--yes` | Skip confirmation prompts; suitable for CI or scripted use |

## Not For

- **Structural / formatting checks** — use `make validate` instead.
- **Fixing skill formatting or frontmatter** — use `make format` or edit manually.
- **Logic / hallucination validation (Phase 2)** — planned as a separate stage; not implemented here.
- **Code review or plan validation** — use `wfc-review` or `wfc-validate`.
