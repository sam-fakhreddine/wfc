---
name: wfc-init
description: Initialize WFC for a project by detecting languages and setting up appropriate quality tools (formatters, linters, test frameworks). Detects Python, JavaScript, TypeScript, Go, Rust, Java, Ruby, C#, and configures black/ruff, prettier/eslint, gofmt/golangci-lint, rustfmt/clippy, etc. Triggers on "initialize WFC", "setup quality tools", "configure project", or explicit /wfc-init. Ideal for onboarding new projects to WFC. Not for projects already configured.
license: MIT
---

# WFC-INIT - Project Initialization

**One-command setup** for WFC quality tools in any project.

## What It Does

1. **Detects languages** in project (Python, JS, TS, Go, Rust, Java, Ruby, C#)
2. **Recommends tools** (formatters, linters, test frameworks)
3. **Generates config files** (.wfc/config.json, pyproject.toml, etc.)
4. **Provides install commands** for all tools
5. **Sets up pre-commit hooks** (optional)
6. **Creates quality check workflow**
7. **Configures Entire.io** (OPTIONAL - agent session capture for debugging)

## Usage

```bash
# Initialize in current directory
/wfc-init

# Initialize specific directory
/wfc-init /path/to/project

# Skip interactive prompts
/wfc-init --yes

# Only detect, don't configure
/wfc-init --detect-only
```

## Language Support

| Language | Formatter | Linter | Tests |
|----------|-----------|--------|-------|
| **Python** | black | ruff | pytest |
| **JavaScript** | prettier | eslint | jest |
| **TypeScript** | prettier | eslint + TS | jest |
| **Go** | gofmt | golangci-lint | go test |
| **Rust** | rustfmt | clippy | cargo test |
| **Java** | google-java-format | checkstyle | junit |
| **Ruby** | rubocop | rubocop | rspec |
| **C#** | dotnet format | dotnet analyze | dotnet test |

## Example Output

```
🔍 Detecting project languages...

Found languages:
  ✅ Python (42 files)
     - Formatter: black
     - Linter: ruff
     - Tests: pytest

  ✅ JavaScript (18 files)
     - Formatter: prettier
     - Linter: eslint
     - Tests: jest

📋 Recommended setup:

  1. Install tools:
     uv pip install black ruff pytest
     npm install --save-dev prettier eslint jest

  2. Create config files:
     ✅ pyproject.toml (Python)
     ✅ .prettierrc.json (JavaScript)
     ✅ .eslintrc.json (JavaScript)

  3. Add to Makefile:
     ✅ make quality-check
     ✅ make format
     ✅ make lint

  4. Setup pre-commit hooks:
     ✅ .pre-commit-config.yaml

  5. Entire.io session capture: ENABLED BY DEFAULT ✅
     📹 Agent sessions automatically captured locally
     🔒 Privacy-first: Local-only, sensitive data redacted
     💡 Helps debug failed agents and learn from mistakes

     Checking for entire CLI...
     ✅ entire CLI found (v1.2.0)
     ✅ Ready to capture sessions

     Disable? (y/n): n
     ✅ Keeping enabled (recommended)

     Installation guide: https://entire.io/install
     Learn more: docs/ENTIRE_IO.md

Proceed with setup? (y/n): y

✅ WFC initialized successfully!

Next steps:
  1. Run: make quality-check
  2. Commit: .wfc/config.json, pyproject.toml, .prettierrc.json
  3. Share with team: Everyone gets same quality tools
```

## Generated Files

### .wfc/config.json (or wfc.config.json at project root)

```json
{
  "languages": [
    {
      "name": "python",
      "formatter": "black",
      "linter": "ruff",
      "test_framework": "pytest"
    },
    {
      "name": "javascript",
      "formatter": "prettier",
      "linter": "eslint",
      "test_framework": "jest"
    }
  ],
  "quality_gate": {
    "enabled": true,
    "run_before_review": true,
    "fail_on_error": true
  },
  "entire_io": {
    "enabled": true,
    "local_only": true,
    "create_checkpoints": true,
    "checkpoint_phases": [
      "UNDERSTAND",
      "TEST_FIRST",
      "IMPLEMENT",
      "REFACTOR",
      "QUALITY_CHECK",
      "SUBMIT"
    ],
    "privacy": {
      "redact_secrets": true,
      "max_file_size": 100000,
      "exclude_patterns": [
        "*.env",
        "*.key",
        "*.pem",
        "*secret*",
        "*credential*",
        ".claude/*"
      ],
      "capture_env": false
    }
  }
}
```

### Makefile (added targets)

```makefile
# Quality checks for all languages
quality-check:
	@echo "🔍 Running quality checks..."
	# Python
	@black --check wfc/
	@ruff check wfc/
	@pytest
	# JavaScript
	@prettier --check src/
	@eslint src/
	@jest
	@echo "✅ All checks passed"

format:
	@echo "🎨 Formatting code..."
	@black wfc/
	@prettier --write src/
	@echo "✅ Code formatted"

lint:
	@echo "🔍 Linting..."
	@ruff check --fix wfc/
	@eslint --fix src/
	@echo "✅ Linting complete"
```

### .pre-commit-config.yaml (optional)

```yaml
repos:
  # Python
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: ['--fix']

  # JavaScript/TypeScript
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        args: ['--fix']
```

## Multi-Language Projects

WFC automatically handles polyglot projects:

```
myproject/
├── backend/          # Python
│   ├── api/
│   └── tests/
├── frontend/         # TypeScript + React
│   ├── src/
│   └── tests/
└── services/         # Go microservices
    ├── auth/
    └── users/

wfc-init detects:
  ✅ Python (backend)
  ✅ TypeScript (frontend)
  ✅ Go (services)

Configures tools for all three!
```

## Integration with wfc-implement

After initialization, wfc-implement automatically uses configured tools:

```python
# wfc-implement agent workflow
def quality_check(files):
    config = load_wfc_config()  # Reads .wfc/config.json

    for lang in config.languages:
        # Use language-specific tools
        if lang.name == "python":
            run_black(files)
            run_ruff(files)
        elif lang.name == "javascript":
            run_prettier(files)
            run_eslint(files)
        # etc.
```

## Entire.io Setup (ENABLED BY DEFAULT)

When initializing a project, wfc-init confirms Entire.io is ready to capture sessions.

### What is Entire.io?

**Agent session capture** for debugging and cross-session learning:
- 📹 Records agent reasoning at each TDD phase
- 🐛 Rewind failed agents to exact failure point
- 📚 Learn from past mistakes across sessions
- 🔒 **Local-only by default** - privacy-first design

### Setup Flow (Entire CLI Installed)

```
🔍 Checking for Entire.io...

Found: entire CLI v1.2.0 ✅

Entire.io session capture: ENABLED BY DEFAULT

Benefits:
  🐛 Debug failed agents 10x faster
  📚 Cross-session learning from failures
  🔍 Understand agent decision-making
  📊 Retrospective analysis input

Privacy guarantees:
  🔒 Local-only by default (never auto-pushed)
  🔒 Sensitive data automatically redacted
  🔒 User controls what gets shared

Disable session capture? (y/n): n

✅ Keeping enabled (recommended)
✅ Privacy settings configured in wfc.config.json

Learn more: docs/ENTIRE_IO.md
```

### If Entire CLI Not Installed

```
🔍 Checking for Entire.io...

Not found. Sessions will not be captured (entire CLI required).

Install entire CLI to enable session capture:
  macOS:    brew install entireio/tap/entire
  npm:      npm install -g @entireio/cli
  pip:      pip install entireio-cli

Learn more: https://entire.io/install

Continue without session capture? (y/n): y

✅ Continuing (install entire CLI later to enable sessions)
```

## Options

### --detect-only

Just show detected languages, don't configure:

```bash
/wfc-init --detect-only

Languages detected:
  - Python (42 files)
  - JavaScript (18 files)
  - Go (7 files)
```

### --language

Initialize for specific language only:

```bash
/wfc-init --language python

Only configuring Python tools:
  - black
  - ruff
  - pytest
```

### --no-pre-commit

Skip pre-commit hook setup:

```bash
/wfc-init --no-pre-commit
```

### --template

Use template for config files:

```bash
/wfc-init --template strict  # Strict linting rules
/wfc-init --template relaxed  # Relaxed rules
/wfc-init --template custom   # Custom template
```

## Philosophy

**ELEGANT**: Detect once, configure automatically
**MULTI-TIER**: Language detection → Config generation → Tool setup
**UNIVERSAL**: Support all major languages, not just Python

## Best Practices

1. **Run on project start**: `cd myproject && /wfc-init`
2. **Commit config**: Share .wfc/config.json with team
3. **Use in CI**: Config drives CI quality checks
4. **Keep updated**: Re-run when adding new languages

## See Also

- `docs/QUALITY_GATE.md` - Quality gate documentation
- `wfc/scripts/language_detector.py` - Language detection logic
- `wfc/scripts/quality_checker.py` - Multi-language quality checker

---

**This is World Fucking Class.** 🚀
