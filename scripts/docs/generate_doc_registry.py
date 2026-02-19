#!/usr/bin/env python3
"""
Generate progressive documentation registry for WFC.

Scans docs/ directory and creates:
- REGISTRY.json: Machine-readable index with summaries
- REGISTRY.md: Human-readable index

Similar to persona registry but for documentation.
"""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class DocMetadata:
    """Metadata for a documentation file"""

    id: str
    path: str
    title: str
    summary: str
    topics: List[str]
    skills: List[str]
    size_lines: int
    size_tokens: int
    category: str


def extract_title_from_file(file_path: Path) -> str:
    """Extract title from markdown file (first # heading)"""
    try:
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("# "):
                    return line[2:].strip()
    except OSError:
        pass
    except Exception as exc:
        logger.warning("Unexpected error reading title from %s: %s", file_path, exc)
    return file_path.stem.replace("_", " ").replace("-", " ").title()


def extract_summary_from_file(file_path: Path, max_chars: int = 150) -> str:
    """Extract summary from markdown file (first paragraph after title)"""
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        summary_lines = []
        started = False

        for line in lines:
            line = line.strip()

            if line.startswith("# "):
                started = True
                continue

            if not started or not line:
                continue

            if line.startswith("#") or line.startswith("```"):
                break

            summary_lines.append(line)

            if len(" ".join(summary_lines)) >= max_chars:
                break

        summary = " ".join(summary_lines)

        if len(summary) > max_chars:
            summary = summary[:max_chars].rsplit(" ", 1)[0] + "..."

        return summary or "Documentation file"

    except OSError:
        return "Documentation file"
    except Exception as exc:
        logger.warning("Unexpected error reading summary from %s: %s", file_path, exc)
        return "Documentation file"


def extract_topics_from_file(file_path: Path) -> List[str]:
    """Extract topics from filename and content"""
    topics = []

    name_parts = file_path.stem.lower().replace("_", "-").split("-")
    topics.extend(name_parts)

    keywords = [
        "plan",
        "implement",
        "review",
        "test",
        "security",
        "architecture",
        "orchestrator",
        "agent",
        "persona",
        "delegation",
        "task",
        "tdd",
        "merge",
        "rollback",
        "quality",
        "observability",
        "threat",
        "ears",
    ]

    try:
        content = file_path.read_text(encoding="utf-8").lower()
        for keyword in keywords:
            if keyword in content and keyword not in topics:
                topics.append(keyword)
    except OSError:
        pass
    except Exception as exc:
        logger.warning("Unexpected error extracting topics from %s: %s", file_path, exc)

    return sorted(set(topics))[:10]


def extract_skills_from_file(file_path: Path) -> List[str]:
    """Extract related WFC skills from content"""
    skills = []
    skill_patterns = [
        "wfc-plan",
        "wfc-implement",
        "wfc-review",
        "wfc-test",
        "wfc-security",
        "wfc-architecture",
        "wfc-observe",
        "wfc-validate",
        "wfc-safeclaude",
        "wfc-retro",
        "wfc-newskill",
    ]

    try:
        content = file_path.read_text(encoding="utf-8").lower()
        for skill in skill_patterns:
            if skill in content and skill not in skills:
                skills.append(skill)
    except OSError:
        pass
    except Exception as exc:
        logger.warning("Unexpected error extracting skills from %s: %s", file_path, exc)

    return sorted(skills)


def categorize_doc(file_path: Path) -> str:
    """Categorize documentation file"""
    path_str = str(file_path).lower()

    if "example" in path_str:
        return "example"
    elif any(x in path_str for x in ["architecture", "design", "adr"]):
        return "architecture"
    elif any(x in file_path.stem.lower() for x in ["guide", "quickstart", "install", "tutorial"]):
        return "guide"
    else:
        return "reference"


