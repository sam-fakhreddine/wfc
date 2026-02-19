# Contributing to WFC

Thank you for your interest in contributing to WFC! This document provides guidelines for contributing personas, features, and improvements.

## How to Contribute

### Contributing Reviewer Knowledge

The most valuable contribution is adding domain knowledge to the 5 fixed specialist reviewers, helping them catch more issues in specific areas.

WFC v2.0 uses 5 fixed reviewers (Security, Correctness, Performance, Maintainability, Reliability). Each reviewer has a `KNOWLEDGE.md` file that accumulates learned patterns from past reviews.

#### 1. Identify a Knowledge Gap

Look for patterns that reviewers are missing. Common gaps:

- Framework-specific pitfalls (e.g., Django ORM N+1, React hook dependency arrays)
- Language idioms a reviewer should flag (e.g., Python mutable default arguments)
- Domain anti-patterns (e.g., JWT expiry misconfigurations)

#### 2. Find the Right Reviewer

```
wfc/references/reviewers/
├── security/KNOWLEDGE.md       # OWASP, injection, auth/authz
├── correctness/KNOWLEDGE.md    # Logic bugs, edge cases, type safety
├── performance/KNOWLEDGE.md    # Algorithmic efficiency, N+1, memory
├── maintainability/KNOWLEDGE.md # Readability, SOLID, DRY, coupling
└── reliability/KNOWLEDGE.md    # Error handling, fault tolerance
```

#### 3. Add a Knowledge Entry

Append to the appropriate `KNOWLEDGE.md`:

```markdown
## [Category]: Short title of the pattern

**Pattern**: What to look for (code or structural signal)

**Risk**: Why this is a problem

**Example (Bad)**:
```python
# Problematic code example
```

**Example (Good)**:

```python
# Correct code example
```

**References**: CVE, CWE, or documentation link (if applicable)

```

#### 4. Validate & Submit PR

```bash
# Check for formatting issues
uv run pre-commit run --all-files

git checkout -b add-knowledge-{reviewer}-{topic}
git add wfc/references/reviewers/{reviewer}/KNOWLEDGE.md
git commit -m "docs(reviewers): add {topic} pattern to {reviewer} knowledge"
git push origin add-knowledge-{reviewer}-{topic}
```

Create PR with description:

- Which reviewer this knowledge extends
- What pattern it teaches
- Example of code that would now be caught

### Adding Features

For new features (CLI commands, integrations, etc.):

1. **Discuss first**: Open an issue describing the feature
2. **Get feedback**: Ensure it aligns with WFC goals
3. **Implement**: Follow existing code patterns
4. **Test**: Add tests in `wfc/tests/`
5. **Document**: Update relevant docs
6. **Submit PR**: Clear description of changes

### Adding Hook Patterns

WFC uses a hook system (`wfc/scripts/hooks/`) for extensible behavior at key workflow points (e.g., post-review simplification, confidence filtering). To add a new hook pattern:

1. **Create a hook module** in `wfc/scripts/hooks/`
2. **Implement the hook interface** - each hook receives context from the workflow step and returns modified context or signals
3. **Register the hook** with the orchestrator so it fires at the correct workflow phase
4. **Add tests** covering the hook behavior
5. **Submit PR** explaining what workflow phase the hook targets and why

### Adding Rules

WFC supports custom rules via the wfc-rules skill. User-defined rules live in `.wfc/rules/` and are preserved across updates. To contribute built-in rules:

1. **Create a rule definition** following the existing rule schema
2. **Place it** in the appropriate rules directory
3. **Test** that the rule fires correctly during review or implementation
4. **Document** the rule's purpose, trigger conditions, and expected behavior

### Available Skills (30 total)

WFC currently provides 30 Agent Skills compliant skills. When contributing, be aware of the full set:

- **wfc-review** - Multi-agent consensus review (5 fixed specialist reviewers)
- **wfc-plan** - Adaptive planning with architecture design phase
- **wfc-implement** - Parallel implementation engine
- **wfc-build** - Intentional Vibe quick feature building
- **wfc-lfg** - Autonomous end-to-end pipeline
- **wfc-deepen** - Post-plan parallel research enhancement
- **wfc-security** - STRIDE threat analysis
- **wfc-architecture** - Architecture docs + C4 diagrams
- **wfc-test** - Property-based test generation
- **wfc-observe** - Observability from properties
- **wfc-validate** - 7-dimension analysis
- **wfc-vibe** - Default conversational mode
- **wfc-init** - Project initialization
- **wfc-safeguard** - Real-time security hook enforcement
- **wfc-rules** - Custom rule definition and enforcement
- **wfc-playground** - Interactive HTML playground generator
- **wfc-compound** - Knowledge codification to docs/solutions/
- **wfc-ba** - Business analysis and requirements gathering
- **wfc-agentic** - GitHub Agentic Workflow generator
- **wfc-export** - Multi-platform skill export
- **wfc-sync** - Rule and pattern discovery and sync
- **wfc-pr-comments** - PR comment triage and fix
- **wfc-gh-debug** - GitHub Actions CI failure debugger
- **wfc-housekeeping** - Project hygiene and dead code cleanup
- **wfc-retro** - Retrospective analysis
- **wfc-newskill** - Meta-skill for creating new WFC skills
- **wfc-safeclaude** - Project-specific command allowlist generator
- **wfc-code-standards** - Language-agnostic coding standards
- **wfc-python** - Python-specific development standards
- **wfc-isthissmart** - Quick idea sanity check

See `docs/skills/README.md` for the full selection matrix.

### Documentation Improvements

Documentation PRs are always welcome:

- Fix typos, clarify instructions
- Add examples in `docs/examples/`
- Improve installation guides
- Add troubleshooting tips

## Code Style

- **Python**: Follow PEP 8, use type hints
- **JSON**: 2-space indentation, sorted keys where logical
- **Markdown**: Use headers, code blocks, clear structure

## Testing

Before submitting PR:

```bash
# Run full test suite
uv run pytest

# Run with coverage
uv run pytest --cov=wfc --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_review_system.py -v

# Validate all WFC skills (Agent Skills compliance)
make validate

# Run all quality checks
make check-all
```

## Review Process

1. **Automated checks**: PR triggers validation
2. **Maintainer review**: 1-2 maintainers review
3. **Discussion**: Address feedback
4. **Merge**: Maintainer merges when ready

## Questions?

- **Issues**: Open an issue for bugs, questions
- **Discussions**: Use GitHub Discussions for ideas
- **Email**: <wfc-maintainers@example.com> (TODO: update)

## License

By contributing, you agree your contributions will be licensed under the MIT License.

---

Thank you for helping make WFC better! 🙌
