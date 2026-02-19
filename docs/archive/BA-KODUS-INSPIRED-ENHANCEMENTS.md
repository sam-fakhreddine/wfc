# Business Analysis: Kodus AI-Inspired Enhancements for WFC

**Document**: BA-KODUS-INSPIRED-ENHANCEMENTS
**Version**: 1.0
**Date**: 2026-02-17
**Author**: Claude (competitive analysis agent)
**Status**: DRAFT — Awaiting WFC planning workflow
**Source**: Deep analysis of [Kodus AI](https://github.com/kodus-ai/kodus-ai) open-source codebase

---

## 1. Executive Summary

Kodus AI is an open-source AI code review platform that has solved several problems WFC currently faces. After deep analysis of their architecture (139 tool uses across their codebase), this document identifies **5 high-leverage features** WFC should adopt, prioritized by impact-to-effort ratio.

**Key insight**: Kodus's primary advantage over WFC is not in review quality (WFC's 5-agent consensus is more mathematically rigorous) but in **false-positive reduction** (multi-layer validation), **evaluation rigor** (dual-judge benchmarking), and **structural code understanding** (AST-based analysis). These are gaps WFC can close.

---

## 2. Current State Analysis

### 2.1 WFC Strengths (Keep)

| Capability | WFC Implementation | Assessment |
|---|---|---|
| Consensus scoring | CS algorithm with MPR, 5 fixed reviewers | Best-in-class, mathematically sound |
| Finding deduplication | SHA-256 fingerprint with ±3 line tolerance | Solid, unique approach |
| Token management | Budget system (S/M/L/XL) | Effective |
| Agent Skills compliance | 20/20 validated skills | Mature |
| TDD workflow | RED-GREEN-REFACTOR with confidence checking | Comprehensive |
| Progressive disclosure | Load-on-demand architecture | Well-designed |

### 2.2 WFC Gaps (Fix)

| Gap | Current State | Impact |
|---|---|---|
| Finding validation | Dedup only (catches dupes, not hallucinations) | High false-positive rate on LLM-generated findings |
| Code structure analysis | Pure LLM analysis (no AST) | Misses structural bugs, can't verify call graphs |
| Evaluation framework | `review_benchmark.py` with basic precision/recall | No multi-model comparison, no dual-judge |
| Observability | Zero production telemetry | Blind to real-world performance |
| Multi-model support | Single model (Claude) per review | Overpaying for tasks that don't need Opus |

---

## 3. Feature Requirements

### FEATURE 1: Finding Validation Pipeline (Priority: CRITICAL)

#### 3.1.1 Problem Statement

WFC's current review flow is: `5 Reviewers → Fingerprint Dedup → Consensus Score → Report`. Deduplication merges identical findings but **does not validate whether findings are real**. LLMs hallucinate code review findings — they report bugs in code that doesn't exist, flag patterns that are actually correct, and misread control flow. Kodus solved this with a 4-layer validation pipeline that reduced false positives dramatically.

#### 3.1.2 Requirements

**MUST HAVE**:

1. **Finding Validator module** (`wfc/scripts/orchestrators/review/finding_validator.py`)
   - Accepts `list[DeduplicatedFinding]` from Fingerprinter
   - Returns `list[ValidatedFinding]` with validation status and confidence adjustment
   - Runs AFTER deduplication, BEFORE consensus scoring
   - New pipeline: `5 Reviewers → Dedup → **Validate** → Consensus Score → Report`

2. **Validation Layer 1: Structural Verification**
   - Parse the target file and verify the finding references real code
   - Confirm the reported line numbers contain relevant code (not comments/whitespace)
   - Verify referenced functions/classes/variables actually exist in scope
   - Implementation: Use Python `ast` module for `.py` files, `tree-sitter` bindings for JS/TS/Go
   - If structural verification fails → mark finding as `UNVERIFIED`, reduce confidence by 50%

3. **Validation Layer 2: LLM Cross-Check (Safeguard Pass)**
   - Send each finding + the actual code snippet to a DIFFERENT model instance
   - Prompt: "Given this code and this finding, is the finding valid? Reply YES/NO with reasoning."
   - Use a smaller/cheaper model (Haiku) for this validation to keep costs down
   - If cross-check says NO → mark finding as `DISPUTED`, reduce confidence by 70%

