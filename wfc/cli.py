#!/usr/bin/env python3
"""
WFC CLI - Command-line interface for World Fucking Class tools

Usage:
    wfc validate [--all] [--xml]                      - Validate WFC skills
    wfc test [--coverage]                             - Run tests
    wfc benchmark [--compare]                         - Run token benchmarks
    wfc lint [--fix]                                  - Run linters
    wfc format                                        - Format code
    wfc install [--dev]                               - Install WFC
    wfc implement [--tasks FILE] [--agents N] [--dry-run] [--enable-entire]  - Execute implementation tasks
    wfc version                                       - Show version
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import Optional


def run_command(cmd: str, cwd: Optional[Path] = None, check: bool = True) -> int:
    """Run a shell command and return exit code."""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    if result.stdout:
        print(result.stdout)

    if check and result.returncode != 0:
        sys.exit(result.returncode)

    return result.returncode


def cmd_validate(all_skills: bool = False, xml: bool = False):
    """Validate WFC skills."""
    print("🔍 Validating WFC skills...")

    skills_ref_dir = Path.home() / "repos/agentskills/skills-ref"

    if not skills_ref_dir.exists():
        print("❌ skills-ref not found at ~/repos/agentskills/skills-ref")
        print("   Clone agentskills repo first:")
        print("   git clone https://github.com/anthropics/agentskills ~/repos/agentskills")
        sys.exit(1)

    skills_dir = Path.home() / ".claude/skills"
    wfc_skills = sorted(skills_dir.glob("wfc-*"))

    if not wfc_skills:
        print("❌ No WFC skills found in ~/.claude/skills/")
        sys.exit(1)

    failed = []

    for skill in wfc_skills:
        skill_name = skill.name

        # Validate structure
        cmd = f"cd {skills_ref_dir} && source .venv/bin/activate && skills-ref validate {skill}"
        result = run_command(cmd, check=False)

        if result != 0:
            failed.append(skill_name)
            print(f"❌ {skill_name} validation failed")
        else:
            print(f"✅ {skill_name} validated")

        # Validate XML if requested
        if xml and result == 0:
            cmd = f"cd {skills_ref_dir} && source .venv/bin/activate && skills-ref to-prompt {skill} | grep -q '<skill>'"
            xml_result = run_command(cmd, check=False)

            if xml_result != 0:
                failed.append(f"{skill_name} (XML)")
                print(f"❌ {skill_name} XML generation failed")

    if failed:
        print(f"\n❌ {len(failed)} skill(s) failed validation:")
        for skill in failed:
            print(f"  - {skill}")
        sys.exit(1)

    print(f"\n✅ All {len(wfc_skills)} WFC skills validated")


def cmd_test(coverage: bool = False):
    """Run tests."""
    if coverage:
        print("🧪 Running tests with coverage...")
        run_command("pytest --cov=wfc --cov-report=html --cov-report=term")
        print("📊 Coverage report: htmlcov/index.html")
    else:
        print("🧪 Running tests...")
        run_command("pytest -v")

    print("✅ Tests passed")


def cmd_benchmark(compare: bool = False):
    """Run token usage benchmarks."""
    print("📊 Running token usage benchmark...")

    cmd = "python scripts/benchmark_tokens.py"
    if compare:
        cmd += " --compare"

    run_command(cmd)


def cmd_lint(fix: bool = False):
    """Run linters."""
    if fix:
        print("🔍 Running linters with auto-fix...")
        run_command("ruff check --fix wfc/")
        run_command("black wfc/")
        print("✅ Code fixed and formatted")
    else:
        print("🔍 Running linters...")
        run_command("ruff check wfc/")
        print("✅ Lint passed")


def cmd_format():
    """Format code."""
    print("🎨 Formatting code...")
    run_command("black wfc/")
    run_command("ruff check --fix wfc/")
    print("✅ Code formatted")


def cmd_install(dev: bool = False):
    """Install WFC."""
    if dev:
        print("🔧 Installing WFC for development...")
        run_command("uv pip install -e '.[dev,tokens]'")
        print("✅ Development environment ready")
    else:
        print("🚀 Installing WFC with all features...")
        run_command("uv pip install -e '.[all]'")
        print("✅ WFC installed")


def cmd_version():
    """Show version."""
    print("WFC - World Fucking Class")
    print("Version: 0.1.0")
    print("Agent Skills Compliant ✅")


def cmd_implement(
    tasks_file: Optional[str] = None,
    agents: Optional[int] = None,
    dry_run: bool = False,
    skip_quality: bool = False,
    enable_entire: bool = False,
):
    """
    Execute implementation tasks with wfc-implement.

    Args:
        tasks_file: Path to TASKS.md (default: plan/TASKS.md)
        agents: Number of parallel agents (default: from config)
        dry_run: Show plan without executing
        skip_quality: Skip quality checks (NOT RECOMMENDED)
        enable_entire: Enable Entire.io session capture (RECOMMENDED for debugging)
    """
    print("🚀 WFC Implement - Multi-Agent Parallel Implementation")
    print("=" * 60)

    # Determine tasks file
    if not tasks_file:
        tasks_file = "plan/TASKS-wfc-implement.md"  # Default

    tasks_path = Path(tasks_file)

    if not tasks_path.exists():
        print(f"❌ Tasks file not found: {tasks_file}")
        print("\nExpected file locations:")
        print("  - plan/TASKS.md (default)")
        print("  - plan/TASKS-*.md")
        print("\nUse /wfc-plan to generate a tasks file first.")
        sys.exit(1)

    print(f"📋 Tasks file: {tasks_file}")

    # Import orchestrator
    try:
        from wfc.skills.implement.orchestrator import WFCOrchestrator
        from wfc.shared.config import WFCConfig
    except ImportError as e:
        print(f"❌ Failed to import wfc-implement: {e}")
        print("\nMake sure WFC is installed:")
        print("  wfc install --dev")
        sys.exit(1)

    # Load config
    config = WFCConfig()

    # Override agent count if specified
    if agents:
        print(f"👥 Agents: {agents} (override)")
        config.set("orchestration.max_agents", agents)
        max_agents = agents
    else:
        max_agents = config.get("orchestration.max_agents", 5)
        print(f"👥 Agents: {max_agents} (from config)")

    # Entire.io status (enabled by default)
    if enable_entire:
        # Force enable even if config says false
        print("📹 Entire.io: ENABLED (forced via --enable-entire)")
        config.set("entire_io.enabled", True)
    else:
        entire_enabled = config.get("entire_io.enabled", True)  # Default: True
        if entire_enabled:
            print("📹 Entire.io: ENABLED (capturing agent sessions)")
        else:
            print("📹 Entire.io: DISABLED (set entire_io.enabled=false in config)")

    # Warn if skipping quality
    if skip_quality:
        print("⚠️  WARNING: Skipping quality checks (NOT RECOMMENDED)")
        print("   Quality gate saves 50%+ review tokens")

    print()

    # Dry run mode
    if dry_run:
        print("🔍 DRY RUN MODE - Showing plan without executing")
        print("=" * 60)
        print()

        # Parse tasks file
        try:
            from wfc.skills.implement.parser import parse_tasks

            task_graph = parse_tasks(tasks_path)

            print(f"📊 Total tasks: {len(task_graph.tasks)}")
            print(f"📊 Dependency levels: {max(task_graph.get_dependency_levels().values()) + 1}")
            print()

            # Show tasks by level
            levels = task_graph.get_dependency_levels()
            max_level = max(levels.values()) if levels else 0

            for level in range(max_level + 1):
                level_tasks = [t for t in task_graph.tasks if levels.get(t.id) == level]

                if level_tasks:
                    print(f"Level {level} ({len(level_tasks)} tasks):")
                    for task in level_tasks:
                        deps = (
                            f" [deps: {', '.join(task.dependencies)}]" if task.dependencies else ""
                        )
                        print(f"  - {task.id}: {task.title} ({task.complexity.value}){deps}")
                    print()

            print("✅ Dry run complete")
            print("\nTo execute: wfc implement (without --dry-run)")

        except Exception as e:
            print(f"❌ Failed to parse tasks: {e}")
            sys.exit(1)

        return

    # Execute mode
    print("🎯 EXECUTE MODE - Starting implementation")
    print("=" * 60)
    print()

    try:
        # Create orchestrator
        orchestrator = WFCOrchestrator(config=config, project_root=Path.cwd())

        # Run implementation
        print("⚙️  Initializing orchestrator...")
        result = orchestrator.run(tasks_path)

        # Display results
        print()
        print("=" * 60)
        print("📊 IMPLEMENTATION COMPLETE")
        print("=" * 60)
        print(f"✅ Completed: {result.tasks_completed}")
        print(f"❌ Failed: {result.tasks_failed}")
        print(f"🔄 Rolled back: {result.tasks_rolled_back}")
        print(f"⏱️  Duration: {result.duration_ms / 1000:.1f}s")
        print(f"🎫 Tokens: {result.total_tokens.get('total', 0):,}")
        print()

        if result.tasks_failed > 0:
            print("⚠️  Some tasks failed - check PLAN-*.md files for recovery plans")
            sys.exit(1)

        print("✅ All tasks completed successfully!")
        print()
        print("This is World Fucking Class. 🚀")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("Worktrees may still exist - check .worktrees/")
        sys.exit(130)

    except Exception as e:
        print(f"\n\n❌ Implementation failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="WFC CLI - World Fucking Class tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Validate
    validate_parser = subparsers.add_parser("validate", help="Validate WFC skills")
    validate_parser.add_argument("--all", action="store_true", help="Validate all skills")
    validate_parser.add_argument("--xml", action="store_true", help="Also validate XML generation")

    # Test
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--coverage", action="store_true", help="Run with coverage")

    # Benchmark
    benchmark_parser = subparsers.add_parser("benchmark", help="Run token benchmarks")
    benchmark_parser.add_argument("--compare", action="store_true", help="Compare against targets")

    # Lint
    lint_parser = subparsers.add_parser("lint", help="Run linters")
    lint_parser.add_argument("--fix", action="store_true", help="Auto-fix issues")

    # Format
    subparsers.add_parser("format", help="Format code")

    # Install
    install_parser = subparsers.add_parser("install", help="Install WFC")
    install_parser.add_argument("--dev", action="store_true", help="Install dev dependencies")

    # Version
    subparsers.add_parser("version", help="Show version")

    # Implement
    implement_parser = subparsers.add_parser("implement", help="Execute implementation tasks")
    implement_parser.add_argument(
        "--tasks", type=str, help="Path to TASKS.md (default: plan/TASKS.md)"
    )
    implement_parser.add_argument("--agents", type=int, help="Number of parallel agents")
    implement_parser.add_argument(
        "--dry-run", action="store_true", help="Show plan without executing"
    )
    implement_parser.add_argument(
        "--skip-quality", action="store_true", help="Skip quality checks (NOT RECOMMENDED)"
    )
    implement_parser.add_argument(
        "--enable-entire",
        action="store_true",
        help="Enable Entire.io session capture (RECOMMENDED for debugging)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Dispatch commands
    if args.command == "validate":
        cmd_validate(all_skills=args.all, xml=args.xml)
    elif args.command == "test":
        cmd_test(coverage=args.coverage)
    elif args.command == "benchmark":
        cmd_benchmark(compare=args.compare)
    elif args.command == "lint":
        cmd_lint(fix=args.fix)
    elif args.command == "format":
        cmd_format()
    elif args.command == "install":
        cmd_install(dev=args.dev)
    elif args.command == "version":
        cmd_version()
    elif args.command == "implement":
        cmd_implement(
            tasks_file=args.tasks,
            agents=args.agents,
            dry_run=args.dry_run,
            skip_quality=args.skip_quality,
            enable_entire=args.enable_entire,
        )


if __name__ == "__main__":
    main()
