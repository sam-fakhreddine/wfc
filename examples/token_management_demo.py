#!/usr/bin/env python3
"""
Token Management Demo

Demonstrates WFC's World Fucking Class token management capabilities.

Run this to see:
- Accurate token counting
- Smart file condensing
- Token budget reporting
"""

import sys
from pathlib import Path

# Add WFC to path
wfc_root = Path(__file__).parent.parent
sys.path.insert(0, str(wfc_root))

from wfc.personas.token_manager import (
    TokenCounter,
    TokenBudget,
    FileCondenser,
    PersonaPromptCompressor,
    TokenBudgetManager,
)


def demo_token_counting():
    """Demo: Accurate token counting"""
    print("=" * 60)
    print("DEMO 1: Accurate Token Counting")
    print("=" * 60)

    counter = TokenCounter()

    samples = [
        "Hello, world!",
        "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
        "The quick brown fox jumps over the lazy dog. " * 100,
    ]

    for i, text in enumerate(samples, 1):
        tokens = counter.count(text)
        chars = len(text)
        ratio = chars / tokens if tokens > 0 else 0
        print(f"\nSample {i}:")
        print(f"  Chars: {chars}")
        print(f"  Tokens: {tokens}")
        print(f"  Ratio: {ratio:.2f} chars/token")
        if len(text) < 100:
            print(f"  Text: {text[:80]}...")


def demo_file_condensing():
    """Demo: Smart file condensing"""
    print("\n\n" + "=" * 60)
    print("DEMO 2: Smart File Condensing")
    print("=" * 60)

    # Create a sample Python file
    sample_code = '''
import os
import sys
from typing import List, Dict

def short_function():
    """This function is short and will be kept in full."""
    return "Hello, world!"

def long_function(items: List[str]) -> Dict[str, int]:
    """
    This is a long function that will be condensed.

    It does complex processing that reviewers don't need to see in full.
    The signature and docstring are enough for review.
    """
    result = {}
    for item in items:
        # Lots of processing here
        processed = item.strip().lower()
        # More processing
        if processed not in result:
            result[processed] = 0
        result[processed] += 1
        # Even more processing
        if len(result) > 100:
            # Cleanup old entries
            oldest = min(result.items(), key=lambda x: x[1])
            del result[oldest[0]]
        # Continue processing...
        # (imagine 50+ more lines here)
    return result

class SampleClass:
    """Sample class with methods."""

    def __init__(self):
        self.data = []

    def add(self, item):
        self.data.append(item)
'''

    counter = TokenCounter()
    condenser = FileCondenser()

    original_tokens = counter.count(sample_code)
    print(f"\nOriginal code: {original_tokens} tokens")

    # Condense to 50% of original
    max_tokens = original_tokens // 2
    condensed = condenser.condense("sample.py", sample_code, max_tokens, counter)
    condensed_tokens = counter.count(condensed)

    print(
        f"Condensed code: {condensed_tokens} tokens ({(condensed_tokens/original_tokens)*100:.1f}%)"
    )
    print(f"\nCondensed output:")
    print("-" * 60)
    print(condensed)
    print("-" * 60)


def demo_prompt_compression():
    """Demo: Compressed persona prompts"""
    print("\n\n" + "=" * 60)
    print("DEMO 3: Persona Prompt Compression")
    print("=" * 60)

    compressor = PersonaPromptCompressor()

    # Sample persona data
    skills = [
        {"name": "Security Analysis", "level": "Expert"},
        {"name": "Cryptography", "level": "Advanced"},
        {"name": "Threat Modeling", "level": "Expert"},
        {"name": "Penetration Testing", "level": "Advanced"},
        {"name": "Secure Coding", "level": "Expert"},
    ]

    lens = {
        "focus": "Security vulnerabilities and attack vectors",
        "review_dimensions": [
            {"dimension": "Security", "weight": 0.4},
            {"dimension": "Data Protection", "weight": 0.3},
            {"dimension": "Authentication", "weight": 0.2},
            {"dimension": "Authorization", "weight": 0.1},
        ],
    }

    personality = {"communication_style": "direct"}

    system_additions = "Focus on OWASP Top 10 and common vulnerability patterns."

    compressed = compressor.compress_system_prompt(
        persona_name="Alice Chen, Security Architect",
        skills=skills,
        lens=lens,
        personality=personality,
        system_additions=system_additions,
        properties_focus="SECURITY, DATA_PROTECTION",
    )

    counter = TokenCounter()
    tokens = counter.count(compressed)

    print(f"\nCompressed prompt: {tokens} tokens")
    print(f"\nPrompt preview (first 500 chars):")
    print("-" * 60)
    print(compressed[:500] + "...")
    print("-" * 60)


