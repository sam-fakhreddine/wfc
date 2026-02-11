# WFC Quick Start Guide

> **Get up and running with World Fucking Class code reviews in 5 minutes**

## Install WFC

```bash
# Clone the repo
git clone https://github.com/yourusername/wfc.git
cd wfc

# Install with uv (recommended) - includes tiktoken for 99% token reduction
uv venv
source .venv/bin/activate
uv pip install -e ".[tokens]"

# Or manual install
./install.sh
```

That's it! WFC is now installed.

### Why uv + pyproject.toml?

- **Faster**: uv is 10-100x faster than pip
- **Proper**: Real Python package with dependency management
- **Complete**: Installs tiktoken automatically for ultra-minimal prompts (99% token reduction)

See [Ultra-Minimal Results](ULTRA_MINIMAL_RESULTS.md) for performance details.

## Your First Review

### Option 1: Auto-Trigger (Natural Language)

Just ask Claude to review code:

```
"Hey Claude, can you review this code for me?"
```

WFC will automatically activate and select 5 relevant expert personas based on your code.

### Option 2: Manual Trigger (Slash Command)

Use the slash command:

```
/wfc-review
```

Or specify files:

```
/wfc-review path/to/my/code
```

## What Happens Next?

WFC will:

1. **Analyze your code** - Detect tech stack (Python? React? Go?)
2. **Select 5 expert personas** - From 54 specialists (security, architecture, performance, etc.)
3. **Spawn independent subagents** - Each persona runs as a separate Claude Code subagent via Task tool
4. **Parallel execution** - All reviews happen concurrently with true isolation (no context bleeding)
5. **Consensus synthesis** - Weighted scoring, consensus areas, unique insights
6. **Return comprehensive report** - Multi-perspective feedback with actionable recommendations

### How It Works (Technical)

WFC uses Claude Code's [Task tool](https://code.claude.com/docs/en/sub-agents) for true independent reviews:

```
/wfc-review
    ↓
Select Personas → Prepare Prompts → Spawn Task Tools (parallel)
    ↓                    ↓                    ↓
5 personas         5 system prompts    5 independent subagents
    ↓                                         ↓
Parse Results ← ← ← ← ← ← ← ← ← ← ← 5 JSON responses
    ↓
Synthesize Consensus → Generate Report
```

Each persona runs in its own subprocess with no visibility into other reviews until synthesis.

## Example Review Output

```
🎭 Selected Expert Personas (5/54)

1. BACKEND_PYTHON_SENIOR (Relevance: 0.92)
2. APPSEC_SPECIALIST (Relevance: 0.89)
3. CODE_REVIEWER (Relevance: 0.85)
4. DB_ARCHITECT_SQL (Relevance: 0.78)
5. PERF_TESTER (Relevance: 0.75)

📊 Consensus Review Results

Overall Score: 8.5/10 ✅ APPROVED

✅ Consensus Areas (4/5 agree):
   - Code structure is clean and modular
   - Database queries are well-optimized
   - Security best practices followed

⚠️ Critical Issues:
   - SQL injection risk in user input (APPSEC_SPECIALIST)
   - Missing index on orders.user_id (DB_ARCHITECT_SQL)

💡 Unique Insights:
   - Consider caching for GET requests (PERF_TESTER)
   - Type hints could be more specific (BACKEND_PYTHON_SENIOR)

Decision: CONDITIONAL_APPROVE
Required Changes: Fix SQL injection, add index
```

## Manual Persona Selection

Override automatic selection:

```
/wfc-review --personas BACKEND_PYTHON_SENIOR,APPSEC_SPECIALIST,SRE_SPECIALIST
```

## Make It Automatic

Create a `CLAUDE.md` file in your project:

```markdown
# Claude Instructions

## Code Review Process

For all code changes, use WFC consensus review:

/wfc-review

Required: ≥8.0/10 score, zero critical issues
```

Now Claude will automatically use WFC for reviews!

## Available Skills

WFC includes 11 skills:

| Skill | What It Does | Trigger |
|-------|--------------|---------|
| `wfc-review` | **Multi-agent consensus code review** | "review this code" |
| `wfc-plan` | Structured implementation planning | "plan this feature" |
| `wfc-implement` | Parallel TDD implementation | "implement this plan" |
| `wfc-test` | Generate tests from properties | "generate tests" |
| `wfc-security` | STRIDE threat modeling | "threat model this" |
| `wfc-isthissmart` | Critical thinking advisor | "is this a good idea?" |
| `wfc-architecture` | Architecture docs + diagrams | "document architecture" |
| `wfc-observe` | Observability from properties | "add monitoring" |
| `wfc-safeclaude` | Safe command allowlist | "reduce approval prompts" |
| `wfc-retro` | Retrospective analysis | "run retrospective" |
| `wfc-newskill` | Create new WFC skills | "create a skill" |

## Common Workflows

### Workflow 1: New Feature

```
1. /wfc-isthissmart "Add OAuth2 login"
   → Validates approach before starting

2. /wfc-plan
   → Generates TASKS.md with dependencies

3. /wfc-implement
   → Executes tasks with TDD + reviews

4. /wfc-review
   → Final consensus review before merge
```

### Workflow 2: Security Audit

```
1. /wfc-security --stride
   → Generates threat model

2. /wfc-review --properties SECURITY,SAFETY
   → Focused security review with relevant personas
```

### Workflow 3: Performance Optimization

```
1. /wfc-review --personas PERF_TESTER,LOAD_TESTING_SPECIALIST,BACKEND_PYTHON_SENIOR
   → Manual persona override for performance focus

2. /wfc-observe
   → Generate monitoring from performance properties
```

## Troubleshooting

### Skills Not Showing Up?

1. **Restart Claude Code** - Skills are loaded at startup
2. **Check installation**:
   ```bash
   ls ~/.claude/skills/ | grep wfc
   ```
   You should see `wfc-review`, `wfc-plan`, etc.

3. **Verify flattening**:
   ```bash
   ls ~/.claude/skills/wfc-review/SKILL.md
   ```
   Should exist (not nested in `skills/` subdirectory)

### Auto-Trigger Not Working?

Make sure skill descriptions are loaded:
```bash
head -5 ~/.claude/skills/wfc-review/SKILL.md
```

Should show updated description with trigger phrases.

### Reviews Not Using Personas?

Check persona library installation:
```bash
ls ~/.claude/skills/wfc/personas/panels/
```

Should show 9 panels with JSON files.

## Next Steps

- **Explore personas**: See [PERSONAS.md](docs/PERSONAS.md) for complete library
- **Customize**: Add your own personas to `~/.claude/skills/wfc/personas/custom/`
- **Integrate**: Add `CLAUDE.md` to your projects for automatic WFC usage
- **Extend**: Use `/wfc-newskill` to create custom workflows

## Get Help

- **Documentation**: [README.md](README.md), [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Issues**: GitHub Issues
- **Examples**: [docs/examples/](docs/examples/)

---

**You're ready to get World Fucking Class code reviews!** 🚀