4. **Validation Layer 3: Historical Pattern Match**
   - Query the Knowledge System (existing `KnowledgeRetriever`) for similar past findings
   - If this exact pattern was previously rejected by a human reviewer → mark as `HISTORICALLY_REJECTED`
   - If this exact pattern was previously accepted → boost confidence by 20%
   - Uses existing KNOWLEDGE.md infrastructure (no new storage needed)

5. **Validation statuses**: `VERIFIED`, `UNVERIFIED`, `DISPUTED`, `HISTORICALLY_REJECTED`
   - Consensus score calculation should weight by validation status
   - `VERIFIED` findings: full weight (1.0x)
   - `UNVERIFIED` findings: reduced weight (0.5x)
   - `DISPUTED` findings: minimal weight (0.2x)
   - `HISTORICALLY_REJECTED` findings: excluded from CS calculation

**SHOULD HAVE**:

1. **Validation metrics** tracked per review:
   - `findings_before_validation: int`
   - `findings_after_validation: int`
   - `false_positive_rate: float` (disputed + rejected / total)
   - Logged in review report

2. **Bypass flag**: `--skip-validation` to disable for speed when iterating quickly

**COULD HAVE**:

1. **ML-based filter** (future): Train a classifier on accepted/rejected findings over time. Kodus uses this as their first filter layer. Requires collecting labeled data first.

#### 3.1.3 Integration Points

- **Input**: `Fingerprinter.deduplicate()` output → `FindingValidator.validate()`
- **Output**: `FindingValidator.validate()` → `ConsensusScore.calculate()`
- **Modified files**:
  - `wfc/scripts/orchestrators/review/orchestrator.py` (add validation step between dedup and scoring)
  - `wfc/scripts/orchestrators/review/consensus_score.py` (accept validation weight multiplier)
  - New: `wfc/scripts/orchestrators/review/finding_validator.py`
- **Tests**: `tests/test_finding_validator.py`

#### 3.1.4 Acceptance Criteria

- [ ] All existing review tests pass (zero regression)
- [ ] Validator catches findings that reference non-existent code (structural verification)
- [ ] Validator reduces confidence on LLM-disputed findings
- [ ] Historical rejection works with existing KNOWLEDGE.md
- [ ] Review report includes validation metrics
- [ ] `--skip-validation` flag works
- [ ] Performance: validation adds < 5 seconds per review for files < 500 lines

---

### FEATURE 2: AST Hybrid Analysis (Priority: HIGH)

#### 3.2.1 Problem Statement

WFC reviews are purely LLM-based — reviewers receive file content as text and reason about it. This means reviews miss structural properties that are trivially detectable via AST parsing: unused imports, unreachable code, type mismatches, cyclomatic complexity, dependency cycles. Kodus uses a dedicated AST microservice with graph-based impact analysis alongside LLM review. WFC should add lightweight AST pre-analysis that enriches the context given to reviewers.

#### 3.2.2 Requirements

**MUST HAVE**:

1. **AST Analyzer module** (`wfc/scripts/orchestrators/review/ast_analyzer.py`)
   - Accepts a list of file paths
   - Returns structured analysis per file: functions, classes, imports, complexity metrics, call graph
   - Supports Python (via `ast` stdlib), TypeScript/JavaScript (via `tree-sitter-javascript`), Go (via `tree-sitter-go`)
   - Falls back gracefully to empty analysis for unsupported languages

2. **Pre-analysis enrichment** in the review pipeline:
   - AST analysis runs BEFORE reviewer task preparation
   - Results injected into each reviewer's context as structured metadata
   - New pipeline: `**AST Analyze** → Prepare Review Tasks → 5 Reviewers → Dedup → Validate → CS`
   - Reviewers receive: file content + AST metadata (function signatures, complexity, dependency list)

3. **Structural findings** generated directly from AST (no LLM needed):
   - Unused imports
   - Unreachable code after return/raise
   - Functions exceeding cyclomatic complexity threshold (default: 15)
   - Deeply nested code (> 4 levels)
   - These are injected as pre-verified findings (validation status = `VERIFIED`)
   - Severity: configurable, default LOW for style, MEDIUM for complexity, HIGH for unreachable code

4. **Impact graph** for changed files:
   - Given a diff, identify which functions changed
   - Trace callers of those functions (1 level deep)
   - Include caller context in reviewer prompts so they can assess blast radius
   - This is what Kodus calls "graph-based impact analysis"

