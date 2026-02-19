# wfc-python

## What It Does

`wfc-python` defines Python-specific development standards for all WFC Python projects. It inherits every universal rule from `wfc-code-standards` (three-tier architecture, SOLID, DPS dimensions 1-11, testing philosophy) and adds Python 3.12+ syntax requirements, the UV toolchain as the exclusive package manager, `black` as the mandatory formatter, `mypy --strict` type checking, and a curated preferred library stack: `structlog`, `orjson`, `httpx`, `pydantic`, `FastAPI`, `tenacity`, `joblib`, `fire`, and `faker`. Like `wfc-code-standards`, this skill is a reference consumed by agents during build, implementation, and review — not invoked directly by users.

## When to Use It

- You are writing or reviewing Python code and want the authoritative list of standards, preferred libraries, and patterns WFC enforces
- An agent flagged a Python-specific violation (e.g., using `requests` instead of `httpx`, `print()` instead of `structlog`, or `import json` instead of `orjson`) and you want context
- You are scaffolding a new Python project and want the canonical `pyproject.toml`, Dockerfile, and CI workflow
- You want to understand when to use async vs. sync, `TaskGroup` vs. `gather`, or `Protocol` vs. `ABC`

This skill is consumed automatically by `wfc-build`, `wfc-implement`, `wfc-test`, and `wfc-review` when the project is Python.

## Usage

```bash
# Not user-invocable as a workflow. Referenced by agents and other skills.
# To enforce these standards in a review:
/wfc-review          # The correctness and maintainability reviewers apply wfc-python rules

# To generate tests following these conventions:
/wfc-test
```

## Example

An agent scaffolding a new Python API service would produce this project structure and toolchain setup:

```
project/
├── api/              # PRESENTATION: FastAPI routes, Pydantic schemas
├── services/         # LOGIC: Business rules (pure functions where possible)
├── repositories/     # DATA: Database and API clients
└── models/           # DOMAIN: Frozen dataclasses, StrEnum states

pyproject.toml (key settings):
  requires-python = ">=3.12"
  dependencies: httpx>=0.27, orjson>=3.9, structlog>=24.1,
                tenacity>=8.2, pydantic>=2.6

[tool.black]   line-length = 88, target-version = ["py312"]
[tool.ruff]    select = ["E","F","W","I","N","UP","B","SIM","TCH"]
               ignore = ["E111","E114","E117","E501","W191","E203"]

CI workflow:
  uv sync --frozen
  uv run black --check .
  uv run ruff check .
  uv run mypy . --strict
  uv run pytest --cov --cov-fail-under=80
  uv lock --check
  uv run pip-audit --strict
```

A wfc-review agent flagging a violation:

```
Maintainability finding (severity 6, confidence 90):
  File: services/order.py, line 47
  Pattern: import requests / requests.get(url) inside async def
  Standard: wfc-python — Never use requests in async code (blocks event loop).
            Use httpx.AsyncClient instead.
  Fix: async with httpx.AsyncClient(timeout=30) as client:
           resp = await client.get(url)
```

## Options

No arguments required. This skill is a passive reference consumed by other skills.

Key enforcement areas:

| Area | Standard |
|------|----------|
| Toolchain | UV exclusively — no pip, pipx, conda, poetry |
| Formatter | black (line-length 88) — ruff defers on style conflicts |
| Type checker | mypy --strict — full annotations required on all public APIs |
| JSON | orjson over stdlib json |
| HTTP client | httpx over requests (async-first) |
| Logging | structlog only — no print(), no stdlib logging |
| Retries | tenacity — no hand-rolled retry loops |
| Testing | pytest only — unittest.TestCase is forbidden |
| Async concurrency | asyncio.TaskGroup (3.11+) — not asyncio.gather |
| File limit | 500 lines hard cap per source file |

## Integration

**Produces:**

- Python-specific violation findings in `wfc-review` reports
- Canonical `pyproject.toml`, Dockerfile template, and CI workflow used by `wfc-implement` when scaffolding Python projects
- The preferred library list referenced by agents when choosing dependencies

**Consumes:**

- All universal standards from `wfc-code-standards` (inherited, not duplicated)

**Next step:** Violations flagged by `wfc-review` against wfc-python standards appear in `REVIEW-{task_id}.md`. Fix them, then re-run `/wfc-review` or let the pre-commit hooks catch them via `black`, `ruff`, and `mypy`.
