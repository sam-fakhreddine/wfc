"""Tests for corpus — skill validation corpus load, validate, and append."""

from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest

from wfc.scripts.orchestrators.skill_validator_llm.corpus import (
    append_entries,
    get_corpus_path,
    load_corpus,
    validate_entry,
)


def _make_entry(
    message: str = "do something",
    skill: str = "wfc-test",
    routing_label: str = "match",
    run_timestamp: str = "2026-02-25T00:00:00Z",
    source_run_id: str = "run-001",
) -> dict:
    return {
        "message": message,
        "skill": skill,
        "routing_label": routing_label,
        "run_timestamp": run_timestamp,
        "source_run_id": source_run_id,
    }


def test_get_corpus_path_structure(tmp_path: Path) -> None:
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        path = get_corpus_path("wfc")

    assert path.name == "skill-validation-corpus.json"
    assert ".wfc" in path.parts
    assert "projects" in path.parts
    assert "wfc" in path.parts


def test_load_corpus_missing_file_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / "nonexistent.json"
    result = load_corpus(path)
    assert result == {"version": 1, "entries": []}


def test_load_corpus_existing_file(tmp_path: Path) -> None:
    corpus = {"version": 1, "entries": [_make_entry()]}
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(corpus), encoding="utf-8")

    result = load_corpus(path)
    assert result["version"] == 1
    assert len(result["entries"]) == 1


def test_load_corpus_returns_dict(tmp_path: Path) -> None:
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps({"version": 1, "entries": []}), encoding="utf-8")
    result = load_corpus(path)
    assert isinstance(result, dict)


def test_validate_entry_valid() -> None:
    validate_entry(_make_entry())


def test_validate_entry_missing_message_raises() -> None:
    entry = _make_entry()
    del entry["message"]
    with pytest.raises(ValueError, match="message"):
        validate_entry(entry)


def test_validate_entry_missing_skill_raises() -> None:
    entry = _make_entry()
    del entry["skill"]
    with pytest.raises(ValueError, match="skill"):
        validate_entry(entry)


def test_validate_entry_missing_routing_label_raises() -> None:
    entry = _make_entry()
    del entry["routing_label"]
    with pytest.raises(ValueError, match="routing_label"):
        validate_entry(entry)


def test_validate_entry_missing_run_timestamp_raises() -> None:
    entry = _make_entry()
    del entry["run_timestamp"]
    with pytest.raises(ValueError, match="run_timestamp"):
        validate_entry(entry)


def test_validate_entry_missing_source_run_id_raises() -> None:
    entry = _make_entry()
    del entry["source_run_id"]
    with pytest.raises(ValueError, match="source_run_id"):
        validate_entry(entry)


def test_validate_entry_invalid_routing_label_raises() -> None:
    entry = _make_entry(routing_label="wrong")
    with pytest.raises(ValueError, match="routing_label"):
        validate_entry(entry)


def test_validate_entry_non_match_label_valid() -> None:
    validate_entry(_make_entry(routing_label="non-match"))


def test_append_entries_creates_file(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    append_entries(corpus_path, [_make_entry()])
    assert corpus_path.exists()


def test_append_entries_new_corpus(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    entry = _make_entry(message="hello world", skill="wfc-build")
    append_entries(corpus_path, [entry])

    result = load_corpus(corpus_path)
    assert len(result["entries"]) == 1
    assert result["entries"][0]["message"] == "hello world"


def test_append_entries_adds_to_existing(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    existing = {"version": 1, "entries": [_make_entry(message="first")]}
    corpus_path.write_text(json.dumps(existing), encoding="utf-8")

    append_entries(corpus_path, [_make_entry(message="second")])

    result = load_corpus(corpus_path)
    messages = {e["message"] for e in result["entries"]}
    assert "first" in messages
    assert "second" in messages


def test_append_entries_dedup_keeps_newer_timestamp(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    old_entry = _make_entry(run_timestamp="2026-01-01T00:00:00Z", source_run_id="old")
    corpus_path.write_text(json.dumps({"version": 1, "entries": [old_entry]}), encoding="utf-8")

    new_entry = _make_entry(run_timestamp="2026-02-01T00:00:00Z", source_run_id="new")
    append_entries(corpus_path, [new_entry])

    result = load_corpus(corpus_path)
    assert len(result["entries"]) == 1
    assert result["entries"][0]["source_run_id"] == "new"


def test_append_entries_dedup_keeps_older_if_newer_is_earlier(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    existing = _make_entry(run_timestamp="2026-03-01T00:00:00Z", source_run_id="newer")
    corpus_path.write_text(json.dumps({"version": 1, "entries": [existing]}), encoding="utf-8")

    older_entry = _make_entry(run_timestamp="2026-01-01T00:00:00Z", source_run_id="older")
    append_entries(corpus_path, [older_entry])

    result = load_corpus(corpus_path)
    assert len(result["entries"]) == 1
    assert result["entries"][0]["source_run_id"] == "newer"


def test_append_entries_file_permissions(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    append_entries(corpus_path, [_make_entry()])

    mode = stat.S_IMODE(corpus_path.stat().st_mode)
    assert mode == 0o600, f"Expected 0o600, got 0o{mode:o}"


def test_append_entries_creates_parent_dirs(tmp_path: Path) -> None:
    corpus_path = tmp_path / "deep" / "nested" / "corpus.json"
    append_entries(corpus_path, [_make_entry()])
    assert corpus_path.exists()


def test_append_entries_invalid_entry_raises_before_write(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    bad_entry = {"message": "oops"}

    with pytest.raises(ValueError):
        append_entries(corpus_path, [bad_entry])

    assert not corpus_path.exists()


def test_append_entries_multiple_new_entries(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    entries = [_make_entry(message=f"msg-{i}", skill="wfc-test") for i in range(5)]
    append_entries(corpus_path, entries)

    result = load_corpus(corpus_path)
    assert len(result["entries"]) == 5


def test_append_entries_no_temp_file_left_on_success(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    append_entries(corpus_path, [_make_entry()])

    temp_files = list(tmp_path.glob(".corpus-tmp-*.json"))
    assert temp_files == [], f"Temp files left behind: {temp_files}"
