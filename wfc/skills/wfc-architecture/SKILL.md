---
name: wfc-architecture
description: >
  Generates and maintains software architecture documentation for systems with source
  code. Triggers on /wfc-architecture or explicit requests to: create/update an
  ARCHITECTURE.md; generate C4 diagrams (Context, Container, Component) in Mermaid;
  author an Architecture Decision Record (ADR) requiring a stated decision and
  rationale; or audit source code structure against an existing ARCHITECTURE.md.
  Requires a codebase path, plan document, or system description with named
  components and boundaries.

  NOT FOR: OpenAPI/Swagger specs or REST endpoint docs (use wfc-api); code review or
  static analysis; non-C4 diagrams (sequence, ER, flowcharts); READMEs, runbooks, or
  general docs; infrastructure-as-code; organizational or data architecture;
  architecture generation when no source material is provided.
license: MIT
---

# WFC:ARCHITECTURE - Architecture Documentation
