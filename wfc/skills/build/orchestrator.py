"""
WFC Build Orchestrator

Intentional Vibe: Quick adaptive interview → complexity assessment → delegate to subagent(s)

CRITICAL: Orchestrator NEVER implements, ONLY coordinates.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional

# Add parent to path for wfc imports
import sys
wfc_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(wfc_root))

from wfc.shared.extended_thinking import ExtendedThinkingDecider, enable_thinking


@dataclass
class BuildSpec:
    """Specification for what to build (from adaptive interview)"""
    goal: str
    files_affected: List[str]
    expected_behavior: str
    tech_stack: str
    acceptance_criteria: List[str]
    complexity: str  # 'simple' or 'complex'
    estimated_agents: int  # 1 or N


class AdaptiveInterviewer:
    """
    Quick adaptive interview for Intentional Vibe.

    Unlike wfc-plan's full interview, this is 3-5 questions max.
    """

    def run_interview(self, initial_description: Optional[str] = None) -> BuildSpec:
        """
        Run quick adaptive interview.

        Args:
            initial_description: Optional user-provided description

        Returns:
            BuildSpec with enough info to spawn subagent(s)
        """
        print("\n🎯 WFC:BUILD - Intentional Vibe Interview\n")

        # Q1: What are you building?
        if initial_description:
            goal = initial_description
            print(f"Goal: {goal}")
        else:
            goal = input("Q1: What are you building?\n→ ")

        # Q2: Which files should this touch?
        files = input("\nQ2: Which files/directories should this affect?\n→ ")
        files_affected = [f.strip() for f in files.split(',') if f.strip()]

        # Q3: Expected behavior?
        expected_behavior = input("\nQ3: What's the expected behavior?\n→ ")

        # Q4: Tech stack?
        tech_stack = input("\nQ4: Tech stack/patterns to follow?\n→ ")

        # Q5: Acceptance criteria (auto-generate or ask)
        print("\nQ5: Acceptance criteria (optional, press Enter to auto-generate)")
        criteria_input = input("→ ")

        if criteria_input:
            acceptance_criteria = [c.strip() for c in criteria_input.split(',')]
        else:
            # Auto-generate basic criteria
            acceptance_criteria = [
                f"Implements: {goal}",
                "All tests pass",
                "Quality checks pass (formatters, linters)",
                f"Follows {tech_stack} patterns"
            ]

        return BuildSpec(
            goal=goal,
            files_affected=files_affected,
            expected_behavior=expected_behavior,
            tech_stack=tech_stack,
            acceptance_criteria=acceptance_criteria,
            complexity='unknown',  # Will be assessed
            estimated_agents=0  # Will be determined
        )


class ComplexityAssessor:
    """
    Assess task complexity to determine: 1 agent or N agents?
    """

    def assess(self, spec: BuildSpec) -> BuildSpec:
        """
        Assess complexity and determine agent count.

        Simple heuristics:
        - 1-2 files → 1 agent
        - 3-5 files → 1-2 agents
        - 6+ files → N agents
        - Keywords like "system", "refactor", "architecture" → N agents

        Args:
            spec: Build specification

        Returns:
            Updated spec with complexity and agent count
        """
        print("\n🔍 Assessing complexity...")

        # Count indicators of complexity
        complexity_score = 0

        # File count
        file_count = len(spec.files_affected)
        if file_count >= 6:
            complexity_score += 3
        elif file_count >= 3:
            complexity_score += 1

        # Keywords in goal
        complex_keywords = [
            'system', 'architecture', 'refactor', 'multiple',
            'dashboard', 'authentication', 'authorization',
            'integration', 'infrastructure'
        ]

        goal_lower = spec.goal.lower()
        for keyword in complex_keywords:
            if keyword in goal_lower:
                complexity_score += 2
                break

        # Multiple tech stacks
        if ' and ' in spec.tech_stack.lower() or '/' in spec.tech_stack:
            complexity_score += 1

        # Determine complexity
        if complexity_score >= 4:
            spec.complexity = 'complex'
            spec.estimated_agents = min(3, max(2, file_count // 3))
        else:
            spec.complexity = 'simple'
            spec.estimated_agents = 1

        print(f"   Complexity: {spec.complexity.upper()}")
        print(f"   Estimated agents: {spec.estimated_agents}")

        return spec


class BuildOrchestrator:
    """
    Main orchestrator for wfc-build.

    CRITICAL: This class ONLY coordinates. It NEVER implements.
    All implementation work is delegated to subagents via Task tool.
    """

    def __init__(self, project_root: Path):
        """Initialize orchestrator."""
        self.project_root = project_root
        self.interviewer = AdaptiveInterviewer()
        self.assessor = ComplexityAssessor()

    def run(self, description: Optional[str] = None) -> Dict:
        """
        Run complete wfc-build workflow.

        CRITICAL: This method NEVER does implementation work.
        It ONLY coordinates subagents.

        Args:
            description: Optional initial description

        Returns:
            Result dict with status and details
        """
        print("\n" + "="*60)
        print("WFC:BUILD - Intentional Vibe Coding")
        print("="*60)

        # Step 1: Adaptive interview
        spec = self.interviewer.run_interview(description)

        # Step 2: Assess complexity
        spec = self.assessor.assess(spec)

        # Step 3: Spawn subagent(s) via Task tool
        print(f"\n🚀 Spawning {spec.estimated_agents} subagent(s)...")

        if spec.estimated_agents == 1:
            # Simple task: 1 subagent
            result = self._spawn_single_agent(spec)
        else:
            # Complex task: N subagents
            result = self._spawn_multi_agents(spec)

        return result

    def _spawn_single_agent(self, spec: BuildSpec) -> Dict:
        """
        Spawn single subagent for simple task.

        CRITICAL: Delegates to Task tool, does NOT implement.
        """
        print("\n📋 Task breakdown:")
        print(f"   Single agent will:")
        print(f"   - Implement: {spec.goal}")
        print(f"   - Affect: {', '.join(spec.files_affected)}")
        print(f"   - Follow: {spec.tech_stack}")

        # Build subagent prompt
        agent_prompt = self._build_agent_prompt(
            agent_id="agent-1",
            task_description=spec.goal,
            files=spec.files_affected,
            behavior=spec.expected_behavior,
            tech_stack=spec.tech_stack,
            criteria=spec.acceptance_criteria
        )

        print("\n🤖 Subagent instructions prepared")
        print("   → Follow TDD workflow (TEST → IMPLEMENT → REFACTOR)")
        print("   → Run quality checks (formatters, linters, tests)")
        print("   → Submit report when complete")

        # In production: Would use Task tool here
        # Task(
        #     subagent_type="general-purpose",
        #     prompt=agent_prompt,
        #     model="sonnet",
        #     description=f"Build: {spec.goal}"
        # )

        print("\n⏳ Waiting for subagent to complete...")
        print("   (In production: polling TaskOutput)")

        return {
            'status': 'spawned',
            'agents': 1,
            'spec': spec,
            'prompt': agent_prompt
        }

    def _spawn_multi_agents(self, spec: BuildSpec) -> Dict:
        """
        Spawn multiple subagents for complex task.

        CRITICAL: Delegates to Task tool, does NOT implement.
        """
        print("\n📋 Task breakdown:")

        # Intelligent task splitting (simplified for now)
        # In production: would use smarter decomposition
        tasks = self._decompose_task(spec)

        print(f"   Split into {len(tasks)} subtasks:")
        for i, task in enumerate(tasks, 1):
            print(f"   {i}. {task['description']}")

        # Build prompts for each agent
        prompts = []
        for i, task in enumerate(tasks, 1):
            agent_prompt = self._build_agent_prompt(
                agent_id=f"agent-{i}",
                task_description=task['description'],
                files=task['files'],
                behavior=spec.expected_behavior,
                tech_stack=spec.tech_stack,
                criteria=task['criteria']
            )
            prompts.append(agent_prompt)

        print(f"\n🤖 Spawning {len(prompts)} subagents in parallel...")

        # In production: Would spawn all Task tools in parallel (single message)
        # for i, prompt in enumerate(prompts, 1):
        #     Task(
        #         subagent_type="general-purpose",
        #         prompt=prompt,
        #         model="sonnet",
        #         description=f"Build subtask {i}"
        #     )

        print("\n⏳ Waiting for all subagents to complete...")
        print("   (In production: polling TaskOutput for each)")

        return {
            'status': 'spawned',
            'agents': len(tasks),
            'spec': spec,
            'tasks': tasks,
            'prompts': prompts
        }

    def _build_agent_prompt(
        self,
        agent_id: str,
        task_description: str,
        files: List[str],
        behavior: str,
        tech_stack: str,
        criteria: List[str],
        complexity: str = 'M'  # Default medium complexity
    ) -> str:
        """
        Build prompt for subagent Task tool invocation.

        Returns complete instructions for TDD workflow.
        Enables extended thinking for complex builds.
        """
        # Decide if extended thinking should be used
        # For build tasks, enable thinking if:
        # - Multi-file (3+ files)
        # - Keywords suggest complexity
        num_files = len(files)
        complexity_keywords = ['architecture', 'system', 'refactor', 'complex']
        has_complexity_keyword = any(
            keyword in task_description.lower()
            for keyword in complexity_keywords
        )

        # Determine complexity
        if num_files >= 6 or has_complexity_keyword:
            calculated_complexity = 'L'
        elif num_files >= 3:
            calculated_complexity = 'M'
        else:
            calculated_complexity = 'S'

        # Get thinking config
        thinking_config = ExtendedThinkingDecider.should_use_extended_thinking(
            complexity=calculated_complexity,
            properties=[],
            retry_count=0,
            is_architecture=has_complexity_keyword
        )

        # Log decision
        if thinking_config.mode.value != 'normal':
            print(f"   ⚡ Extended thinking enabled for {agent_id}")
            print(f"      Reason: {thinking_config.reason}")

        # Build prompt
        prompt_parts = [
            f"You are {agent_id}, a WFC build agent.",
            "",
            "## Task",
            f"{task_description}",
            f"Complexity: {calculated_complexity}",
        ]

        # Add extended thinking section if enabled
        thinking_section = thinking_config.to_prompt_section()
        if thinking_section:
            prompt_parts.append(thinking_section)

        prompt_parts.extend([
            "",
            "## Files to Create/Modify",
            '\n'.join(f"- {f}" for f in files),
            "",
            "## Expected Behavior",
            behavior,
            "",
            "## Tech Stack/Patterns",
            tech_stack,
            "",
            "## Acceptance Criteria",
            '\n'.join(f"- {c}" for c in criteria),
            "",
            "## Workflow (TDD - STRICT)",
            "",
        ])
            "1. UNDERSTAND",
            "   - Read task description above",
            "   - Review existing files (if any)",
            "   - Understand expected behavior",
            "",
            "2. TEST_FIRST (RED)",
            "   - Write tests BEFORE implementation",
            "   - Tests must cover acceptance criteria",
            "   - Run tests → they MUST FAIL",
            "",
            "3. IMPLEMENT (GREEN)",
            "   - Write minimum code to pass tests",
            f"   - Follow {tech_stack} patterns",
            "   - Run tests → they MUST PASS",
            "",
            "4. REFACTOR",
            "   - Clean up code without changing behavior",
            "   - Maintain SOLID & DRY principles",
            "   - Run tests → still PASS",
            "",
            "5. QUALITY_CHECK",
            "   - Run formatters (black, prettier, etc.)",
            "   - Run linters (ruff, eslint, etc.)",
            "   - Run all tests",
            "   - BLOCKS if any check fails",
            "",
            "6. SUBMIT",
            "   - Verify all acceptance criteria met",
            "   - Produce agent report",
            "   - Include: files changed, tests added, quality check results",
        ]

        return '\n'.join(prompt_parts)

    def _decompose_task(self, spec: BuildSpec) -> List[Dict]:
        """
        Decompose complex task into subtasks.

        Simplified heuristic:
        - Group files by directory/component
        - Assign related files to same agent

        In production: Would use smarter decomposition.
        """
        # Simple grouping by directory
        file_groups = {}
        for file_path in spec.files_affected:
            # Get first directory component
            parts = file_path.split('/')
            group = parts[0] if len(parts) > 1 else 'root'

            if group not in file_groups:
                file_groups[group] = []
            file_groups[group].append(file_path)

        # Create tasks from groups
        tasks = []
        for i, (group, files) in enumerate(file_groups.items(), 1):
            tasks.append({
                'id': f'subtask-{i}',
                'description': f"{spec.goal} - {group} component",
                'files': files,
                'criteria': [
                    f"Implements {group} component for: {spec.goal}",
                    "All tests pass",
                    "Quality checks pass"
                ]
            })

        return tasks


# CLI entry point
def main():
    """Main entry point for testing"""
    orchestrator = BuildOrchestrator(Path.cwd())

    import sys
    description = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else None

    result = orchestrator.run(description)

    print("\n" + "="*60)
    print("✅ Orchestrator completed")
    print(f"   Status: {result['status']}")
    print(f"   Agents spawned: {result['agents']}")
    print("="*60)


if __name__ == '__main__':
    main()
