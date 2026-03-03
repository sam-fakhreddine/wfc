# Claude Code — WFC Integration

## WFC Skills

WFC skills are available as slash commands. Use them for structured development workflows.

### Core Workflow

```
/wfc-lfg "feature description"   # Full auto: plan → implement → review → PR
/wfc-build "feature"              # Quick single feature (adaptive interview)
/wfc-plan                         # Structured planning for complex features
/wfc-implement                    # Execute TASKS.md with parallel TDD agents
/wfc-review                       # 5-agent consensus code review
```

### When to Use WFC

- **Always** for features >100 lines or security-sensitive changes
- **Always** before merging PRs (`/wfc-review`)
- **Skip** for docs, typos, config tweaks

### Quality Threshold

- Required Consensus Score: ≥7.0/10
- Zero critical findings from Security or Reliability reviewers
- At least 3/5 reviewers agree on findings

### Branch Policy

- Agents push to `claude/*` branches → auto-merge PR to `develop`
- Never push directly to `main`
