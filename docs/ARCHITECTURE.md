# WFC Architecture

> **System design and implementation details for the WFC multi-agent consensus review framework**

## Overview

WFC is built on a **multi-agent orchestration pattern** where specialized expert personas independently review code and contribute to consensus decision-making.

## Core Components

### 1. Persona Library (`wfc/personas/`)

**Purpose**: Pool of expert personas that can be dynamically selected based on task context

**Structure**:
```
personas/
├── panels/                    # 9 expert panels
│   ├── engineering/           # 11 personas
│   ├── security/              # 8 personas
│   ├── architecture/          # 7 personas
│   ├── quality/               # 8 personas
│   ├── data/                  # 4 personas
│   ├── product/               # 3 personas
│   ├── operations/            # 4 personas
│   ├── domain-experts/        # 5 personas
│   └── specialists/           # 4 personas
├── schemas/                   # JSON schemas for validation
├── persona_orchestrator.py    # Selection + registry logic
├── persona_executor.py        # Subagent execution
└── registry.json              # Fast lookup index
```

**Persona Definition**:
Each persona is a JSON file containing:
- `skills`: Technical expertise with proficiency levels
- `lens`: Decision-making perspective and focus areas
- `personality`: Communication style, risk tolerance
- `selection_criteria`: When to use this persona (tech stacks, task types, anti-patterns)
- `model_preference`: Which Claude model to use (opus/sonnet/haiku)

### 2. Orchestrator (`wfc/skills/review/orchestrator.py`)

**Purpose**: Coordinates the review process from request to consensus

**Flow**:
```
ReviewRequest
    ↓
Extract context (tech stack, complexity, properties)
    ↓
PersonaSelector.select_personas() → 5 personas
    ↓
PersonaExecutor.execute_parallel_reviews()
    ↓
Consensus.calculate() → weighted synthesis
    ↓
ReviewResult
```

**Key Methods**:
- `review()`: Main entry point, determines persona vs legacy mode
- `_review_with_personas()`: Persona-based review flow
- `_extract_tech_stack()`: Analyze files to detect technologies

### 3. Persona Selector (`wfc/personas/persona_orchestrator.py`)

**Purpose**: Intelligent selection of relevant personas based on task context

**Selection Algorithm** (multi-stage scoring):

1. **Tech Stack Matching (40% weight)**
   ```python
   # Extract from file extensions and imports
   tech_stack = ['python', 'fastapi', 'postgresql']
   # Match persona tech_stacks
   score += overlap_ratio * 0.4
   ```

2. **Properties Alignment (30% weight)**
   ```python
   # SECURITY property → security personas
   # PERFORMANCE property → performance experts
   if property in persona.properties:
       score += 0.3
   ```

3. **Complexity Filtering (15% weight)**
   ```python
   # XL tasks need expert/senior personas
   # S tasks can use any complexity range
   if complexity in persona.complexity_range:
       score += 0.15
   ```

4. **Task Type (10% weight)**
   ```python
   # api-implementation, refactoring, security-fix, etc.
   if task_type in persona.task_types:
       score += 0.1
   ```

5. **Domain Knowledge (5% weight)**
   ```python
   # Payment processing → fintech expert
   if domain_keyword in persona.domain_knowledge:
       score += 0.05
   ```

6. **Diversity Enforcement**
   ```python
   # No more than 2 personas from same panel
   panel_counts = Counter(p.panel for p in selected)
   if panel_counts[persona.panel] >= 2:
       exclude
   ```

**Output**: Top 5 personas ranked by relevance score

### 4. Persona Executor (`wfc/personas/persona_executor.py`)

**Purpose**: Execute independent reviews as separate subagents

**Critical Design**: Each persona runs in **isolation** (no context sharing)

```python
def execute_parallel_reviews(personas, request):
    """
    Spawn SEPARATE subagent for each persona.
    No context shared during review phase.
    """
    reviews = []
    for persona in personas:
        # Build persona-specific system prompt
        system_prompt = build_persona_system_prompt(persona, request)

        # Spawn INDEPENDENT subagent
        review = spawn_subagent(
            persona_id=persona["id"],
            system_prompt=system_prompt,
            model=resolve_model_name(persona["model_preference"]["default"])
        )
        reviews.append(review)

    return reviews
```

**Why Isolation Matters**:
- **No anchoring bias**: Personas don't see others' opinions
- **Genuine independence**: True expert assessment
- **Disagreements preserved**: Not averaged away prematurely
- **Unique insights surface**: Only 1 persona caught something critical

### 5. Consensus Engine (`wfc/skills/review/consensus.py`)

**Purpose**: Synthesize independent reviews into unified decision

**Synthesis Steps**:

1. **Weighted Scoring**
   ```python
   # Weight by relevance, not fixed weights
   overall = sum(review.score * relevance for review, relevance in zip(reviews, scores))
   ```

