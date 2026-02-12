"""
WFC Memory Manager - Orchestration Layer

SOLID: Dependency Inversion - Composes specialized components
DRY: No duplication - delegates to specialized classes
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .schemas import ReflexionEntry, WorkflowMetric, OperationalPattern
from .reflexion import ReflexionLogger
from .metrics import MetricsLogger
from .pattern_detector import PatternDetector
from .ops_tasks import OpsTasksGenerator


class MemoryManager:
    """
    WFC Memory Manager - CROSS-SESSION LEARNING

    Orchestrates specialized components:
    - ReflexionLogger: Error learning
    - MetricsLogger: Performance tracking
    - PatternDetector: SEE SOMETHING SAY SOMETHING
    - OpsTasksGenerator: OPS_TASKS.md generation

    SOLID: Dependency Inversion Principle
    DRY: Delegates to specialized classes
    """

    # SEE SOMETHING SAY SOMETHING thresholds
    PATTERN_THRESHOLD = 3  # Generate OPS_TASKS.md after 3 occurrences
    OPS_TASKS_THRESHOLD = 10  # Recommend wfc-plan after 10 patterns

    def __init__(self, memory_dir: Optional[Path] = None):
        """
        Initialize memory manager.

        Args:
            memory_dir: Directory for memory files (default: wfc/memory/)
        """
        if memory_dir:
            self.memory_dir = Path(memory_dir)
        else:
            # Default: wfc/memory/
            self.memory_dir = Path(__file__).parent.parent.parent / "memory"

        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # File paths
        reflexion_file = self.memory_dir / "reflexion.jsonl"
        metrics_file = self.memory_dir / "workflow_metrics.jsonl"
        patterns_file = self.memory_dir / "operational_patterns.jsonl"
        ops_tasks_file = self.memory_dir / "OPS_TASKS.md"

        # Initialize specialized components (Dependency Injection)
        self.reflexion = ReflexionLogger(reflexion_file)
        self.metrics = MetricsLogger(metrics_file)
        self.pattern_detector = PatternDetector(patterns_file, threshold=self.PATTERN_THRESHOLD)
        self.ops_tasks = OpsTasksGenerator(ops_tasks_file)

        # Expose file paths for backwards compatibility
        self.reflexion_file = reflexion_file
        self.metrics_file = metrics_file
        self.patterns_file = patterns_file
        self.ops_tasks_file = ops_tasks_file

    # ========================================================================
    # Reflexion Methods (Delegate to ReflexionLogger)
    # ========================================================================

    def log_reflexion(self, entry: ReflexionEntry) -> None:
        """Log a reflexion entry."""
        self.reflexion.log(entry)

    def search_similar_errors(
        self, task_description: str, max_results: int = 5
    ) -> List[ReflexionEntry]:
        """Search for similar past errors."""
        return self.reflexion.search_similar(task_description, max_results)

    def get_common_failure_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most common failure patterns."""
        return self.reflexion.get_common_patterns(limit)

    # ========================================================================
    # Metrics Methods (Delegate to MetricsLogger)
    # ========================================================================

    def log_metric(self, metric: WorkflowMetric) -> None:
        """Log a workflow metric."""
        self.metrics.log(metric)

    def get_average_tokens_for_complexity(self, complexity: str) -> Dict[str, float]:
        """Get average token usage for a complexity level."""
        return self.metrics.get_average_tokens(complexity)

    def get_success_rate_for_complexity(self, complexity: str) -> float:
        """Get success rate for a complexity level."""
        return self.metrics.get_success_rate(complexity)

    # ========================================================================
    # Pattern Detection Methods (Delegate to PatternDetector)
    # ========================================================================

    def scan_for_known_patterns(self, content: str, context: str = "") -> List[str]:
        """Scan content for known pattern signatures."""
        return self.pattern_detector.scan_content(content, context)

    def log_pattern_occurrence(self, pattern_id: str) -> None:
        """
        Log an occurrence of a known pattern.

        Creates a reflexion entry that will be picked up by pattern detection.
        """
        pattern_def = self.pattern_detector.get_pattern_definition(pattern_id)

        if not pattern_def:
            return

        entry = ReflexionEntry(
            timestamp=datetime.now().isoformat(),
            task_id="AUTO_DETECTED",
            mistake=pattern_def["description"],
            evidence="Detected in command/file content",
            fix=pattern_def["fix"],
            rule=pattern_def["error_type"],
            severity=pattern_def["severity"],
        )

        self.log_reflexion(entry)

    def detect_patterns(self) -> List[OperationalPattern]:
        """Detect recurring patterns from reflexion entries."""
        common_patterns = self.get_common_failure_patterns(limit=50)
        return self.pattern_detector.detect_from_reflexion(common_patterns)

    def save_pattern(self, pattern: OperationalPattern) -> None:
        """Save an operational pattern."""
        self.pattern_detector.save_pattern(pattern)

    def get_all_patterns(self) -> List[OperationalPattern]:
        """Get all operational patterns."""
        return self.pattern_detector.get_all_patterns()

    # ========================================================================
    # OPS_TASKS Methods (Delegate to OpsTasksGenerator)
    # ========================================================================

    def generate_ops_tasks(self, force: bool = False) -> Optional[str]:
        """Generate OPS_TASKS.md from detected patterns."""
        patterns = self.detect_patterns()
        return self.ops_tasks.generate(patterns, force)

    def check_ops_tasks_threshold(self) -> Optional[str]:
        """
        Check if OPS_TASKS.md should be generated.

        Returns:
            Reminder message if threshold met, None otherwise
        """
        patterns = self.detect_patterns()

        if len(patterns) >= self.OPS_TASKS_THRESHOLD:
            return f"""
╔══════════════════════════════════════════════════════════════╗
║  SEE SOMETHING SAY SOMETHING - Pattern Threshold Reached!    ║
╚══════════════════════════════════════════════════════════════╝

🔍 {len(patterns)} operational patterns detected

Recommend running:
  wfc memory ops-tasks

This will generate OPS_TASKS.md with all patterns.
Then run:
  wfc plan --from-ops-tasks

To create a systematic fix plan.
"""
        elif len(patterns) >= self.PATTERN_THRESHOLD:
            ops_file = self.generate_ops_tasks()
            if ops_file:
                return f"""
ℹ️  SEE SOMETHING SAY SOMETHING: {len(patterns)} patterns detected
   Generated: {ops_file}

   Review and run: wfc plan --from-ops-tasks
"""

        return None
