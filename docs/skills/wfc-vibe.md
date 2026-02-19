# wfc-vibe

## What It Does

`wfc-vibe` is WFC's natural brainstorming mode — a conversational interface where you can think out loud without being pushed into a formal workflow. It tracks conversation context, detects when scope grows large enough to warrant planning, and drops a single passive reminder around every 10 messages. When you are ready to act, say "let's plan this" or "let's build this" and it hands off to `wfc-plan` or `wfc-build` with a summary of what you discussed.

## When to Use It

- You are in early-stage ideation and not ready to commit to a plan
- You want to explore possibilities, talk through architecture, or think out loud
- You have a rough idea and want to shape it through conversation before implementing
- You want WFC's help without triggering a formal interview or task structure
- You find other AI assistants too eager to jump into action before you are ready

Do not use wfc-vibe when you already know what you want to build — go directly to `/wfc-build` or `/wfc-plan`.

## Usage

```bash
# wfc-vibe is the default conversational mode — just start chatting.
# No slash command needed. Say /wfc-vibe to activate it explicitly.

# When ready to act:
"let's plan this"
"let's build this"
"I want to implement this"
```

## Example

```
User: I'm thinking about adding user authentication to the app.

Claude: What kind of auth are you considering?

User: JWT tokens. Maybe Redis for sessions.

Claude: Makes sense. How about the user model — email + password hash, roles?

User: Yeah. And we need RBAC, audit logging, email notifications, and webhooks.

Claude: 💭 This is growing into a sizable project. Consider using /wfc-plan
        to structure it when ready.

User: (continues exploring for a few more messages...)

Claude: 💡 Tip: Say "let's plan this" anytime to move to implementation.

User: let's plan this

Claude: 📋 Here's what I captured:

Goal: User management system with auth and RBAC
Features: JWT auth, Redis sessions, roles, audit logs, email, webhooks
Tech: FastAPI, Redis, PostgreSQL
Estimated complexity: L (3-4 agents)

Route to: wfc-plan (complex multi-feature project)
Ready to start? (yes/no)
```

## Options

No arguments required. Behavior is configured via `wfc.json` if needed:

```json
{
  "vibe": {
    "reminder_frequency": [8, 12],
    "max_scope_suggestions": 1,
    "transition_preview": true
  }
}
```

`reminder_frequency` controls how many messages between passive planning hints (randomized in range). `max_scope_suggestions` limits scope-growth warnings to one per conversation so they are not annoying.

## Integration

**Produces:**

- A structured context summary (goal, features, tech, estimated complexity) handed off to the next skill
- Telemetry entries for vibe sessions, transitions, and scope suggestions

**Consumes:**

- Your free-form conversation — no structured input required

**Next step:** When you say "let's plan this" or "let's build this," wfc-vibe transitions to `/wfc-plan` (for complex multi-feature work) or `/wfc-build` (for single-feature fast iteration), carrying the conversation context forward automatically.
