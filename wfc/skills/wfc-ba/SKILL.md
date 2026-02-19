---
name: wfc-ba
description: Business analysis and requirements gathering skill. Conducts structured stakeholder interviews, competitive analysis, gap analysis, and generates planner-ready BA documents with MoSCoW requirements, integration seams, acceptance criteria, and risk assessment. Use when starting new features that need requirements clarity before planning. Triggers on "analyze requirements", "gather requirements", "business analysis", or explicit /wfc-ba.
license: MIT
---

# WFC:BA - Business Analysis & Requirements Gathering

**"Measure twice, plan once"** - Structured requirements before structured plans.

## What It Does

1. **Domain Discovery** - Understands the system, stakeholders, and current state
2. **Requirements Elicitation** - Structured interview with adaptive depth
3. **Gap Analysis** - Compares current state vs desired state
4. **Competitive/Prior Art Research** - Analyzes existing solutions (repos, docs, APIs)
5. **BA Document Generation** - Produces planner-ready output for `/wfc-plan`

## Why This Exists

Without BA, the planning workflow receives vague requirements and makes assumptions. Those assumptions compound through implementation. A 10-minute BA interview saves hours of rework.

```
WITHOUT BA:
  Vague idea → /wfc-plan (guesses) → /wfc-implement (wrong thing) → Rework

WITH BA:
  Vague idea → /wfc-ba (clarifies) → /wfc-validate (validates) → /wfc-plan (precise) → /wfc-implement (right thing)
```

## Usage

```bash
# Default: full interactive BA session
/wfc-ba

# With topic
/wfc-ba "rate limiting for API endpoints"

# With reference material (repo URL, doc, or file)
/wfc-ba "improve review system" --ref https://github.com/competitor/repo

# Quick mode (fewer questions, smaller output)
/wfc-ba "add dark mode" --quick

# From existing notes/requirements
/wfc-ba --from-file requirements-draft.md
```

## The BA Interview

The interview has 4 phases. Each phase adapts based on previous answers.

### Phase 1: Context & Stakeholders

Establishes the WHO, WHAT, and WHY before diving into details.

```
Q: What system or module does this affect?
Q: Who are the primary users/stakeholders?
Q: What triggered this work? (pain point, opportunity, tech debt)
Q: What's the current state? (what exists today)
Q: What's the desired outcome? (what "done" looks like)
```

**Adaptive behavior**: If the user describes a greenfield project, skip current-state questions. If they reference an existing module, read that module's code before continuing.

### Phase 2: Requirements Elicitation

Gathers concrete requirements using MoSCoW prioritization in real-time.

```
Q: What MUST this do? (non-negotiable behaviors)
Q: What SHOULD this do? (valuable but deferrable)
Q: What COULD this do? (nice-to-have, future iteration)
Q: What WON'T this do? (explicit scope exclusion)
```

For each MUST requirement:

```
Q: How would you verify this works? (acceptance criterion)
Q: What's the performance expectation? (bounds)
Q: Are there security implications? (threat surface)
```

**Adaptive behavior**: For security-sensitive features, automatically deepen security questions. For performance-sensitive features, probe for latency/throughput bounds. For UI features, ask about accessibility and responsiveness.

### Phase 3: Technical Constraints & Integration

Maps where the feature connects to existing systems.

```
Q: What existing code does this touch? (files, modules, APIs)
Q: What does this consume as input? (data sources, events, user actions)
Q: What does this produce as output? (data, side effects, UI changes)
Q: Are there hard technical constraints? (language, framework, dependencies)
Q: What must NOT break? (regression boundaries)
```

**Adaptive behavior**: If the user names specific files, read them to understand interfaces. If they mention APIs, check for existing schemas or contracts.

### Phase 4: Risk & Prior Art

Identifies what could go wrong and what already exists.

```
Q: What's the biggest risk to this feature? (technical, business, timeline)
Q: Has anything similar been attempted before? (in this codebase or elsewhere)
Q: Are there open-source solutions we should study? (prior art)
Q: What dependencies does this introduce? (new libraries, services, APIs)
```

**Adaptive behavior**: If the user references a competitor or open-source project, use web search and code exploration to analyze it. Feed findings back into requirements.

## Outputs

### 1. BA Document (BA-{feature-slug}.md)

The primary output. Structured for direct consumption by `/wfc-plan`.

