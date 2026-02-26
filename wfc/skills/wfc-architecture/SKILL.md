---
name: wfc-architecture
description: >
  Generates and maintains software architecture documentation for systems with
  source code. Invoke when the user explicitly asks to: create or update an
  ARCHITECTURE.md file; generate C4 diagrams (Context, Container, or Component
  level) in Mermaid format; author an Architecture Decision Record (ADR) for a
  specific technology choice or design tradeoff (user must state the decision
  and rationale); or audit whether source code structure matches an existing
  ARCHITECTURE.md. Requires a codebase, plan document, or system description
  with named components. Also triggers on explicit /wfc-architecture command.
  Not for: API specs, code review, sequence/ER/flowchart diagrams, README
  files, IaC, organizational design, or when no source material is provided.
license: MIT
---

# WFC:ARCHITECTURE - Architecture Documentation
