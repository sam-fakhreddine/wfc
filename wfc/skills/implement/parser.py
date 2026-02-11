"""
WFC Implement - TASKS.md Parser

ELEGANT: Simple markdown parsing, converts to Task objects
"""

import re
from pathlib import Path
from typing import List, Optional

from wfc.shared.schemas import Task, TaskComplexity, TaskGraph


class TasksParser:
    """
    Parse TASKS.md into TaskGraph.

    Format expected:
    ## TASK-001: Title
    - **Complexity**: M
    - **Dependencies**: [TASK-002, TASK-003]
    - **Properties**: [PROP-001]
    - **Files**: [src/file.py]
    ...
    """

    def parse(self, tasks_file: Path) -> TaskGraph:
        """Parse TASKS.md file."""
        content = tasks_file.read_text()
        graph = TaskGraph()

        # Split by task headers (## TASK-XXX:)
        task_pattern = r'## (TASK-\d+):\s*(.+?)(?=\n##|\Z)'
        matches = re.finditer(task_pattern, content, re.DOTALL)

        for match in matches:
            task_id = match.group(1)
            task_content = match.group(2)

            task = self._parse_task(task_id, task_content)
            if task:
                graph.add(task)

        return graph

    def _parse_task(self, task_id: str, content: str) -> Optional[Task]:
        """Parse single task block."""
        lines = content.split('\n')

        # Extract title (first line after ID)
        title = lines[0].strip() if lines else "Untitled"

        # Extract fields
        complexity = self._extract_complexity(content)
        dependencies = self._extract_list(content, "Dependencies")
        properties = self._extract_list(content, "Properties")
        files = self._extract_list(content, "Files")
        requirements = self._extract_list(content, "Requirements")

        # Extract description and acceptance criteria
        description = self._extract_description(content)
        acceptance_criteria = self._extract_acceptance_criteria(content)

        if not acceptance_criteria:
            acceptance_criteria = ["Implementation complete"]

        return Task(
            id=task_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            complexity=complexity,
            dependencies=dependencies,
            properties_satisfied=properties,
            requirements=requirements,
            files_likely_affected=files
        )

    def _extract_complexity(self, content: str) -> TaskComplexity:
        """Extract complexity (S, M, L, XL)."""
        match = re.search(r'\*\*Complexity\*\*:\s*([SMLX]+)', content)
        if match:
            value = match.group(1)
            try:
                return TaskComplexity(value)
            except ValueError:
                pass
        return TaskComplexity.M  # Default

    def _extract_list(self, content: str, field_name: str) -> List[str]:
        """Extract list field like Dependencies, Properties, etc."""
        pattern = rf'\*\*{field_name}\*\*:\s*\[(.*?)\]'
        match = re.search(pattern, content)
        if match:
            items = match.group(1)
            if items.strip():
                return [item.strip() for item in items.split(',')]
        return []

    def _extract_description(self, content: str) -> str:
        """Extract description section."""
        match = re.search(r'\*\*Description\*\*:\s*(.+?)(?=\*\*|$)', content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return "No description provided"

    def _extract_acceptance_criteria(self, content: str) -> List[str]:
        """Extract acceptance criteria list."""
        match = re.search(r'\*\*Acceptance Criteria\*\*:\s*(.+?)(?=\*\*|$)', content, re.DOTALL)
        if match:
            criteria_text = match.group(1).strip()
            # Extract numbered or bulleted items
            criteria = []
            for line in criteria_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                    # Remove numbering/bullets
                    clean = re.sub(r'^[\d\-\*\.\)]+\s*', '', line)
                    if clean:
                        criteria.append(clean)
            return criteria
        return []


def parse_tasks(tasks_file: Path) -> TaskGraph:
    """Convenience function."""
    parser = TasksParser()
    return parser.parse(tasks_file)
