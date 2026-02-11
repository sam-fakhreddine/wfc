"""
Persona Review Executor

Prepares persona review tasks for Claude Code to execute via Task tool.
Each persona runs as an independent subagent with no context sharing.

ARCHITECTURE:
------------
This module does NOT spawn subagents itself. Instead, it:
1. Builds persona-specific system prompts
2. Prepares task specifications
3. Returns them for Claude Code to execute via Task tool calls

EXECUTION FLOW:
--------------
1. prepare_subagent_tasks() - Build task specs for N personas
2. Claude Code calls Task tool N times (in parallel)
3. parse_subagent_results() - Parse JSON responses from subagents
4. Synthesis happens in consensus.py

WHY THIS ARCHITECTURE:
---------------------
- Python code in skills cannot directly call Task tool
- Only Claude Code itself can make Task tool calls
- This provides proper subagent isolation (no context bleeding)
- Enables true parallel execution via Claude Code's Task system
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import sys
import logging

logger = logging.getLogger(__name__)

# Import model resolution (NEW PATHS)
try:
    sys.path.insert(0, str(Path.home() / ".claude/skills/wfc"))
    from scripts.personas.persona_orchestrator import resolve_model_name
except:
    def resolve_model_name(model_ref: str) -> str:
        """Fallback if import fails"""
        return model_ref if model_ref.startswith("claude-") else "claude-sonnet-4-20250514"

# Import token management
try:
    from .token_manager import TokenBudgetManager, TokenBudget
    TOKEN_MANAGER_AVAILABLE = True
except ImportError:
    TOKEN_MANAGER_AVAILABLE = False
    logger.warning("TokenBudgetManager not available - using legacy prompt building")


@dataclass
class PersonaReviewRequest:
    """Request for a persona to review code"""
    task_id: str
    files: List[str]
    properties: List[Dict[str, Any]]
    persona_id: str
    persona_name: str
    system_prompt: str
    model: str


@dataclass
class PersonaReviewResult:
    """Result from a persona's review"""
    persona_id: str
    persona_name: str
    score: float  # 0-10
    passed: bool  # score >= 7
    summary: str
    comments: List[Dict[str, Any]]
    reasoning: str
    relevance_score: float  # From selection


def build_persona_system_prompt(
    persona: Dict,
    request_files: List[str],
    request_properties: List[Dict[str, Any]]
) -> str:
    """
    Build a complete system prompt for a persona.

    Combines:
    - Persona's core identity and expertise
    - Persona's decision-making lens
    - Review dimensions and weights
    - Task-specific context
    """

    # Extract persona details
    name = persona.get("name", "Expert Reviewer")
    skills = persona.get("skills", [])
    lens = persona.get("lens", {})
    personality = persona.get("personality", {})
    system_additions = persona.get("system_prompt_additions", "")

    # Build skills description
    skills_text = "\n".join([
        f"  - {skill['name']} ({skill['level']}): {skill.get('context', '')}"
        for skill in skills[:5]  # Top 5 skills
    ])

    # Build review dimensions
    dimensions = lens.get("review_dimensions", [])
    dimensions_text = "\n".join([
        f"  - {d['dimension']}: {d['weight']*100:.0f}% weight"
        for d in dimensions
    ])

    # Extract properties to focus on
    property_names = [p.get("type", "") for p in request_properties if p.get("type")]
    properties_text = ", ".join(property_names) if property_names else "General code quality"

    # Build the system prompt
    prompt = f"""You are {name}, an expert code reviewer.

# Your Expertise

{system_additions}

## Core Skills
{skills_text}

## Review Philosophy
{lens.get("philosophy", "Apply rigorous engineering standards")}

## Primary Focus Areas
{lens.get("focus", "Code quality and best practices")}

## Review Dimensions (Weighted)
{dimensions_text}

## Communication Style
- Style: {personality.get("communication_style", "direct")}
- Detail Level: {personality.get("detail_orientation", "balanced")}
- Risk Tolerance: {personality.get("risk_tolerance", "moderate")}

# Your Task

Review the provided code files with focus on: {properties_text}

Provide your review in the following JSON format:

{{
  "score": <float 0-10>,
  "passed": <boolean, true if score >= 7>,
  "summary": "<concise 1-2 sentence summary>",
  "reasoning": "<detailed explanation of your assessment>",
  "comments": [
    {{
      "file": "<filename>",
      "line": <line number or 0>,
      "severity": "<critical|high|medium|low|info>",
      "message": "<what the issue is>",
      "suggestion": "<how to fix it>"
    }}
  ]
}}

# Important Guidelines

1. **Be specific**: Reference exact files and line numbers when possible
2. **Apply your lens**: Weight issues according to your review dimensions
3. **Independent thinking**: You don't see other reviewers' opinions - provide YOUR expert perspective
4. **Actionable feedback**: Every comment should have a clear suggestion
5. **Severity calibration**:
   - critical: Security vulnerabilities, data loss, system crashes
   - high: Significant bugs, performance issues, major design flaws
   - medium: Code quality issues, minor bugs, maintainability concerns
   - low: Style issues, optimizations, nice-to-haves
   - info: Observations, suggestions, educational comments

Review the code now and respond with ONLY the JSON format above.
"""

    return prompt


