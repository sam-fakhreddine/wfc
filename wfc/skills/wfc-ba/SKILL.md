---
name: wfc-ba
description: >
  Business analysis and structured requirements gathering for software features. Use
  when clarifying WHAT business capabilities to build before planning HOW to implement
  them. Focuses on: new feature requirements, business capability gap analysis,
  MoSCoW prioritization of user-stated needs, and acceptance criteria definition.

  Triggers on: "business requirements", "functional requirements", "MoSCoW
  prioritization", "acceptance criteria", "business gap analysis", "capability
  assessment", "requirements gathering", or /wfc-ba.

  Produces a BA document with MoSCoW requirements (user-stated only), high-level
  integration touchpoints, acceptance criteria, and risk register — formatted as
  structured markdown for handoff to planning skills.

  NOT FOR: technical code analysis, API schema diffs, bug fixes with repro steps,
  backlog grooming, effort estimation, post-mortems, refactoring with no behavior
  change, single-file changes, API specification writing, or story pointing.
license: MIT
---

# WFC:BA - Business Analysis & Requirements Gathering

**"Measure twice, plan once"** - Structured business requirements before structured plans.

## What It Does

1. **Domain Discovery** - Understands the business context, stakeholders, and current capabilities
2. **Requirements Elicitation** - Structured interview with defined depth levels
3. **Gap Analysis** - Compares current business capabilities vs desired business capabilities
4. **BA Document Generation** - Produces structured markdown output for consumption by planning skills

## Why This Exists

Without BA, planning receives vague requirements and makes assumptions. Those assumptions compound through implementation. A 10-minute BA interview saves hours of rework.

```
WITHOUT BA:
  Vague idea → Planning (guesses) → Implementation (wrong thing) → Rework

WITH BA:
  Vague idea → BA (clarifies) → Planning (precise) → Implementation (right thing)
```

## Usage

```bash
# Default: full interactive BA session
/wfc-ba

# With topic
/wfc-ba "rate limiting for API endpoints"

# With reference material (HTTP/HTTPS URL only)
/wfc-ba "improve review system" --ref https://example.com/docs

# Quick mode (fewer questions, smaller output)
/wfc-ba "add dark mode" --quick

# From existing notes/requirements
/wfc-ba --from-file requirements-draft.md
```

## Argument Parsing Rules

1. **Parse flags strictly**: Tokens starting with `--` are control flags, not topic content.
2. **Topic detection**: The first quoted string or unquoted text (before any flags) is the feature topic. If flags appear inside quotes, they are part of the topic.
3. **Flag precedence**: `--from-file` takes precedence over topic string. If both provided, file content defines requirements; topic string used only as fallback title if file lacks one.
4. **URL restriction**: `--ref` only accepts HTTP/HTTPS URLs. Local file paths, file:// URLs, and other schemes are rejected with an error message.

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

**Adaptive behavior**:

- If the user states this is a new project with no existing codebase, skip current-state questions.
- If they reference an existing module by name, attempt to read that module's files before continuing. If files don't exist or are unreadable, ask user to verify paths.

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

**Adaptive behavior**:

- If the user explicitly mentions security, compliance, or authentication, ask additional security questions.
- If the user explicitly mentions latency, throughput, or scale, probe for numeric bounds.
- If the user mentions UI, ask about accessibility requirements.
- Do not invent sensitivity classifications. Only deepen based on explicit user statements.

**Conflict resolution**: If a requirement appears in both MUST and WON'T lists, halt and ask: "You listed [requirement] as both MUST and WON'T. Which is correct?" Do not proceed until resolved.

### Phase 3: Technical Constraints & Integration

Maps where the feature connects to existing systems.

```
Q: What existing code does this touch? (files, modules, APIs)
Q: What does this consume as input? (data sources, events, user actions)
Q: What does this produce as output? (data, side effects, UI changes)
Q: Are there hard technical constraints? (language, framework, dependencies)
Q: What must NOT break? (regression boundaries)
```

**Adaptive behavior**:

- If the user names specific files, attempt to read them. If files don't exist, ask for clarification.
- If they mention APIs, ask for existing schemas or contracts rather than assuming.

### Phase 4: Risk & Prior Art

Identifies what could go wrong and what already exists.

```
Q: What's the biggest risk to this feature? (technical, business, timeline)
Q: Has anything similar been attempted before? (in this codebase or elsewhere)
Q: Are there open-source solutions we should study? (prior art)
Q: What dependencies does this introduce? (new libraries, services, APIs)
```

