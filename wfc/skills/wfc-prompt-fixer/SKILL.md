---
name: wfc-prompt-fixer
description: Fix Claude prompts using a 3-agent pipeline (Analyzer → Fixer → Reporter). Diagnoses prompt quality against a rubric of 17 antipatterns, assigns grade A-F, rewrites to fix issues while preserving intent, and validates fixes adversarially. Works on any Claude prompt. Auto-detects WFC skill structure and adds WFC-specific checks for Agent Skills compliance, token management patterns, and TEAMCHARTER alignment. Supports batch mode processing up to 4 prompts in parallel. Auto-creates PRs for fixes.
license: MIT
---

# wfc-prompt-fixer

Fix Claude prompts using evidence-based diagnostics and structured rewrites.

## What It Does

Analyzes Claude prompts against a rubric of known failure modes and produces fixed versions that:

- Preserve original intent
- Resolve antipatterns (decorative roles, vague specs, contradictory instructions, etc.)
- Optimize for Claude 4.x literal instruction following
- Maintain token efficiency

## When to Use

Use `/wfc-prompt-fixer` when:

- A prompt produces inconsistent or unexpected results
- You want to optimize prompt structure before production
- Migrating prompts from Claude 3.x to Claude 4.x
- Batch-fixing all WFC skill prompts for consistency
- New prompt needs validation before deployment

## Workflow

**Single prompt:**

```bash
/wfc-prompt-fixer path/to/prompt.md
```

**Batch mode (4 parallel):**

```bash
/wfc-prompt-fixer --batch wfc/skills/*/SKILL.md
```

**WFC mode (explicit):**

```bash
/wfc-prompt-fixer --wfc wfc/skills/wfc-build/SKILL.md
```

## Architecture

**3-Agent Pipeline:**

1. **Analyzer** (Router + Diagnostician combined)
   - Classifies prompt type, complexity, deployment context
   - Scores against rubric (17 antipatterns, 4 categories, 14 dimensions)
   - Assigns grade A-F
   - Auto-detects WFC structure (YAML frontmatter, SKILL.md filename)

2. **Fixer** (Rewriter + Validator combined with retry loop)
   - Rewrites prompt to fix diagnosed issues
   - Self-validates adversarially (intent preservation, regressions, scope creep)
   - Retries on validation failure (max 2 attempts)

3. **Reporter**
   - Generates human-readable summary
   - Includes: grade before/after, critical changes, unresolved items, fixed prompt
   - Writes to `.development/prompt-fixer/<run-id>/report.md`

**Short-circuit:** Grade A prompts skip Fixer, go straight to Reporter with "no changes needed"

**Batch mode:** Processes up to 4 prompts in parallel (each runs full 3-agent pipeline)

## Diagnostic Rubric

**4 Categories, 14 Dimensions** (scored 0-3 each):

1. **STRUCTURE** (high weight)
   - XML segmentation
   - Instruction hierarchy
   - Information ordering

2. **SPECIFICITY** (high weight)
   - Task definition
   - Output format
   - Constraint completeness
   - Success criteria

3. **BEHAVIORAL CONTROL** (medium weight)
   - Role utility
   - Tone calibration
   - Guardrails
   - Verification loops

4. **CLAUDE 4.X OPTIMIZATION** (high weight)
   - Thinking guidance
   - Tool integration
   - Literal compliance
   - Anti-sycophancy

**Grading Thresholds:**

- **A**: No critical/major issues, avg ≥ 2.5 (skip rewrite)
- **B**: No critical, avg ≥ 2.0
- **C**: 1-2 major issues, avg ≥ 1.5
- **D**: Critical issues, avg < 1.5
- **F**: Fundamentally broken

## 17 Antipatterns

**General (14):**

- AP-01: Decorative role ("helpful assistant")
- AP-02: Vague output spec ("give me a good summary")
- AP-03: Contradictory instructions ("be concise" + "be thorough")
- AP-04: Missing uncertainty handling
- AP-05: Prose wall (instructions buried in paragraphs)
- AP-06: Hallucination prayer ("do not hallucinate")
- AP-07: Stateful assumption ("remember what I said")
- AP-08: Implicit inference reliance (underspecified, expects model to guess)
- AP-09: Example pollution (bad patterns in examples)
- AP-10: Sycophancy invitation (no anti-flattery constraint)
- AP-11: Missing negative constraints (no "do NOT" instructions)
- AP-12: Unreferenced context (unused context block)
- AP-13: Token bloat (redundant instructions)
- AP-14: Missing verification step (no self-check before output)

**WFC-Specific (3):**

- AP-15: Full file content sent (violates token management)
- AP-16: Missing TEAMCHARTER values alignment
- AP-17: Invalid Agent Skills frontmatter

## WFC Detection

Auto-enabled when:

- File named `SKILL.md` or `PROMPT.md`
- YAML frontmatter with `name:` field
- Path matches `wfc/skills/*/` or `wfc/references/reviewers/*/`

Adds WFC-specific checks:

- Agent Skills spec compliance (frontmatter format)
- Token management patterns (file reference architecture)
- TEAMCHARTER alignment (values mentioned in prompts)

Disable with `--no-wfc` flag if false positive.

## Outputs

**Workspace:** `.development/prompt-fixer/<run-id>/`

```
<run-id>/
├── input/
│   └── prompt.md
├── 01-analyzer/
│   └── analysis.json          # {grade, scores, issues, wfc_mode}
├── 02-fixer/
│   ├── fixed_prompt.md        # Rewritten prompt
│   ├── changelog.md           # Numbered list of changes
│   └── unresolved.md          # Items needing human input
├── 03-reporter/
│   └── report.md              # Final deliverable
└── metadata.json              # {timestamp, mode, retries}
```

**Branch (if --auto-pr):**

```
Single: claude/fix-prompt-{skill-name}
Batch:  claude/fix-prompts-batch-{timestamp}
```

## Integration

**With wfc-doctor:**

```bash
/wfc-doctor  # Runs wfc-prompt-fixer --batch --wfc on all skills
```

**With wfc-newskill:**

```bash
/wfc-newskill  # Validates generated prompt via wfc-prompt-fixer
```

**With make validate:**

```bash
make validate  # Can include prompt quality checks (future)
```

## Token Budget

Per-prompt:

- Analyzer: ~5k + prompt size
- Fixer: ~3k + prompt size
- Reporter: ~2.5k

Batch (4 parallel): ~40k + 4×prompt_size (well within 200k window)

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
