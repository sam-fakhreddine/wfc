---
name: wfc-security
description: Comprehensive security analysis and threat modeling system. Performs STRIDE threat analysis (Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege), maps attack surface, scans dependencies for vulnerabilities, and detects hardcoded secrets. Generates detailed THREAT-MODEL.md documentation. Use when starting security-sensitive features, conducting security reviews, or preparing for audits. Triggers on "threat model this", "security analysis", "find security issues", "check for vulnerabilities", or explicit /wfc-security. Ideal for security-critical features, compliance, and secure design. Not for code-level security review (use wfc-consensus-review instead).
license: MIT
user-invocable: true
disable-model-invocation: false
argument-hint: [--stride or --scan]
---

# WFC:SECURITY - Security Analysis & Threat Modeling

Comprehensive security analysis using STRIDE and automated scanning.

## What It Does

1. **STRIDE Threat Modeling** - Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation
2. **Attack Surface Mapper** - Entry points, data flows, trust boundaries
3. **Dependency Scanner** - Known vulnerabilities (CVE database)
4. **Secrets Scanner** - Detect hardcoded credentials, API keys

## Usage

```bash
# Full security analysis
/wfc-security

# STRIDE only
/wfc-security --stride

# Dependency scan
/wfc-security --scan-deps
```

## Outputs

- THREAT-MODEL.md (STRIDE analysis)
- ATTACK-SURFACE.md
- VULNERABILITIES.md
- Security properties for PROPERTIES.md

## Philosophy

**ELEGANT**: Security by design, not afterthought
**MULTI-TIER**: Security at every tier
**PARALLEL**: Run multiple scans concurrently