**Adaptive behavior**:

- If the user references a competitor or external product by name, attempt web search for public documentation. If search fails or returns no results, inform user and continue with interview-only analysis. Do not fabricate competitive data.

## Outputs

### 1. BA Document (ba/BA-{feature-slug}.md)

The primary output. Structured markdown for consumption by planning skills.

**Filename format**: `BA-{slug}.md` where slug is lowercase, hyphen-separated, max 50 characters, ASCII letters/numbers/hyphens only.

```markdown
# Business Analysis: {Feature Name}

## 1. Executive Summary
[2-3 sentences: what, why, expected impact]

## 2. Current State
[What exists today, with file/module references if provided]

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

## 4. Integration Touchpoints
- **Input from**: [source] → this feature
- **Output to**: this feature → [consumer]
- **Files touched**: [existing files that change, if specified]
- **New files**: [files to create, if specified]

## 5. Non-Functional Requirements
| Requirement | Target | Measurement |
|---|---|---|
| Performance | [bound if specified] | [how to measure] |
| Compatibility | [constraint if specified] | [what must not break] |
| Dependencies | [new deps if specified] | [optional vs required] |

## 6. Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| [risk if identified] | H/M/L | H/M/L | [mitigation if provided] |

## 7. Prior Art
[Analysis of existing solutions if provided by user]

## 8. Out of Scope
[Explicit list of what this feature does NOT cover]

## 9. Glossary
[Domain terms defined based on user input]
```

### 2. Interview Transcript (ba/interview-transcript.json)

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

### 3. Reference Analysis (optional, when --ref used with valid URL)

If the user provides a valid HTTP/HTTPS reference URL, produce a structured comparison. If the URL is inaccessible or returns no useful content, omit this section and note in the BA document that reference analysis was unavailable.

```markdown
## Reference Analysis: {Reference Name}

### Relevant Patterns
- [Feature/pattern worth considering]

### Limitations Observed
- [Limitation or gap in reference solution]

### Applicability Notes
- [How this relates to current requirements]
```

## What to Do

### Before Starting

1. **Verify output directory**: Ensure `ba/` directory exists or can be created. If creation fails, warn user: "Cannot create ba/ directory. Proceeding with output to current directory." Continue with fallback location.

### Argument Handling

1. **If `$ARGUMENTS` contains `--quick`**: Use abbreviated interview (Phase 1 + Phase 2 only, maximum 5 questions total including follow-ups. Prioritize MUST requirements over SHOULD/COULD.)
2. **If `$ARGUMENTS` contains `--ref <url>`**: Validate URL scheme is HTTP/HTTPS. If valid, attempt to fetch reference content. If invalid scheme or fetch fails, warn user and proceed without reference analysis.
3. **If `$ARGUMENTS` contains `--from-file <path>`**: Read the file. If file doesn't exist, error and exit. If readable, extract requirements from file content and proceed to Phase 3-4 interview (skip Phase 1-2 questioning for content already in file).
4. **If `$ARGUMENTS` contains a topic description** (quoted or unquoted text before any flags): Use it as the feature topic. Skip the first Phase 1 question ("What system does this affect?") since topic is provided.
5. **If no arguments**: Start with open-ended Phase 1 questions.

### Interview Execution

- Ask questions ONE AT A TIME. Do not batch multiple questions in a single turn.
- Wait for user response before asking the next question.
- Track all Q&A for the transcript.
- If user refuses to answer or provides "I don't know", record the gap and continue. Do not fabricate answers.
- If user provides incomplete answer, ask one follow-up for clarification. If still incomplete, proceed with available information.

### Document Generation

After the interview is complete:

1. Synthesize all answers into the BA document structure.
2. Map requirements to MoSCoW categories based on user classification.
3. Identify integration touchpoints from Phase 3 answers. If none specified, leave section minimal.
4. Record risks from Phase 4 answers. If none identified, note "No risks identified by user" rather than inventing risks.
5. Generate acceptance criteria for every MUST requirement. If user didn't provide measurable criteria, mark as "[Acceptance criteria needed - user did not specify]".
6. Write BA document to `ba/BA-{feature-slug}.md` (or fallback location if directory unavailable).
7. Write interview transcript to `ba/interview-transcript.json`.
8. If `--ref` was used and reference content was successfully retrieved, include reference analysis in the BA document.

### Output Location

```
ba/
├── BA-{feature-slug}.md           # Primary BA document
└── interview-transcript.json      # Machine-readable Q&A transcript
```
