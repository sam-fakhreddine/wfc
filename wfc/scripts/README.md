# WFC Scripts

All executable Python code for WFC.

## Structure

```
scripts/
├── personas/              # Persona system
│   ├── persona_executor.py
│   ├── persona_orchestrator.py
│   ├── token_manager.py
│   ├── ultra_minimal_prompts.py
│   └── file_reference_prompts.py
└── skills/                # Skill implementations
    └── review/
        ├── agents.py
        ├── orchestrator.py
        └── consensus.py
```

## Usage

```python
from wfc.scripts.personas.persona_executor import PersonaReviewExecutor
from wfc.scripts.skills.review.orchestrator import ReviewOrchestrator
```

## Paths

- **Persona data**: `wfc/references/personas/panels/`
- **Scripts**: `wfc/scripts/`
- **Docs**: `wfc/references/`
