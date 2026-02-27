---
name: wfc-architecture
description: >
  Synchronizes software architecture documentation (ARCHITECTURE.md) and diagrams
  for systems with existing source code. Triggers on requests to: map system
  boundaries using C4 models (Context, Container, Component); author Architecture
  Decision Records (ADRs); or verify code structure compliance against an existing
  ARCHITECTURE.md.
  
  INPUTS: Requires a valid codebase path. Text-based system descriptions are
  supplementary context only; this skill does not design systems from scratch.
  
  OUTPUTS: Generates/updates ARCHITECTURE.md and Mermaid diagrams. Restricts C4
  diagrams to Context and Container levels. Audits are strictly for structural
  compliance with the provided documentation.
license: MIT
---

# WFC:ARCHITECTURE - Architecture Documentation

## Operational Rules

1. **Input Validation**: If no codebase path is provided or the path is empty, abort execution and request valid source code.
2. **Document Synchronization**:
    * When updating `ARCHITECTURE.md`, preserve existing human-authored context and rationale.
    * Update only the technical facts (dependencies, boundaries, tech stack) that have changed.
3. **C4 Diagram Constraints**:
    * Generate diagrams using standard Mermaid flowchart syntax (do not rely on `C4Context` plugin availability).
    * Limit generation to **System Context** and **Container** diagrams.
    * If a **Component** diagram is requested for a large repository (>50 files), aggregate classes into logical modules rather than diagramming individual files to prevent token overflow.
4. **ADR Standards**: When authoring Architecture Decision Records, default to the **Nygard** format (Title, Status, Context, Decision, Consequences) unless a specific template is provided in the request.
5. **Compliance Audits**: "Audit" strictly refers to comparing the directory structure and dependency imports against the layers defined in `ARCHITECTURE.md`. Do not evaluate code quality, style, or algorithmic complexity.
