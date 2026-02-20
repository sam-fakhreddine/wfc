"""Semantic Firewall - UserPromptSubmit hook for WFC.

Reads ``{"prompt": "user text"}`` from stdin, embeds the prompt,
compares against curated attack signatures via cosine similarity,
and blocks / warns / passes accordingly.

Exit codes:
    0 - pass (or warn, or fail-open on any internal error)
    2 - block (prompt too similar to a known attack signature)

Design principles:
    - Fail-open: always exit 0 on internal errors
    - 500ms hard timeout
    - Self-hardening: stores blocked embeddings for future signature curation
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("wfc.security.semantic_firewall")

_SIGNATURES_DIR: Path = Path(__file__).parent / "signatures"
_HARDENED_DIR: Path = Path.home() / ".wfc" / "firewall"
_DEFAULT_THRESHOLD_BLOCK: float = 0.85
_DEFAULT_THRESHOLD_WARN: float = 0.70
_TIMEOUT_MS: int = 500
_FRESHNESS_DAYS: int = 30
_HARDENED_CAP: int = 100

_provider: Any = None
_signature_embeddings: list[list[float]] | None = None
_signature_metadata: list[dict[str, Any]] | None = None


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors. Pure stdlib implementation.

    Returns 0.0 for mismatched lengths or zero-magnitude vectors.
    """
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def _get_provider() -> Any:
    """Lazy-initialise the embedding provider. Returns None on failure."""
    global _provider
    if _provider is not None:
        return _provider
    try:
        from wfc.scripts.knowledge.embeddings import get_embedding_provider

        _provider = get_embedding_provider()
        return _provider
    except Exception:
        logger.debug("Failed to initialise embedding provider", exc_info=True)
        return None


def _load_signatures(provider: Any) -> tuple[list[list[float]], list[dict[str, Any]]]:
    """Load and embed attack signatures from seed_signatures.json.

    Caches results in module-level globals on first successful load.
    Returns (embeddings, metadata) tuples. On any error returns ([], []).
    """
    global _signature_embeddings, _signature_metadata
    if _signature_embeddings is not None:
        return _signature_embeddings, _signature_metadata
    try:
        sig_path = _SIGNATURES_DIR / "seed_signatures.json"
        if not sig_path.exists():
            return [], []

        data = json.loads(sig_path.read_text())
        signatures = data.get("signatures", [])
        if not signatures:
            return [], []

        valid_sigs = [s for s in signatures if s.get("text") and s.get("id")]
        if not valid_sigs:
            return [], []

        texts = [sig["text"] for sig in valid_sigs]
        embeddings = provider.embed(texts)
        metadata = [
            {"id": sig["id"], "category": sig.get("category", "unknown")} for sig in valid_sigs
        ]
        _signature_embeddings = embeddings
        _signature_metadata = metadata
        return embeddings, metadata
    except Exception:
        logger.debug("Failed to load signatures", exc_info=True)
        return [], []


def _emit_metric(event_type: str, payload: dict[str, Any] | None = None) -> None:
    """Emit an observability event. Never raises."""
    try:
        from wfc.observability.instrument import emit_event

        emit_event(
            event_type,
            source="semantic_firewall",
            payload=payload or {},
        )
    except Exception:
        pass


def _check_freshness() -> None:
    """Check if signatures are stale (> _FRESHNESS_DAYS days old).

    Emits a ``firewall.signatures_stale`` event if so. Never raises.
    """
    try:
        manifest_path = _SIGNATURES_DIR / "manifest.json"
        if not manifest_path.exists():
            return

        manifest = json.loads(manifest_path.read_text())
        updated_epoch = manifest.get("updated_epoch", 0)
        age_days = (time.time() - updated_epoch) / 86400

        if age_days > _FRESHNESS_DAYS:
            from wfc.observability.instrument import emit_event

            emit_event(
                "firewall.signatures_stale",
                source="semantic_firewall",
                payload={"age_days": round(age_days, 1)},
                level="warning",
            )
    except Exception:
        logger.debug("Freshness check failed", exc_info=True)


def _store_hardened_embedding(
    prompt_text: str,
    embedding: list[float],
    similarity: float,
) -> None:
    """Store a blocked prompt's embedding for future signature curation.

    - Deduplicates by SHA-256 hash of prompt text
    - Caps stored entries at _HARDENED_CAP (100)
    - Writes atomically to ~/.wfc/firewall/hardened.json
    - Never raises.
    """
    try:
        import fcntl
        import tempfile as _tempfile

        prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()
        _HARDENED_DIR.mkdir(parents=True, exist_ok=True)
        _HARDENED_DIR.chmod(0o700)
        hardened_path = _HARDENED_DIR / "hardened.json"
        lock_path = _HARDENED_DIR / ".hardened.lock"

        with open(lock_path, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)

            entries: list[dict[str, Any]] = []
            if hardened_path.exists() and not hardened_path.is_symlink():
                try:
                    entries = json.loads(hardened_path.read_text())
                except Exception:
                    entries = []

            if any(e.get("hash") == prompt_hash for e in entries):
                return

            if len(entries) >= _HARDENED_CAP:
                return

            entries.append(
                {
                    "hash": prompt_hash,
                    "embedding": embedding,
                    "similarity": similarity,
                    "timestamp": time.time(),
                }
            )
            fd, tmp_path = _tempfile.mkstemp(dir=str(_HARDENED_DIR))
            try:
                os.fchmod(fd, 0o600)
                os.write(fd, json.dumps(entries).encode())
            finally:
                os.close(fd)
            os.replace(tmp_path, str(hardened_path))
    except Exception:
        logger.debug("Failed to store hardened embedding", exc_info=True)


