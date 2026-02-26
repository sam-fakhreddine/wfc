"""corpus.py — Skill validation corpus management (load, validate, append)."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

_REQUIRED_ENTRY_FIELDS: tuple[str, ...] = (
    "message",
    "skill",
    "routing_label",
    "run_timestamp",
    "source_run_id",
)

_VALID_ROUTING_LABELS: frozenset[str] = frozenset({"match", "non-match"})


def get_corpus_path(repo: str) -> Path:
    """Return the canonical corpus JSON path for a repository.

    Args:
        repo: Repository name (e.g. "wfc").

    Returns:
        Path to ``~/.wfc/projects/{repo}/skill-validation-corpus.json``.
    """
    return Path.home() / ".wfc" / "projects" / repo / "skill-validation-corpus.json"


def _empty_corpus() -> dict:
    """Return an empty corpus dict matching the schema."""
    return {"version": 1, "entries": []}


def load_corpus(path: Path) -> dict:
    """Load a corpus JSON file, returning an empty corpus if it does not exist.

    Args:
        path: Path to the corpus JSON file.

    Returns:
        Corpus dict with ``"version"`` and ``"entries"`` keys.
    """
    if not path.exists():
        return _empty_corpus()

    text = path.read_text(encoding="utf-8")
    data: dict = json.loads(text)
    return data


def validate_entry(entry: dict) -> None:
    """Validate that a corpus entry contains all required fields.

    Args:
        entry: A single corpus entry dict.

    Raises:
        ValueError: Naming the first missing required field.
    """
    for field in _REQUIRED_ENTRY_FIELDS:
        if field not in entry:
            raise ValueError(
                f"Corpus entry is missing required field: '{field}'. "
                f"Entry keys present: {list(entry.keys())}"
            )
    routing_label = entry.get("routing_label")
    if routing_label not in _VALID_ROUTING_LABELS:
        raise ValueError(
            f"Invalid routing_label {routing_label!r}. "
            f"Must be one of: {sorted(_VALID_ROUTING_LABELS)}"
        )


def append_entries(corpus_path: Path, new_entries: list[dict]) -> None:
    """Append new entries to the corpus with deduplication.

    Deduplication key: (message, skill, routing_label).
    On collision: keep the entry with the **latest** ``run_timestamp`` and
    update ``source_run_id`` to the newer value.

    The write is atomic: data is written to a temp file (same directory,
    uuid4 suffix) then ``os.rename()`` to the final path.  The temp file
    is cleaned up via try/finally on any failure.

    Args:
        corpus_path: Path to the corpus JSON file (need not exist yet).
        new_entries: List of new entry dicts to merge in.

    Raises:
        ValueError: If any entry in ``new_entries`` fails validation.
    """
    for entry in new_entries:
        validate_entry(entry)

    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus = load_corpus(corpus_path)

    index: dict[tuple, dict] = {}
    for entry in corpus.get("entries", []):
        key: tuple = (entry["message"], entry["skill"], entry["routing_label"])
        index[key] = entry

    for entry in new_entries:
        key = (entry["message"], entry["skill"], entry["routing_label"])
        if key in index:
            existing = index[key]
            if entry["run_timestamp"] >= existing["run_timestamp"]:
                index[key] = {**existing, **entry}
        else:
            index[key] = entry

    corpus["entries"] = list(index.values())

    tmp_path = corpus_path.parent / f".corpus-tmp-{uuid.uuid4().hex}.json"
    try:
        tmp_path.write_text(
            json.dumps(corpus, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        os.rename(tmp_path, corpus_path)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    os.chmod(corpus_path, 0o600)