def parse_persona_review_response(response: str, persona_id: str, persona_name: str) -> PersonaReviewResult:
    """
    Parse the JSON response from a persona review.

    Falls back to reasonable defaults if parsing fails.
    """
    try:
        # Extract JSON from response (might have markdown code blocks)
        json_str = response.strip()
        if json_str.startswith("```"):
            # Remove markdown code blocks
            lines = json_str.split("\n")
            json_str = "\n".join([
                line for line in lines
                if not line.strip().startswith("```")
            ])

        data = json.loads(json_str)

        return PersonaReviewResult(
            persona_id=persona_id,
            persona_name=persona_name,
            score=float(data.get("score", 5.0)),
            passed=bool(data.get("passed", False)),
            summary=data.get("summary", "Review completed"),
            comments=data.get("comments", []),
            reasoning=data.get("reasoning", ""),
            relevance_score=0.0  # Will be set by caller
        )

    except json.JSONDecodeError as e:
        # Fallback to a default review if parsing fails
        logger.warning("Failed to parse review from %s: %s", persona_name, e, exc_info=True)
        return PersonaReviewResult(
            persona_id=persona_id,
            persona_name=persona_name,
            score=5.0,
            passed=False,
            summary=f"Review parsing failed: {e}",
            comments=[],
            reasoning=f"Failed to parse response: {response[:200]}",
            relevance_score=0.0
        )


def create_persona_review_prompt(
    files: List[str],
    properties: List[Dict[str, Any]]
) -> str:
    """
    Create the user prompt with code files and properties.
    """
    prompt_parts = []

    # Add properties context
    if properties:
        prompt_parts.append("# Properties to Verify\n")
        for prop in properties:
            prop_type = prop.get("type", "UNKNOWN")
            prop_stmt = prop.get("statement", "")
            prompt_parts.append(f"- **{prop_type}**: {prop_stmt}")
        prompt_parts.append("\n")

    # Add files
    prompt_parts.append("# Code Files to Review\n")

    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            prompt_parts.append(f"\n## File: {file_path}\n")
            prompt_parts.append("```")
            # Try to guess language from extension
            ext = Path(file_path).suffix.lstrip('.')
            if ext:
                prompt_parts.append(ext)
            prompt_parts.append(f"\n{content}\n```\n")

        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.warning("Error reading file %s: %s", file_path, e, exc_info=True)
            prompt_parts.append(f"\n## File: {file_path}\n")
            prompt_parts.append(f"Error reading file: {e}\n")

    return "\n".join(prompt_parts)