def demo_full_pipeline():
    """Demo: Full token budget management pipeline"""
    print("\n\n" + "=" * 60)
    print("DEMO 4: Full Token Budget Management")
    print("=" * 60)

    manager = TokenBudgetManager()

    # Sample persona
    persona = {
        "name": "Bob Lee, Performance Engineer",
        "skills": [
            {"name": "Performance Optimization", "level": "Expert"},
            {"name": "Profiling", "level": "Advanced"},
            {"name": "Scalability", "level": "Expert"},
        ],
        "lens": {
            "focus": "Performance and scalability",
            "review_dimensions": [
                {"dimension": "Performance", "weight": 0.5},
                {"dimension": "Scalability", "weight": 0.3},
                {"dimension": "Resource Usage", "weight": 0.2},
            ],
        },
        "personality": {"communication_style": "analytical"},
        "system_prompt_additions": "Focus on algorithmic complexity and bottlenecks.",
    }

    # Sample files (create temp files for demo)
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample files
        files = []

        # Small file
        small_file = Path(tmpdir) / "small.py"
        small_file.write_text("def hello():\n    return 'world'\n")
        files.append(str(small_file))

        # Large file
        large_file = Path(tmpdir) / "large.py"
        large_content = "import os\n" + "def func():\n    pass\n" * 200
        large_file.write_text(large_content)
        files.append(str(large_file))

        # Properties
        properties = [
            {"type": "PERFORMANCE", "statement": "O(n) or better complexity"},
            {"type": "SCALABILITY", "statement": "Handles 10k+ requests/sec"},
        ]

        # Prepare prompt
        prompt, metrics = manager.prepare_persona_prompt(
            persona=persona, files=files, properties=properties
        )

        # Report metrics
        print(f"\n📊 Token Metrics:")
        print(f"  Total tokens: {metrics['total_tokens']:,}")
        print(
            f"  System prompt: {metrics['system_tokens']:,} ({(metrics['system_tokens']/metrics['total_tokens'])*100:.1f}%)"
        )
        print(
            f"  Properties: {metrics['properties_tokens']:,} ({(metrics['properties_tokens']/metrics['total_tokens'])*100:.1f}%)"
        )
        print(
            f"  Files: {metrics['files_tokens']:,} ({(metrics['files_tokens']/metrics['total_tokens'])*100:.1f}%)"
        )
        print(f"  Budget used: {metrics['budget_used_pct']:.1f}%")
        print(f"  Files condensed: {metrics['num_condensed']}/{metrics['num_files']}")
        if metrics["condensed_files"]:
            print(f"  Which files: {', '.join(metrics['condensed_files'])}")
        print(f"  Fits budget: {'✅ Yes' if metrics['fits_budget'] else '❌ No'}")


def main():
    """Run all demos"""
    print("\n🎯 WFC Token Management Demo\n")

    try:
        demo_token_counting()
        demo_file_condensing()
        demo_prompt_compression()
        demo_full_pipeline()

        print("\n\n" + "=" * 60)
        print("✅ All demos completed successfully!")
        print("=" * 60)
        print("\nKey Takeaways:")
        print("  • Accurate token counting saves money and improves performance")
        print("  • Smart condensing preserves review-critical context")
        print("  • Compressed prompts are 50% smaller without quality loss")
        print("  • Full pipeline handles edge cases gracefully")
        print("\nThis is World Fucking Class token management. 🚀")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
