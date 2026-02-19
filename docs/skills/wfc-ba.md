# wfc-ba

## What It Does

Conducts a structured, adaptive stakeholder interview to turn a vague feature idea into a precise, planner-ready Business Analysis document. It guides you through four phases — context and stakeholders, MoSCoW requirements, technical constraints, and risk and prior art — reading code and searching the web between questions as needed. The output is a `BA-{feature}.md` document that `/wfc-plan` can consume to generate a full `TASKS.md` without asking any clarifying questions.

## When to Use It

- Starting a feature where requirements are unclear or contested
- Multiple stakeholders have different expectations for the same work
- The feature touches several modules or external systems
- There is a competitor or reference implementation worth analyzing
- A previous implementation attempt failed and you need to understand why
- The feature has security, performance, or compliance implications

## Usage

```bash
/wfc-ba [topic] [options]
```

## Example

```bash
/wfc-ba "add finding validation to review pipeline"
```

Interview excerpt:

```
[PHASE 1: CONTEXT]
Q: What system does this affect?
A: The review pipeline in wfc/scripts/orchestrators/review/

Q: What triggered this work?
A: Too many false-positive findings from reviewers

[PHASE 2: REQUIREMENTS]
Q: What MUST this do?
A: Verify findings reference real code; cross-check with a second model pass

Q: How would you verify structural checks work?
A: A finding citing line 50 in a 30-line file must be caught and dropped

Q: What WON'T this include?
A: No ML-based filtering, no external API calls beyond Anthropic

[GENERATION]
✅ BA document: ba/BA-finding-validation.md
✅ Transcript:   ba/interview-transcript.json

Next: /wfc-validate to validate, then /wfc-plan to generate tasks
```

## Options

| Flag / Argument | Description |
|-----------------|-------------|
| `"topic"` | Feature description to seed the interview |
| `--quick` | Abbreviated interview (Phases 1-2 only, 3-5 questions, ~5 min) |
| `--ref <url>` | Include competitive analysis of a reference repo or doc |
| `--from-file <path>` | Start from existing requirements draft (skip Phases 1-2) |

## Integration

**Produces:**

- `ba/BA-{feature-slug}.md` — Structured BA document (MoSCoW requirements, integration seams, acceptance criteria, risk table, glossary)
- `ba/interview-transcript.json` — Machine-readable Q&A record for traceability
- `ba/competitive-analysis.md` — Optional, generated when `--ref` is provided

**Consumes:**

- User answers (interactive interview, one question at a time)
- Codebase files (reads referenced modules between questions)
- Web search (fetches prior art or competitor docs when referenced)

**Next step:** Run `/wfc-validate` to confirm the BA document passes all 7 quality dimensions before handing it to `/wfc-plan`.