_MAX_INPUT_SIZE = 1_000_000


def _parse_input() -> str | None:
    """Read stdin, parse JSON, extract prompt text. Returns None to fail-open."""
    raw = sys.stdin.read(_MAX_INPUT_SIZE)
    if not raw or not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    prompt = data.get("prompt", "")
    if not prompt or not prompt.strip():
        return None
    return prompt


def _embed_with_timeout(provider: Any, prompt: str, deadline: float) -> list[float] | None:
    """Embed prompt with remaining-time timeout. Returns None to fail-open."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        _emit_metric("firewall.timeout", {"phase": "pre_embedding"})
        return None
    try:
        from concurrent.futures import ThreadPoolExecutor
        from concurrent.futures import TimeoutError as FuturesTimeoutError

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(provider.embed_query, prompt)
            try:
                result = future.result(timeout=max(0.01, remaining))
            except FuturesTimeoutError:
                _emit_metric("firewall.timeout", {"phase": "embed_query"})
                return None
    except SystemExit:
        raise
    except Exception:
        _emit_metric("firewall.embed_failure")
        return None
    if not isinstance(result, list):
        _emit_metric("firewall.embed_failure", {"reason": "non_list_return"})
        return None
    return result


def _score_signatures(
    prompt_emb: list[float],
    sig_embs: list[list[float]],
    deadline: float,
) -> tuple[float, int] | None:
    """Find best matching signature by cosine similarity. Returns None on timeout."""
    max_similarity = 0.0
    best_match_idx = -1
    for i, sig_emb in enumerate(sig_embs):
        sim = _cosine_similarity(prompt_emb, sig_emb)
        if sim > max_similarity:
            max_similarity = sim
            best_match_idx = i
    if time.monotonic() > deadline:
        _emit_metric("firewall.timeout", {"phase": "post_comparison"})
        return None
    return max_similarity, best_match_idx


def _apply_decision(
    max_sim: float,
    best_idx: int,
    sig_metadata: list[dict[str, Any]],
    prompt: str,
    prompt_emb: list[float],
) -> None:
    """Apply block/warn/pass thresholds. Always calls sys.exit()."""
    if max_sim >= _DEFAULT_THRESHOLD_BLOCK:
        matched = sig_metadata[best_idx] if best_idx >= 0 else {}
        _emit_metric(
            "firewall.block",
            {
                "similarity": round(max_sim, 4),
                "matched_id": matched.get("id", "unknown"),
                "category": matched.get("category", "unknown"),
            },
        )
        _store_hardened_embedding(prompt, prompt_emb, max_sim)
        try:
            from wfc.scripts.security.refusal_agent import emit_and_exit

            emit_and_exit(
                reason=f"Semantic firewall: prompt blocked (similarity={max_sim:.3f})",
                pattern_id=matched.get("id", "semantic-firewall"),
                suggestion="Rephrase your prompt to avoid patterns similar to known attack signatures.",
            )
        except SystemExit:
            raise
        except Exception:
            sys.exit(2)

    elif max_sim >= _DEFAULT_THRESHOLD_WARN:
        matched = sig_metadata[best_idx] if best_idx >= 0 else {}
        _emit_metric(
            "firewall.warning",
            {
                "similarity": round(max_sim, 4),
                "matched_id": matched.get("id", "unknown"),
                "category": matched.get("category", "unknown"),
            },
        )
        warning_payload = {
            "warning": True,
            "reason": f"Semantic firewall: elevated similarity ({max_sim:.3f})",
            "matched_category": matched.get("category", "unknown"),
        }
        print(json.dumps(warning_payload), file=sys.stderr)
        sys.exit(0)

    else:
        sys.exit(0)


def _run() -> None:
    """Core firewall logic. May call sys.exit(0) or sys.exit(2).

    Raises SystemExit on all code paths. Exceptions propagate to main()
    which catches them for fail-open.
    """
    deadline = time.monotonic() + (_TIMEOUT_MS / 1000.0)

    prompt = _parse_input()
    if prompt is None:
        sys.exit(0)

    _check_freshness()

    provider = _get_provider()
    if provider is None:
        _emit_metric("firewall.no_provider")
        sys.exit(0)

    sig_embeddings, sig_metadata = _load_signatures(provider)
    if not sig_embeddings:
        _emit_metric("firewall.no_signatures")
        sys.exit(0)

    prompt_embedding = _embed_with_timeout(provider, prompt, deadline)
    if prompt_embedding is None:
        sys.exit(0)

    if time.monotonic() > deadline:
        _emit_metric("firewall.timeout", {"phase": "pre_comparison"})
        sys.exit(0)

    scores = _score_signatures(prompt_embedding, sig_embeddings, deadline)
    if scores is None:
        sys.exit(0)

    _apply_decision(scores[0], scores[1], sig_metadata, prompt, prompt_embedding)


def main() -> None:
    """Entry point. Wraps _run() in fail-open try/except.

    CRITICAL: Always exits 0 on any internal error.
    """
    try:
        _run()
    except SystemExit:
        raise
    except Exception:
        logger.debug("Semantic firewall internal error (fail-open)", exc_info=True)
        sys.exit(0)


if __name__ == "__main__":
    main()
