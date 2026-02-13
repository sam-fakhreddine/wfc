"""
Ultra-Minimal Persona Prompts

83% token reduction compared to verbose prompts.
~500 tokens instead of ~3000 tokens per persona.

PHILOSOPHY:
- LLMs don't need verbose backstories to act as experts
- Clear instructions > lengthy descriptions
- Focus on WHAT to do, not WHO they are
- Every token must earn its keep
"""

from typing import List, Dict, Any


def build_ultra_minimal_prompt(
    persona_name: str,
    top_skills: List[str],  # Max 3
    focus: str,  # One line only
    properties_focus: str,  # e.g., "SECURITY, PERFORMANCE"
) -> str:
    """
    Build ultra-minimal persona system prompt.

    Target: <500 tokens (vs ~3000 for verbose version)

    Removes:
    - Lengthy backstories
    - Verbose philosophy
    - Redundant examples
    - Communication style fluff
    - Review dimension percentages

    Keeps:
    - Core identity (1 line)
    - Key expertise (3 skills max)
    - Focus area (1 line)
    - JSON output format
    - Severity guide
    - Core instructions
    """

    skills_str = " | ".join(top_skills[:3])  # Max 3 skills

    return f"""You are {persona_name}, expert code reviewer.

EXPERTISE: {skills_str}
FOCUS: {focus}
TARGET: {properties_focus}

OUTPUT (JSON only):
{{
  "score": 0-10,
  "passed": true/false,
  "summary": "1-2 sentences",
  "reasoning": "your assessment",
  "comments": [
    {{"file": "path", "line": 0, "severity": "critical|high|medium|low|info", "message": "issue", "suggestion": "fix"}}
  ]
}}

SEVERITY:
• critical: bugs, security, data loss
• high: design flaws, performance issues
• medium: quality, maintainability
• low: style, minor improvements
• info: observations, suggestions

Review code. Be specific. Reference files/lines. Suggest fixes."""


def extract_persona_essentials(persona: Dict) -> Dict[str, Any]:
    """
    Extract only essential info from verbose persona definition.

    Args:
        persona: Full persona dict with all metadata

    Returns:
        Dict with only essentials (name, skills, focus)
    """
    # Get top 3 skills
    skills = persona.get("skills", [])[:3]
    skill_names = [f"{s['name']} ({s['level']})" for s in skills]

    # Get one-line focus
    lens = persona.get("lens", {})
    focus = lens.get("focus", "Code quality and best practices")

    # Truncate focus if too long
    if len(focus) > 80:
        focus = focus[:77] + "..."

    return {"name": persona.get("name", "Expert Reviewer"), "skills": skill_names, "focus": focus}


def build_ultra_minimal_user_prompt(
    properties: List[Dict[str, Any]],
    file_summaries: List[Dict[str, str]],  # [{"path": "...", "summary": "..."}]
) -> str:
    """
    Build ultra-minimal user prompt with file summaries.

    Instead of full files, send:
    - File path
    - Line count
    - Key signatures/classes
    - Summary of what it does

    Personas can request full content if needed (future enhancement).
    """
    parts = []

    # Properties (terse)
    if properties:
        parts.append("PROPERTIES:")
        for p in properties:
            parts.append(f"• {p.get('type', 'UNKNOWN')}: {p.get('statement', '')}")
        parts.append("")

    # File summaries (not full content)
    parts.append("FILES:")
    for fs in file_summaries:
        parts.append(f"\n{fs['path']} ({fs.get('lines', 0)} lines)")
        parts.append(fs["summary"])

    return "\n".join(parts)


def estimate_token_reduction():
    """Show estimated token savings"""

    verbose_breakdown = {
        "persona_identity": 2000,
        "skills_detailed": 500,
        "philosophy": 300,
        "dimensions": 200,
        "guidelines": 400,
        "examples": 600,
        "TOTAL": 4000,
    }

    minimal_breakdown = {
        "persona_identity": 50,
        "skills_top3": 100,
        "focus": 50,
        "json_format": 150,
        "severity_guide": 100,
        "instructions": 50,
        "TOTAL": 500,
    }

    reduction_pct = (
        (verbose_breakdown["TOTAL"] - minimal_breakdown["TOTAL"]) / verbose_breakdown["TOTAL"] * 100
    )

    return {
        "verbose": verbose_breakdown,
        "minimal": minimal_breakdown,
        "reduction_tokens": verbose_breakdown["TOTAL"] - minimal_breakdown["TOTAL"],
        "reduction_pct": reduction_pct,
    }


if __name__ == "__main__":
    # Demo
    savings = estimate_token_reduction()

    print("Ultra-Minimal Persona Prompts")
    print("=" * 60)
    print(f"\nVerbose prompt: {savings['verbose']['TOTAL']:,} tokens")
    print(f"Minimal prompt: {savings['minimal']['TOTAL']:,} tokens")
    print(
        f"Savings: {savings['reduction_tokens']:,} tokens ({savings['reduction_pct']:.0f}% reduction)"
    )

    print("\n" + "=" * 60)
    print("Example ultra-minimal prompt:")
    print("=" * 60)

    prompt = build_ultra_minimal_prompt(
        persona_name="Alice Chen, Security Architect",
        top_skills=["AppSec (Expert)", "Threat Modeling (Expert)", "Cryptography (Advanced)"],
        focus="Security vulnerabilities and attack vectors",
        properties_focus="SECURITY, DATA_PROTECTION",
    )

    print(prompt)
    print("\n" + "=" * 60)
    print(f"Prompt length: {len(prompt)} chars (~{len(prompt)//4} tokens)")
