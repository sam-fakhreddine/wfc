# wfc-security

## What It Does

Performs a comprehensive security analysis of your codebase using STRIDE threat modeling (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege). It maps your attack surface and trust boundaries, scans dependencies for known CVEs, and detects hardcoded secrets or credentials. The output is a structured THREAT-MODEL.md that documents risks and mitigations suitable for audits or security reviews.

## When to Use It

- Starting a security-sensitive feature (auth, payments, data access)
- Preparing for a security audit or compliance review
- Onboarding a new module and want to understand its attack surface
- Suspecting hardcoded secrets or vulnerable dependencies in the codebase
- Performing a scheduled security health check before a release

## Usage

```bash
/wfc-security [options]
```

## Example

```bash
/wfc-security --stride
```

Output excerpt from THREAT-MODEL.md:

```markdown
## STRIDE Analysis

### S — Spoofing
| Threat | Target | Severity | Mitigation |
|--------|--------|----------|------------|
| JWT token forgery | /api/auth | HIGH | Verify signature with RS256; rotate secrets quarterly |

### T — Tampering
| Threat | Target | Severity | Mitigation |
|--------|--------|----------|------------|
| Request body manipulation | POST /api/orders | MEDIUM | Validate schema with Pydantic; reject unknown fields |

### E — Elevation of Privilege
| Threat | Target | Severity | Mitigation |
|--------|--------|----------|------------|
| Role bypass via crafted token | Admin endpoints | CRITICAL | Enforce RBAC server-side; never trust client claims |

## Attack Surface Summary
Entry points: 12 HTTP routes, 2 WebSocket channels, 1 internal cron job
Trust boundaries: Public internet → API gateway → Internal services → Database
```

## Options

| Flag | Description |
|------|-------------|
| (none) | Full analysis: STRIDE + attack surface + dependency scan + secrets scan |
| `--stride` | STRIDE threat modeling only |
| `--scan-deps` | Dependency vulnerability scan (CVE database) only |

## Integration

**Produces:**

- `THREAT-MODEL.md` — STRIDE analysis with mitigations
- `ATTACK-SURFACE.md` — Entry points, data flows, trust boundaries
- `VULNERABILITIES.md` — Dependency CVEs and secrets findings
- Security properties block suitable for appending to `PROPERTIES.md`

**Consumes:**

- Existing codebase (reads source files to map entry points and data flows)
- Dependency manifests (`pyproject.toml`, `package.json`, `go.mod`, etc.)

**Next step:** Feed the generated security properties into `/wfc-observe` to create alert rules for runtime violations, or use `/wfc-review` for code-level security review of specific files.
