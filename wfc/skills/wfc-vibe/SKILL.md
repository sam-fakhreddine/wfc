---
name: wfc-vibe
description: >
  Activates for open-ended, pre-structure ideation where no plan, task,
  artifact, or implementation target exists yet. For early-stage exploration:
  generating possibilities, questioning assumptions, expanding problem space
  without committing to a solution.

  LOAD when ALL of: user signals open-ended exploration with no existing
  artifact (/wfc-vibe, or 'brainstorm', 'explore ideas', 'let's ideate' —
  semantic intent required, not substring match); no concrete artifact
  referenced; no specific implementation target stated.

  Not for: 'vibe' as sentiment or negation; concrete artifact present (file,
  function, schema) → wfc-build; organizing already-formed ideas → wfc-plan;
  specific technical decisions → wfc-build; implementation, debugging,
  refactoring, or architecture review of existing systems.

  Does not hand off programmatically — produces a context summary and
  instructs user to invoke /wfc-plan or /wfc-build explicitly.
license: MIT
---

# wfc-vibe — Open-Ended Ideation Mode

Conversational mode for pre-structure brainstorming. No artifact, plan, or
implementation target exists yet. The user is expanding the problem space,
not solving a defined problem.

## Activation Conditions

Load this skill only when:

1. User expresses open-ended exploration with **no referenced artifact**
2. Trigger is semantic (intent to ideate freely), not substring (the word "vibe" alone is insufficient)
3. No specific technical decision, named file, or existing system is the subject

If any concrete artifact or implementation target is present at load time, do not activate — route to wfc-build.

## What This Skill Does

- Responds conversationally without imposing workflow structure
- Tracks topics, candidate features, and open questions mentioned during the session
- Issues a single scope-growth suggestion if the user's own project grows beyond 3 distinct features with first-person ownership signals ("we need", "I want to add", "let's include")
- Issues a single passive reminder at approximately 10 user turns if no transition has occurred and no closure signal is present
- Produces a structured context summary when the user signals transition intent

## What This Skill Does Not Do

- Does not transfer control to wfc-plan or wfc-build programmatically
- Does not track state across context truncations or session restarts; counter-based guarantees (scope suggestion once, reminder at ~10 turns) apply to a single uninterrupted session only
- Does not emit telemetry
- Does not size complexity or estimate agent counts — those fields are omitted from transition output
- Does not trigger scope suggestions on
