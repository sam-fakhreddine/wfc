# WFC Task Tool Integration - Working Example

This document demonstrates how to use WFC's persona-based review system with Claude Code's Task tool for true independent subagent execution.

## Architecture Overview

```
User invokes /wfc-review
        ↓
1. prepare_persona_review()
   ├─ Select 5 relevant personas from 54
   ├─ Build persona-specific system prompts
   └─ Return task specifications
        ↓
2. Claude Code spawns Task tools (in parallel)
   ├─ Task #1: BACKEND_PYTHON_SENIOR reviews code
   ├─ Task #2: APPSEC_SPECIALIST reviews code
   ├─ Task #3: SOLUTIONS_ARCHITECT reviews code
   ├─ Task #4: CODE_REVIEWER reviews code
   └─ Task #5: TECH_DEBT_ANALYST reviews code
        ↓
3. finalize_persona_review(results)
   ├─ Parse JSON responses
   ├─ Weight by relevance scores
   ├─ Calculate consensus
   └─ Generate report
```

## Step-by-Step Example

### Phase 1: Prepare Review

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path.home() / ".claude/skills/wfc"))
sys.path.insert(0, str(Path.home() / ".claude/skills/wfc-review"))

from personas.persona_orchestrator import (
    PersonaRegistry, PersonaSelector, PersonaSelectionContext,
    extract_tech_stack_from_files
)
from personas.persona_executor import PersonaReviewExecutor

# Initialize
personas_dir = Path.home() / ".claude/skills/wfc/personas"
registry = PersonaRegistry(personas_dir)
selector = PersonaSelector(registry)
executor = PersonaReviewExecutor()

# Files to review
files = [
    "/path/to/your/code.py",
    "/path/to/your/other_code.py"
]

# Build selection context
tech_stack = extract_tech_stack_from_files(files)
context = PersonaSelectionContext(
    task_id="example-review",
    files=files,
    tech_stack=tech_stack,
    task_type="refactoring",
    complexity="M",
    properties=["CORRECTNESS", "MAINTAINABILITY"],
    domain_context=[]
)

# Select personas
selected = selector.select_personas(
    context=context,
    num_personas=5,
    require_diversity=True,
    min_relevance=0.3
)

print(f"Selected {len(selected)} personas:")
for sp in selected:
    print(f"  • {sp.persona.name} (relevance: {sp.relevance_score:.2f})")

# Prepare task specifications
personas_with_relevance = [
    (sp.persona.to_dict(), sp.relevance_score)
    for sp in selected
]

task_specs = executor.prepare_subagent_tasks(
    personas_with_relevance=personas_with_relevance,
    files=files,
    properties=[
        {'type': 'CORRECTNESS', 'statement': 'Code is functionally correct'},
        {'type': 'MAINTAINABILITY', 'statement': 'Code is maintainable'}
    ]
)

print(f"\nPrepared {len(task_specs)} review tasks for Task tool execution")
```

### Phase 2: Execute via Task Tool (Claude Code)

Now Claude Code spawns the subagents in parallel using the Task tool.

**Important**: The Task tool is a Claude Code built-in tool, NOT a Python import. Python code cannot directly call Task - only Claude Code can invoke it.

When Claude Code receives the task_specs from Phase 1, it spawns Task tools like this:

```
For each task_spec in task_specs:
    Claude Code calls Task tool with:
    - subagent_type: "general-purpose"
    - prompt: task_spec["prompt"]  (system prompt + review instructions)
    - model: task_spec["model"]    (sonnet, opus, or haiku)
    - description: task_spec["description"]

All Task calls are made in PARALLEL (single message, multiple tool invocations).
Each Task runs as an independent subprocess with isolated context.
```

The result from each Task is a JSON string containing the persona's review:
```json
{
  "persona_id": "BACKEND_PYTHON_SENIOR",
  "score": 8.5,
  "passed": true,
  "summary": "Clean code with good separation of concerns",
  "reasoning": "...",
  "comments": [...]
}
```

Claude Code collects all results and prepares them for Phase 3.

### Phase 3: Synthesize Results

```python
# Parse results
persona_results = executor.parse_subagent_results(results)