2. **Consensus Detection**
   ```python
   # Find issues mentioned by N+ personas (N=3 by default)
   consensus_issues = find_issues_mentioned_by_n_plus(reviews, threshold=3)
   ```

3. **Unique Insights**
   ```python
   # Issues only 1 persona caught (specialist value)
   unique = find_issues_mentioned_by_only_one(reviews)
   ```

4. **Divergent Views**
   ```python
   # Where experts disagree (important signal)
   divergence = find_conflicting_recommendations(reviews)
   ```

5. **Decision Making**
   ```python
   if overall_score >= 9.0: return "APPROVE"
   elif overall_score >= 7.0: return "CONDITIONAL_APPROVE"
   else: return "NEEDS_WORK"
   ```

### 6. Model Resolution (`wfc/personas/persona_orchestrator.py`)

**Purpose**: Map persona model preferences to actual Claude model IDs

```python
MODEL_MAPPING = {
    "opus": "claude-opus-4-20250514",
    "sonnet": "claude-sonnet-4-20250514",
    "haiku": "claude-haiku-4-5-20251001"
}

def resolve_model_name(model_ref: str) -> str:
    """
    Personas specify "opus", "sonnet", or "haiku"
    This resolves to actual model IDs
    Future model updates: just change mapping
    """
    return MODEL_MAPPING.get(model_ref, MODEL_MAPPING["sonnet"])
```

## Data Flow

### End-to-End Review Flow

```
User → /wfc:consensus-review TASK-001
    ↓
Orchestrator.review(ReviewRequest)
    ↓
    ├─→ Extract context from files
    │   ├─ Tech stack: ['python', 'fastapi']
    │   ├─ Complexity: 'L'
    │   └─ Properties: ['SECURITY', 'PERFORMANCE']
    ↓
PersonaSelector.select_personas(context, num=5)
    ↓
    ├─→ Score all personas (tech 40%, properties 30%, ...)
    ├─→ Enforce diversity (max 2 per panel)
    └─→ Return top 5 with relevance scores
    ↓
PersonaExecutor.execute_parallel_reviews(personas, request)
    ↓
    ├─→ Persona 1 (subagent) → Review 1
    ├─→ Persona 2 (subagent) → Review 2
    ├─→ Persona 3 (subagent) → Review 3
    ├─→ Persona 4 (subagent) → Review 4
    └─→ Persona 5 (subagent) → Review 5
    ↓
    [All reviews complete independently]
    ↓
Consensus.calculate(reviews, relevance_scores)
    ↓
    ├─→ Weighted score: 8.2/10
    ├─→ Consensus: 4/5 agree on auth flow
    ├─→ Critical: PII in JWT (2 caught)
    └─→ Unique: Missing index (1 caught)
    ↓
ReviewResult → User
```

## Configuration

### WFC Config (`wfc/shared/config/wfc_config.py`)

```python
DEFAULTS = {
    "personas": {
        "enabled": True,                 # Use persona system
        "num_reviewers": 5,              # How many personas
        "require_diversity": True,       # Enforce panel diversity
        "min_relevance_score": 0.3,      # Filter low-relevance personas
        "synthesis": {
            "consensus_threshold": 3,    # N personas for consensus
            "weight_by_relevance": True  # Weight scores
        }
    },
    "models": {
        "opus": "claude-opus-4-20250514",
        "sonnet": "claude-sonnet-4-20250514",
        "haiku": "claude-haiku-4-5-20251001"
    }
}
```

## Extension Points

### Adding New Personas

1. Create JSON in `wfc/personas/panels/{panel}/{PERSONA_ID}.json`
2. Follow schema: `wfc/personas/schemas/persona.schema.json`
3. Rebuild registry:
   ```bash
   cd ~/.claude/skills/wfc/personas
   python3 -c "from persona_orchestrator import PersonaRegistry; PersonaRegistry.rebuild_registry()"
   ```

### Custom Selection Logic

Override `PersonaSelector.select_personas()` to implement custom scoring:

```python
class CustomSelector(PersonaSelector):
    def select_personas(self, context, num_personas=5):
        # Custom logic here
        return selected_personas
```

### Custom Synthesis

Override `Consensus.calculate()` for different synthesis strategies:

```python
class CustomConsensus(Consensus):
    def calculate(self, reviews, relevance_scores):
        # Custom synthesis logic
        return consensus_result
```

## Performance Characteristics

- **Persona Selection**: O(P) where P = number of personas (~54)
- **Review Execution**: O(N) where N = num_reviewers (5), reviews run in parallel
- **Consensus**: O(N) linear in number of reviews
- **Registry Lookup**: O(1) with indexes

## Future Enhancements

1. **True Parallel Execution**: Use Task tool for concurrent subagent spawning
2. **Adaptive Selection**: Learn from review outcomes to improve selection
3. **Persona Composition**: Combine persona traits dynamically
4. **Caching**: Cache persona selections for similar tasks
5. **Analytics**: Track persona performance metrics

---

**Version**: 1.0.0
**Last Updated**: 2026-02-10