**SHOULD HAVE**:

1. **Language detection** from file extension (already partially exists in hooks `_checkers/`)
   - Reuse `wfc/scripts/hooks/_checkers/` infrastructure for language detection
   - AST parser selection based on detected language

2. **Complexity report** in review output:
   - Per-function cyclomatic complexity
   - Per-file aggregate complexity
   - Highlighted if complexity increased from the diff

**COULD HAVE**:

1. **Cross-file dependency graph** — full project-level import graph. Expensive to compute, defer to later.

#### 3.2.3 Integration Points

- **Input**: `ReviewRequest.files` → `ASTAnalyzer.analyze()`
- **Output**: `ASTAnalysis` metadata → `ReviewerEngine.prepare_review_tasks()` (enriched context)
- **Output**: Structural findings → `Fingerprinter` (as pre-verified findings)
- **Modified files**:
  - `wfc/scripts/orchestrators/review/orchestrator.py` (add AST pre-analysis step)
  - `wfc/scripts/orchestrators/review/reviewer_engine.py` (accept AST metadata in task preparation)
  - New: `wfc/scripts/orchestrators/review/ast_analyzer.py`
- **Dependencies**: `tree-sitter` (optional, for JS/TS/Go support). Python `ast` is stdlib.
- **Tests**: `tests/test_ast_analyzer.py`

#### 3.2.4 Acceptance Criteria

- [ ] Python AST analysis extracts functions, classes, imports, complexity
- [ ] Structural findings (unused imports, unreachable code) generated without LLM
- [ ] Impact graph traces callers of changed functions (1 level)
- [ ] Reviewer prompts include AST metadata
- [ ] Graceful fallback for unsupported languages (no crash, empty metadata)
- [ ] tree-sitter is optional dependency (Python ast works without it)
- [ ] Performance: AST analysis < 2 seconds for files < 1000 lines

---

### FEATURE 3: Evaluation & Benchmarking Framework (Priority: HIGH)

#### 3.3.1 Problem Statement

WFC has `review_benchmark.py` with basic precision/recall/F1 metrics but no systematic evaluation of review quality across models, languages, or finding types. Kodus built a dual-judge evaluation framework using promptfoo with 80 curated examples across 4 languages, benchmarking 9 models with two independent judges. WFC needs this level of rigor to prove and improve review quality.

#### 3.3.2 Requirements

**MUST HAVE**:

