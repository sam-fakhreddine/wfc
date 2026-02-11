# Contributing to WFC

Thank you for your interest in contributing to WFC! This document provides guidelines for contributing personas, features, and improvements.

## How to Contribute

### Adding New Personas

The most valuable contribution is adding expert personas to expand "the bench."

#### 1. Choose a Persona

Identify a gap in current coverage:
- **Language specialists** (Kotlin, Swift, Scala, Elixir, etc.)
- **Framework experts** (Django, Spring, Rails, etc.)
- **Domain experts** (Legal tech, Education, Energy, etc.)
- **Specialized skills** (GraphQL, WebAssembly, etc.)

Check existing personas to avoid duplicates:
```bash
grep -r "\"name\":" wfc/personas/panels/
```

#### 2. Create Persona File

Create JSON file in appropriate panel:
```bash
# Choose panel: engineering, security, architecture, quality, data, product, operations, domain-experts, specialists
cd wfc/personas/panels/{panel}/
touch MY_EXPERT_ID.json
```

#### 3. Define Persona

Use this template:

```json
{
  "id": "MY_EXPERT_ID",
  "name": "Descriptive Expert Name",
  "panel": "engineering",
  "subpanel": "backend",

  "skills": [
    {
      "name": "Primary Skill",
      "level": "expert",
      "context": "Specific expertise details"
    },
    {
      "name": "Secondary Skill",
      "level": "proficient",
      "context": "Supporting expertise"
    }
  ],

  "domain_knowledge": [
    "Domain Area 1",
    "Domain Area 2"
  ],

  "lens": {
    "focus": "What this persona pays attention to",
    "philosophy": "Core belief guiding reviews",
    "review_dimensions": [
      {"dimension": "key_dimension", "weight": 0.3},
      {"dimension": "secondary_dimension", "weight": 0.25}
    ]
  },

  "personality": {
    "communication_style": "direct",
    "risk_tolerance": "moderate",
    "detail_orientation": "balanced"
  },

  "selection_criteria": {
    "task_types": [
      "task-type-1",
      "task-type-2"
    ],
    "tech_stacks": [
      "tech1",
      "tech2"
    ],
    "complexity_range": ["M", "L", "XL"],
    "anti_patterns": [
      "anti-pattern-1",
      "anti-pattern-2"
    ],
    "properties": [
      "PROPERTY1",
      "PROPERTY2"
    ]
  },

  "model_preference": {
    "default": "sonnet",
    "reasoning": "Why this model is appropriate",
    "fallback": "opus"
  },

  "system_prompt_additions": "Detailed persona description for Claude. Explain expertise, what to catch, how to evaluate...",

  "tags": [
    "tag1",
    "tag2",
    "tag3"
  ],

  "version": "1.0.0",
  "enabled": true
}
```

#### 4. Guidelines for Good Personas

**Skills**:
- 3-5 skills max
- Use levels: `expert`, `proficient`, `intermediate`
- Provide context for each skill

**Lens**:
- Focus: What specifically they look for
- Philosophy: 1-2 sentence guiding principle
- Dimensions: 3-5 weighted dimensions (should sum to 1.0)

**Selection Criteria**:
- `task_types`: When is this persona relevant?
- `tech_stacks`: What technologies trigger selection?
- `complexity_range`: S, M, L, XL
- `anti_patterns`: What bad patterns does this persona catch?
- `properties`: Which review properties align?

**System Prompt**:
- Be specific about what the persona catches
- Mention specific patterns, anti-patterns
- Explain evaluation criteria
- Keep under 200 words

**Model Selection**:
- `opus`: Deep reasoning needed (cryptography, distributed systems, complex architecture)
- `sonnet`: Balanced (most personas) - pattern matching, code review
- `haiku`: Simple, fast checks (future use)

#### 5. Validate Schema

```bash
cd wfc/personas
python3 -c "
import json
from pathlib import Path
with open('panels/{panel}/{PERSONA_ID}.json') as f:
    persona = json.load(f)
print(f'✅ Valid persona: {persona[\"name\"]}')
"
```

#### 6. Submit PR

```bash
git checkout -b add-persona-{name}
git add wfc/personas/panels/{panel}/{PERSONA_ID}.json
git commit -m "Add {Persona Name} to {panel} panel"
git push origin add-persona-{name}
```

Create PR with description:
- What expertise does this persona add?
- When should it be selected?
- Example scenarios where it's valuable

### Improving Selection Algorithm

To enhance persona selection:

1. **Fork the repo**
2. **Modify** `wfc/personas/persona_orchestrator.py`
3. **Add tests** in `wfc/personas/tests/`
4. **Document** changes in PR

Example improvements:
- Better tech stack detection
- Improved scoring weights
- New selection dimensions
- Caching for performance

### Adding Features

For new features (CLI commands, integrations, etc.):

1. **Discuss first**: Open an issue describing the feature
2. **Get feedback**: Ensure it aligns with WFC goals
3. **Implement**: Follow existing code patterns
4. **Test**: Add tests in `wfc/tests/`
5. **Document**: Update relevant docs
6. **Submit PR**: Clear description of changes

### Documentation Improvements

Documentation PRs are always welcome:

- Fix typos, clarify instructions
- Add examples in `docs/examples/`
- Improve installation guides
- Add troubleshooting tips

## Code Style

- **Python**: Follow PEP 8, use type hints
- **JSON**: 2-space indentation, sorted keys where logical
- **Markdown**: Use headers, code blocks, clear structure

## Testing

Before submitting PR:

```bash
# Test persona selection
cd wfc/personas/tests
python3 -m pytest test_persona_selection.py -v

# Validate all persona JSONs
cd wfc/personas
for f in panels/*/*.json; do
    python3 -c "import json; json.load(open('$f'))" || echo "Invalid: $f"
done

# Rebuild registry
python3 -c "from persona_orchestrator import PersonaRegistry; PersonaRegistry.rebuild_registry()"
```

## Review Process

1. **Automated checks**: PR triggers validation
2. **Maintainer review**: 1-2 maintainers review
3. **Discussion**: Address feedback
4. **Merge**: Maintainer merges when ready

## Questions?

- **Issues**: Open an issue for bugs, questions
- **Discussions**: Use GitHub Discussions for ideas
- **Email**: wfc-maintainers@example.com (TODO: update)

## License

By contributing, you agree your contributions will be licensed under the MIT License.

---

Thank you for helping make WFC better! 🙌
