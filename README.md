# WFC - World Fucking Class

> **Multi-agent consensus review system for Claude Code with intelligent persona selection**

WFC (World Fucking Class) is an advanced code review framework that leverages multiple expert AI personas to provide comprehensive, multi-perspective code reviews. Instead of a single review, WFC assembles a panel of specialized experts tailored to your specific task.

## 🎯 What is WFC?

WFC transforms code review by:
- **Intelligent Persona Selection**: Automatically selects 5 relevant experts from a pool of 50+ specialized reviewers
- **True Parallel Review**: Each persona reviews independently (no anchoring bias)
- **Consensus Synthesis**: Combines perspectives with relevance weighting
- **Panel Diversity**: Ensures diverse viewpoints across security, architecture, performance, and more

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/sam-fakhreddine/wfc.git
cd wfc
pip install -e ".[all]"
```

The installer will:
- Copy WFC to `~/.claude/skills/wfc`
- Set up the persona library
- Configure custom persona directory

### Basic Usage

In Claude Code, trigger a consensus review:

```
/wfc:consensus-review TASK-001
```

WFC will:
1. Analyze your task context (tech stack, complexity, properties)
2. Select 5 relevant expert personas
3. Execute independent parallel reviews
4. Synthesize consensus with weighted scoring
5. Return comprehensive multi-perspective feedback

### Manual Persona Selection

Override automatic selection:

```
/wfc:consensus-review TASK-001 --personas BACKEND_PYTHON_SENIOR,APPSEC_SPECIALIST,DB_ARCHITECT_SQL
```

## ✅ WFC:IMPLEMENT - Multi-Agent Parallel Implementation (Complete)

**Status**: ✅ **PRODUCTION READY** (Phases 1-3: 100%)

wfc:implement is a multi-agent parallel implementation engine that:
- Orchestrates up to 5 agents in parallel in isolated git worktrees
- Enforces TDD workflow (RED-GREEN-REFACTOR)
- Integrates universal quality gate (Trunk.io - 100+ tools)
- Uses confidence-first implementation (SuperClaude pattern)
- Learns from past mistakes across sessions (ReflexionMemory)
- Auto-merges with rollback capability (main always passing)

### Quick Usage

```bash
# Create a structured plan
wfc plan

# Execute implementation
wfc implement --tasks plan/TASKS.md

# Dry run (show plan without executing)
wfc implement --dry-run

# Health check
make doctor
```

### Features

**Core** (Phase 1):
- ✅ **Universal Quality Gate** - Trunk.io integration (all languages)
- ✅ **Complete TDD Workflow** - 6 phases (UNDERSTAND → TEST_FIRST → IMPLEMENT → REFACTOR → QUALITY_CHECK → SUBMIT)
- ✅ **Merge Engine with Rollback** - Main branch always passing
- ✅ **CLI Interface** - User-friendly with dry-run mode

**Intelligence** (Phase 2):
- ✅ **Confidence Checking** - Assess before acting (≥90% proceed, 70-89% ask, <70% stop)
- ✅ **Memory System** - Cross-session learning from mistakes
- ✅ **Token Budgets** - Complexity-based with historical optimization

**Polish** (Phase 3):
- ✅ **PROJECT_INDEX.json** - Machine-readable project structure
- ✅ **make doctor** - Comprehensive health checks
- ✅ **Integration Tests** - >80% coverage (22 comprehensive tests)
- ✅ **Complete Documentation** - Full guide in docs/WFC_IMPLEMENTATION.md

**Documentation**:
- [Complete Guide](docs/WFC_IMPLEMENTATION.md) - Full documentation
- [Implementation Patterns](PLANNING.md#implementation-patterns) - TDD, confidence-first, cross-session learning
- [Usage Examples](CLAUDE.md#wfcimplement---multi-agent-parallel-implementation) - Quick reference

## 🎭 The Expert Panel System

WFC includes **54+ expert personas** across **9 specialized panels**:

### Engineering Panel (11 personas)
Backend specialists (Python, Node.js, Java, Go, Rust), Frontend experts (React, Vue, Angular), Mobile (iOS, Android), Full-stack generalist

### Security Panel (8 personas)
Application security, Infrastructure security, Penetration testing, Compliance (SOC2, GDPR), Cloud security, API security, Secrets management, Cryptography

### Architecture Panel (7 personas)
Solutions architecture, API design, Microservices, Domain-driven design, Event-driven architecture, Cloud architecture, Integration patterns

### Quality Panel (8 personas)
Performance testing, Load testing, Code review, Test automation, Chaos engineering, Accessibility testing, Security testing

### Data Panel (4 personas)
SQL database architecture, NoSQL specialists, Data engineering, ML engineering

### Product Panel (3 personas)
Developer experience, Technical PM, UX research

### Operations Panel (4 personas)
SRE, Platform engineering, DevOps, Observability

### Domain Experts Panel (5 personas)
Fintech/payments, Healthcare/HIPAA, E-commerce, Gaming, IoT/embedded

### Specialists Panel (4 personas)
Accessibility (WCAG), Performance optimization, Internationalization, Technical debt analysis

## 📊 How Persona Selection Works

WFC uses a multi-stage selection algorithm:

1. **Tech Stack Matching (40%)**: Extracts technologies from files, matches persona expertise
2. **Properties Alignment (30%)**: SECURITY → security personas, PERFORMANCE → performance experts
3. **Complexity Filtering (15%)**: XL tasks need senior personas, S tasks can use any
4. **Task Type Classification (10%)**: API design, refactoring, feature implementation, etc.
5. **Domain Knowledge (5%)**: Payment processing → fintech expert
6. **Diversity Enforcement**: Maximum 2 personas per panel (ensures broad perspective)

### Example Selection

```
Task: Implement OAuth2 login with JWT tokens
Files: auth_service.py, jwt_handler.py
Tech Stack: Python, FastAPI, PostgreSQL, Redis
Complexity: L
Properties: SECURITY, SAFETY