```markdown
# Business Analysis: {Feature Name}

## 1. Executive Summary
[2-3 sentences: what, why, expected impact]

## 2. Current State
[What exists today, with file/module references]

## 3. Requirements

### MUST (Non-Negotiable)
- [Requirement] → Acceptance: [measurable criterion]
- [Requirement] → Acceptance: [measurable criterion]

### SHOULD (Valuable, Deferrable)
- [Requirement]

### COULD (Future Iteration)
- [Requirement]

### WON'T (Explicit Exclusion)
- [Exclusion] — Reason: [why excluded]

## 4. Integration Seams
- **Input from**: [source] → this feature
- **Output to**: this feature → [consumer]
- **Files touched**: [existing files that change]
- **New files**: [files to create]

## 5. Non-Functional Requirements
| Requirement | Target | Measurement |
|---|---|---|
| Performance | [bound] | [how to measure] |
| Compatibility | [constraint] | [what must not break] |
| Dependencies | [new deps] | [optional vs required] |

## 6. Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| [risk] | H/M/L | H/M/L | [mitigation] |

## 7. Prior Art
[Analysis of existing solutions, competitors, or related work]

## 8. Out of Scope
[Explicit list of what this feature does NOT cover]

## 9. Glossary
[Domain terms defined for the planner]
```

### 2. Interview Transcript (interview-transcript.json)

Machine-readable record of all Q&A for traceability.

```json
{
  "feature": "rate-limiting",
  "timestamp": "2026-02-17T10:30:00Z",
  "phases": [
    {
      "phase": "context",
      "questions": [
        {
          "question": "What system does this affect?",
          "answer": "All /api/* endpoints",
          "follow_ups": []
        }
      ]
    }
  ],
  "duration_minutes": 12,
  "requirements_count": {"must": 4, "should": 2, "could": 1, "wont": 2}
}
```

### 3. Competitive Analysis (optional, when --ref used)

If the user provides a reference repo/URL, produce a structured comparison:

```markdown
## Competitive Analysis: {Reference Name}

### Strengths (adopt)
- [Feature/pattern worth adopting]

### Weaknesses (avoid)
- [Anti-pattern or limitation to avoid]

### Gaps (WFC advantage)
- [What WFC already does better]

### Inspiration (adapt)
- [Ideas to adapt, not copy directly]
```

## Architecture

```
User: /wfc-ba "add rate limiting"
    ↓
┌──────────────────────────────────────┐
│  INTERVIEWER                         │
│  Phase 1: Context & Stakeholders     │
│  Phase 2: Requirements (MoSCoW)     │
│  Phase 3: Technical Constraints      │
│  Phase 4: Risk & Prior Art           │
│                                      │
│  Adaptive: reads code, searches web  │
│  as needed between questions         │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│  ANALYZER                            │
│  - Gap analysis (current vs desired) │
│  - Integration seam mapping          │
│  - Risk assessment                   │
│  - Prior art research (if --ref)     │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│  GENERATOR                           │
│  - BA document (markdown)            │
│  - Interview transcript (JSON)       │
│  - Competitive analysis (if --ref)   │
└──────────────────────────────────────┘
```

### Multi-Tier Design

```
┌─────────────────────────────┐
│  PRESENTATION               │  User interaction, question display
│  (interview UX)             │  Output formatting, progress indicators
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│  LOGIC                      │  Interview orchestration, adaptive depth
│  - Interviewer              │  Gap analysis, requirement structuring
│  - Analyzer                 │  Risk assessment, seam mapping
│  - Generator                │  Document generation, JSON serialization
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│  DATA                       │  BA documents (markdown)
│  (filesystem)               │  Transcripts (JSON), analysis artifacts
└─────────────────────────────┘
```

## Integration with WFC

### Upstream (feeds into)

- **wfc-validate** — BA document is validated for quality (next step in pipeline)
- **wfc-plan** — After validation, BA feeds into structured planning
- **wfc-build** — Quick mode BA can feed directly into build for small features

### Downstream (consumes from)

- **Codebase** — Reads existing code to understand current state
- **Web** — Searches for prior art and competitive analysis
- **User** — Interactive interview

### Workflow Position

```
/wfc-ba (requirements) → /wfc-validate (validate) → /wfc-plan (planning) → /wfc-implement (building)
    ↑                                                                                ↓
    └──────────────────── feedback loop (requirements change) ←──────────────────────┘
```

## What to Do

1. **If `$ARGUMENTS` contains `--quick`**, use abbreviated interview (Phase 1 + Phase 2 only, 3-5 questions total)
2. **If `$ARGUMENTS` contains `--ref <url>`**, perform competitive analysis on the referenced resource
3. **If `$ARGUMENTS` contains `--from-file <path>`**, read the file and use it as initial requirements (skip Phase 1-2, go to Phase 3-4)
4. **If `$ARGUMENTS` contains a description**, use it as the feature topic and adapt interview accordingly
5. **If no arguments**, start with open-ended Phase 1 questions

### Interview Execution

