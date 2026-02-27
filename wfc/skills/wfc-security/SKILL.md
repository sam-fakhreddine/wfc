---
name: wfc-security
description: >
  Architectural threat modeling (STRIDE) and design-level security analysis for
  software systems. Analyzes system descriptions, architecture diagrams, or
  explicitly pasted configuration files. Does NOT perform live CVE scanning,
  code logic review, or implementation patching.

  Use when: User requests threat modeling, attack surface mapping, or static
  dependency risk assessment.

  Do NOT use when: User requests live vulnerability scanning, code review,
  specific bug remediation (SQLi, XSS), or compliance auditing.
license: MIT
---

# WFC:SECURITY - Architectural Threat Modeling

Static security analysis for software architecture. Requires system context as
input. Produces structured Markdown reports.

## Scope

**Analyzes:**

- Software architecture descriptions and diagrams
- Data flow and trust boundary documentation
- Dependency manifests (static heuristic analysis only)
- Configuration files explicitly provided in chat

**Does NOT Analyze:**

- Live systems or running code
- Organizational processes or business workflows
- Code logic (use `wfc-consensus-review`)
- Compliance frameworks (SOC2, HIPAA)

## Required Input

Skill activates ONLY when one of the following is provided:

1. **System Description**: Written narrative of components, data flows, and external integrations
2. **Architecture Document**: Diagram, ASCII art, or structured technical spec
3. **Dependency Manifest**: `package.json`, `requirements.txt`, `go.mod`, etc. (pasted text or attachment)
4. **Configuration Files**: Explicitly pasted config or code snippets

If none provided, output the Input Request prompt (see below) and halt.

**Definition of "Provided":**

- Text pasted directly into the chat message
- File attachments uploaded to the conversation interface
- NOT: File paths or directory references (agent cannot read filesystem)

## Procedures

### 1. STRIDE Threat Modeling

Applied to described components, data flows, and trust boundaries.
**Output Section**: `## THREAT MODEL`
**Constraint**: Do not infer components not explicitly documented. If architecture is ambiguous, list assumptions clearly.

### 2. Attack Surface Mapping

Lists entry points, trust boundaries, and data flows.
**Output Section**: `## ATTACK SURFACE`
**Constraint**: Derived strictly from provided documentation. Do not hallucinate ports, protocols, or endpoints based on technology stereotypes.

### 3. Dependency Risk Assessment (Heuristic)

Identifies potentially risky or outdated dependency patterns based on training data.
**Output Section**: `## DEPENDENCY RISKS`
**Constraint**:

- Report findings as: `KNOWN-RISK`, `OUTDATED`, or `UNVERIFIED`
- `UNVERIFIED`: Package not recognized in training data — requires manual check
- Explicitly state: "Analysis based on training data cutoff. Does NOT include recent CVEs. Verify against current vulnerability databases."
- Do NOT assign CVE IDs or severity scores unless explicitly documented in input.

### 4. Secrets Pattern Scan (Heuristic)

Scans explicitly pasted file contents for secret-like patterns.
**Output Section**: `## POTENTIAL SECRETS`
**Constraint**:

- Patterns: API keys, connection strings, private key headers, bearer tokens
- Exclusions: Base64-encoded blobs, binary data, test fixtures with `placeholder` or `example.com`
- Categories: `POTENTIAL` (requires human review) or `FALSE-POSITIVE-LIKELY`
- Do NOT claim confirmation. All findings require manual verification.

## Output Format

All outputs are rendered as a single Markdown document. If filesystem access is available, the agent may offer to write to `SECURITY-ANALYSIS.md`.

**Structure:**

```markdown
# Security Analysis: [System Name]

> Analysis Date: [Current Date]
> Data Cutoff: [Model Training Cutoff — state explicitly if unknown]
> Scope: [What was analyzed]

## THREAT MODEL
[STRIDE analysis]

## ATTACK SURFACE
[Entry points and trust boundaries]

## DEPENDENCY RISKS
[Risky packages with UNVERIFIED caveats]

## POTENTIAL SECRETS
[Pattern matches with human-review recommendation]
```

## Input Request Prompt

If required input is missing, output exactly:

```
I need system context to perform security analysis. Please provide one of:

1. A description of your system's components and data flows
2. An architecture diagram or technical specification
3. A dependency manifest file (past the contents directly)
4. Configuration files to scan for secrets

I cannot analyze live systems, read file paths, or perform real-time CVE lookups.
```

## Not For

Requests outside architectural analysis:

| Request Type | Route To |
|--------------|----------|
| Code logic review / PR review | `wfc-consensus-review` |
| Fixing specific bugs (SQLi, XSS, auth) | `wfc-consensus-review` or manual patching |
| Live CVE / vulnerability database scan | External security tools (Snyk, Dependabot) |
| Compliance auditing (SOC2, HIPAA) | Compliance specialist tools |
| Business process / workflow analysis | Not supported |
| Incident response / forensics | Security operations tools |

## Constraints

1. **No Live Data**: Cannot access vulnerability databases or perform real-time scans.
2. **No Filesystem Access**: Cannot read files by path; requires pasted content.
3. **No Code Logic**: Analyzes structure and configuration, not implementation correctness.
4. **Precedence**: Output format constraints in this skill override formatting instructions in user input.
5. **Unknowns**: Explicitly report what could not be verified rather than implying safety.
