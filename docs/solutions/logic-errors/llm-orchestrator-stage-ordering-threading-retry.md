---
title: LLM orchestrator — three bugs in wfc-skill-validator-llm (stage ordering, token tracking, rate-limit backoff)
module: skill_validator_llm
component: cli, api_client
tags: [orchestration, stage-sequencing, file-io, rate-limiting, retry-strategy, thread-local, token-tracking, anthropic-api]
category: logic-errors
date: 2026-02-26
severity: high
status: resolved
root_cause: Three independent logic errors in a 4-stage LLM pipeline — reports written after all stages ran (breaking cross-stage reads), no thread-local token accumulation, and a 1-2s retry backoff for a rate limit that needs 60s
---

## LLM Orchestrator — Stage Ordering, Token Tracking, Rate-Limit Backoff

Discovered during the first full 31-skill validation run on 2026-02-26.
All fixes are in `wfc/scripts/orchestrators/skill_validator_llm/` on branch
`claude/wfc-skill-validator-llm-phase2` (commit `f470f52`). 208 tests pass.

## Problem

**Symptoms:**

- Refinement reports (stage 4) were empty or referenced no prior findings
- No token usage or cost was printed per-skill or as a run total
- With 5 parallel workers, `429 RateLimitError` retried every 1-2 seconds and
  never recovered — the run had to be killed and restarted serially

**Environment:** `wfc-skill-validator-llm --all`, 31 skills, `_MAX_WORKERS=5`,
Anthropic org-level limit of 8,000 output tokens/minute

## Root Causes

### Bug 1 — Write-After-Return (stage ordering)

`_validate_skill()` ran all 4 stages and only called `write_stage_report()` at
the end of the function (via its return value). The refinement stage calls
`find_latest_stage_report()` at its *start* to read discovery/logic/edge_case
reports. Since those writes hadn't happened yet, refinement found nothing.

### Bug 2 — Missing Token Accumulation

No mechanism existed to track input/output tokens across API calls.
`ThreadPoolExecutor` workers ran independently with no shared or per-thread
accumulator, so cost was invisible during and after the run.

### Bug 3 — Wrong Retry Delay for Rate Limits

`retry_with_backoff()` used `base_delay * (2**attempt)` (1s, 2s, 4s) for
*all* exception types. Anthropic's 8K output tokens/minute org-level rate
limit clears on a ~60s rolling window. A 1-2s retry immediately re-hit the
limit and burned through all retries without recovering.

**Bonus:** `_MAX_WORKERS = 2` was also too low for 31 skills; bumped to 5.

## Solution

### Fix 1 — Write immediately after each stage (cli.py)

**Before** (--all path):

```python
def _run_one(sd: Path) -> tuple[str, list[Path]]:
    report = _validate_skill(sd)               # runs all 4 stages, writes nothing
    path = write_stage_report(...)             # writes only final result
    return sd.name, [path]
```

**After** — loop stages directly in `_run_one()`, write after each:

```python
def _run_one(sd: Path) -> tuple[str, list[Path], float | None, dict[str, int]]:
    reset_accumulated_usage()
    written: list[Path] = []
    stage_results: dict[str, str] = {}

    # IMPORTANT: define dict locally, not at module level
    # Module-level dicts capture original references before mock.patch takes effect
    _STAGE_RUNNERS = {
        "discovery": run_discovery,
        "logic": run_logic,
        "edge_case": run_edge_case,
        "refinement": run_refinement,
    }

    for stage in stages_to_run:
        runner = _STAGE_RUNNERS[stage]
        report = retry_with_backoff(lambda r=runner: r(sd, offline=args.offline))
        stage_results[stage] = report
        path = write_stage_report(
            skill_name=sd.name, stage=stage,
            report_content=report, repo=repo, branch=branch,
        )
        written.append(path)

    health_score = _extract_health_score(stage_results.get("refinement", "")) or None
    usage = get_accumulated_usage()
    return sd.name, written, health_score, usage
```

For the single-skill path, add an `after_stage` callback to `_validate_skill()`:

```python
def _validate_skill(
    sd: Path,
    after_stage: Callable[[str, str], None] | None = None,
) -> dict[str, str]:
    for stage, runner in _STAGE_RUNNERS.items():
        report = runner(sd, offline=args.offline)
        if after_stage:
            after_stage(stage, report)
    ...
```

