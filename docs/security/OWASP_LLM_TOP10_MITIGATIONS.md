# WFC vs OWASP Top 10 for LLM Applications (2025)

How WFC's architecture, hook infrastructure, consensus review, and token management mitigate each risk.

**Coverage: 9/9 applicable risks mitigated with defense-in-depth.**

---

## LLM01: Prompt Injection

> Attacks targeting the input layer using crafted prompts to cause undesired model behavior.

| Defense | Mechanism |
|---|---|
| **94% prompt surface reduction** | Ultra-minimal prompts (200 tokens vs 3000) - less surface to inject into |
| **Strict JSON output schema** | Personas must return `{score, passed, summary, comments[]}` - injections can't break structure |
| **PreToolUse hook blocking** | `security_hook.py` blocks `eval()`, `new Function()`, `os.system()` in real-time |
| **Parameterized prompt building** | `token_manager.py` builds prompts from metadata, never concatenates untrusted strings into role definitions |

**Key files:** `wfc/scripts/personas/ultra_minimal_prompts.py`, `wfc/scripts/hooks/security_hook.py`

---

## LLM02: Sensitive Information Disclosure

> Risk of exposing personal data, credentials, and secrets through model outputs.

| Defense | Mechanism |
|---|---|
| **Hardcoded secret detection** | `patterns/security.json` catches `API_KEY=`, `PASSWORD=`, `PRIVATE_KEY=` patterns |
| **File references, not content** | `file_reference_prompts.py` sends paths to LLM, not raw source code containing secrets |
| **1K system prompt budget** | `token_manager.py` caps system prompts at 1,000 tokens - limits what can be disclosed |
| **Sensitive file blocking** | Pre-commit hooks detect `.env`, `credentials.json`, `id_rsa` before commit |

**Key files:** `wfc/scripts/hooks/patterns/security.json`, `wfc/scripts/personas/token_manager.py`

---

## LLM03: Supply Chain

> Vulnerabilities in external components including training datasets, adapters, and pre-trained models.

| Defense | Mechanism |
|---|---|
| **Hash-pinned lockfile** | `uv.lock` pins every package to exact version + SHA256 hash |
| **Near-zero runtime deps** | `pyproject.toml` has 0 required deps; tiktoken is optional |
| **Package manager detection** | `wfc-safeclaude` validates lockfiles exist before allowing install commands |
| **UV-only enforcement** | CLAUDE.md mandates `uv run` / `uv pip` - no unverified pip usage |

**Key files:** `uv.lock`, `pyproject.toml`, `wfc/skills/wfc-safeclaude/`

---

## LLM04: Data and Model Poisoning

> Attackers manipulate training or fine-tuning data to introduce vulnerabilities, biases, or backdoors.

| Defense | Mechanism |
|---|---|
| **Schema-validated personas** | `Persona.from_dict()` requires exact fields - malformed JSON rejected |
| **Enabled flag gating** | Only personas with `"enabled": true` are loaded into the registry |
| **Rule validation** | `config_loader.py` skips rules missing required `name` field, logs warnings |
| **Trusted sources only** | Personas loaded from `wfc/references/personas/` (checked into git), not external URLs |

**Key files:** `wfc/scripts/personas/persona_orchestrator.py`, `wfc/scripts/hooks/config_loader.py`

---

## LLM05: Improper Output Handling

> LLM outputs passed to downstream systems without proper validation or sanitization.

| Defense | Mechanism |
|---|---|
| **Confidence filtering** | Comments with `confidence < 80` filtered out of reports (`consensus.py`) |
| **Critical severity bypass** | Critical findings always surface regardless of confidence score |
| **JSON parse fallback** | `persona_executor.py` returns `score=5.0, passed=False` on malformed output - never trusts broken responses |
| **Path validation** | `_validate_output_path()` blocks writes to `/etc`, `/bin`, `~/.ssh`, `~/.aws` |

**Key files:** `wfc/scripts/orchestrators/review/consensus.py`, `wfc/scripts/personas/persona_executor.py`, `wfc/scripts/orchestrators/review/orchestrator.py`

---

## LLM06: Excessive Agency

> Granting agentic LLMs unprecedented tool access, permissions, and autonomy beyond intended use.

| Defense | Mechanism |
|---|---|
| **Real-time tool blocking** | `pretooluse_hook.py` intercepts every Write/Edit/Bash call, exits 2 to block |
| **6 blocked dangerous patterns** | `eval()`, `new Function()`, `os.system()`, `shell=True`, `rm -rf /`, `rm -rf ~` |
| **Tool allowlist generation** | `wfc-safeclaude` creates project-specific safe command lists |
| **Custom rule enforcement** | `.wfc/rules/*.md` let teams define additional restrictions without code |
| **Never push to main** | Architectural policy - WFC creates PRs, user must review and merge manually |
| **Fail-open on hook errors** | Hook bugs never block the user (always `exit 0` on internal errors) |

