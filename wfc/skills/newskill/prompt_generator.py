"""
Skill Prompt Generator

Generates Claude Code agentic prompts for new skills.
"""

from pathlib import Path
from .interview import SkillSpec


class PromptGenerator:
    """
    Generates skill prompts following WFC conventions.

    ELEGANT: Simple template-based generation.
    """

    def generate(self, spec: SkillSpec) -> str:
        """Generate complete skill prompt"""
        return f"""---
name: {spec.trigger}
description: {spec.description}
user-invocable: true
disable-model-invocation: false
argument-hint: [arguments]
---

# {spec.trigger.upper()} - {spec.name.title().replace('-', ' ')}

{spec.purpose}

## What It Does

{spec.description}

## Usage

```bash
# Basic usage
{spec.trigger}

# With arguments
{spec.trigger} [args]
```

## Inputs

{self._format_list(spec.inputs)}

## Outputs

{self._format_list(spec.outputs)}

## Integration with WFC

### Consumes
{self._format_list(spec.integration)}

### Produces
{self._format_list(spec.outputs)}

## Configuration

```json
{{
  "{spec.name}": {{
{self._format_config(spec.configuration)}
  }}
}}
```

## Telemetry

Tracks:
{self._format_list(spec.telemetry)}

## Architecture

{self._format_agents(spec.agents)}

## Philosophy

**ELEGANT**: Simple, effective, maintainable
**MULTI-TIER**: Clean separation of concerns
**PARALLEL**: Concurrent execution where possible
"""

    def _format_list(self, items: List[str]) -> str:
        """Format list of items"""
        return '\n'.join(f"- {item.strip()}" for item in items if item.strip())

    def _format_config(self, config: Dict[str, Any]) -> str:
        """Format configuration"""
        if not config:
            return '    "enabled": true'
        return '\n'.join(f'    "{k}": "{v}"' for k, v in config.items())

    def _format_agents(self, agents: Dict[str, Any]) -> str:
        """Format agent architecture"""
        if agents.get("count", 0) == 0:
            return "Single-agent skill (no subagents)"
        return f"Uses {agents.get('count', 1)} agent(s) in {agents.get('architecture', 'unknown')} architecture"

    def save(self, spec: SkillSpec, path: Path) -> None:
        """Save generated prompt to file"""
        content = self.generate(spec)
        with open(path, 'w') as f:
            f.write(content)
