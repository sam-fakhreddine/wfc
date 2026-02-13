# WFC Documentation

Organized reference documentation for the WFC framework.

## Sections

### [Architecture](architecture/)
System design, planning, and progressive disclosure patterns.
- [ARCHITECTURE.md](architecture/ARCHITECTURE.md) - System architecture and component design
- [PLANNING.md](architecture/PLANNING.md) - Architecture decisions and absolute rules
- [PROGRESSIVE_DISCLOSURE.md](architecture/PROGRESSIVE_DISCLOSURE.md) - Progressive disclosure pattern

### [Security](security/)
Security enforcement, safety policies, and OWASP compliance.
- [OWASP_LLM_TOP10_MITIGATIONS.md](security/OWASP_LLM_TOP10_MITIGATIONS.md) - OWASP LLM Top 10 coverage analysis
- [GIT_SAFETY_POLICY.md](security/GIT_SAFETY_POLICY.md) - Git safety and destructive action prevention
- [HOOKS_AND_TELEMETRY.md](security/HOOKS_AND_TELEMETRY.md) - PreToolUse hooks, security patterns, telemetry

### [Workflow](workflow/)
Development workflow and installation guides. See also [CONTRIBUTING.md](../CONTRIBUTING.md) in the repo root.
- [PR_WORKFLOW.md](workflow/PR_WORKFLOW.md) - Pull request workflow and branch strategy
- [WFC_BUILD.md](workflow/WFC_BUILD.md) - Build system and intentional vibe workflow
- [WFC_IMPLEMENTATION.md](workflow/WFC_IMPLEMENTATION.md) - Multi-agent parallel implementation engine
- [UNIVERSAL_INSTALL.md](workflow/UNIVERSAL_INSTALL.md) - Universal installer documentation

### [Quality](quality/)
Quality systems, review personas, and quality gates.
- [QUALITY_GATE.md](quality/QUALITY_GATE.md) - Quality gate configuration and thresholds
- [QUALITY_SYSTEM.md](quality/QUALITY_SYSTEM.md) - Quality system architecture
- [PERSONAS.md](quality/PERSONAS.md) - 56 expert review personas

### [Reference](reference/)
Technical reference, compliance, and registries.
- [AGENT_SKILLS_COMPLIANCE.md](reference/AGENT_SKILLS_COMPLIANCE.md) - Agent Skills spec compliance (17/17)
- [REGISTRY.md](reference/REGISTRY.md) - Documentation registry (human-readable)
- [REGISTRY.json](reference/REGISTRY.json) - Documentation registry (machine-readable)
- [PROJECT_INDEX.json](reference/PROJECT_INDEX.json) - Machine-readable project structure
- [DOC_REGISTRY_USAGE.md](reference/DOC_REGISTRY_USAGE.md) - How to use the doc registry
- [CLAUDE_INTEGRATION.md](reference/CLAUDE_INTEGRATION.md) - Claude Code integration guide
- [EARS.md](reference/EARS.md) - EARS requirements notation

### [Examples](examples/)
Working examples and demos.
- [ears_oauth2_example.md](examples/ears_oauth2_example.md) - EARS OAuth2 example
- [orchestrator_delegation_demo.md](examples/orchestrator_delegation_demo.md) - Orchestrator delegation demo
- [task_tool_demo.md](examples/task_tool_demo.md) - Task tool usage demo
