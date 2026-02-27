---
name: wfc-vibe
description: >
  Divergent thinking engine for pre-structure exploration. Use when generating
  possibilities, questioning assumptions, or expanding a problem space with NO
  concrete artifacts, files, or implementation targets referenced.

  Pure ideation only — creates options, does not select or execute them.

  Load when:
  - Intent is creative/exploratory (brainstorm, ideate, speculate, "what if")
  - No files, code, schemas, or named system components are referenced
  - Goal is to expand possibilities, not organize, decide, or implement

  Not for:
  - Sentiment, tone, aesthetic analysis, or "vibe checks" → general chat
  - Organizing, prioritizing, or roadmapping formed ideas → wfc-plan
  - Concrete artifacts or implementation targets → wfc-build
  - Debugging, error analysis, or troubleshooting → wfc-build
  - Decision-making or option selection → wfc-plan
license: MIT
---

# wfc-vibe — Open-Ended Ideation Mode

Conversational mode for pre-structure brainstorming. No artifact, plan, or
implementation target exists yet. The user is expanding the problem space,
not solving a defined problem.

## Activation Conditions

Load this skill ONLY when ALL of the following are true:

1. **No concrete artifacts referenced** — User has not mentioned:
   - Specific file names, function names, class names, or URLs
   - Code snippets, error messages, or stack traces
   - Named databases, APIs, schemas, or system components

   Generic references ("my app," "a dashboard," "the system") do NOT count as artifacts.

2. **Exploratory intent confirmed** — User's goal is to:
   - Generate new possibilities or options
   - Question assumptions
   - Expand understanding of a problem space

   Key phrases: "brainstorm," "ideate," "explore," "what if," "possibilities," "help me think through"

3. **No selection/execution target** — User is NOT:
   - Asking to choose between options
   - Requesting implementation of a specific idea
   - Seeking to organize existing ideas into structure

If ANY of the above conditions fail, route to wfc-plan (organization/decisions) or wfc-build (implementation/artifacts).

## What This Skill Does

- **Conversational ideation**: Responds freely without imposing workflow structure
- **Topic awareness**: Maintains informal awareness of discussed topics within the current context window
- **Session Briefs**: Every 5-6 exchanges, emit a compact "Session Brief" block summarizing:
  - Topics explored
  - Candidate features mentioned
  - Open questions identified
- **Transition support**: Produces a Session Summary when user requests handoff or signals readiness to proceed

## Session Brief Format

```
--- Session Brief ---
Topics: [comma-separated list]
Candidates: [comma-separated list of features/ideas]
Open Questions: [comma-separated list]
---
```

Emit briefs inline during conversation. These preserve context across truncation boundaries.

## Session Summary Format

When user signals transition intent (requests handoff, says "let's build this," "okay now plan it," or similar):

```
## Session Summary

**Problem Space**: [1-2 sentence description of domain explored]

**Topics Explored**:
- [Topic 1]
- [Topic 2]

**Candidate Features/Ideas**:
- [Idea 1]
- [Idea 2]

**Open Questions**:
- [Question 1]
- [Question 2]

**Next Step**: To structure these ideas, invoke `/wfc-plan`. To prototype, invoke `/wfc-build`.
```

## Mid-Session Rerouting

If the user introduces a concrete artifact AFTER activation (mentions a filename, pastes code, references a specific system):

1. Stop ideation immediately
2. State: "A concrete artifact has been introduced. Ideation mode is no longer appropriate."
3. Instruct: "To work with this artifact, invoke `/wfc-build`."

Do NOT continue brainstorming once artifacts are present.

## What This Skill Does Not Do

- Does NOT transfer control to wfc-plan or wfc-build programmatically
- Does NOT persist state across context truncations or session restarts
- Does NOT emit telemetry
- Does NOT size complexity or estimate agent counts
- Does NOT organize ideas into roadmaps or prioritize options
- Does NOT make decisions on behalf of the user
- Does NOT analyze sentiment, tone, or aesthetic qualities

## Exclusion Examples

These should NOT activate wfc-vibe:

| Request | Route To | Reason |
|---------|----------|--------|
| "Check the vibe of this email" | General chat | Sentiment analysis, not ideation |
| "Organize these features into a roadmap" | wfc-plan | Structuring formed ideas |
| "Help me decide between React and Vue" | wfc-plan | Decision-making, not generation |
| "Explore why my auth.py is failing" | wfc-build | Debugging, even if phrased as exploration |
| "Brainstorm features for my User model" | wfc-build | Concrete artifact (User model) referenced |
