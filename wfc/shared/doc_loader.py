"""
Progressive documentation loader for WFC.

Loads doc summaries first, fetches full content on-demand.
Similar to persona loader but for documentation.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DocSummary:
    """Lightweight doc summary for progressive disclosure"""

    id: str
    path: str
    title: str
    summary: str
    topics: List[str]
    skills: List[str]
    size_lines: int
    size_tokens: int
    category: str

    @classmethod
    def from_dict(cls, data: dict) -> "DocSummary":
        """Create from registry dict"""
        return cls(
            id=data["id"],
            path=data["path"],
            title=data["title"],
            summary=data["summary"],
            topics=data["topics"],
            skills=data["skills"],
            size_lines=data["size_lines"],
            size_tokens=data["size_tokens"],
            category=data["category"],
        )


@dataclass
class Doc:
    """Full documentation with content"""

    metadata: DocSummary
    content: str

    @property
    def id(self) -> str:
        return self.metadata.id

    @property
    def title(self) -> str:
        return self.metadata.title

    @property
    def topics(self) -> List[str]:
        return self.metadata.topics

    @property
    def skills(self) -> List[str]:
        return self.metadata.skills


class DocLoader:
    """
    Progressive documentation loader.

    Loads summaries first (low tokens), fetches full content on-demand.
    """

    def __init__(self, docs_dir: Optional[Path] = None):
        """
        Initialize doc loader.

        Args:
            docs_dir: Path to docs directory (auto-detected if None)
        """
        if docs_dir is None:
            # Auto-detect docs directory
            # Try multiple locations for flexibility
            possible_paths = [
                Path.cwd() / "docs",
                Path(__file__).parent.parent.parent / "docs",
                Path.home() / ".claude/skills/wfc/docs",
                Path.home() / ".wfc/docs",
            ]

            for path in possible_paths:
                if (path / "reference" / "REGISTRY.json").exists():
                    docs_dir = path
                    break

            if docs_dir is None:
                raise FileNotFoundError("Could not find docs/reference/REGISTRY.json")

        self.docs_dir = docs_dir
        self.registry_path = docs_dir / "reference" / "REGISTRY.json"

        if not self.registry_path.exists():
            raise FileNotFoundError(f"Registry not found: {self.registry_path}")

        # Load registry
        with open(self.registry_path) as f:
            self.registry = json.load(f)

        # Create summary index
        self.summaries = {doc["id"]: DocSummary.from_dict(doc) for doc in self.registry["docs"]}

        # Cache for loaded docs
        self._cache: Dict[str, Doc] = {}

    def list_summaries(
        self,
        category: Optional[str] = None,
        skill: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> List[DocSummary]:
        """
        List doc summaries (progressive disclosure - lightweight).

        Args:
            category: Filter by category (guide, example, reference, architecture)
            skill: Filter by related skill (e.g., 'wfc-implement')
            topic: Filter by topic (e.g., 'orchestrator', 'delegation')

        Returns:
            List of doc summaries
        """
        summaries = list(self.summaries.values())

        if category:
            summaries = [s for s in summaries if s.category == category]

        if skill:
            summaries = [s for s in summaries if skill in s.skills]

        if topic:
            summaries = [s for s in summaries if topic in s.topics]

        return sorted(summaries, key=lambda s: s.title)

    def load_doc(self, doc_id: str) -> Doc:
        """
        Load full documentation by ID.

        Uses cache to avoid re-reading files.

        Args:
            doc_id: Document ID from registry

        Returns:
            Full Doc with content

        Raises:
            KeyError: If doc_id not found in registry
        """
        # Check cache first
        if doc_id in self._cache:
            return self._cache[doc_id]

        # Get summary
        if doc_id not in self.summaries:
            raise KeyError(f"Doc not found: {doc_id}")

        summary = self.summaries[doc_id]

        # Load content
        doc_path = self.docs_dir / summary.path
        if not doc_path.exists():
            raise FileNotFoundError(f"Doc file not found: {doc_path}")

        content = doc_path.read_text()

        # Create Doc
        doc = Doc(metadata=summary, content=content)

        # Cache it
        self._cache[doc_id] = doc

        return doc

    def search(
        self, query: str, category: Optional[str] = None, max_results: int = 5
    ) -> List[DocSummary]:
        """
        Search docs by keyword (searches title, summary, topics).

        Args:
            query: Search keyword
            category: Optional category filter
            max_results: Maximum results to return

        Returns:
            List of matching doc summaries, sorted by relevance
        """
        query_lower = query.lower()
        results = []

        for summary in self.summaries.values():
            # Category filter
            if category and summary.category != category:
                continue

            # Calculate relevance score
            score = 0

            # Title match (highest weight)
            if query_lower in summary.title.lower():
                score += 10

            # Summary match
            if query_lower in summary.summary.lower():
                score += 5

            # Topic match
            if any(query_lower in topic.lower() for topic in summary.topics):
                score += 3

            # Skill match
            if any(query_lower in skill.lower() for skill in summary.skills):
                score += 3

            if score > 0:
                results.append((score, summary))

        # Sort by relevance
        results.sort(key=lambda x: x[0], reverse=True)

        return [summary for _, summary in results[:max_results]]

    def get_stats(self) -> Dict:
        """Get registry statistics"""
        return {
            "total_docs": self.registry["total_docs"],
            "total_lines": self.registry["total_lines"],
            "total_tokens_full": self.registry["total_tokens_full"],
            "total_tokens_summaries": self.registry["total_tokens_summaries"],
            "savings_percent": self.registry["savings_percent"],
            "categories": self._count_by_category(),
        }

    def _count_by_category(self) -> Dict[str, int]:
        """Count docs by category"""
        counts = {}
        for summary in self.summaries.values():
            counts[summary.category] = counts.get(summary.category, 0) + 1
        return counts


# Convenience function for quick access
def load_doc(doc_id: str, docs_dir: Optional[Path] = None) -> Doc:
    """
    Load a doc by ID (convenience function).

    Args:
        doc_id: Document ID
        docs_dir: Optional docs directory path

    Returns:
        Full Doc with content
    """
    loader = DocLoader(docs_dir)
    return loader.load_doc(doc_id)


def search_docs(query: str, max_results: int = 5) -> List[DocSummary]:
    """
    Search docs by keyword (convenience function).

    Args:
        query: Search keyword
        max_results: Maximum results

    Returns:
        List of matching doc summaries
    """
    loader = DocLoader()
    return loader.search(query, max_results=max_results)


# Example usage
if __name__ == "__main__":
    loader = DocLoader()

    print("📊 Registry Stats:")
    stats = loader.get_stats()
    print(f"  Total docs: {stats['total_docs']}")
    print(f"  Total lines: {stats['total_lines']:,}")
    print(f"  Full load: {stats['total_tokens_full']:,} tokens")
    print(f"  Summaries: {stats['total_tokens_summaries']:,} tokens")
    print(f"  Savings: {stats['savings_percent']}%")
    print("\nCategories:")
    for cat, count in stats["categories"].items():
        print(f"  - {cat}: {count} docs")

    print("\n🔍 Search: 'orchestrator'")
    results = loader.search("orchestrator", max_results=3)
    for summary in results:
        print(f"  - {summary.title} ({summary.category})")
        print(f"    {summary.summary}")

    print("\n📄 Load full doc: 'examples_orchestrator_delegation_demo'")
    doc = loader.load_doc("examples_orchestrator_delegation_demo")
    print(f"  Title: {doc.title}")
    print(f"  Size: {doc.metadata.size_lines} lines")
    print(f"  Content preview: {doc.content[:200]}...")