- Ask questions ONE AT A TIME (not batched)
- Wait for user response before asking the next question
- Adapt follow-up questions based on answers
- Read referenced code files between questions when the user mentions specific files
- Use web search when the user references external tools, libraries, or competitors
- Keep track of all Q&A for the transcript

### Document Generation

After the interview is complete:

1. Synthesize all answers into the BA document structure
2. Map requirements to MoSCoW categories
3. Identify integration seams from technical constraint answers
4. Assess risks from Phase 4 answers
5. Generate acceptance criteria for every MUST requirement
6. Write BA document to `ba/BA-{feature-slug}.md`
7. Write interview transcript to `ba/interview-transcript.json`
8. If `--ref` was used, write competitive analysis to `ba/competitive-analysis.md`
9. **Run `/wfc-validate`** on the generated BA document to validate quality before handing off to planning
10. Apply any Must-Do revisions from validate feedback to the BA document

### Output Location

```
ba/
├── BA-{feature-slug}.md           # Primary BA document
├── interview-transcript.json       # Machine-readable Q&A record
└── competitive-analysis.md         # Optional (when --ref used)
```

## BA Document Quality Checklist

A good BA document passes these checks:

- [ ] Every MUST requirement has a measurable acceptance criterion
- [ ] Integration seams list specific files (not vague module names)
- [ ] Non-functional requirements have numeric targets
- [ ] Risks have mitigations (not just identification)
- [ ] Out of Scope section exists (prevents scope creep)
- [ ] Glossary defines domain-specific terms
- [ ] Executive summary is 2-3 sentences (not a paragraph)
- [ ] WON'T section has reasons (not just a list)

## The Planner Litmus Test

The BA document is ready when a planner can answer: **"Can I generate TASKS.md with TDD test plans without asking a single clarifying question?"**

If the planner would ask "but what about X?" — X is missing from the BA.

## When to Use

### Use /wfc-ba when

- Starting a new feature and requirements are unclear
- Multiple stakeholders have different expectations
- The feature touches multiple systems or modules
- There's a competitor or reference implementation to analyze
- Previous implementation attempts failed (need to understand why)
- The feature has security, performance, or compliance implications

### Skip BA when

- Bug fix with clear reproduction steps
- Single-file change with obvious scope
- Refactoring with no behavior change
- Documentation updates

### Quick Mode vs Full Mode

| Aspect | Quick (--quick) | Full (default) |
|---|---|---|
| Questions | 3-5 | 10-20 |
| Phases | 1-2 only | All 4 |
| Output | Minimal BA doc | Complete BA doc |
| Competitive analysis | No | Yes (if --ref) |
| Best for | Small features | Medium-large features |
| Time | 5 minutes | 15-30 minutes |

## Configuration

```json
{
  "ba": {
    "output_dir": "./ba",
    "interview_mode": "adaptive",
    "default_mode": "full",
    "auto_read_code": true,
    "auto_web_search": true,
    "generate_transcript": true
  }
}
```

## Example Session

```
User: /wfc-ba "add finding validation to review pipeline"

[PHASE 1: CONTEXT]
Q: What system does this affect?
A: The review pipeline in wfc/scripts/skills/review/

Q: What's the current state?
A: Reviews produce findings but some are false positives

Q: What triggered this?
A: Analyzed Kodus AI - they have a 4-layer validation pipeline

[PHASE 2: REQUIREMENTS]
Q: What MUST the validation do?
A: Verify findings reference real code, cross-check with different model

Q: How would you verify structural checks work?
A: Finding that references line 50 but file only has 30 lines → caught

Q: Performance bound?
A: < 5 seconds per review for files under 500 lines

Q: What WON'T this include?
A: No ML-based filtering, no external API calls beyond Anthropic

[PHASE 3: TECHNICAL]
Q: What existing files does this touch?
A: orchestrator.py (add step), consensus_score.py (weight by validation)
   → [reads orchestrator.py to understand current pipeline]

Q: What's the input/output contract?
A: Input: DeduplicatedFinding list. Output: ValidatedFinding list.

[PHASE 4: RISK]
Q: Biggest risk?
A: Validation itself could be wrong (meta-false-positives)

Q: Prior art?
A: Kodus AI's validation pipeline (already analyzed)

[GENERATION]
✅ BA document: ba/BA-finding-validation.md
✅ Transcript: ba/interview-transcript.json

Next: Run `/wfc-validate` to validate, then `/wfc-plan` to generate tasks
```

## Philosophy

**ELEGANT**: Simple questions, structured output, no ceremony
**ADAPTIVE**: Questions change based on answers (not a fixed script)
**PLANNER-READY**: Output format designed for `/wfc-plan` consumption
**EVIDENCE-BASED**: Reads code and searches web during interview, not after
