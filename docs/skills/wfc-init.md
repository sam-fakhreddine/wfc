# wfc-init

## What It Does

`wfc-init` bootstraps WFC quality tooling for any project in a single command. It scans your project to detect which languages are present, recommends the appropriate formatter, linter, and test framework for each, generates config files, adds Makefile targets, and optionally sets up pre-commit hooks. It handles polyglot projects automatically — a backend/frontend/services monorepo gets Python, TypeScript, and Go tools configured in one pass. The output is a `.wfc/config.json` that all other WFC skills (especially `wfc-implement`) use to run the right quality checks for your stack.

## When to Use It

- When bringing a new project onto WFC for the first time
- After adding a new language or framework to an existing project
- When a team member clones a repo and needs consistent local tooling configured
- To generate a standardized `make quality-check` / `make format` / `make lint` Makefile regardless of the tech stack

## Usage

```bash
# Initialize in current directory (interactive)
/wfc-init

# Initialize a specific directory
/wfc-init /path/to/project

# Skip all confirmation prompts
/wfc-init --yes

# Only detect languages, don't write any files
/wfc-init --detect-only

# Configure a single language only
/wfc-init --language python

# Skip pre-commit hook setup
/wfc-init --no-pre-commit

# Use a linting strictness template
/wfc-init --template strict
/wfc-init --template relaxed
```

## Example

```
/wfc-init

Detecting project languages...

Found:
  Python       (42 files) — black, ruff, pytest
  JavaScript   (18 files) — prettier, eslint, jest

Recommended setup:

  1. Install tools:
     uv pip install black ruff pytest
     npm install --save-dev prettier eslint jest

  2. Create config files:
     pyproject.toml          (Python black + ruff settings)
     .prettierrc.json        (JavaScript formatting)
     .eslintrc.json          (JavaScript linting)

  3. Add to Makefile:
     make quality-check
     make format
     make lint

  4. Setup pre-commit hooks:
     .pre-commit-config.yaml

  5. Entire.io session capture: ENABLED BY DEFAULT
     Local-only agent session recording for debugging failed agents.
     entire CLI found (v1.2.0). Disable? (y/n): n

Proceed with setup? (y/n): y

Writing .wfc/config.json...
Writing pyproject.toml...
Writing .prettierrc.json...
Writing .eslintrc.json...
Writing .pre-commit-config.yaml...
Adding Makefile targets...

WFC initialized successfully.

Next steps:
  1. Run: make quality-check
  2. Commit: .wfc/config.json, pyproject.toml, .prettierrc.json
  3. Share with team: everyone gets the same quality tools
```

## Options

| Flag | Description |
|------|-------------|
| `--yes` | Skip all interactive prompts, accept defaults |
| `--detect-only` | Report detected languages without writing any files |
| `--language <lang>` | Configure tools for one language only |
| `--no-pre-commit` | Skip `.pre-commit-config.yaml` generation |
| `--template strict` | Use strict linting rules (zero tolerance) |
| `--template relaxed` | Use relaxed linting rules (warnings only) |
| `--template custom` | Prompt for each setting individually |

**Supported languages:**

| Language | Formatter | Linter | Tests |
|----------|-----------|--------|-------|
| Python | black | ruff | pytest |
| JavaScript | prettier | eslint | jest |
| TypeScript | prettier | eslint + tsc | jest |
| Go | gofmt | golangci-lint | go test |
| Rust | rustfmt | clippy | cargo test |
| Java | google-java-format | checkstyle | junit |
| Ruby | rubocop | rubocop | rspec |
| C# | dotnet format | dotnet analyze | dotnet test |

## Integration

**Produces:**

- `.wfc/config.json` — machine-readable config consumed by `wfc-implement` quality gates
- `pyproject.toml`, `.prettierrc.json`, `.eslintrc.json`, etc. — tool-specific config files
- Updated `Makefile` with `quality-check`, `format`, and `lint` targets
- `.pre-commit-config.yaml` (optional) for pre-commit hook enforcement

**Consumes:**

- Project directory structure (file counts per language extension)
- `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml` (if present, for existing tool versions)

**Next step:** After initializing, run `make quality-check` to verify the toolchain is working, then commit the generated config files. From there, use `/wfc-build` or `/wfc-implement` for feature development — they will automatically use the configured tools for quality gates.
