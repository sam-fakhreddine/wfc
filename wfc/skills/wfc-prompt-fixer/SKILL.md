---
name: wfc-prompt-fixer
description: >-
  Analyzes and rewrites existing Claude-specific prompts (system prompts,
  user-turn templates, or WFC Agent Skills) to fix structural issues and
  antipatterns. Pipeline: Analyzer grades A-F against 14 dimensions and
  17 antipatterns → Fixer rewrites C-F prompts (preserving intent, output
  format, and constraints) → Reporter validates and summarizes. A/B prompts
  skip Fixer and receive diagnostic report only.

  Modes: Single file, --batch (up to 4 parallel, auto-scales for token budget),
  --auto-pr (requires gh CLI + write access), --wfc (explicit WFC mode).

  Trigger: /wfc-prompt-fixer, "fix this prompt", "rewrite this prompt",
  "debug prompt errors", "grade this prompt", "analyze prompt quality",
  "optimize for Claude 4" (applies only to Claude prompts).
license: MIT
---

# wfc-prompt-fixer

Analyzes and rewrites Claude prompts using evidence-based diagnostics and structured rewrites.

## What It Does

Analyzes Claude prompts against a rubric of known failure modes and produces:

- **Grade A-F** with dimension scores (0-3 scale)
- **Fixed version** (for C-F prompts) that preserves original intent
- **Changelog** of specific changes made
- **Unresolved items** requiring human input

## When to Use

Use `/wfc-prompt-fixer` when:

- You have an existing Claude prompt producing errors or inconsistent results
- You want a quality grade and diagnostic report for a prompt
- You need to optimize prompt structure for Claude 4.x
- You want to batch-fix multiple WFC skill prompts

**Do not use for:** New prompts from scratch, cross-model conversion, general text editing, or prompt theory explanations without any diagnostic/fix request.

## Workflow

**Single prompt:**

```bash
/wfc-prompt-fixer path/to/prompt.md
```

**Batch mode (auto-scales for token budget):**

```bash
/wfc-prompt-fixer --batch wfc/skills/*/SKILL.md
```

**WFC mode (explicit):**

```bash
/wfc-prompt-fixer --wfc wfc/skills/wfc-build/SKILL.md
```

**Fix and create PR:**

```bash
/wfc-prompt-fixer --auto-pr wfc/skills/wfc-security/SKILL.md
```

## Architecture

**3-Agent Pipeline:**

### 1. Analyzer

Reads prompt from `workspace/input/prompt.md`. Performs:

- File type detection (WFC vs generic prompt)
- Husk check: if semantic content < 10% of file, exit with code `E001: SCAFFOLD_DETECTED`
- Scores against rubric (14 dimensions, 17 antipatterns)
- Assigns grade A-F

**Grading (thresholds are floors, 1.99 = C):**

- **A**: avg ≥ 2.5, zero Critical/Major issues → skip Fixer
- **B**: avg ≥ 2.0, zero Critical issues → skip Fixer
- **C**: avg ≥ 1.5, 1-2 Major issues → route to Fixer
- **D**: avg < 1.5 OR any Critical issue → route to Fixer
- **F**: Unparseable or fundamentally broken → route to Fixer

Writes: `workspace/01-analyzer/analysis.json`

### 2. Fixer

Reads `analysis.json`. Performs:

- Rewrites prompt to fix diagnosed issues
- **Constraint:** Preserve task statement intent (semantic, not literal), output format, and explicit constraints
- Self-validates: confirms grade improved to B+ and no intent regression
- Max 2 retry attempts on validation failure

Writes: `workspace/02-fixer/fixed_prompt.md`, `changelog.md`, `unresolved.md`

### 3. Reporter

Reads all workspace outputs. Generates:

- Before/after grade comparison
- Critical changes summary
- Unresolved items list
- Fixed prompt content

If `--auto-pr`: Attempts branch creation via `gh` CLI. Captures exit code. Reports success OR specific failure with error log.

Writes: `workspace/03-reporter/report.md`

**Batch Mode:** Orchestrator performs pre-flight check: `if sum(prompt_sizes) > 120k`, reduce batch size from 4→2→1. Fails with `E002: BATCH_TOKEN_OVERFLOW` if single prompt > 50k.

### Agent Spawning

Orchestrator constructs sub-agent prompts using the specifications in this document. No external template files required.

```python
# Orchestrator spawns agents via Task tool
Task(
    subagent_type="general-purpose",
    prompt=<constructed_from_this_skill_definition>,
    description="Spawn <analyzer|fixer|reporter> agent"
)
```

## Diagnostic Rubric

**4 Categories, 14 Dimensions** (scored 0-3 each):

### 1. STRUCTURE (weight: 2.0x)

- XML segmentation (0 = prose wall, 3 = clear XML sections)
- Instruction hierarchy (0 = flat, 3 = clear priority ordering)
- Information ordering (0 = random, 3 = logical flow)

### 2. SPECIFICITY (weight: 1.5x)

