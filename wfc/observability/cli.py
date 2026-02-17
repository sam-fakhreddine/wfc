"""CLI commands for observability: wfc metrics."""

from __future__ import annotations

import json

from wfc.observability import get_registry, init, is_initialized


def cmd_metrics(format: str = "json") -> None:
    """Dump current metrics snapshot."""
    if not is_initialized():
        init()

    registry = get_registry()
    snapshot = registry.snapshot()

    if format == "table":
        _print_table(snapshot)
    else:
        print(json.dumps(snapshot, indent=2, default=str))


def _print_table(snapshot: dict) -> None:
    """Print metrics as a human-readable table."""
    metrics = snapshot.get("metrics", [])
    if not metrics:
        print("No metrics recorded.")
        return

    name_w = max(len(m["name"]) for m in metrics)
    name_w = max(name_w, 4)
    type_w = max(len(m["type"]) for m in metrics)
    type_w = max(type_w, 4)

    header = f"{'Name':<{name_w}}  {'Type':<{type_w}}  {'Value':>12}"
    print(header)
    print("-" * len(header))

    for m in metrics:
        name = m["name"]
        mtype = m["type"]
        if mtype == "counter":
            value = str(m.get("value", 0))
        elif mtype == "gauge":
            value = str(m.get("value", 0))
        elif mtype in ("histogram", "timer"):
            count = m.get("count", 0)
            p50 = m.get("p50", 0)
            value = f"n={count} p50={p50:.3f}" if count else "n=0"
        else:
            value = str(m.get("value", "?"))
        print(f"{name:<{name_w}}  {mtype:<{type_w}}  {value:>12}")