def scan_docs_directory(docs_dir: Path) -> List[DocMetadata]:
    """Scan docs directory and collect metadata"""
    docs = []

    md_files = sorted(docs_dir.rglob("*.md"))

    for md_file in md_files:
        if md_file.name.startswith("REGISTRY"):
            continue

        try:
            lines = len(md_file.read_text(encoding="utf-8").splitlines())
        except Exception:
            lines = 0

        tokens = lines * 8

        rel_path = md_file.relative_to(docs_dir)
        doc_id = str(rel_path).replace("/", "_").replace(".md", "").lower()

        metadata = DocMetadata(
            id=doc_id,
            path=str(rel_path),
            title=extract_title_from_file(md_file),
            summary=extract_summary_from_file(md_file),
            topics=extract_topics_from_file(md_file),
            skills=extract_skills_from_file(md_file),
            size_lines=lines,
            size_tokens=tokens,
            category=categorize_doc(md_file),
        )

        docs.append(metadata)

    return docs


def _savings_percent(docs: List[DocMetadata]) -> float:
    """Compute token savings percentage, returning 0.0 if total tokens is zero."""
    total_tokens = sum(d.size_tokens for d in docs)
    if total_tokens == 0:
        return 0.0
    return round((1 - (len(docs) * 100) / total_tokens) * 100, 1)


def generate_registry_json(docs: List[DocMetadata], output_path: Path) -> None:
    """Generate REGISTRY.json"""
    registry = {
        "version": "1.0.0",
        "generated": "auto-generated by scripts/docs/generate_doc_registry.py",
        "total_docs": len(docs),
        "total_lines": sum(d.size_lines for d in docs),
        "total_tokens_full": sum(d.size_tokens for d in docs),
        "total_tokens_summaries": len(docs) * 100,
        "savings_percent": _savings_percent(docs),
        "docs": [asdict(d) for d in docs],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)

    print(f"✅ Generated {output_path}")
    print(f"   - {len(docs)} docs indexed")
    print(f"   - {registry['total_lines']:,} total lines")
    print(f"   - {registry['total_tokens_full']:,} tokens (full)")
    print(f"   - {registry['total_tokens_summaries']:,} tokens (summaries)")
    print(f"   - {registry['savings_percent']}% token savings")


def generate_registry_markdown(docs: List[DocMetadata], output_path: Path) -> None:
    """Generate REGISTRY.md"""
    lines = [
        "# WFC Documentation Registry",
        "",
        "Auto-generated index of all WFC documentation.",
        "",
        f"**Total Docs:** {len(docs)}",
        f"**Total Lines:** {sum(d.size_lines for d in docs):,}",
        f"**Total Tokens (Full):** {sum(d.size_tokens for d in docs):,}",
        f"**Total Tokens (Summaries):** {len(docs) * 100:,}",
        f"**Token Savings:** {_savings_percent(docs)}%",
        "",
        "---",
        "",
    ]

    categories = {}
    for doc in docs:
        categories.setdefault(doc.category, []).append(doc)

    for category, cat_docs in sorted(categories.items()):
        lines.extend(
            [
                f"## {category.title()} ({len(cat_docs)} docs)",
                "",
            ]
        )

        for doc in sorted(cat_docs, key=lambda d: d.title):
            lines.extend(
                [
                    f"### {doc.title}",
                    f"- **Path:** `{doc.path}`",
                    f"- **ID:** `{doc.id}`",
                    f"- **Summary:** {doc.summary}",
                    f"- **Size:** {doc.size_lines} lines (~{doc.size_tokens:,} tokens)",
                    f"- **Topics:** {', '.join(doc.topics) if doc.topics else 'N/A'}",
                    f"- **Skills:** {', '.join(doc.skills) if doc.skills else 'N/A'}",
                    "",
                ]
            )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ Generated {output_path}")


def main():
    """Main entry point"""
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    docs_dir = repo_root / "docs"

    if not docs_dir.exists():
        print(f"❌ Error: docs directory not found at {docs_dir}")
        return 1

    print(f"📁 Scanning {docs_dir}")

    docs = scan_docs_directory(docs_dir)

    if not docs:
        print("⚠️  No documentation files found")
        return 1

    reference_dir = docs_dir / "reference"
    reference_dir.mkdir(parents=True, exist_ok=True)
    generate_registry_json(docs, reference_dir / "REGISTRY.json")
    generate_registry_markdown(docs, reference_dir / "REGISTRY.md")

    print("\n✅ Documentation registry generated successfully!")
    print("\nUsage:")
    print("  from wfc.shared.doc_loader import DocLoader")
    print("  loader = DocLoader()")
    print("  doc = loader.load_doc('orchestrator_delegation_demo')")

    return 0


if __name__ == "__main__":
    exit(main())
