"""
WFC Automatic Telemetry - Local Metrics Collection

Automatically captures and stores metrics for every WFC task execution.
Local storage only - no external services.

Developer can view metrics anytime with: wfc metrics [task_id]
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import os


@dataclass
class TaskMetrics:
    """Metrics for a single task execution"""

    task_id: str
    complexity: str  # S, M, L, XL
    status: str  # success, failed, in_progress
    timestamp: str

    # Extended thinking metrics
    thinking_budget_allocated: int
    thinking_budget_used: int
    thinking_truncated: bool
    thinking_mode: str  # normal, extended, unlimited

    # Retry metrics
    retry_count: int
    max_retries: int = 4

    # Debugging metrics (optional)
    debugging_time_min: Optional[float] = None
    root_cause_documented: Optional[bool] = None
    bugs_fixed: int = 0

    # Performance metrics
    duration_seconds: Optional[float] = None
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0

    # Quality metrics
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    coverage_percent: Optional[float] = None

    # Review metrics (if reviewed)
    review_score: Optional[float] = None
    review_passed: Optional[bool] = None

    # Properties satisfied
    properties: List[str] = None
    properties_satisfied: Dict[str, bool] = None

    def __post_init__(self):
        if self.properties is None:
            self.properties = []
        if self.properties_satisfied is None:
            self.properties_satisfied = {}


class AutoTelemetry:
    """
    Automatic telemetry collection for WFC tasks.

    Stores metrics locally in ~/.wfc/telemetry/ by default.
    Developer can view metrics anytime.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize auto telemetry with storage directory"""
        if storage_dir is None:
            # Default: ~/.wfc/telemetry/
            storage_dir = Path.home() / ".wfc" / "telemetry"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Metrics file for current session
        self.session_file = (
            self.storage_dir / f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}.jsonl"
        )

        # Aggregated metrics file
        self.aggregate_file = self.storage_dir / "aggregate.json"

    def log_task_start(
        self,
        task_id: str,
        complexity: str,
        properties: List[str],
        thinking_budget: int,
        thinking_mode: str,
    ) -> None:
        """Log task start - creates initial metrics entry"""
        metrics = TaskMetrics(
            task_id=task_id,
            complexity=complexity,
            status="in_progress",
            timestamp=datetime.now().isoformat(),
            thinking_budget_allocated=thinking_budget,
            thinking_budget_used=0,
            thinking_truncated=False,
            thinking_mode=thinking_mode,
            retry_count=0,
            properties=properties,
        )

        self._append_metrics(metrics)
        print(f"📊 Metrics logging started for {task_id}")

    def log_task_complete(
        self,
        task_id: str,
        status: str,  # success or failed
        thinking_budget_used: int,
        thinking_truncated: bool,
        retry_count: int,
        duration_seconds: float,
        tokens_input: int,
        tokens_output: int,
        tests_run: int,
        tests_passed: int,
        tests_failed: int,
        coverage_percent: Optional[float] = None,
        debugging_time_min: Optional[float] = None,
        root_cause_documented: Optional[bool] = None,
        bugs_fixed: int = 0,
        review_score: Optional[float] = None,
        review_passed: Optional[bool] = None,
        properties_satisfied: Optional[Dict[str, bool]] = None,
    ) -> None:
        """Log task completion - updates metrics entry"""

        # Read existing metrics for this task (if any)
        existing = self._find_task_metrics(task_id)

        if existing:
            # Update existing entry
            metrics = existing
            metrics.status = status
            metrics.thinking_budget_used = thinking_budget_used
            metrics.thinking_truncated = thinking_truncated
            metrics.retry_count = retry_count
            metrics.duration_seconds = duration_seconds
            metrics.tokens_input = tokens_input
            metrics.tokens_output = tokens_output
            metrics.tokens_total = tokens_input + tokens_output
            metrics.tests_run = tests_run
            metrics.tests_passed = tests_passed
            metrics.tests_failed = tests_failed
            metrics.coverage_percent = coverage_percent
            metrics.debugging_time_min = debugging_time_min
            metrics.root_cause_documented = root_cause_documented
            metrics.bugs_fixed = bugs_fixed
            metrics.review_score = review_score
            metrics.review_passed = review_passed
            if properties_satisfied:
                metrics.properties_satisfied = properties_satisfied
        else:
            # Create new entry (task_start wasn't called)
            metrics = TaskMetrics(
                task_id=task_id,
                complexity="M",  # Default
                status=status,
                timestamp=datetime.now().isoformat(),
                thinking_budget_allocated=0,
                thinking_budget_used=thinking_budget_used,
                thinking_truncated=thinking_truncated,
                thinking_mode="normal",
                retry_count=retry_count,
                duration_seconds=duration_seconds,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tokens_total=tokens_input + tokens_output,
                tests_run=tests_run,
                tests_passed=tests_passed,
                tests_failed=tests_failed,
                coverage_percent=coverage_percent,
                debugging_time_min=debugging_time_min,
                root_cause_documented=root_cause_documented,
                bugs_fixed=bugs_fixed,
                review_score=review_score,
                review_passed=review_passed,
                properties_satisfied=properties_satisfied or {},
            )

        self._append_metrics(metrics)
        self._update_aggregate(metrics)

        # Print summary
        self._print_task_summary(metrics)

    def _append_metrics(self, metrics: TaskMetrics) -> None:
        """Append metrics to session file (JSONL format)"""
        with open(self.session_file, "a") as f:
            f.write(json.dumps(asdict(metrics)) + "\n")

    def _update_aggregate(self, metrics: TaskMetrics) -> None:
        """Update aggregated metrics file"""
        # Load existing aggregate
        if self.aggregate_file.exists():
            with open(self.aggregate_file) as f:
                aggregate = json.load(f)
        else:
            aggregate = {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "total_tokens": 0,
                "total_duration_seconds": 0,
                "truncation_count": 0,
                "avg_retries": 0,
                "tasks": [],
            }

        # Update aggregate stats
        aggregate["total_tasks"] += 1
        if metrics.status == "success":
            aggregate["successful_tasks"] += 1
        elif metrics.status == "failed":
            aggregate["failed_tasks"] += 1

        aggregate["total_tokens"] += metrics.tokens_total
        if metrics.duration_seconds:
            aggregate["total_duration_seconds"] += metrics.duration_seconds
        if metrics.thinking_truncated:
            aggregate["truncation_count"] += 1

        # Recalculate avg retries
        total_retries = sum(t.get("retry_count", 0) for t in aggregate["tasks"])
        total_retries += metrics.retry_count
        aggregate["avg_retries"] = total_retries / aggregate["total_tasks"]

        # Add/update task in aggregate list
        task_entry = {
            "task_id": metrics.task_id,
            "complexity": metrics.complexity,
            "status": metrics.status,
            "timestamp": metrics.timestamp,
            "retry_count": metrics.retry_count,
            "truncated": metrics.thinking_truncated,
            "tokens": metrics.tokens_total,
        }

        # Remove old entry if exists
        aggregate["tasks"] = [t for t in aggregate["tasks"] if t["task_id"] != metrics.task_id]
        aggregate["tasks"].append(task_entry)

        # Keep only last 100 tasks in aggregate
        aggregate["tasks"] = aggregate["tasks"][-100:]

        # Save aggregate
        with open(self.aggregate_file, "w") as f:
            json.dump(aggregate, f, indent=2)

    def _find_task_metrics(self, task_id: str) -> Optional[TaskMetrics]:
        """Find existing metrics for task in session file"""
        if not self.session_file.exists():
            return None

        # Read all lines and find matching task_id (last occurrence)
        matching = None
        with open(self.session_file) as f:
            for line in f:
                data = json.loads(line)
                if data["task_id"] == task_id:
                    matching = TaskMetrics(**data)

        return matching

    def _print_task_summary(self, metrics: TaskMetrics) -> None:
        """Print task completion summary"""
        print("\n" + "=" * 60)
        print(f"📊 WFC TASK METRICS: {metrics.task_id}")
        print("=" * 60)
        print(f"Status: {metrics.status.upper()}")
        print(f"Complexity: {metrics.complexity}")
        print(
            f"Duration: {metrics.duration_seconds:.1f}s"
            if metrics.duration_seconds
            else "Duration: N/A"
        )
        print(f"\nThinking:")
        print(f"  Mode: {metrics.thinking_mode}")
        print(
            f"  Budget: {metrics.thinking_budget_used}/{metrics.thinking_budget_allocated} tokens"
        )
        print(f"  Truncated: {'⚠️ YES' if metrics.thinking_truncated else '✅ No'}")
        print(
            f"  Utilization: {(metrics.thinking_budget_used/metrics.thinking_budget_allocated*100):.1f}%"
            if metrics.thinking_budget_allocated > 0
            else "  Utilization: N/A"
        )

        print(f"\nRetries: {metrics.retry_count}/{metrics.max_retries}")

        if metrics.tests_run > 0:
            print(f"\nTests:")
            print(f"  Run: {metrics.tests_run}")
            print(f"  Passed: {metrics.tests_passed}")
            print(f"  Failed: {metrics.tests_failed}")
            if metrics.coverage_percent:
                print(f"  Coverage: {metrics.coverage_percent:.1f}%")

        if metrics.bugs_fixed > 0:
            print(f"\nDebugging:")
            print(f"  Bugs fixed: {metrics.bugs_fixed}")
            if metrics.debugging_time_min:
                print(f"  Time spent: {metrics.debugging_time_min:.1f} min")
            if metrics.root_cause_documented is not None:
                print(
                    f"  Root cause documented: {'✅ Yes' if metrics.root_cause_documented else '❌ No'}"
                )

        if metrics.review_score:
            print(f"\nReview:")
            print(f"  Score: {metrics.review_score:.1f}/10")
            print(f"  Status: {'✅ Passed' if metrics.review_passed else '❌ Failed'}")

        print(
            f"\nTokens: {metrics.tokens_total:,} ({metrics.tokens_input:,} in, {metrics.tokens_output:,} out)"
        )
        print(f"Metrics saved to: {self.storage_dir}")
        print("=" * 60 + "\n")

    def view_task_metrics(self, task_id: str) -> Optional[TaskMetrics]:
        """View metrics for a specific task"""
        metrics = self._find_task_metrics(task_id)
        if metrics:
            self._print_task_summary(metrics)
            return metrics
        else:
            print(f"❌ No metrics found for {task_id}")
            return None

    def view_aggregate_metrics(self) -> Dict[str, Any]:
        """View aggregated metrics across all tasks"""
        if not self.aggregate_file.exists():
            print("❌ No aggregate metrics yet")
            return {}

        with open(self.aggregate_file) as f:
            aggregate = json.load(f)

        print("\n" + "=" * 60)
        print("📊 WFC AGGREGATE METRICS")
        print("=" * 60)
        print(f"Total Tasks: {aggregate['total_tasks']}")
        print(
            f"Success Rate: {(aggregate['successful_tasks']/aggregate['total_tasks']*100):.1f}%"
            if aggregate["total_tasks"] > 0
            else "Success Rate: N/A"
        )
        print(f"  ✅ Successful: {aggregate['successful_tasks']}")
        print(f"  ❌ Failed: {aggregate['failed_tasks']}")
        print(f"\nAverage Retries: {aggregate['avg_retries']:.2f}")
        print(f"Truncation Events: {aggregate['truncation_count']}")
        print(f"Total Tokens Used: {aggregate['total_tokens']:,}")
        print(
            f"Total Duration: {aggregate['total_duration_seconds']/60:.1f} min"
            if aggregate["total_duration_seconds"] > 0
            else "Total Duration: N/A"
        )
        print("=" * 60 + "\n")

        return aggregate


# Global instance for easy access
_telemetry = None


def get_telemetry() -> AutoTelemetry:
    """Get global telemetry instance"""
    global _telemetry
    if _telemetry is None:
        _telemetry = AutoTelemetry()
    return _telemetry


# Convenience functions
def log_task_start(
    task_id: str, complexity: str, properties: List[str], thinking_budget: int, thinking_mode: str
):
    """Log task start"""
    get_telemetry().log_task_start(task_id, complexity, properties, thinking_budget, thinking_mode)


def log_task_complete(
    task_id: str,
    status: str,
    thinking_budget_used: int,
    thinking_truncated: bool,
    retry_count: int,
    duration_seconds: float,
    tokens_input: int,
    tokens_output: int,
    tests_run: int,
    tests_passed: int,
    tests_failed: int,
    **kwargs,
):
    """Log task completion"""
    get_telemetry().log_task_complete(
        task_id=task_id,
        status=status,
        thinking_budget_used=thinking_budget_used,
        thinking_truncated=thinking_truncated,
        retry_count=retry_count,
        duration_seconds=duration_seconds,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        tests_run=tests_run,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        **kwargs,
    )


def view_metrics(task_id: Optional[str] = None):
    """View metrics (specific task or aggregate)"""
    telemetry = get_telemetry()
    if task_id:
        return telemetry.view_task_metrics(task_id)
    else:
        return telemetry.view_aggregate_metrics()


# Generic event logging for hooks, PR creation, etc.
def log_event(event_type: str, data: Dict[str, Any]) -> None:
    """
    Log generic event to telemetry (NEW in Phase 6).

    Supports event types:
    - pr_created: PR creation events
    - hook_warning: Git hook violation warnings
    - workflow_violation: Workflow compliance violations
    - merge_complete: Merge operation completion
    - Any custom event type

    Args:
        event_type: Event type identifier
        data: Event data dictionary

    Example:
        log_event("pr_created", {
            "pr_url": "https://github.com/user/repo/pull/42",
            "task_id": "TASK-001",
            "success": True
        })
    """
    try:
        telemetry = get_telemetry()

        # Create event entry
        event = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            **data,
        }

        # Append to events file
        events_file = telemetry.storage_dir / "events.jsonl"
        with open(events_file, "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        # Telemetry failure should not break workflow - fail silently
        pass


def get_workflow_metrics(days: int = 30) -> Dict[str, Any]:
    """
    Get workflow compliance metrics (NEW in Phase 6).

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        Dict with workflow metrics:
            - pr_creation_success_rate
            - direct_main_commits
            - force_pushes
            - conventional_commits
            - hook_warnings
    """
    telemetry = get_telemetry()
    events_file = telemetry.storage_dir / "events.jsonl"

    if not events_file.exists():
        return {
            "pr_creation_success_rate": 0,
            "total_prs": 0,
            "successful_prs": 0,
            "direct_main_commits": 0,
            "force_pushes": 0,
            "conventional_commits": 0,
            "total_commits": 0,
            "hook_warnings": [],
        }

    # Parse events
    from datetime import datetime, timedelta

    cutoff = datetime.now() - timedelta(days=days)

    pr_events = []
    hook_warnings = []
    commit_events = []

    try:
        with open(events_file) as f:
            for line in f:
                event = json.loads(line)
                event_time = datetime.fromisoformat(event["timestamp"])

                if event_time < cutoff:
                    continue

                if event["event"] == "pr_created":
                    pr_events.append(event)
                elif event["event"] == "hook_warning":
                    hook_warnings.append(event)
                elif event["event"] == "commit_with_task":
                    commit_events.append(event)

    except Exception:
        pass

    # Calculate metrics
    total_prs = len(pr_events)
    successful_prs = sum(1 for e in pr_events if e.get("success", False))

    direct_main_commits = sum(
        1 for e in hook_warnings if e.get("violation") == "direct_commit_to_protected"
    )

    force_pushes = sum(1 for e in hook_warnings if e.get("violation") == "force_push")

    conventional_commits = sum(
        1 for e in hook_warnings if e.get("violation") != "non_conventional_commit"
    )
    total_commits = len(commit_events) + len(
        [e for e in hook_warnings if "commit" in e.get("violation", "")]
    )

    return {
        "pr_creation_success_rate": (successful_prs / total_prs * 100) if total_prs > 0 else 0,
        "total_prs": total_prs,
        "successful_prs": successful_prs,
        "direct_main_commits": direct_main_commits,
        "force_pushes": force_pushes,
        "conventional_commits": conventional_commits,
        "total_commits": total_commits,
        "hook_warnings": hook_warnings[:20],  # Last 20
    }


def print_workflow_metrics(days: int = 30) -> None:
    """
    Print workflow compliance metrics (NEW in Phase 6).

    Args:
        days: Number of days to look back (default: 30)
    """
    metrics = get_workflow_metrics(days)

    print(f"\n{'=' * 60}")
    print(f"📊 WFC WORKFLOW METRICS (Last {days} Days)")
    print(f"{'=' * 60}")

    # PR Creation
    print(f"\nPR Creation:")
    print(f"  Total PRs: {metrics['total_prs']}")
    print(f"  Successful: {metrics['successful_prs']}")
    print(f"  Success Rate: {metrics['pr_creation_success_rate']:.1f}%")

    # Workflow Compliance
    print(f"\nWorkflow Compliance:")
    print(f"  Direct Main Commits: {metrics['direct_main_commits']} warnings")
    print(f"  Force Pushes: {metrics['force_pushes']} warnings")
    print(
        f"  Conventional Commits: {metrics['conventional_commits']}/{metrics['total_commits']} "
        f"({metrics['conventional_commits']/metrics['total_commits']*100:.1f}%)"
        if metrics["total_commits"] > 0
        else "  Conventional Commits: N/A"
    )

    # Recent Warnings
    if metrics["hook_warnings"]:
        print(f"\nRecent Hook Warnings ({len(metrics['hook_warnings'])}):")
        for warning in metrics["hook_warnings"][:5]:
            hook = warning.get("hook", "unknown")
            violation = warning.get("violation", "unknown")
            print(f"  - [{hook}] {violation}")

    print(f"{'=' * 60}\n")


# CLI entry point
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  View aggregate metrics: python3 -m wfc.shared.telemetry_auto")
        print("  View task metrics:      python3 -m wfc.shared.telemetry_auto TASK-001")
        sys.exit(1)

    if sys.argv[1] == "aggregate" or sys.argv[1] == "--all":
        view_metrics()
    else:
        view_metrics(sys.argv[1])
