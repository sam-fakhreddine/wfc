# Progressive Disclosure - Documentation Organization

**Philosophy**: Load only what's needed when needed

## Documentation Hierarchy

### Level 1: Quick Start (5 minutes)
**Goal**: Get running immediately

- README.md (overview + installation)
- QUICKSTART.md (5-minute setup)
- Basic usage examples

**When**: First-time users, quick reference

---

### Level 2: Essential Guides (15-30 minutes)
**Goal**: Understand core features

- docs/workflow/WFC_IMPLEMENTATION.md (complete guide)
- CLAUDE.md (development workflow)
- PLANNING.md (architecture + patterns)

**When**: Regular users, feature implementation

---

### Level 3: Deep Dives (1-2 hours)
**Goal**: Master specific features

- docs/reference/AGENT_SKILLS_COMPLIANCE.md (spec details)
- docs/quality/QUALITY_SYSTEM.md (quality gates)

**When**: Advanced users, custom workflows

---

### Level 4: Reference (as needed)
**Goal**: Find specific information

- API documentation
- Persona library reference
- Configuration options
- Troubleshooting

**When**: Solving specific problems

---

## Progressive Loading Pattern

### 1. SKILL.md (Entry Point)
- < 500 lines
- High-level overview
- Usage examples
- Link to deeper docs

```markdown
# wfc-implement

Multi-agent parallel implementation engine.

[Quick Start](#quick-start) | [Features](#features) | **[Complete Guide](../../docs/workflow/WFC_IMPLEMENTATION.md)**

## Quick Start
...basic usage...

## Features
...feature list...

## Learn More
- [Complete Guide](../../docs/workflow/WFC_IMPLEMENTATION.md) - Full documentation
- [Implementation Patterns](../../PLANNING.md#implementation-patterns) - Code patterns
```

### 2. docs/ (Deep Dives)
- Comprehensive guides
- Architecture docs
- Pattern libraries
- No length limits

### 3. references/ (On Demand)
- Large reference docs
- Persona catalogs
- Token management details
- Loaded only when needed

---

## Reorganization Plan

### Current Structure (Flat)
```
/
├── README.md
├── QUICKSTART.md
├── CLAUDE.md
├── PLANNING.md
├── docs/
│   ├── architecture/     # System design
│   ├── security/         # OWASP, hooks
│   ├── workflow/         # Install, build, implementation
│   ├── quality/          # Quality gates, personas
│   ├── reference/        # Compliance, registries
│   └── examples/
```

### Proposed Structure (Progressive)
```
/
├── README.md                     # L1: Overview (5min)
├── QUICKSTART.md                 # L1: Quick start (5min)
│
├── guides/                       # L2: Essential (15-30min)
│   ├── GETTING_STARTED.md
│   ├── IMPLEMENTATION.md         # Was: docs/WFC_IMPLEMENTATION.md
│   ├── DEVELOPMENT.md            # Was: CLAUDE.md
│   └── ARCHITECTURE.md           # Was: PLANNING.md
│
├── advanced/                     # L3: Deep dives (1-2h)
│   ├── superclaude/
│   │   ├── patterns.md
│   │   ├── token_optimization.md
│   │   └── memory_system.md
│   ├── agent_skills/
│   │   ├── compliance.md
│   │   └── validation.md
│   └── quality/
│       ├── quality_gates.md
│       └── testing.md
│
└── reference/                    # L4: As needed
    ├── api/
    │   ├── cli.md
    │   ├── python_api.md
    │   └── configuration.md
    ├── personas/
    │   ├── catalog.md
    │   └── custom.md
    └── troubleshooting/
        ├── common_issues.md
        └── faq.md
```

---

## Benefits

**Faster Onboarding**:
- Get started in 5 minutes (not 1 hour)
- Learn incrementally
- Only read what's needed

**Better Discovery**:
- Clear hierarchy
- Logical grouping
- Easy to find information

**Reduced Cognitive Load**:
- Not overwhelmed with 20+ docs
- Progressive learning curve
- Just-in-time information

**Maintainability**:
- Logical organization
- Clear ownership
- Easy to update

---

## Migration Strategy

**Phase 1**: Add progressive structure (new directories)
**Phase 2**: Move docs to new locations
**Phase 3**: Update all links
**Phase 4**: Add index pages with navigation
**Phase 5**: Deprecate old locations (symlinks)

---

## Navigation Pattern

Every document includes breadcrumb navigation:

```markdown
# Document Title

[Home](/) > [Guides](/guides) > This Document

Quick Links: [Getting Started](/guides/GETTING_STARTED.md) | [API Reference](/reference/api)
```

Every level links up and down:

- **Up**: Link to parent category
- **Down**: Link to child documents
- **Related**: Link to related topics

---

**This is World Fucking Class.** 🚀
