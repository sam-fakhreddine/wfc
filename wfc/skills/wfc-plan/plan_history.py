"""
Plan History and Versioning

Manages plan versions with timestamps and metadata.
Keeps a history of all generated plans for reference.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class PlanMetadata:
    """Metadata for a single plan"""

    plan_id: str  # e.g., "plan_20260211_143022"
    timestamp: str  # ISO format
    goal: str
    context: str
    directory: str
    task_count: int
    property_count: int
    test_count: int


class PlanHistory:
    """
    Manages plan history and versioning.

    Creates timestamped directories for each plan and maintains
    a history index.
    """

    def __init__(self, base_dir: Path = None):
        """
        Initialize plan history manager.

        Args:
            base_dir: Base directory for plans (default: ./plans)
        """
        self.base_dir = base_dir or Path("./plans")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.base_dir / "HISTORY.json"

    def generate_plan_id(self, goal: str = None) -> str:
        """
        Generate unique plan ID with timestamp.

        Args:
            goal: Optional goal to include in ID

        Returns:
            Plan ID like "plan_20260211_143022" or "plan_oauth2_20260211_143022"
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if goal:
            # Sanitize goal for directory name
            sanitized = goal.lower()
            sanitized = "".join(c if c.isalnum() or c == " " else "" for c in sanitized)
            sanitized = "_".join(sanitized.split())[:30]  # Max 30 chars
            return f"plan_{sanitized}_{timestamp}"
        else:
            return f"plan_{timestamp}"

    def get_next_plan_dir(self, goal: str = None) -> Path:
        """
        Get the next plan directory (timestamped).

        Args:
            goal: Optional goal to include in directory name

        Returns:
            Path to new plan directory
        """
        plan_id = self.generate_plan_id(goal)
        plan_dir = self.base_dir / plan_id
        plan_dir.mkdir(parents=True, exist_ok=True)
        return plan_dir

    def add_to_history(self, metadata: PlanMetadata) -> None:
        """
        Add plan to history index.

        Args:
            metadata: Plan metadata to record
        """
        history = self.load_history()
        history.append(asdict(metadata))

        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=2)

    def load_history(self) -> List[Dict]:
        """
        Load plan history.

        Returns:
            List of plan metadata dictionaries
        """
        if not self.history_file.exists():
            return []

        with open(self.history_file) as f:
            return json.load(f)

    def get_latest_plan(self) -> Optional[Dict]:
        """
        Get metadata for the most recent plan.

        Returns:
            Plan metadata dict or None if no history
        """
        history = self.load_history()
        return history[-1] if history else None

    def list_plans(self, limit: int = 10) -> List[Dict]:
        """
        List recent plans.

        Args:
            limit: Maximum number of plans to return

        Returns:
            List of plan metadata (most recent first)
        """
        history = self.load_history()
        return list(reversed(history[-limit:]))

    def find_plans_by_goal(self, goal_substring: str) -> List[Dict]:
        """
        Find plans by goal keyword.

        Args:
            goal_substring: Substring to search for in goals

        Returns:
            List of matching plan metadata
        """
        history = self.load_history()
        return [plan for plan in history if goal_substring.lower() in plan.get("goal", "").lower()]

    def get_plan_path(self, plan_id: str) -> Optional[Path]:
        """
        Get path to a specific plan.

        Args:
            plan_id: Plan ID to find

        Returns:
            Path to plan directory or None if not found
        """
        plan_dir = self.base_dir / plan_id
        return plan_dir if plan_dir.exists() else None

    def generate_history_markdown(self) -> str:
        """
        Generate markdown summary of plan history.

        Returns:
            Markdown-formatted history
        """
        history = self.load_history()

        if not history:
            return "# Plan History\n\nNo plans created yet.\n"

        lines = [
            "# Plan History",
            "",
            f"**Total Plans:** {len(history)}",
            "",
            "---",
            "",
        ]

        for plan in reversed(history):  # Most recent first
            lines.extend(
                [
                    f"## {plan['plan_id']}",
                    f"- **Created:** {plan['timestamp']}",
                    f"- **Goal:** {plan['goal']}",
                    (
                        f"- **Context:** {plan['context'][:100]}..."
                        if len(plan.get("context", "")) > 100
                        else f"- **Context:** {plan.get('context', 'N/A')}"
                    ),
                    f"- **Directory:** `{plan['directory']}`",
                    f"- **Tasks:** {plan['task_count']}",
                    f"- **Properties:** {plan['property_count']}",
                    f"- **Tests:** {plan['test_count']}",
                    "",
                ]
            )

        return "\n".join(lines)


def create_plan_metadata(
    plan_id: str,
    directory: Path,
    goal: str,
    context: str,
    task_count: int,
    property_count: int,
    test_count: int,
) -> PlanMetadata:
    """
    Create plan metadata.

    Args:
        plan_id: Unique plan identifier
        directory: Plan directory path
        goal: Plan goal
        context: Plan context
        task_count: Number of tasks
        property_count: Number of properties
        test_count: Number of tests

    Returns:
        PlanMetadata instance
    """
    return PlanMetadata(
        plan_id=plan_id,
        timestamp=datetime.now().isoformat(),
        goal=goal,
        context=context,
        directory=str(directory),
        task_count=task_count,
        property_count=property_count,
        test_count=test_count,
    )


# CLI for testing
if __name__ == "__main__":
    history = PlanHistory()

    # Test: Generate plan directories
    print("Generating plan directories...")
    plan1 = history.get_next_plan_dir("Add OAuth2 authentication")
    print(f"Plan 1: {plan1}")

    plan2 = history.get_next_plan_dir("Implement caching layer")
    print(f"Plan 2: {plan2}")

    # Test: Add to history
    print("\nAdding to history...")
    metadata1 = create_plan_metadata(
        plan_id=plan1.name,
        directory=plan1,
        goal="Add OAuth2 authentication",
        context="Security requirement for production",
        task_count=5,
        property_count=3,
        test_count=12,
    )
    history.add_to_history(metadata1)

    metadata2 = create_plan_metadata(
        plan_id=plan2.name,
        directory=plan2,
        goal="Implement caching layer",
        context="Performance optimization for API",
        task_count=3,
        property_count=2,
        test_count=8,
    )
    history.add_to_history(metadata2)

    # Test: List plans
    print("\nRecent plans:")
    for plan in history.list_plans():
        print(f"  - {plan['plan_id']}: {plan['goal']}")

    # Test: Generate markdown
    print("\nHistory markdown:")
    print(history.generate_history_markdown())
