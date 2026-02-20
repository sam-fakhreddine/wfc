# WFC Documentation Registry - Usage Guide

Progressive documentation loading for 96.5% token savings.

## Quick Start

```python
from wfc.shared.doc_loader import DocLoader

# Initialize loader (auto-detects docs directory)
loader = DocLoader()

# List all doc summaries (lightweight - only ~100 tokens per doc)
summaries = loader.list_summaries()
for summary in summaries:
    print(f"{summary.title}: {summary.summary}")

# Load full doc content (on-demand)
doc = loader.load_doc('examples_orchestrator_delegation_demo')
print(doc.content)  # Full markdown content
```

## Token Savings

| Metric | Value |
|--------|-------|
| **Total docs** | 22 |
| **Total lines** | 7,804 |
| **Full load** | 62,432 tokens |
| **Summaries only** | 2,200 tokens |
| **Savings** | **96.5%** |

## API Reference

### DocLoader

```python
loader = DocLoader(docs_dir=None)  # Auto-detects if None
```

#### List Summaries (Lightweight)

```python
# All docs
all_docs = loader.list_summaries()

# Filter by category
guides = loader.list_summaries(category='guide')
examples = loader.list_summaries(category='example')
architecture = loader.list_summaries(category='architecture')
reference = loader.list_summaries(category='reference')

# Filter by skill
implement_docs = loader.list_summaries(skill='wfc-implement')
review_docs = loader.list_summaries(skill='wfc-review')

# Filter by topic
orchestrator_docs = loader.list_summaries(topic='orchestrator')
tdd_docs = loader.list_summaries(topic='tdd')
```

#### Search Docs

```python
# Search by keyword
results = loader.search('orchestrator', max_results=5)

# Search within category
guides = loader.search('install', category='guide')
```

#### Load Full Doc

```python
# Load by ID (from registry)
doc = loader.load_doc('examples_orchestrator_delegation_demo')

# Access metadata
print(doc.title)           # "WFC Orchestrator Delegation..."
print(doc.topics)          # ['orchestrator', 'delegation', ...]
print(doc.skills)          # ['wfc-implement']
print(doc.content)         # Full markdown content
```

#### Get Stats

```python
stats = loader.get_stats()
print(f"Total docs: {stats['total_docs']}")
print(f"Token savings: {stats['savings_percent']}%")
print(f"Categories: {stats['categories']}")
```

## Convenience Functions

```python
from wfc.shared.doc_loader import load_doc, search_docs

# Quick load
doc = load_doc('examples_task_tool_demo')

# Quick search
results = search_docs('delegation', max_results=3)
```

## DocSummary Fields

```python
summary.id              # 'examples_orchestrator_delegation_demo'
summary.path            # 'examples/orchestrator_delegation_demo.md'
summary.title           # 'WFC Orchestrator Delegation...'
summary.summary         # First paragraph (150 chars max)
summary.topics          # ['orchestrator', 'delegation', 'task', ...]
summary.skills          # ['wfc-implement']
summary.size_lines      # 347
summary.size_tokens     # 2776 (estimated)
summary.category        # 'example'
```

## Categories

- **guide** - Installation, quickstart, tutorials
- **example** - Working examples, demos
- **architecture** - Architecture docs, ADRs, design
- **reference** - Technical references, specs

## Integration with Skills

Skills can use progressive doc loading to minimize context:

```python
# Instead of this (loads full 62K tokens):
# Read all docs at once ❌

# Do this (loads only what's needed):
loader = DocLoader()

# Step 1: List relevant docs (2.2K tokens)
summaries = loader.list_summaries(skill='wfc-implement')
print("Available docs:")
for s in summaries:
    print(f"  - {s.title}: {s.summary}")

# Step 2: Load only the doc user needs (on-demand)
if user_wants_delegation_guide:
    doc = loader.load_doc('examples_orchestrator_delegation_demo')
    # Now you have full content (2.8K tokens)
```

## Regenerating Registry

After adding/modifying docs:

```bash
python3 scripts/docs/generate_doc_registry.py
```

This will:

1. Scan `docs/` directory
2. Extract titles, summaries, topics
3. Generate `docs/reference/REGISTRY.json` (machine-readable)
4. Generate `docs/reference/REGISTRY.md` (human-readable)

## Example: Skill Integration

```python
# In a skill prompt
from wfc.shared.doc_loader import DocLoader

loader = DocLoader()

# List docs about the current task
docs = loader.list_summaries(topic='orchestrator')

# Show user which docs are available (lightweight)
print("📚 Related documentation:")
for doc in docs:
    print(f"  • {doc.title}")
    print(f"    {doc.summary}")

# If user asks for details, load full doc
if user_asks_about_delegation:
    doc = loader.load_doc('examples_orchestrator_delegation_demo')
    # Use doc.content for detailed explanation
```

## Benefits

### ✅ Token Efficiency

Load only what you need, when you need it.

### ✅ Fast Context Loading

2.2K tokens for all summaries vs 62K for full docs.

### ✅ Searchable

Find docs by keyword, skill, topic, or category.

### ✅ Auto-Indexed

Run generator script to update registry automatically.

### ✅ Cached

Loaded docs cached in memory for session.

## Comparison: Before vs After

### Before (No Registry)

```python
# Load all docs (62K tokens)
quickstart = Path('docs/QUICKSTART.md').read_text()
install = Path('docs/workflow/UNIVERSAL_INSTALL.md').read_text()
architecture = Path('docs/architecture/ARCHITECTURE.md').read_text()
# ... 19 more files

# ❌ 62,432 tokens loaded
# ❌ Slow
# ❌ Context bloat
```

### After (With Registry)

```python
loader = DocLoader()

# List summaries (2.2K tokens)
summaries = loader.list_summaries()

# Load only what you need
doc = loader.load_doc('quickstart')

# ✅ 96.5% token savings
# ✅ Fast
# ✅ Minimal context
```

---

**Progressive disclosure: Load summaries first, fetch details on-demand.**

Similar pattern to persona registry but for documentation.
