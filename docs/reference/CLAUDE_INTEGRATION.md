# Integrating WFC with Claude Code

> **How to ensure Claude automatically uses WFC in your workflows**

After installing WFC, you need to configure Claude Code to actually use it. This is done through your project's `CLAUDE.md` file.

## Quick Setup

### 1. Create or Update CLAUDE.md

In your project root, create a `CLAUDE.md` file:

```bash
cd /path/to/your/project
touch CLAUDE.md
```

### 2. Add WFC Instructions

Add these instructions to tell Claude when and how to use WFC:

```markdown
# Claude Instructions for This Project

## Code Review Workflow

When reviewing code or pull requests, use the WFC (Workflow Claude) multi-agent consensus review system:

### Automatic Review Trigger

For any significant code change (>50 lines, new features, security-sensitive code, or architectural changes):

1. **Use WFC consensus review**:
   ```

   /wfc-consensus-review TASK-{id}

   ```

2. **WFC will automatically**:
   - Analyze tech stack and complexity
   - Select 5 relevant expert personas
   - Execute independent parallel reviews
   - Synthesize consensus with weighted feedback

### When to Use WFC

✅ **Always use for**:
- Pull request reviews
- New feature implementations (medium/large)
- Security-sensitive changes
- Architecture/design decisions
- Performance-critical code
- Database schema changes
- API changes (breaking or non-breaking)

🤔 **Consider using for**:
- Refactoring tasks
- Bug fixes (non-trivial)
- Test coverage improvements

⏩ **Skip for**:
- Typo fixes
- Documentation-only changes
- Single-line changes
- Configuration updates (non-security)

### Manual Persona Override

For specialized reviews, manually select personas:

```

/wfc-consensus-review TASK-{id} --personas APPSEC_SPECIALIST,DB_ARCHITECT_SQL,BACKEND_PYTHON_SENIOR

```

### Review Quality Standards

WFC consensus reviews should achieve:
- **Overall Score**: ≥8.0/10 for approval
- **Consensus**: ≥3 personas agree on critical points
- **Security**: No critical security issues flagged
- **Performance**: No major performance concerns

## Tech Stack Context

This project uses:
- **Backend**: Python 3.11, FastAPI, PostgreSQL, Redis
- **Frontend**: React 18, TypeScript, Vite
- **Infrastructure**: Docker, Kubernetes, AWS
- **Testing**: pytest, React Testing Library

This context helps WFC select relevant personas automatically.

## Properties to Focus On

For this project, prioritize these properties in reviews:
- **SECURITY**: We handle payment data (PCI compliance)
- **PERFORMANCE**: Real-time features, <100ms latency requirement
- **RELIABILITY**: 99.9% uptime SLA
- **MAINTAINABILITY**: Junior developers onboard frequently

## Custom Review Instructions

When using WFC, ask reviewers to specifically check:
- [ ] Database queries are optimized (no N+1)
- [ ] API endpoints have proper authentication
- [ ] Error messages don't leak sensitive data
- [ ] All external inputs are validated
- [ ] Changes maintain backwards compatibility
```

### 3. Commit CLAUDE.md

```bash
git add CLAUDE.md
git commit -m "Add Claude Code instructions with WFC integration"
```

## Advanced Configuration

### Project-Specific Persona Preferences

You can guide WFC to prefer certain personas for your project:

```markdown
## WFC Persona Preferences

For this project, prefer these personas when relevant:
- **FINTECH_PAYMENTS**: We're a payment processor
- **BACKEND_PYTHON_SENIOR**: Primary language
- **DB_ARCHITECT_SQL**: PostgreSQL is critical
- **APPSEC_SPECIALIST**: Security is paramount
- **SRE_SPECIALIST**: Production reliability focus
```

### Automated Review Gates

Set up review quality gates:

```markdown
## Review Quality Gates

All PRs must pass WFC consensus review with:
- Overall score ≥ 8.0/10
- Zero critical security issues
- Zero blocking performance issues
- All tests passing

Reviewers should run:
```

/wfc-consensus-review PR-{number}

```

Before approving any PR.
```

### Team Workflow Integration

For teams, standardize WFC usage:

```markdown
## Team Review Process

### Step 1: Developer Self-Review
Before submitting PR, run:
```

/wfc-consensus-review TASK-{id}

```

Address any issues with score <8.0

### Step 2: Human Review
Senior engineer reviews:
- Code logic and business requirements
- Test coverage
- Documentation

### Step 3: Final WFC Check
Before merge, final consensus review:
```

/wfc-consensus-review PR-{number}

```

Must achieve ≥8.5/10 for production deployment.
```

## Example CLAUDE.md Templates

### Startup Project (Move Fast)

```markdown
# Claude Instructions

## WFC Usage
Use WFC for:
- Features (M/L/XL complexity)
- Security changes
- Breaking changes

Skip for:
- Small bug fixes
- Documentation
- Experimental features (we iterate quickly)

Preferred personas: BACKEND_PYTHON_SENIOR, FRONTEND_REACT_EXPERT, CODE_REVIEWER
```

### Enterprise Project (High Assurance)

```markdown
# Claude Instructions

## WFC Usage
**MANDATORY for ALL code changes** except documentation-only.

Minimum requirements:
- Overall score ≥ 9.0/10
- Zero critical issues (security, performance, reliability)
- Consensus on all major points
- Compliance review for regulated code

Always include: APPSEC_SPECIALIST, COMPLIANCE_AUDITOR, SRE_SPECIALIST

Review properties: SECURITY, SAFETY, COMPLIANCE, RELIABILITY
```

### Open Source Project

```markdown
# Claude Instructions

## WFC Usage for Contributors

Before submitting PR, run WFC self-review:
```

/wfc-consensus-review FEATURE-{name}

```

This helps catch issues early and speeds up maintainer review.

Focus areas:
- Code quality (maintainability for future contributors)
- Documentation (clear for new users)
- Test coverage (regression prevention)
- Backwards compatibility (don't break existing users)

Personas: CODE_REVIEWER, TEST_AUTOMATION_EXPERT, TECH_DEBT_ANALYST
```

## Verification

After setting up CLAUDE.md, verify Claude uses WFC:

1. Start a new Claude Code session
2. Ask: "What's the review process for this project?"
3. Claude should reference WFC consensus review
4. Test: "Review this file: src/api/auth.py"
5. Claude should trigger WFC automatically for significant changes

## Troubleshooting

### Claude doesn't use WFC automatically

**Fix**: Make CLAUDE.md instructions more explicit:

```markdown
IMPORTANT: For all code reviews, you MUST use:
/wfc-consensus-review TASK-{id}

Do not review code manually. Always use WFC for multi-perspective analysis.
```

### WFC selects wrong personas

**Fix**: Add tech stack and properties context:

```markdown
## Tech Stack
- Python, FastAPI, PostgreSQL

## Properties
- SECURITY (we handle PII)
- PERFORMANCE (real-time system)
```

### Scores are too strict

**Fix**: Calibrate thresholds:

```markdown
## Review Standards
- ≥7.0: Acceptable for experimental features
- ≥8.0: Required for production code
- ≥9.0: Required for security-critical code
```

## Best Practices

1. **Be Specific**: Tell Claude exactly when to use WFC
2. **Set Context**: Provide tech stack and properties
3. **Define Thresholds**: What scores are acceptable?
4. **Override When Needed**: Some reviews need specific personas
5. **Iterate**: Adjust CLAUDE.md based on what works

---

**Next Steps**: See [examples/](../examples/) for real-world CLAUDE.md configurations.