1. **Curated evaluation dataset** (`wfc/scripts/benchmark/eval_dataset/`)
   - Minimum 40 examples (10 per language: Python, TypeScript, Go, Java)
   - Each example: source file + known findings (ground truth) + expected severity
   - Examples cover: true positives (real bugs), true negatives (clean code), false-positive traps (patterns that look like bugs but aren't)
   - Format: JSON with schema validation

2. **Dual-judge evaluation** (`wfc/scripts/benchmark/eval_judge.py`)
   - After WFC reviews an eval example, two independent LLM judges score the review
   - Judge 1: Claude (Sonnet or Haiku — must be different from the reviewer model)
   - Judge 2: Configurable (default: same model, different temperature; stretch: GPT via API)
   - Judges evaluate: precision (were reported findings real?), recall (were real bugs found?), severity accuracy (was severity correctly assigned?)
   - Inter-judge agreement metric (Cohen's Kappa or simple agreement %)

3. **Automated eval runner** (`wfc/scripts/benchmark/eval_runner.py`)
   - Runs full WFC review pipeline against eval dataset
   - Collects: findings, consensus scores, validation metrics
   - Submits to dual judges
   - Produces aggregate report: precision, recall, F1, severity accuracy, false-positive rate
   - CLI: `wfc benchmark run` / `make benchmark-eval`

4. **Regression detection**:
   - Store eval results in `wfc/scripts/benchmark/eval_results/` (gitignored)
   - Compare current run against previous baseline
   - Alert if precision drops > 5% or recall drops > 10%
   - Baseline stored as JSON (committed to repo)

**SHOULD HAVE**:

1. **Per-reviewer breakdown**: Which of the 5 reviewers contributes most true positives vs false positives?
   - Helps identify which reviewer prompts need tuning
   - Output: per-reviewer precision/recall table

2. **Model comparison mode**: Run the same eval across different models (Opus, Sonnet, Haiku)
   - Output: cost vs quality tradeoff table
   - Informs multi-model routing decisions (Feature 5)

**COULD HAVE**:

1. **promptfoo integration** — Kodus uses promptfoo as the eval harness. Consider adopting it for standardized eval infrastructure.

#### 3.3.3 Integration Points

- **Input**: Eval dataset (JSON files with ground truth)
- **Output**: Eval report (precision, recall, F1, per-reviewer breakdown)
- **Modified files**:
  - `wfc/scripts/benchmark/review_benchmark.py` (extend or replace)
  - New: `wfc/scripts/benchmark/eval_judge.py`
  - New: `wfc/scripts/benchmark/eval_runner.py`
  - New: `wfc/scripts/benchmark/eval_dataset/` (directory)
- **Tests**: `tests/test_eval_framework.py`

#### 3.3.4 Acceptance Criteria

- [ ] Eval dataset has >= 40 examples across 4 languages
- [ ] Dual-judge evaluation produces agreement metrics
- [ ] Eval runner produces aggregate precision/recall/F1
- [ ] Regression detection alerts on quality drops
- [ ] Per-reviewer breakdown available
- [ ] `make benchmark-eval` works end-to-end
- [ ] Eval results are reproducible (deterministic with fixed seeds)

---

### FEATURE 4: Production Observability (Priority: MEDIUM)

#### 3.4.1 Problem Statement

WFC has zero production telemetry. When a review takes too long, produces bad results, or fails silently, there is no visibility. Kodus runs Sentry (error tracking) + OpenTelemetry (distributed tracing) + Pyroscope (continuous profiling) + PostHog (product analytics) + LangChain tracing (LLM call logging). WFC needs at minimum OpenTelemetry tracing to understand real-world performance.

#### 3.4.2 Requirements

**MUST HAVE**:

1. **OpenTelemetry integration** (`wfc/scripts/telemetry/`)
   - Instrument key review pipeline operations as spans:
     - `wfc.review` (root span)
     - `wfc.review.ast_analysis`
     - `wfc.review.prepare_tasks`
     - `wfc.review.execute_reviewers`
     - `wfc.review.deduplicate`
     - `wfc.review.validate`
     - `wfc.review.consensus_score`
     - `wfc.review.report`
   - Each span records: duration, input size (lines/tokens), output size (findings count)
   - Traces exportable to any OTLP-compatible backend (Jaeger, Honeycomb, Grafana Tempo)

2. **Structured logging** with correlation IDs:
   - Every review gets a unique `review_id` (UUID)
   - All log messages within that review include the `review_id`
   - Log format: JSON structured (machine-parseable)
   - Levels: existing `logging` module, but with structured output option

3. **Metrics collection**:
   - `wfc.review.duration_seconds` (histogram)
   - `wfc.review.findings_count` (counter, by severity)
   - `wfc.review.consensus_score` (gauge)
   - `wfc.review.validation.false_positive_rate` (gauge)
   - `wfc.review.tokens_used` (counter, by reviewer)
   - Exportable via OpenTelemetry Metrics API

4. **Opt-in by default**: Telemetry DISABLED unless explicitly enabled
   - Config: `WFC_TELEMETRY_ENABLED=true` environment variable
   - Endpoint: `WFC_OTLP_ENDPOINT=http://localhost:4317`
   - Zero overhead when disabled (no-op spans/metrics)

**SHOULD HAVE**:

1. **LLM call tracing**: Log model, prompt length, response length, latency for each reviewer call
   - Helps identify slow reviewers or token-heavy prompts

2. **Dashboard template**: Grafana JSON dashboard for WFC metrics (committed as a reference)

**COULD HAVE**:

1. **Pyroscope continuous profiling** for CPU-heavy operations (AST parsing, fingerprinting)
2. **PostHog-style product analytics** (which skills are used most, review pass rates over time)

#### 3.4.3 Integration Points

- **Modified files**:
  - `wfc/scripts/orchestrators/review/orchestrator.py` (add span instrumentation)
  - New: `wfc/scripts/telemetry/__init__.py`
  - New: `wfc/scripts/telemetry/tracing.py`
  - New: `wfc/scripts/telemetry/metrics.py`
- **Dependencies**: `opentelemetry-api`, `opentelemetry-sdk` (optional, only when enabled)
- **Tests**: `tests/test_telemetry.py`

#### 3.4.4 Acceptance Criteria

- [ ] Review pipeline instrumented with OpenTelemetry spans
- [ ] Structured JSON logging with review_id correlation
- [ ] Key metrics collected (duration, findings, score, tokens)
- [ ] Telemetry disabled by default, opt-in via env var
- [ ] Zero performance overhead when disabled
- [ ] Traces visible in Jaeger/OTLP-compatible backend when enabled
- [ ] All existing tests pass (no import errors when otel not installed)

---

### FEATURE 5: Multi-Model Review Routing (Priority: LOW)

#### 3.5.1 Problem Statement

WFC sends all 5 reviewers to the same Claude model. Kodus routes different analysis tasks to different models based on their strengths: Deepseek V3 for deep reasoning, GPT-4O for general analysis, Gemini 2.5 Flash for speed. This is both cost-efficient and quality-optimized. WFC should support routing reviewers to different models.

#### 3.5.2 Requirements

**MUST HAVE**:

1. **Model routing configuration** (`wfc/config/model_routing.json`):

   ```json
   {
     "default": "claude-sonnet-4-5-20250929",
     "reviewers": {
       "security": "claude-opus-4-6",
       "correctness": "claude-sonnet-4-5-20250929",
       "performance": "claude-sonnet-4-5-20250929",
       "maintainability": "claude-haiku-4-5-20251001",
       "reliability": "claude-opus-4-6"
     },
     "validation_cross_check": "claude-haiku-4-5-20251001"
   }
   ```

   - Security and reliability use strongest model (highest stakes)
   - Maintainability uses cheapest model (style checks don't need Opus)
   - Cross-check validation uses cheapest model (binary yes/no)

2. **Model parameter in reviewer task specs**:
   - `ReviewerEngine.prepare_review_tasks()` includes model recommendation per task
   - Orchestrator passes model hint to Task tool via `model` parameter
   - Fallback to default model if specified model is unavailable

3. **Cost tracking** per review:
   - Estimated cost based on model × tokens
   - Reported in review summary
   - Helps users understand cost impact of model routing choices

**SHOULD HAVE**:

1. **Auto-routing based on diff complexity**:
   - Small diffs (< 50 lines): use Haiku for all reviewers
   - Medium diffs (50-500 lines): use Sonnet for all
   - Large diffs (> 500 lines): use Opus for security/reliability, Sonnet for rest
   - Override with explicit config

**COULD HAVE**:

1. **Non-Claude model support** (OpenAI, Deepseek, Gemini) via API adapters
   - Requires standardizing the reviewer prompt/response format
   - Significant effort, defer to much later

#### 3.5.3 Integration Points

- **Modified files**:
  - `wfc/scripts/orchestrators/review/reviewer_engine.py` (model parameter in task specs)
  - `wfc/scripts/orchestrators/review/orchestrator.py` (pass model to Task tool)
  - New: `wfc/config/model_routing.json`
  - New: `wfc/scripts/orchestrators/review/model_router.py`
- **Tests**: `tests/test_model_router.py`

#### 3.5.4 Acceptance Criteria

- [ ] Model routing config loads and validates
- [ ] Each reviewer task spec includes model parameter
- [ ] Cost tracking reported in review summary
- [ ] Fallback to default model works
- [ ] Existing reviews work unchanged with default config

---

## 4. Implementation Priority & Sequencing

```
Phase 1 (Critical Path):
  ├── FEATURE 1: Finding Validation Pipeline ──────────── [CRITICAL, ~3-5 tasks]
  │   └── Directly reduces false positives (biggest user pain point)
  │
  └── FEATURE 2: AST Hybrid Analysis ─────────────────── [HIGH, ~3-4 tasks]
      └── Feeds into validation (structural verification layer)
      └── Provides pre-verified findings (free accuracy boost)

Phase 2 (Quality Assurance):
  └── FEATURE 3: Eval & Benchmarking Framework ────────── [HIGH, ~3-4 tasks]
      └── Must exist before we can prove Phase 1 improved quality
      └── Baseline BEFORE Phase 1, measure AFTER

Phase 3 (Operational Maturity):
  ├── FEATURE 4: Production Observability ─────────────── [MEDIUM, ~2-3 tasks]
  │   └── Needed for production monitoring, not blocking
  │
  └── FEATURE 5: Multi-Model Routing ──────────────────── [LOW, ~2-3 tasks]
      └── Cost optimization, nice-to-have
```

**Recommended order**: Start with Feature 3 (eval framework) to establish a quality baseline, THEN implement Features 1 and 2, THEN re-run eval to prove improvement. Features 4 and 5 are independent and can be done anytime.

**Total estimated scope**: 14-19 tasks across 5 features.

---

## 5. Dependencies & Risks

### 5.1 Dependencies

| Dependency | Feature(s) | Risk | Mitigation |
|---|---|---|---|
| `tree-sitter` Python bindings | Feature 2 | Optional dep, may have build issues | Python `ast` as fallback, tree-sitter optional |
| `opentelemetry-api/sdk` | Feature 4 | Optional dep, adds install complexity | Zero-overhead no-op when not installed |
| LLM API access for cross-check | Feature 1 | Adds API calls = cost + latency | Use cheapest model (Haiku), make skippable |
| Eval dataset curation | Feature 3 | Manual effort to create 40+ examples | Start with 20, expand over time |

### 5.2 Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Validation adds too much latency | Medium | Medium | Structural checks are fast; LLM cross-check is optional/async |
| AST parsing breaks on malformed code | Medium | Low | Wrap in try/except, fall back to LLM-only review |
| Eval dataset biased toward Python | High | Medium | Enforce language distribution in dataset schema |
| Multi-model routing breaks Task tool | Low | High | Keep single-model as default, routing is opt-in |

---

## 6. Non-Functional Requirements

| Requirement | Target | Measurement |
|---|---|---|
| Review latency increase (with validation) | < 30% increase | Benchmark before/after |
| AST analysis time per file | < 2 seconds for < 1000 lines | Automated benchmark |
| Eval framework run time | < 10 minutes for full dataset | CI measurement |
| Telemetry overhead (disabled) | Zero | Benchmark with/without |
| Telemetry overhead (enabled) | < 5% CPU | Profiling |
| Test coverage for new code | > 85% | `make test-coverage` |
| Zero regression on existing tests | 830+ tests passing | CI gate |

---

## 7. Success Metrics

Post-implementation, measure these against baseline:

1. **False positive rate**: Target < 15% (measure via eval framework)
2. **Recall for known bugs**: Target > 80% (measure via eval dataset)
3. **Review precision**: Target > 85% (findings that are real / total findings)
4. **Severity accuracy**: Target > 70% (correct severity / total findings)
5. **Cost per review**: Track via model routing, target 30% reduction with smart routing
6. **User satisfaction**: Fewer "this finding is wrong" complaints in PR comments

---

## 8. Out of Scope

The following Kodus features were analyzed but deemed NOT worth adopting:

1. **Full microservice architecture** — Kodus runs NestJS + multiple microservices. WFC's monolithic skill architecture is simpler and better suited to CLI-first design.
2. **GitHub/GitLab app integration** — Kodus runs as a GitHub App with webhook handlers. WFC operates locally via Claude Code. Different deployment model.
3. **ML fine-tuning pipeline** — Kodus trains models on accepted/rejected findings. Requires significant labeled data that WFC doesn't have yet. Revisit after eval framework generates enough data.
4. **Multi-tenant SaaS infrastructure** — Kodus has organization/team management. WFC is single-user.
5. **Pyroscope continuous profiling** — Overkill for a CLI tool. Standard benchmarking is sufficient.

---

## 9. Glossary

| Term | Definition |
|---|---|
| **CS** | Consensus Score — WFC's mathematical scoring algorithm for review findings |
| **MPR** | Minority Protection Rule — elevates critical findings even if only one reviewer flags them |
| **AST** | Abstract Syntax Tree — parsed structural representation of source code |
| **OTLP** | OpenTelemetry Protocol — standard for exporting telemetry data |
| **DLQ** | Dead Letter Queue — storage for failed/unprocessable tasks |
| **Dual-Judge** | Two independent LLM evaluators scoring the same review for reliability |
| **Finding Validation** | Post-dedup process to verify findings are real, not hallucinated |

---

*This document is designed as input for `/wfc-plan`. Run the planning workflow against this BA to generate TASKS.md with formal properties and TDD test plans.*
