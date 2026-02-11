"""
File Reference Prompts - Progressive Disclosure Architecture

Instead of sending full file contents (12k tokens), send file metadata (300 tokens)
and let personas use Read/Grep tools to examine what they need.

ARCHITECTURE:
┌─────────────────────────────────────────────────────────────┐
│ Initial Prompt: 300 tokens                                  │
│ ├─ System prompt: 200 tokens (ultra-minimal)                │
│ └─ File metadata: 100 tokens (paths + line counts)          │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Persona uses tools to read selectively                      │
│ ├─ Read(file="auth.py", offset=100, limit=50) → 400 tokens  │
│ ├─ Grep(pattern="password", path="src/") → 200 tokens       │
│ └─ Read(file="config.py") → 600 tokens                      │
│ Total reads: ~1,200 tokens                                  │
└─────────────────────────────────────────────────────────────┘
                        ↓
            Total: ~1,500 tokens (vs 12,000!)

BENEFITS:
- 88% token reduction per persona
- Scales to 100+ file codebases
- Personas focus on their expertise
- Mirrors human review workflow
"""

from pathlib import Path
from typing import List, Dict, Any


def count_file_lines(filepath: str) -> int:
    """Count lines in a file"""
    try:
        with open(filepath, 'r') as f:
            return sum(1 for _ in f)
    except:
        return 0


def get_domain_focus_areas(focus: str) -> str:
    """
    Get domain-specific focus areas to guide (not prescribe) the review.

    Tells personas WHAT to look for, but not HOW to find it.
    """

    focus_lower = focus.lower()

    # Security-focused personas
    if "security" in focus_lower or "vulnerab" in focus_lower:
        return """As a security expert, examine:
- Authentication and authorization mechanisms
- Input validation and sanitization
- Cryptographic implementations and key management
- Token/session handling
- SQL injection, XSS, CSRF vulnerabilities
- Hardcoded secrets or credentials
- Insecure deserialization or eval() usage"""

    # Application security
    elif "appsec" in focus_lower or "owasp" in focus_lower:
        return """As an application security specialist, examine:
- OWASP Top 10 vulnerabilities
- User input handling and output encoding
- Authentication flows and session management
- Authorization checks and access controls
- Data validation at trust boundaries
- Security headers and CORS policies"""

    # Performance-focused personas
    elif "performance" in focus_lower or "optimi" in focus_lower:
        return """As a performance expert, examine:
- Algorithmic complexity (O(n²) loops, recursion depth)
- Database query patterns (N+1 queries, missing indexes)
- Caching strategies and cache invalidation
- Memory allocation patterns
- Resource pooling and connection management
- Hot paths and critical performance sections"""

    # Scalability
    elif "scal" in focus_lower:
        return """As a scalability expert, examine:
- Concurrency and race conditions
- Shared state and locking mechanisms
- Resource limits and rate limiting
- Connection pooling and async patterns
- Bottlenecks in distributed systems
- Queue depths and backpressure handling"""

    # Architecture
    elif "architecture" in focus_lower or "design" in focus_lower:
        return """As an architecture expert, examine:
- Module boundaries and coupling
- Dependency injection and inversion
- Separation of concerns
- Design patterns and their application
- API contracts and interfaces
- Circular dependencies
- Abstraction layers"""

    # Python-specific
    elif "python" in focus_lower:
        return """As a Python expert, examine:
- Pythonic idioms and best practices
- Type hints and annotations
- Exception handling patterns
- Context managers and resource cleanup
- List comprehensions vs loops
- Mutable default arguments
- Generator usage and memory efficiency"""

    # Machine Learning
    elif "ml" in focus_lower or "machine learning" in focus_lower:
        return """As an ML expert, examine:
- Data leakage between train/test sets
- Model architecture choices
- Feature engineering and preprocessing
- Training loop implementation
- Gradient handling and backpropagation
- GPU memory management
- Overfitting prevention"""

    # Backend/API
    elif "backend" in focus_lower or "api" in focus_lower:
        return """As a backend expert, examine:
- REST/GraphQL API design
- Request/response handling
- Error handling and status codes
- Database transaction management
- Service integration patterns
- Async/await usage
- Middleware and request pipelines"""

    # Default: general code quality
    else:
        return """As a code quality expert, examine:
- Code clarity and readability
- Function/class size and complexity
- Naming conventions
- Error handling completeness
- Test coverage gaps
- Documentation quality
- Technical debt markers (TODO, FIXME, HACK)"""