Selected Personas:
1. APPSEC_SPECIALIST (0.95 relevance) - OAuth/JWT expert
2. BACKEND_PYTHON_SENIOR (0.88) - FastAPI patterns
3. API_SECURITY_SPECIALIST (0.82) - Token security
4. DB_ARCHITECT_SQL (0.72) - Token storage
5. SRE_SPECIALIST (0.61) - Key rotation, monitoring
```

## 🔬 Independent Subagent Execution

**Critical Design Principle**: Each persona runs as a **separate subagent** with no context sharing.

```python
# Each persona reviews independently
reviews = parallel_map(execute_persona_review, selected_personas)

# THEN synthesis happens
consensus = synthesize_reviews(reviews, relevance_scores)
```

**Why this matters:**
- No anchoring bias (personas don't see each other's opinions)
- Genuine independent expert assessment
- Disagreements preserved (not averaged away)
- Unique insights surface (only 1 persona caught it)

## 📈 Consensus Synthesis

After independent reviews complete:

1. **Weighted Scoring**: Scores weighted by relevance (not fixed weights)
2. **Consensus Detection**: Issues mentioned by 3+ personas
3. **Unique Insights**: Critical findings only 1 persona caught
4. **Divergent Views**: Where experts disagree (important signal)
5. **Unified Report**: Comprehensive synthesis with decision

### Example Output

```
Overall Score: 8.0/10 (relevance-weighted)

✅ Consensus Areas (4/5 agree):
   - Auth flow implementation is solid
   - Clean FastAPI patterns throughout

⚠️ Critical Issues:
   - PII in JWT payload (Compliance + Security caught)
   - Missing token refresh rotation (Security only)

💡 Unique Insights:
   - Token table missing index on user_id (DB Architect only)
   - No metrics for token failures (SRE only)

Decision: CONDITIONAL_APPROVE
Required Changes: Remove username from JWT, add refresh rotation, add index
```

## 🛠️ Extending WFC

### Adding Custom Personas

1. Create JSON file in `~/.claude/skills/wfc/personas/custom/`:

```json
{
  "id": "MY_CUSTOM_EXPERT",
  "name": "My Custom Expert",
  "panel": "engineering",
  "skills": [...],
  "lens": {...},
  "selection_criteria": {...}
}
```

2. Regenerate registry:

```bash
cd ~/.claude/skills/wfc/personas
python3 -c "from persona_orchestrator import PersonaRegistry; PersonaRegistry.rebuild_registry()"
```

Custom personas are gitignored and won't be tracked.

### Adding to the Core Library

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines on contributing personas to the main library.

## 📚 Documentation

- **[Architecture](docs/ARCHITECTURE.md)**: System design, components, data flow
- **[Personas](docs/PERSONAS.md)**: Complete persona library reference
- **[Contributing](docs/CONTRIBUTING.md)**: How to add personas, extend features
- **[Examples](docs/examples/)**: Common use cases and workflows

## 🔧 Configuration

WFC configuration lives in `~/.claude/skills/wfc/shared/config/wfc_config.py`:

```python
DEFAULTS = {
    "personas": {
        "enabled": True,
        "num_reviewers": 5,              # How many personas to select
        "require_diversity": True,       # Enforce panel diversity
        "min_relevance_score": 0.3,      # Minimum relevance threshold
        "synthesis": {
            "consensus_threshold": 3,    # N personas must agree
            "weight_by_relevance": True  # Weight scores by relevance
        }
    }
}
```

## 🧪 Testing

Run WFC test suite:

```bash
cd ~/.claude/skills/wfc/personas/tests
python3 -m pytest test_persona_selection.py -v
```

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](docs/CONTRIBUTING.md).

Areas where contributions are especially valuable:
- Adding new expert personas
- Improving selection algorithm
- Adding domain-specific expertise
- Documentation and examples

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built on Claude Code's agent framework. Inspired by ensemble methods in machine learning and the wisdom of diverse expert panels.

---

**Current Version**: 0.1.0
**Personas**: 54 expert reviewers across 9 panels
**Skills**: 11 Agent Skills compliant (wfc-implement, wfc-review, wfc-plan, wfc-test, wfc-security, wfc-architecture, wfc-observe, wfc-retro, wfc-safeclaude, wfc-isthissmart, wfc-newskill)
**wfc:implement**: ✅ Production ready (Phases 1-3 complete)
**Model Support**: Claude Opus 4.6, Sonnet 4.5, Haiku 4.5

**This is World Fucking Class.** 🚀
