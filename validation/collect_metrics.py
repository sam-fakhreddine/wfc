#!/usr/bin/env python3
"""
WFC Validation Metrics Collection

Collects metrics from WFC task execution for validation analysis.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class MetricsCollector:
    """Collects and aggregates validation metrics"""

    def __init__(self, metrics_file: Path = Path("validation/metrics.json")):
        self.metrics_file = metrics_file
        self.data = self._load_metrics()

    def _load_metrics(self) -> Dict[str, Any]:
        """Load existing metrics or create new"""
        if self.metrics_file.exists():
            with open(self.metrics_file) as f:
                return json.load(f)
        return {
            "validation_metadata": {
                "start_date": datetime.now().isoformat(),
                "status": "in_progress",
                "tasks_completed": 0,
                "tasks_target": 10
            },
            "tasks": [],
            "aggregated_metrics": {}
        }

    def _save_metrics(self):
        """Save metrics to file"""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def add_task_result(
        self,
        task_id: str,
        complexity: str,
        properties: list,
        status: str,
        thinking_budget_used: int,
        thinking_budget_total: int,
        truncated: bool,
        retry_count: int,
        debugging_time_min: Optional[float] = None,
        root_cause_documented: Optional[bool] = None
    ):
        """Add individual task result"""
        task_data = {
            "task_id": task_id,
            "complexity": complexity,
            "properties": properties,
            "status": status,
            "thinking": {
                "budget_used": thinking_budget_used,
                "budget_total": thinking_budget_total,
                "truncated": truncated,
                "utilization": thinking_budget_used / thinking_budget_total if thinking_budget_total > 0 else 0
            },
            "retries": retry_count,
            "debugging": {
                "time_min": debugging_time_min,
                "root_cause_documented": root_cause_documented
            },
            "timestamp": datetime.now().isoformat()
        }

        self.data["tasks"].append(task_data)
        self.data["validation_metadata"]["tasks_completed"] = len(self.data["tasks"])
        self._save_metrics()

        print(f"✅ Added metrics for {task_id}")
        print(f"   Status: {status}")
        print(f"   Thinking: {thinking_budget_used}/{thinking_budget_total} tokens")
        print(f"   Truncated: {truncated}")
        print(f"   Retries: {retry_count}")

    def calculate_aggregates(self):
        """Calculate aggregated metrics from all tasks"""
        if not self.data["tasks"]:
            print("⚠️  No tasks to aggregate")
            return

        tasks = self.data["tasks"]
        total = len(tasks)

        # Success rate
        successful = sum(1 for t in tasks if t["status"] == "success")
        success_rate = (successful / total) * 100

        # Truncation rate
        truncated = sum(1 for t in tasks if t["thinking"]["truncated"])
        truncation_rate = (truncated / total) * 100

        # Retry stats
        avg_retries = sum(t["retries"] for t in tasks) / total
        zero_retries = sum(1 for t in tasks if t["retries"] == 0)
        unlimited_retries = sum(1 for t in tasks if t["retries"] >= 3)

        # Root cause compliance
        bug_fixes = [t for t in tasks if t["debugging"]["root_cause_documented"] is not None]
        if bug_fixes:
            root_cause_compliance = (sum(1 for t in bug_fixes if t["debugging"]["root_cause_documented"]) / len(bug_fixes)) * 100
        else:
            root_cause_compliance = None

        # Debugging time
        debug_times = [t["debugging"]["time_min"] for t in tasks if t["debugging"]["time_min"] is not None]
        avg_debug_time = sum(debug_times) / len(debug_times) if debug_times else None

        self.data["aggregated_metrics"] = {
            "success_rate": round(success_rate, 1),
            "truncation_rate": round(truncation_rate, 1),
            "avg_retries": round(avg_retries, 2),
            "zero_retry_rate": round((zero_retries / total) * 100, 1),
            "unlimited_retry_rate": round((unlimited_retries / total) * 100, 1),
            "root_cause_compliance": round(root_cause_compliance, 1) if root_cause_compliance is not None else None,
            "avg_debug_time_min": round(avg_debug_time, 1) if avg_debug_time else None
        }

        self._save_metrics()

        print("\n📊 Aggregated Metrics:")
        print(f"   Success Rate: {success_rate:.1f}% (target: ≥85%)")
        print(f"   Truncation Rate: {truncation_rate:.1f}% (target: <5%)")
        print(f"   Avg Retries: {avg_retries:.2f} (target: <1)")
        if root_cause_compliance is not None:
            print(f"   Root Cause Compliance: {root_cause_compliance:.1f}% (target: 100%)")

    def generate_report(self):
        """Generate validation report summary"""
        self.calculate_aggregates()

        if not self.data["tasks"]:
            print("⚠️  No tasks completed yet")
            return

        metrics = self.data["aggregated_metrics"]
        completed = self.data["validation_metadata"]["tasks_completed"]
        target = self.data["validation_metadata"]["tasks_target"]

        print("\n" + "="*60)
        print("WFC VALIDATION REPORT SUMMARY")
        print("="*60)
        print(f"\nProgress: {completed}/{target} tasks completed")
        print(f"\nSuccess Rate: {metrics['success_rate']}% {'✅' if metrics['success_rate'] >= 85 else '❌'}")
        print(f"Truncation Rate: {metrics['truncation_rate']}% {'✅' if metrics['truncation_rate'] < 5 else '❌'}")
        print(f"Avg Retries: {metrics['avg_retries']} {'✅' if metrics['avg_retries'] < 1 else '⚠️'}")

        if metrics.get('root_cause_compliance'):
            print(f"Root Cause Compliance: {metrics['root_cause_compliance']}% {'✅' if metrics['root_cause_compliance'] == 100 else '❌'}")

        # GO/NO-GO decision
        if completed >= target:
            go_criteria = [
                metrics['success_rate'] >= 85,
                metrics['truncation_rate'] < 30,  # Improvement metric
                metrics.get('root_cause_compliance', 0) == 100 if metrics.get('root_cause_compliance') is not None else True
            ]

            if all(go_criteria):
                print("\n🟢 GO DECISION: Proceed to Week 3 expansion")
            else:
                print("\n🔴 NO-GO DECISION: Address issues before proceeding")
        else:
            print(f"\n⏳ PENDING: Complete {target - completed} more tasks")

        print("="*60)


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Add task result:")
        print("    python3 collect_metrics.py add TASK-001 M [SAFETY] success 3500 5000 false 0")
        print("  Generate report:")
        print("    python3 collect_metrics.py report")
        return

    command = sys.argv[1]
    collector = MetricsCollector()

    if command == "add" and len(sys.argv) >= 9:
        task_id = sys.argv[2]
        complexity = sys.argv[3]
        properties = sys.argv[4].strip("[]").split(",") if sys.argv[4] != "[]" else []
        status = sys.argv[5]
        budget_used = int(sys.argv[6])
        budget_total = int(sys.argv[7])
        truncated = sys.argv[8].lower() == "true"
        retry_count = int(sys.argv[9])

        debugging_time = float(sys.argv[10]) if len(sys.argv) > 10 and sys.argv[10] != "None" else None
        root_cause = sys.argv[11].lower() == "true" if len(sys.argv) > 11 and sys.argv[11] != "None" else None

        collector.add_task_result(
            task_id=task_id,
            complexity=complexity,
            properties=properties,
            status=status,
            thinking_budget_used=budget_used,
            thinking_budget_total=budget_total,
            truncated=truncated,
            retry_count=retry_count,
            debugging_time_min=debugging_time,
            root_cause_documented=root_cause
        )

    elif command == "report":
        collector.generate_report()

    else:
        print("Invalid command. Use 'add' or 'report'")


if __name__ == "__main__":
    main()