- Task definition (0 = vague, 3 = explicit actionable statement)
- Output format (0 = unspecified, 3 = precise schema)
- Constraint completeness (0 = missing, 3 = explicit do/don't list)
- Success criteria (0 = undefined, 3 = measurable conditions)

### 3. BEHAVIORAL CONTROL (weight: 1.0x)

- Role utility (0 = decorative, 3 = functional role with context)
- Tone calibration (0 = undefined, 3 = explicit tone guide)
- Guardrails (0 = none, 3 = explicit boundaries)
- Verification loops (0 = none, 3 = self-check required)

### 4. CLAUDE 4.X OPTIMIZATION (weight: 1.5x)

- Thinking guidance (0 = none, 3 = explicit thinking instructions)
- Tool integration (0 = confused, 3 = clear tool usage patterns)
- Literal compliance (0 = ambiguous, 3 = explicit literal interpretation)
- Anti-sycophancy (0 = invites flattery, 3 = explicit neutrality)

**Weighted average:** `sum(score × weight) / sum(weights)`

## 17 Antipatterns

### Critical (blocks deployment, auto-fails grade)

- **AP-03**: Contradictory instructions ("be concise" + "be thorough")
- **AP-04**: Missing uncertainty handling (no "if unsure, say so")
- **AP-17**: Invalid Agent Skills frontmatter (missing required fields)

### Major (degrades quality, routes to Fixer)

- **AP-01**: Decorative role ("helpful assistant" without functional context)
- **AP-02**: Vague output spec ("give me a good summary")
- **AP-05**: Prose wall (instructions buried in paragraphs, no structure)
- **AP-06**: Hallucination prayer ("do not hallucinate" without specific constraints)
- **AP-07**: Stateful assumption ("remember what I said" without explicit context passing)
- **AP-08**: Implicit inference reliance (underspecified, expects model to guess)
- **AP-09**: Example pollution (examples demonstrate bad patterns)
- **AP-10**: Sycophancy invitation (no anti-flattery/neutral tone constraint)
- **AP-11**: Missing negative constraints (only positive instructions)
- **AP-12**: Unreferenced context (provided but never used in instructions)
- **AP-13**: Token bloat (redundant instructions, could be compressed)
- **AP-14**: Missing verification step (no self-check before output)

### WFC-Specific (only checked in WFC mode)

- **AP-15**: Full file content sent (violates token management, should reference files)
- **AP-16**: Schema misalignment (output format doesn't match WFC conventions)

## WFC Detection

Auto-enabled when ALL conditions met:

1. Filename matches `SKILL.md` or `PROMPT.md`
2. Path matches `wfc/skills/*/` or `wfc/references/reviewers/*/`
3. YAML frontmatter present with BOTH `name:` AND `license:` fields

If frontmatter exists but lacks required fields, falls back to standard mode with warning: `WFC_MODE_INCONCLUSIVE: Missing required frontmatter fields.`

Disable with `--no-wfc` flag.

## Outputs

**Workspace:** `.development/prompt-fixer/<run-id>/`

```
<run-id>/
├── input/
│   └── prompt.md
├── 01-analyzer/
│   └── analysis.json          # {grade, scores, issues, wfc_mode, husk_detected}
├── 02-fixer/
│   ├── fixed_prompt.md        # Rewritten prompt
│   ├── changelog.md           # Numbered list of changes
│   └── unresolved.md          # Items needing human input
├── 03-reporter/
│   └── report.md              # Final deliverable
└── metadata.json              # {timestamp, mode, retries, token_usage}
```

**Run ID format:** `{input_filename}-{YYMMDDHHMM}` (e.g., `wfc-build-2410271430`)

**Branch format (if --auto-pr succeeds):**

```
Single: claude/fix-prompt-{skill-name}
Batch:  claude/fix-prompts-batch-{YYMMDDHHMM}
```

## Token Budget

**Per-prompt limits:**

- Analyzer: ~5k overhead + prompt size
- Fixer: ~3k overhead + prompt size
- Reporter: ~2.5k overhead

**Batch limits:**

- Pre-flight check: rejects if `sum(prompt_sizes) > 120k`
- Auto-scales: 4 → 2 → 1 parallel based on total size
- Single prompt limit: 50k tokens (hard reject)

## Error Codes

- `E001: SCAFFOLD_DETECTED` — Input contains < 10% actionable content
- `E002: BATCH_TOKEN_OVERFLOW` — Batch exceeds 120k combined or single prompt > 50k
- `E003: CIRCULAR_DEPENDENCY` — Input path resolves to wfc-prompt-fixer's own SKILL.md
- `E004: GIT_PUSH_FAILED` — `--auto-pr` failed (includes gh error message in report)
- `E005: VALIDATION_EXHAUSTED` — Fixer failed 2 retry attempts without passing validation

## Examples

**Fix a broken skill prompt:**

```bash
/wfc-prompt-fixer wfc/skills/wfc-build/SKILL.md
```

**Batch-fix all reviewers:**

```bash
/wfc-prompt-fixer --batch wfc/references/reviewers/*/PROMPT.md
```

**Fix and auto-PR:**

```bash
/wfc-prompt-fixer --auto-pr wfc/skills/wfc-security/SKILL.md
```

**Fix external prompt (non-WFC):**

```bash
/wfc-prompt-fixer --no-wfc ~/Downloads/customer-support-prompt.md
```

**Grade only (no rewrite):**

```bash
/wfc-prompt-fixer --grade-only path/to/prompt.md
```
