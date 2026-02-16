"""
WFC Say:Do Ratio & TEAMCHARTER Values Alignment Metrics

SOLID: Single Responsibility - Say:Do ratio and values alignment computation

Functions:
- compute_say_do_ratio: Ratio of tasks completed at estimated complexity
- aggregate_values_alignment: Count violated/upheld per value from ReflexionEntries
- generate_values_mermaid_chart: Mermaid bar chart of values adherence
- generate_values_recommendations: Actionable recommendations tied to specific values
"""

from typing import Dict, List

from .schemas import ReflexionEntry


def compute_say_do_ratio(tasks: List[Dict]) -> float:
    """
    Compute Say:Do ratio from task telemetry.

    A task is "on-estimate" when:
    - estimated_complexity == actual_complexity
    - quality_gate_passed is True (defaults to True if missing)
    - re_estimated is False (defaults to False if missing)

    Args:
        tasks: List of task dicts with keys:
            task_id, estimated_complexity, actual_complexity,
            quality_gate_passed (optional), re_estimated (optional)

    Returns:
        Ratio 0.0..1.0. Returns 0.0 for empty list.
    """
    if not tasks:
        return 0.0

    on_estimate = 0
    for task in tasks:
        est = task.get("estimated_complexity")
        act = task.get("actual_complexity")
        qg_passed = task.get("quality_gate_passed", True)
        re_est = task.get("re_estimated", False)

        if est == act and qg_passed and not re_est:
            on_estimate += 1

    return on_estimate / len(tasks)


def aggregate_values_alignment(entries: List[ReflexionEntry]) -> Dict[str, Dict[str, int]]:
    """
    Aggregate values alignment from ReflexionEntry team_values_impact fields.

    Args:
        entries: List of ReflexionEntry objects

    Returns:
        Dict mapping value name -> {status: count}.
        Example: {"accountability": {"violated": 2, "upheld": 1}}
    """
    result: Dict[str, Dict[str, int]] = {}

    for entry in entries:
        if entry.team_values_impact is None:
            continue

        for value_name, status in entry.team_values_impact.items():
            if value_name not in result:
                result[value_name] = {}
            result[value_name][status] = result[value_name].get(status, 0) + 1

    return result


def generate_values_mermaid_chart(alignment: Dict[str, Dict[str, int]]) -> str:
    """
    Generate a Mermaid xychart-beta bar chart showing values adherence.

    Args:
        alignment: Output from aggregate_values_alignment

    Returns:
        Mermaid chart string (wrapped in ```mermaid fences)
    """
    if not alignment:
        return "_No values alignment data available._"

    values = sorted(alignment.keys())
    upheld_counts = []
    violated_counts = []

    for value in values:
        counts = alignment[value]
        upheld_counts.append(counts.get("upheld", 0))
        violated_counts.append(counts.get("violated", 0))

    # Build x-axis labels (capitalize for display)
    labels = ", ".join(f'"{v.replace("_", " ").title()}"' for v in values)

    lines = [
        "```mermaid",
        "xychart-beta",
        '    title "TEAMCHARTER Values Adherence"',
        f"    x-axis [{labels}]",
        '    y-axis "Count"',
        f"    bar [{', '.join(str(c) for c in upheld_counts)}]",
        f"    bar [{', '.join(str(c) for c in violated_counts)}]",
        "```",
    ]

    return "\n".join(lines)


def generate_values_recommendations(alignment: Dict[str, Dict[str, int]]) -> List[str]:
    """
    Generate actionable recommendations tied to specific values.

    Values with high violation rates get recommendations.
    Values with zero violations may get positive recognition.

    Args:
        alignment: Output from aggregate_values_alignment

    Returns:
        List of recommendation strings
    """
    if not alignment:
        return []

    recommendations: List[str] = []

    # Sort values by violation count descending
    scored = []
    for value_name, counts in alignment.items():
        violated = counts.get("violated", 0)
        upheld = counts.get("upheld", 0)
        total = violated + upheld
        violation_rate = violated / total if total > 0 else 0.0
        scored.append((value_name, violated, upheld, total, violation_rate))

    scored.sort(key=lambda x: x[4], reverse=True)

    for value_name, violated, upheld, total, violation_rate in scored:
        display_name = value_name.replace("_", " ").title()

        if violated == 0:
            # No violations -- skip or give positive note (not a concern)
            continue

        if violation_rate >= 0.7:
            recommendations.append(
                f"{display_name} score is critically low -- "
                f"{violated} of {total} entries show violations. "
                f"Immediate team discussion recommended."
            )
        elif violation_rate >= 0.4:
            recommendations.append(
                f"{display_name} shows a concerning trend -- "
                f"{violated} violations across {total} entries. "
                f"Review recent tasks for root causes."
            )
        else:
            recommendations.append(
                f"{display_name} had {violated} violation(s) "
                f"out of {total} entries. Monitor going forward."
            )

    return recommendations
