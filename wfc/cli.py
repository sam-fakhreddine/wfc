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

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def run_command(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> int:
    """
    Run a command and return exit code.

    Security: Uses shell=False with list arguments to prevent shell injection.
    Accepts List[str] instead of str to enforce safe usage.

    Args:
        cmd: Command as list of arguments (e.g., ["echo", "hello"])
        cwd: Optional working directory
        check: If True, exit on non-zero return code

    Returns:
        Process exit code
    """
    # SECURITY: shell=False + list args prevents shell injection (H-01 fix).
    result = subprocess.run(
        args=cmd, shell=False, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
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

        cmd = ["skills-ref", "validate", str(skill)]
        result = run_command(cmd, check=False, cwd=skills_ref_dir)

        if result != 0:
            failed.append(skill_name)
            print(f"❌ {skill_name} validation failed")
        else:
            print(f"✅ {skill_name} validated")

        if xml and result == 0:
            cmd = ["skills-ref", "to-prompt", str(skill)]
            import subprocess as sp

            # SECURITY: shell=False, list args; cmd built from Path objects, not user input.
            proc = sp.run(cmd, cwd=skills_ref_dir, stdout=sp.PIPE, text=True)
            grep_proc = sp.run(["grep", "-q", "<skill>"], input=proc.stdout, shell=False)
            xml_result = grep_proc.returncode

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
        run_command(["uv", "run", "pytest", "--cov=wfc", "--cov-report=html", "--cov-report=term"])
        print("📊 Coverage report: htmlcov/index.html")
    else:
        print("🧪 Running tests...")
        run_command(["uv", "run", "pytest", "-v"])

    print("✅ Tests passed")


def cmd_benchmark(compare: bool = False):
    """Run token usage benchmarks."""
    print("📊 Running token usage benchmark...")

    cmd = ["uv", "run", "python", "scripts/benchmark_tokens.py"]
    if compare:
        cmd.append("--compare")

    run_command(cmd)


def cmd_lint(fix: bool = False):
    """Run linters."""
    if fix:
        print("🔍 Running linters with auto-fix...")
        run_command(["uv", "run", "ruff", "check", "--fix", "wfc/"])
        run_command(["uv", "run", "black", "wfc/"])
        print("✅ Code fixed and formatted")
    else:
        print("🔍 Running linters...")
        run_command(["uv", "run", "ruff", "check", "wfc/"])
        print("✅ Lint passed")


def cmd_format():
    """Format code."""
    print("🎨 Formatting code...")
    run_command(["uv", "run", "black", "wfc/"])
    run_command(["uv", "run", "ruff", "check", "--fix", "wfc/"])
    print("✅ Code formatted")


def cmd_install(dev: bool = False):
    """Install WFC."""
    if dev:
        print("🔧 Installing WFC for development...")
        run_command(["uv", "pip", "install", "-e", ".[dev,tokens]"])
        print("✅ Development environment ready")
    else:
        print("🚀 Installing WFC with all features...")
        run_command(["uv", "pip", "install", "-e", ".[all]"])
        print("✅ WFC installed")


def cmd_version():
    """Show version."""
    try:
        from importlib.metadata import version

        ver = version("wfc")
    except Exception:
        ver = "dev"
    print("WFC - World Fucking Class")
    print(f"Version: {ver}")
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

    if not tasks_file:
        tasks_file = "plan/TASKS-wfc-implement.md"

    tasks_path = Path(tasks_file)

    if not tasks_path.exists():
        print(f"❌ Tasks file not found: {tasks_file}")
        print("\nExpected file locations:")
        print("  - plan/TASKS.md (default)")
        print("  - plan/TASKS-*.md")
        print("\nUse /wfc-plan to generate a tasks file first.")
        sys.exit(1)

    print(f"📋 Tasks file: {tasks_file}")

    try:
        from wfc_implement.orchestrator import WFCOrchestrator

        from wfc.shared.config import WFCConfig
        from wfc.skills import wfc_implement  # noqa: F401 — activates PEP 562 bridge
    except ImportError as e:
        print(f"❌ Failed to import wfc-implement: {e}")
        print("\nMake sure WFC is installed:")
        print("  wfc install --dev")
        sys.exit(1)

    config = WFCConfig()

    if agents:
        print(f"👥 Agents: {agents} (override)")
        config.set("orchestration.max_agents", agents)
        max_agents = agents
    else:
        max_agents = config.get("orchestration.max_agents", 5)
        print(f"👥 Agents: {max_agents} (from config)")

    if enable_entire:
        print("📹 Entire.io: ENABLED (forced via --enable-entire)")
        config.set("entire_io.enabled", True)
    else:
        entire_enabled = config.get("entire_io.enabled", True)
        if entire_enabled:
            print("📹 Entire.io: ENABLED (capturing agent sessions)")
        else:
            print("📹 Entire.io: DISABLED (set entire_io.enabled=false in config)")

    if skip_quality:
        print("⚠️  WARNING: Skipping quality checks (NOT RECOMMENDED)")
        print("   Quality gate saves 50%+ review tokens")

    print()

    if dry_run:
        print("🔍 DRY RUN MODE - Showing plan without executing")
        print("=" * 60)
        print()

        try:
            from wfc_implement.parser import parse_tasks

            task_graph = parse_tasks(tasks_path)

            print(f"📊 Total tasks: {len(task_graph.tasks)}")
            print(f"📊 Dependency levels: {max(task_graph.get_dependency_levels().values()) + 1}")
            print()

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

    print("🎯 EXECUTE MODE - Starting implementation")
    print("=" * 60)
    print()

    try:
        orchestrator = WFCOrchestrator(config=config, project_root=Path.cwd())

        print("⚙️  Initializing orchestrator...")
        result = orchestrator.run(tasks_path)

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

    validate_parser = subparsers.add_parser("validate", help="Validate WFC skills")
    validate_parser.add_argument("--all", action="store_true", help="Validate all skills")
    validate_parser.add_argument("--xml", action="store_true", help="Also validate XML generation")

    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--coverage", action="store_true", help="Run with coverage")

    benchmark_parser = subparsers.add_parser("benchmark", help="Run token benchmarks")
    benchmark_parser.add_argument("--compare", action="store_true", help="Compare against targets")

    lint_parser = subparsers.add_parser("lint", help="Run linters")
    lint_parser.add_argument("--fix", action="store_true", help="Auto-fix issues")

    subparsers.add_parser("format", help="Format code")

    install_parser = subparsers.add_parser("install", help="Install WFC")
    install_parser.add_argument("--dev", action="store_true", help="Install dev dependencies")

    subparsers.add_parser("version", help="Show version")

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
