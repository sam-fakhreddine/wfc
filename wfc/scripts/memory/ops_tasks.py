"""
WFC OPS_TASKS Generator - SEE SOMETHING SAY SOMETHING

SOLID: Single Responsibility - Only generates OPS_TASKS.md
"""

from pathlib import Path
from typing import List, Optional
from datetime import datetime
from .schemas import OperationalPattern


class OpsTasksGenerator:
    """
    Generates OPS_TASKS.md from operational patterns.

    Single Responsibility: OPS_TASKS.md generation
    """

    def __init__(self, ops_tasks_file: Path):
        """
        Initialize OPS_TASKS generator.

        Args:
            ops_tasks_file: Path to OPS_TASKS.md
        """
        self.ops_tasks_file = ops_tasks_file

    def generate(self, patterns: List[OperationalPattern], force: bool = False) -> Optional[str]:
        """
        Generate OPS_TASKS.md from patterns.

        Args:
            patterns: List of operational patterns
            force: Force generation even if no patterns

        Returns:
            Path to OPS_TASKS.md if generated, None otherwise
        """
        if not patterns and not force:
            return None

        content = self._build_markdown(patterns)

        with open(self.ops_tasks_file, "w") as f:
            f.write(content)

        return str(self.ops_tasks_file)

    def _build_markdown(self, patterns: List[OperationalPattern]) -> str:
        """Build markdown content from patterns."""
        ready_count = sum(1 for p in patterns if p.status == "READY_FOR_PLAN")
        high_count = sum(1 for p in patterns if p.severity == "high")
        critical_count = sum(1 for p in patterns if p.severity == "critical")

        content = f"""# WFC Operational Improvements

**SEE SOMETHING SAY SOMETHING** - Recurring patterns detected by WFC

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

- **Total Patterns**: {len(patterns)}
- **Ready for Plan**: {ready_count}
- **High Severity**: {high_count}
- **Critical Severity**: {critical_count}

---

## Patterns Detected

"""

        for pattern in patterns:
            severity_emoji = {"low": "🔵", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(
                pattern.severity, "⚪"
            )

            content += f"""### {pattern.pattern_id}: {pattern.error_type} {severity_emoji}

- **First Detected**: {pattern.first_detected[:10]}
- **Occurrences**: {pattern.occurrence_count}x
- **Description**: {pattern.description}
- **Fix**: {pattern.fix}
- **Impact**: {pattern.impact}
- **Status**: {pattern.status}

"""

        content += """---

## Next Steps

Run `wfc-plan` to generate a systematic fix plan:

```bash
wfc plan --from-ops-tasks
```

This will create TASKS.md from the patterns above.

After implementing fixes, clear this file:

```bash
rm wfc/memory/OPS_TASKS.md
wfc memory clear-patterns
```

"""

        return content

    def exists(self) -> bool:
        """Check if OPS_TASKS.md exists."""
        return self.ops_tasks_file.exists()

    def clear(self) -> None:
        """Clear OPS_TASKS.md."""
        if self.ops_tasks_file.exists():
            self.ops_tasks_file.unlink()