def build_file_reference_prompt(
    persona_name: str,
    top_skills: List[str],
    focus: str,
    properties_focus: str,
    files: List[str],
    persona_id: str = ""
) -> str:
    """
    Build ultra-minimal prompt with file references + domain guidance.

    The "Plinko chip" approach: Each persona gets specific starting guidance
    that steers them toward relevant code paths based on their expertise.

    Args:
        persona_name: Persona identity
        top_skills: Top 3 skills
        focus: One-line focus area
        properties_focus: Properties to verify
        files: List of file paths to review
        persona_id: Persona ID for domain-specific guidance

    Returns:
        Prompt (~500 tokens with guidance vs 12,000 with full contents)
    """

    # Build file metadata
    file_lines = []
    for filepath in files:
        line_count = count_file_lines(filepath)
        # Show relative path if possible
        try:
            rel_path = str(Path(filepath).relative_to(Path.cwd()))
        except:
            rel_path = filepath

        file_lines.append(f"  • {rel_path} ({line_count} lines)")

    files_text = "\n".join(file_lines)
    skills_text = " | ".join(top_skills[:3])

    # Get domain-specific focus areas (what to look for, not how to find it)
    domain_focus = get_domain_focus_areas(focus)

    return f"""You are {persona_name}, expert code reviewer.

EXPERTISE: {skills_text}
FOCUS: {focus}
TARGET: {properties_focus}

FILES AVAILABLE:
{files_text}

YOUR DOMAIN FOCUS:
{domain_focus}

These are the areas that matter for {properties_focus} from your perspective.
Use Grep/Read tools to explore code relevant to your expertise.

TOOLS:
• Grep - Search for patterns: Grep(pattern="your_pattern", path=".")
• Read - Examine files: Read(file_path="path/to/file.py", offset=100, limit=50)
• Glob - Find files: Glob(pattern="**/*.py")

REVIEW APPROACH:
1. Identify which files/areas are most relevant to your domain
2. Use tools to examine those areas (~200-500 lines total)
3. Provide focused feedback on what you found

OUTPUT (JSON):
{{
  "score": 0-10,
  "passed": true/false,
  "summary": "your verdict",
  "reasoning": "based on code you examined",
  "comments": [{{"file": "path", "line": 0, "severity": "critical|high|medium|low|info", "message": "issue", "suggestion": "fix"}}],
  "files_reviewed": ["files you examined"]
}}

SEVERITY:
• critical: bugs, security vulnerabilities, data loss
• high: design flaws, performance issues
• medium: code quality, maintainability
• low: style, minor improvements
• info: observations, suggestions

Begin your review. Use tools to examine code relevant to your expertise."""


def estimate_token_savings():
    """Calculate token savings from file reference approach"""

    # Scenario: 6 files, average 300 lines each
    num_files = 6
    avg_lines = 300

    # Current approach: full contents
    current = {
        "system_prompt": 206,
        "file_contents": num_files * avg_lines * 4,  # ~4 chars/token
        "total": 0
    }
    current["total"] = current["system_prompt"] + current["file_contents"]

    # File reference approach
    file_ref = {
        "system_prompt": 206,
        "file_metadata": 100,  # Just paths + line counts
        "selective_reads": 1200,  # Persona reads ~3 files worth
        "total": 0
    }
    file_ref["total"] = file_ref["system_prompt"] + file_ref["file_metadata"] + file_ref["selective_reads"]

    reduction_pct = ((current["total"] - file_ref["total"]) / current["total"]) * 100

    return {
        "current": current,
        "file_ref": file_ref,
        "savings": current["total"] - file_ref["total"],
        "reduction_pct": reduction_pct
    }


if __name__ == "__main__":
    # Demo
    savings = estimate_token_savings()

    print("File Reference Prompts - Token Savings")
    print("=" * 60)
    print(f"\nCurrent approach (full contents):")
    print(f"  System prompt: {savings['current']['system_prompt']:,} tokens")
    print(f"  File contents: {savings['current']['file_contents']:,} tokens")
    print(f"  Total: {savings['current']['total']:,} tokens")

    print(f"\nFile reference approach:")
    print(f"  System prompt: {savings['file_ref']['system_prompt']:,} tokens")
    print(f"  File metadata: {savings['file_ref']['file_metadata']:,} tokens")
    print(f"  Selective reads: {savings['file_ref']['selective_reads']:,} tokens")
    print(f"  Total: {savings['file_ref']['total']:,} tokens")

    print(f"\nSavings: {savings['savings']:,} tokens ({savings['reduction_pct']:.1f}% reduction)")

    print("\n" + "=" * 60)
    print("Example prompt:")
    print("=" * 60)

    prompt = build_file_reference_prompt(
        persona_name="Alice Chen, Security Architect",
        top_skills=["AppSec (Expert)", "Threat Modeling (Expert)", "Cryptography (Advanced)"],
        focus="Security vulnerabilities and attack vectors",
        properties_focus="SECURITY, DATA_PROTECTION",
        files=[
            "/Users/sam/repos/wfc/wfc/personas/token_manager.py",
            "/Users/sam/repos/wfc/wfc/personas/ultra_minimal_prompts.py",
            "/Users/sam/repos/wfc/pyproject.toml"
        ]
    )

    print(prompt)
    print("\n" + "=" * 60)
    print(f"Prompt length: {len(prompt)} chars (~{len(prompt)//4} tokens)")
    print("=" * 60)
    print("\nPersona would then use Read tool to examine specific files")
    print("and only load what they need for their review!")