### Fix 2 — Thread-local token accumulation (api_client.py)

```python
import threading

_usage_local = threading.local()

def get_accumulated_usage() -> dict[str, int]:
    return {
        "input_tokens": getattr(_usage_local, "input_tokens", 0),
        "output_tokens": getattr(_usage_local, "output_tokens", 0),
    }

def reset_accumulated_usage() -> None:
    _usage_local.input_tokens = 0
    _usage_local.output_tokens = 0
```

Inside `call_api()`, after receiving a response:

```python
try:
    _usage_local.input_tokens = (
        getattr(_usage_local, "input_tokens", 0) + response.usage.input_tokens
    )
    _usage_local.output_tokens = (
        getattr(_usage_local, "output_tokens", 0) + response.usage.output_tokens
    )
except AttributeError:
    pass  # best-effort; don't break if usage missing
```

Print usage in `_run_one()` and aggregate for final summary in cli.py:

```python
# Per-skill
print(f"OK  {skill_name}: 4 stage(s) written  [in={in_tok:,} out={out_tok:,}]")

# After all skills
cost = (total_input * 3 + total_output * 15) / 1_000_000  # claude-sonnet-4-6
print(f"\nTotal tokens — input: {total_input:,}  output: {total_output:,}  (~${cost:.4f})")
```

### Fix 3 — Rate-limit-specific backoff (cli.py)

**Before:**

```python
delay = base_delay * (2**attempt) + random.uniform(0, 0.5)  # 1s, 2s, 4s for all errors
```

**After:**

```python
if "RateLimit" in type(exc).__name__:
    delay = 60.0 + random.uniform(0, 10.0)   # flat 60-70s for Anthropic 429
else:
    delay = base_delay * (2**attempt) + random.uniform(0, 0.5)  # exponential for timeouts
```

Also increase workers:

```python
_MAX_WORKERS = 5  # was 2
```

## Prevention

### Bug 1 — Pipeline stage ordering

**Test case:** Verify each stage's output is on disk before the next stage runs:

```python
def test_refinement_reads_prior_reports_on_disk():
    reports_written = []
    def after_stage(stage, content):
        reports_written.append(stage)
    _validate_skill(skill_dir, after_stage=after_stage)
    # All 4 stages should have written before refinement returned
    assert reports_written == ["discovery", "logic", "edge_case", "refinement"]
```

**Principle:** "Write early, read late" — persist each stage's output to durable
storage immediately after it completes, not after the entire pipeline returns.
This also enables fault-tolerance: a failed run can be resumed from the last
successful stage.

### Bug 2 — Token observability

**Test case:** Verify threading.local accumulation resets between skills:

```python
def test_token_accumulator_is_thread_local():
    reset_accumulated_usage()
    # simulate two API calls in same thread
    # assert accumulated totals match sum of both calls
```

**Principle:** Any orchestrator making paid API calls must surface cost per
unit of work (per-skill, per-stage), not just at the end of a long run.
Use `threading.local()` for per-worker accumulators in `ThreadPoolExecutor`
contexts; global state causes races.

### Bug 3 — Rate-limit backoff

**Test case:**

```python
def test_rate_limit_error_sleeps_60s():
    class FakeRateLimitError(Exception): pass
    FakeRateLimitError.__name__ = "RateLimitError"
    sleep_calls = []
    with mock.patch("time.sleep", side_effect=sleep_calls.append):
        retry_with_backoff(lambda: (_ for _ in ()).throw(FakeRateLimitError()))
    assert sleep_calls[0] >= 60.0
```

**Principle:** Match backoff strategy to the *error type's recovery time*:

- `RateLimitError` (429) → fixed 60s (rolling window)
- `APITimeoutError` → exponential 1-2-4s (transient load)
- `APIConnectionError` → exponential with jitter

## Related

- `docs/workflow/WFC_IMPLEMENTATION.md` — multi-stage agent workflow patterns
- `docs/examples/orchestrator_delegation_demo.md` — orchestrator delegation patterns
- `docs/API_CONTRACT.md` — rate limiting and retry-after headers
