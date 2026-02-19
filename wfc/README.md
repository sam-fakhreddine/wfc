# WFC - World Fucking Class

Multi-agent consensus code review with ultra-minimal personas.

## Agent Skills Compliant Structure

```
wfc/                              # Main shared library
├── pyproject.toml                # Package definition
├── scripts/                      # ✅ Executable code
│   ├── personas/                 #    Persona system
│   └── skills/                   #    Skill implementations
├── references/                   # ✅ Reference docs (loaded on demand)
│   ├── personas/                 #    54 expert personas
│   ├── ARCHITECTURE.md
│   ├── TOKEN_MANAGEMENT.md
│   └── ULTRA_MINIMAL_RESULTS.md
└── assets/                       # ✅ Static resources
    └── templates/

Skills: wfc-review, wfc-plan, wfc-implement, etc.
Each skill: SKILL.md + scripts/ + references/ + assets/
```

## Key Features

- **99% token reduction** (30k → 315 tokens per persona)
- **File reference prompts** (progressive disclosure)
- **54 expert personas** (security, architecture, performance, etc.)
- **Agent Skills compliant** (proper structure, progressive disclosure)

## Installation

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[tokens]"
```

## Usage

See individual skills:

- `/wfc-review` - Consensus code review
- `/wfc-plan` - Feature planning
- `/wfc-implement` - Parallel implementation

## Architecture

**Progressive Disclosure** (Agent Skills pattern):

1. Load SKILL.md (< 500 lines)
2. Load references/ on demand
3. Execute scripts/ as needed

**Ultra-Minimal Personas** (315 tokens):

- Identity + focus + tools
- No verbose backstories
- Trust the LLM to be expert

This is World Fucking Class. 🚀