**Key files:** `wfc/scripts/hooks/pretooluse_hook.py`, `wfc/scripts/hooks/patterns/security.json`, `wfc/scripts/hooks/rule_engine.py`, `wfc/skills/wfc-safeclaude/`

---

## LLM07: System Prompt Leakage

> Exposure of sensitive information embedded in system prompts, including internal rules and credentials.

| Defense | Mechanism |
|---|---|
| **94% smaller prompts** | 200 tokens per persona vs 3,000 - 94% less content to leak |
| **No secrets in prompts** | Prompts contain only: identity + focus + output format. No credentials, no API keys |
| **File paths not content** | LLM receives `src/auth.py (142 lines)` not the actual source code |
| **1K token hard cap** | System prompt budget physically limited to 1,000 tokens in `TokenBudget` |

**Key files:** `wfc/scripts/personas/ultra_minimal_prompts.py`, `wfc/scripts/personas/token_manager.py`

---

## LLM08: Vector and Embedding Weaknesses

> Vulnerabilities in RAG pipelines affecting vector database security and embedding processes.

**Not applicable.** WFC uses no RAG, no vector stores, no embeddings. Persona selection is deterministic (tag matching, tech stack, panel diversity scoring).

---

## LLM09: Misinformation

> LLMs generating false but credible-sounding content through hallucinations, biases, and over-reliance.

| Defense | Mechanism |
|---|---|
| **Multi-agent consensus** | 4-5+ independent agents must all pass (score >= 7/10) |
| **Consensus area detection** | Issues mentioned by 3+ reviewers surfaced as high-confidence findings |
| **Divergent view flagging** | Score variance > 4.0 flagged as disagreement (likely hallucination) |
| **Unique insight capture** | Single-agent findings marked separately - reviewer can evaluate |
| **Relevance-weighted scoring** | Domain experts carry more weight; off-topic agents carry less |
| **Confidence threshold** | Low-confidence claims filtered by default (threshold=80) |

**Key files:** `wfc/scripts/orchestrators/review/consensus.py`, `wfc/scripts/personas/persona_executor.py`

---

## LLM10: Unbounded Consumption

> Uncontrolled resource usage causing performance degradation, downtime, or unexpected costs.

| Defense | Mechanism |
|---|---|
| **150K token hard budget** | `TokenBudget.total = 150000` - absolute ceiling per review |
| **Per-file allocation** | Budget divided evenly across files - no single file hogs resources |
| **Adaptive condensing** | Files over budget automatically condensed (keep signatures, truncate bodies) |
| **5-persona default cap** | `num_personas=5` x ~1.5K tokens = 7.5K total per review cycle |
| **Model tier selection** | Cost-aware: haiku for simple reviews, sonnet for standard, opus for complex |
| **10K response buffer** | Reserved response space prevents unbounded generation |

**Key files:** `wfc/scripts/personas/token_manager.py`, `wfc/scripts/orchestrators/review/orchestrator.py`

---

## Coverage Summary

| OWASP Risk | WFC Coverage | Primary Defense Layer |
|---|---|---|
| LLM01: Prompt Injection | **HIGH** | Minimal prompts + JSON schema + hook blocking |
| LLM02: Sensitive Info Disclosure | **HIGH** | Secret patterns + path refs + prompt caps |
| LLM03: Supply Chain | **HIGH** | Hash-pinned uv.lock + zero runtime deps |
| LLM04: Data Poisoning | **HIGH** | Schema validation + enabled gating + trusted sources |
| LLM05: Improper Output Handling | **HIGH** | Confidence filtering + parse fallback + path validation |
| LLM06: Excessive Agency | **HIGH** | Real-time PreToolUse hooks + allowlists + PR-only workflow |
| LLM07: System Prompt Leakage | **HIGH** | 94% surface reduction + no secrets + token caps |
| LLM08: Vector/Embedding | **N/A** | No embeddings used |
| LLM09: Misinformation | **HIGH** | Multi-agent consensus + divergence detection |
| LLM10: Unbounded Consumption | **HIGH** | Hard token budgets + adaptive condensing + model tiers |

---

## Architectural Principles

1. **Defense in Depth** - Multiple layers (patterns + rules + consensus + output validation)
2. **Fail-Safe Design** - Errors never block workflow (exit 0 on hook failures)
3. **Visible Enforcement** - All security decisions logged with reasons
4. **No Trust of LLM Output** - Multi-agent consensus required, single agent never sufficient
5. **Token Awareness** - Every persona controlled within budget, no runaway costs
6. **Zero External Dependencies** - Core functionality works with no external packages

---

*Reference: [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/)*

*Last updated: 2026-02-13*
