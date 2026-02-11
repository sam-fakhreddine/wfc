# WFC Agent Skills Compliance Restructure

## Phase 1: Main WFC Module (Shared Library)
```
wfc/
├── pyproject.toml
├── README.md
├── scripts/                    # All executable code
│   ├── __init__.py
│   ├── personas/
│   │   ├── __init__.py
│   │   ├── persona_executor.py
│   │   ├── persona_orchestrator.py
│   │   ├── token_manager.py
│   │   ├── ultra_minimal_prompts.py
│   │   └── file_reference_prompts.py
│   └── skills/
│       └── review/
│           ├── __init__.py
│           ├── agents.py
│           ├── orchestrator.py
│           └── consensus.py
├── references/                 # Reference documentation
│   ├── personas/
│   │   ├── panels/            # All persona JSON files
│   │   └── registry.json
│   ├── ARCHITECTURE.md
│   ├── TOKEN_MANAGEMENT.md
│   └── ULTRA_MINIMAL_RESULTS.md
└── assets/                     # Static resources
    └── templates/

## Phase 2: Individual Skills
Each skill (wfc-review, wfc-plan, etc.) follows:
```
skill-name/
├── SKILL.md                    # < 500 lines, focused
├── scripts/                    # Skill-specific code
├── references/                 # Detailed docs
└── assets/                     # Templates, data
```

Execute: Yes/No?
