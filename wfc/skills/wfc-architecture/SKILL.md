---
name: wfc-architecture
description: Architecture documentation generation and analysis. Creates comprehensive ARCHITECTURE.md with C4 diagrams (Context, Container, Component) in Mermaid format, generates Architecture Decision Records (ADRs), and audits code alignment with documentation. Use when starting new projects, documenting existing systems, or verifying architectural consistency. Triggers on "document architecture", "create architecture diagrams", "audit architecture alignment", or explicit /wfc-architecture. Ideal for onboarding, architecture reviews, and maintaining up-to-date system documentation. Not for code implementation or detailed API specs.
license: MIT
---

# WFC:ARCHITECTURE - Architecture Generation & Analysis

Generates comprehensive architecture documentation from plans and code.

## What It Does

1. **Architecture Generator** - Creates ARCHITECTURE.md from plan
2. **C4 Diagram Generator** - Mermaid diagrams (Context, Container, Component)
3. **ADR Generator** - Architecture Decision Records
4. **Architecture Audit** - Compares code vs documentation

## Usage

```bash
# Generate architecture docs
/wfc-architecture --generate

# Audit existing architecture
/wfc-architecture --audit

# Generate specific diagram
/wfc-architecture --c4 context
```

## Outputs

- ARCHITECTURE.md
- C4-CONTEXT.mmd (Mermaid)
- C4-CONTAINER.mmd
- C4-COMPONENT.mmd
- ADR-XXX.md files

## Philosophy

**ELEGANT**: Simple, visual documentation
**MULTI-TIER**: Diagrams show tier separation
**PARALLEL**: Can generate all diagrams concurrently
