---
name: wfc-security
description: >
  Architectural security analysis and threat modeling for SOFTWARE SYSTEMS
  only. Requires a system description, architecture outline, or codebase
  context — produces no output and prompts if none is provided.

  Performs: STRIDE threat modeling; trust boundary and attack surface mapping;
  dependency manifest analysis (training-data knowledge, NOT a live CVE scan);
  hardcoded secrets pattern review across files explicitly provided.

  TRIGGERS: "threat model this", "STRIDE analysis", "attack surface mapping",
  "prepare for security audit", "security architecture review", "check
  dependency manifest", "scan for hardcoded secrets". Ambiguous phrases
  ("find security issues", "security analysis"): clarify whether subject is
  a system/architecture (route here) or file/code block (wfc-review).

  Not for: reviewing files or PRs for bugs; remediating vulnerabilities;
  secure code guidance; generic "find bugs"; physical security; requests
  with no input; re-running when output files exist (use --overwrite).
license: MIT

---

# WFC:SECURITY - Security Analysis & Threat Modeling

Architectural security analysis using STRIDE and structured review.
Operates on software systems only. Requires system context as input.

## Required Input

This skill produces no analysis without at least one of:

- A written system description (components, data flows, external integrations)
- An architecture diagram or document
- A dependency manifest file (package.json, requirements.txt, go.mod, etc.)
- Code or configuration files explicitly pasted into the conversation

If none of these are provided, the skill outputs a structured input-request
prompt and stops. It does not fabricate a system to analyze.

## What It Does

1. **STRIDE Threat Modeling** — Applied to the described system's components,
   data flows, and trust boundaries. Output: THREAT-MODEL.md with per-component
   threat enumeration.

2. **Attack Surface Mapping** — Derived strictly from provided architecture
   documentation. Lists entry points, trust boundaries, and data flows as
   described. Output: ATTACK-SURFACE.md.

3. **Dependency Manifest Analysis** — Reviews provided manifest files for
   dependency versions with known vulnerability associations. Based on
   training-data knowledge as of model cutoff date. NOT a live CVE scan.
   Output: VULNERABILITIES.md with explicit caveat stating data source
   and its limitations.

4. **Secrets Pattern Review** — Reviews files explicitly provided in the
   conversation for common secret patterns (API key formats, connection
   strings, private key PEM headers, bearer token assignments). Cannot
   scan files not provided. Categorizes findings as CONFIRMED, LIKELY,
   or REVIEW-REQUIRED. Applies common false-positive exclusions
   (placeholder strings, test fixture annotations). Output: appended to
   VULNERABILITIES.md under a dedicated Secrets section.

## Usage

```bash
# Full analysis (requires system description or architecture docs as input)
/wfc-security

# STRIDE threat model only — suppresses dependency and secrets steps entirely
/wfc-security --stride

# Dependency manifest analysis only — requires manifest file as input
/wfc-security --scan-deps

# Force overwrite of existing output files
/wfc-security --overwrite

# Scope to a single service in a monorepo
/wfc-security --scope services/auth
```

### Flag Semantics

| Flag | Effect |
|------|--------|
| `--stride