print("\nPersona Reviews:")
for result in persona_results:
    status = "✅" if result.passed else "❌"
    print(f"  {status} {result.persona_name}: {result.score:.1f}/10")
    print(f"     {result.summary}")

# Now use orchestrator to finalize
from orchestrator import ReviewOrchestrator

orchestrator = ReviewOrchestrator()
final_result = orchestrator.finalize_persona_review(
    request=request,
    selected_personas=selected,
    subagent_responses=results,
    output_dir=Path("/tmp/wfc-reviews")
)

print(f"\n{'='*60}")
print(f"FINAL CONSENSUS: {final_result.consensus.overall_score:.1f}/10")
print(f"Status: {'✅ APPROVED' if final_result.consensus.passed else '❌ REJECTED'}")
print(f"Report: {final_result.report_path}")
```

## Key Benefits

### ✅ True Independence
Each persona runs as a separate subprocess with its own:
- System prompt
- Context window
- No visibility into other reviews

### ✅ True Parallelism
Claude Code executes all Task calls concurrently, not sequentially in threads.

### ✅ Proper Isolation
No context bleeding - personas can't see each other's opinions until synthesis.

### ✅ Model Selection
Each persona can use a different model:
- Security reviews → Opus (more thorough)
- Simple reviews → Haiku (faster, cheaper)
- Balanced reviews → Sonnet

## Example Output

```
✨ Selected 5 personas:
  • Senior Backend Python Developer (relevance: 0.92)
  • Application Security Specialist (relevance: 0.89)
  • Solutions Architect (relevance: 0.85)
  • Code Reviewer (relevance: 0.82)
  • Technical Debt Analyst (relevance: 0.78)

Prepared 5 review tasks for Task tool execution

[Claude Code spawns 5 Task tools in parallel]

Persona Reviews:
  ✅ Senior Backend Python Developer: 8.5/10
     Clean code with good separation of concerns
  ✅ Application Security Specialist: 9.0/10
     No security vulnerabilities detected
  ✅ Solutions Architect: 8.8/10
     Architecture follows best practices
  ✅ Code Reviewer: 8.2/10
     Minor style issues, overall good quality
  ⚠️  Technical Debt Analyst: 6.5/10
     Some technical debt, refactoring recommended

============================================================
FINAL CONSENSUS: 8.2/10
Status: ✅ APPROVED
Report: /tmp/wfc-reviews/REVIEW-example-review.md
```

## Comparison: Old vs New

### Old Architecture (Wrong)
```python
# Python tried to spawn subagents with ThreadPoolExecutor
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(review, persona) for persona in personas]
    # ❌ Can't actually spawn subagents from Python
    # ❌ Just simulated reviews
    # ❌ All in same process (context bleeding possible)
```

### New Architecture (Correct)
```python
# Phase 1: Python prepares specifications
task_specs = prepare_subagent_tasks(personas)

# Phase 2: Claude Code spawns real subagents
for spec in task_specs:
    Task(prompt=spec["prompt"], model=spec["model"])  # Real subprocess
    # ✅ True subagent isolation
    # ✅ Parallel execution by Claude Code
    # ✅ No context bleeding

# Phase 3: Python synthesizes results
results = parse_subagent_results(responses)
```

## Next Steps

1. **Integration**: Update `/wfc-review` skill to use this pattern
2. **Testing**: Create test suite for persona selection accuracy
3. **Documentation**: Add more examples for different use cases
4. **Optimization**: Implement caching for frequently used personas

---

**Architecture Status**: ✅ Correct implementation following Claude Code best practices

Based on: https://code.claude.com/docs/en/sub-agents