class PersonaReviewExecutor:
    """
    Executes persona reviews as independent subagents.

    Each persona:
    1. Receives a persona-specific system prompt
    2. Runs as an independent subagent (no context sharing)
    3. Reviews code from their unique lens
    4. Returns structured feedback

    WORLD FUCKING CLASS:
    - Accurate token counting
    - Smart file condensing when needed
    - Compressed system prompts
    - Token usage reporting
    """

    def __init__(self, use_token_manager: bool = True):
        """
        Initialize executor.

        Args:
            use_token_manager: Use WFC token management (recommended)
        """
        self.use_token_manager = use_token_manager and TOKEN_MANAGER_AVAILABLE

        if self.use_token_manager:
            self.token_manager = TokenBudgetManager()
            logger.info("✅ WFC Token Manager enabled")
        else:
            self.token_manager = None
            logger.warning("⚠️  Legacy prompt building (no token management)")

    def prepare_subagent_tasks(
        self,
        personas_with_relevance: List[tuple],  # [(persona, relevance_score), ...]
        files: List[str],
        properties: List[Dict[str, Any]],
        token_budget: Optional[TokenBudget] = None
    ) -> List[Dict[str, Any]]:
        """
        Prepare subagent task specifications for Claude Code to execute.

        Returns a list of task specs that Claude Code will use to spawn
        subagents via the Task tool. Each persona runs independently.

        WORLD FUCKING CLASS:
        - Uses TokenBudgetManager for smart prompt optimization
        - Reports token usage per persona
        - Auto-condenses files when needed

        Args:
            personas_with_relevance: List of (persona, relevance_score) tuples
            files: List of file paths to review
            properties: List of properties to verify
            token_budget: Optional budget override

        Returns:
            List of task specifications with prompts and metadata (includes token metrics)
        """
        tasks = []
        total_metrics = {
            "total_prompts_tokens": 0,
            "total_condensed_files": 0,
            "personas_over_budget": 0
        }

        # Use WFC token manager if available
        if self.use_token_manager:
            for persona, relevance_score in personas_with_relevance:
                persona_id = persona["id"]
                persona_name = persona["name"]

                # Build optimized prompt with token management
                full_prompt, metrics = self.token_manager.prepare_persona_prompt(
                    persona=persona,
                    files=files,
                    properties=properties,
                    budget=token_budget
                )

                # Get model for this persona
                model = resolve_model_name(
                    persona.get("model_preference", {}).get("default", "sonnet")
                )

                # Create task specification
                task_spec = {
                    "persona_id": persona_id,
                    "persona_name": persona_name,
                    "prompt": full_prompt,
                    "model": model,
                    "relevance_score": relevance_score,
                    "description": f"Review by {persona_name}",
                    "token_metrics": metrics  # WFC: Include token stats
                }

                tasks.append(task_spec)

                # Aggregate metrics
                total_metrics["total_prompts_tokens"] += metrics["total_tokens"]
                total_metrics["total_condensed_files"] += metrics["num_condensed"]
                if not metrics["fits_budget"]:
                    total_metrics["personas_over_budget"] += 1

            # Log token usage summary
            avg_tokens = total_metrics["total_prompts_tokens"] / len(tasks) if tasks else 0
            logger.info("🎯 Token Budget Summary:")
            logger.info(f"  • Avg tokens/persona: {avg_tokens:.0f}")
            logger.info(f"  • Total condensed files: {total_metrics['total_condensed_files']}")
            if total_metrics["personas_over_budget"] > 0:
                logger.warning(f"  ⚠️  {total_metrics['personas_over_budget']} personas over budget!")

        else:
            # Legacy mode (backward compatible)
            user_prompt = create_persona_review_prompt(files, properties)

            for persona, relevance_score in personas_with_relevance:
                persona_id = persona["id"]
                persona_name = persona["name"]

                # Build persona-specific system prompt
                system_prompt = build_persona_system_prompt(persona, files, properties)

                # Combine into full prompt
                full_prompt = f"""{system_prompt}

{user_prompt}

Remember to respond with ONLY valid JSON in the specified format."""

                # Get model for this persona
                model = resolve_model_name(
                    persona.get("model_preference", {}).get("default", "sonnet")
                )

                # Create task specification
                task_spec = {
                    "persona_id": persona_id,
                    "persona_name": persona_name,
                    "prompt": full_prompt,
                    "model": model,
                    "relevance_score": relevance_score,
                    "description": f"Review by {persona_name}"
                }

                tasks.append(task_spec)

        return tasks

    def parse_subagent_results(
        self,
        subagent_responses: List[Dict[str, Any]]
    ) -> List[PersonaReviewResult]:
        """
        Parse results from Claude Code subagent Task tool executions.

        Args:
            subagent_responses: List of dicts with:
                - persona_id: str
                - persona_name: str
                - relevance_score: float
                - response: str (JSON response from subagent)

        Returns:
            List of PersonaReviewResult objects
        """
        results = []

        for item in subagent_responses:
            persona_id = item["persona_id"]
            persona_name = item["persona_name"]
            relevance_score = item["relevance_score"]
            response = item["response"]

            # Parse the JSON response
            result = parse_persona_review_response(
                response=response,
                persona_id=persona_id,
                persona_name=persona_name
            )
            result.relevance_score = relevance_score

            results.append(result)

        return results
