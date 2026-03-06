"""Context Mapper — Agent 1 of the CLAUDE.md remediation pipeline.

Inventories the CLAUDE.md file and its surrounding codebase to produce a
ContextManifest. This is a pure analysis step: no files are modified.

The mapper runs locally (no LLM call) for speed — filesystem inspection is
deterministic and doesn't require Claude's reasoning.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


_IMPERATIVE_PATTERN = re.compile(
    r"^\s*[-*]\s+(?:always|never|do not|don't|must|should|use|avoid|run|ensure)\b",
    re.IGNORECASE | re.MULTILINE,
)
_COMMAND_PATTERN = re.compile(r"`([a-z][a-z0-9 _\-./]*(?:\s+[a-z][a-z0-9 _\-./]*){0,5})`")
_PATH_PATTERN = re.compile(r"`([./~][^\s`]+|[a-z][a-z0-9_\-/]+\.[a-z]{1,6})`")
_ALWAYS_NEVER_PATTERN = re.compile(r"\b(?:always|never|must|do not|don't)\b", re.IGNORECASE)


def _count_instructions(content: str) -> int:
    """Heuristic: count imperative statements in CLAUDE.md content."""
    imperative_items = len(_IMPERATIVE_PATTERN.findall(content))
    no_code = re.sub(r"```[\s\S]*?```", "", content)
    always_never = len(_ALWAYS_NEVER_PATTERN.findall(no_code))
    return max(imperative_items, always_never)


def _estimate_tokens(content: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(content) // 4


def _extract_commands(content: str) -> list[str]:
    """Extract backtick-wrapped commands from CLAUDE.md."""
    no_code_fences = re.sub(r"```[\s\S]*?```", "", content)
    return list(dict.fromkeys(_COMMAND_PATTERN.findall(no_code_fences)))


def _extract_paths(content: str) -> list[str]:
    """Extract file/directory path references."""
    no_code_fences = re.sub(r"```[\s\S]*?```", "", content)
    return list(dict.fromkeys(_PATH_PATTERN.findall(no_code_fences)))


def _extract_sections(content: str) -> list[str]:
    """Extract markdown section headers (## level)."""
    return re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)


def _count_code_blocks(content: str) -> int:
    return len(re.findall(r"```", content)) // 2


def _detect_package_manager(root: Path) -> str:
    if (root / "uv.lock").exists() or (root / "pyproject.toml").exists():
        return "uv"
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "package-lock.json").exists():
        return "npm"
    if (root / "Pipfile").exists():
        return "pipenv"
    return "unknown"


def _detect_language(root: Path) -> str:
    if (root / "pyproject.toml").exists() or (root / "setup.py").exists():
        return "Python"
    if (root / "package.json").exists():
        return "JavaScript/TypeScript"
    if (root / "Cargo.toml").exists():
        return "Rust"
    if (root / "go.mod").exists():
        return "Go"
    if (root / "pom.xml").exists() or (root / "build.gradle").exists():
        return "Java"
    return "unknown"


def _detect_framework(root: Path) -> str:
    if (root / "pyproject.toml").exists():
        try:
            content = (root / "pyproject.toml").read_text(errors="replace")
            if "fastapi" in content.lower():
                return "FastAPI"
            if "django" in content.lower():
                return "Django"
            if "flask" in content.lower():
                return "Flask"
        except OSError:
            pass
    if (root / "package.json").exists():
        try:
            content = (root / "package.json").read_text(errors="replace")
            if '"next"' in content:
                return "Next.js"
            if '"react"' in content:
                return "React"
            if '"vue"' in content:
                return "Vue"
        except OSError:
            pass
    return "unknown"


def _get_available_scripts(root: Path) -> list[str]:
    scripts: list[str] = []
    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text())
            scripts.extend(f"npm run {k}" for k in data.get("scripts", {}).keys())
        except (json.JSONDecodeError, OSError):
            pass
    makefile = root / "Makefile"
    if makefile.exists():
        try:
            content = makefile.read_text(errors="replace")
            targets = re.findall(r"^([a-zA-Z][a-zA-Z0-9_-]+)\s*:", content, re.MULTILINE)
            scripts.extend(f"make {t}" for t in targets if not t.startswith("."))
        except OSError:
            pass
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(errors="replace")
            in_scripts = False
            for line in content.splitlines():
                if "[project.scripts]" in line:
                    in_scripts = True
                    continue
                if in_scripts and line.startswith("["):
                    break
                if in_scripts and "=" in line:
                    name = line.split("=")[0].strip()
                    scripts.append(f"uv run {name}")
        except OSError:
            pass
    return list(dict.fromkeys(scripts))


def _check_linter(root: Path) -> tuple[bool, str | None]:
    configs = {
        ".eslintrc": "eslint",
        ".eslintrc.js": "eslint",
        ".eslintrc.json": "eslint",
        "biome.json": "biome",
        ".prettierrc": "prettier",
        ".prettierrc.json": "prettier",
        "ruff.toml": "ruff",
        ".ruff.toml": "ruff",
    }
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            if "[tool.ruff]" in pyproject.read_text(errors="replace"):
                return True, "ruff"
        except OSError:
            pass
    for fname, ltype in configs.items():
        if (root / fname).exists():
            return True, ltype
    return False, None


def _check_formatter(root: Path) -> tuple[bool, str | None]:
    fmt_configs = {
        ".prettierrc": "prettier",
        ".prettierrc.json": "prettier",
        "biome.json": "biome",
    }
    for fname, ftype in fmt_configs.items():
        if (root / fname).exists():
            return True, ftype
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(errors="replace")
            if "[tool.black]" in content:
                return True, "black"
            if "[tool.ruff.format]" in content:
                return True, "ruff"
        except OSError:
            pass
    return False, None


def _check_test_framework(root: Path) -> tuple[bool, str | None]:
    if (root / "pytest.ini").exists() or (root / "conftest.py").exists():
        return True, "pytest"
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(errors="replace")
            if "[tool.pytest" in content:
                return True, "pytest"
        except OSError:
            pass
    if (root / "jest.config.js").exists() or (root / "jest.config.ts").exists():
        return True, "jest"
    if (root / "vitest.config.ts").exists() or (root / "vitest.config.js").exists():
        return True, "vitest"
    return False, None


def _get_top_level_dirs(root: Path) -> list[str]:
    try:
        return sorted(
            d.name
            for d in root.iterdir()
            if d.is_dir()
            and not d.name.startswith(".")
            and d.name not in {"__pycache__", "node_modules", ".venv", "venv"}
        )
    except OSError:
        return []


def _check_doc_locations(root: Path) -> list[str]:
    locations = []
    for name in ["docs", "doc", "documentation", "agent_docs", "wiki"]:
        d = root / name
        if d.exists() and d.is_dir():
            locations.append(str(d.relative_to(root)))
    if (root / "README.md").exists():
        locations.append("README.md")
    return locations


def _validate_commands(commands: list[str], available: list[str]) -> list[dict[str, Any]]:
    result = []
    available_lower = [s.lower() for s in available]
    always_valid = {
        "git",
        "cd",
        "ls",
        "mkdir",
        "rm",
        "cp",
        "mv",
        "echo",
        "cat",
        "python",
        "python3",
        "uv",
        "node",
        "npm",
        "npx",
        "pnpm",
        "cargo",
        "go",
        "make",
        "curl",
        "wget",
    }
    for cmd in commands:
        cmd_lower = cmd.lower()
        exists = any(cmd_lower in a or a in cmd_lower for a in available_lower)
        if cmd.split()[0].lower() in always_valid:
            exists = True
        result.append({"command": cmd, "exists": exists})
    return result


def _validate_paths(paths: list[str], root: Path) -> list[dict[str, Any]]:
    result = []
    for p in paths:
        clean = p.lstrip("~/")
        exists = (root / clean).exists()
        result.append({"path": p, "exists": exists})
    return result


def _check_red_flags(
    content: str,
    total_lines: int,
    instruction_count: int,
    has_linter: bool,
    commands_valid: list[dict],
    paths_valid: list[dict],
) -> list[str]:
    flags = []
    if total_lines > 300:
        flags.append(
            f"CLAUDE.md exceeds 300 lines ({total_lines} lines) — active performance degradation risk"
        )
    if instruction_count > 100:
        flags.append(f"Instruction count {instruction_count} exceeds safe budget ceiling of 100")
    if has_linter and re.search(
        r"(?:indent|spacing|quotes|semicolons|trailing|style)", content, re.IGNORECASE
    ):
        flags.append("File contains inline code style rules when a linter config exists")
    stale_cmds = [c["command"] for c in commands_valid if not c["exists"]]
    if stale_cmds:
        flags.append(f"Stale/unverifiable commands: {', '.join(stale_cmds[:3])}")
    stale_paths = [p["path"] for p in paths_valid if not p["exists"]]
    if stale_paths:
        flags.append(f"References to nonexistent paths: {', '.join(stale_paths[:3])}")
    if "TODO" in content or "FIXME" in content:
        flags.append("File contains TODO/FIXME items — incomplete or boilerplate")
    if not re.search(r"\[.*?\]\(.*?\)|See `|Read `|Refer to `", content):
        if total_lines > 100:
            flags.append(
                "No progressive disclosure — no pointers to external docs despite file size"
            )
    return flags


def map_project(project_root: str | Path) -> dict[str, Any]:
    """Inspect a project root and return the Context Mapper manifest as a dict.

    This is the primary entry point. Returns a JSON-serialisable dict matching
    the schema defined in the spec. Never raises — errors are returned as
    red_flags entries.
    """
    root = Path(project_root).resolve()
    claude_md_path = root / "CLAUDE.md"

    try:
        content = claude_md_path.read_text(errors="replace") if claude_md_path.exists() else ""
    except OSError as e:
        return {"claude_md": {"total_lines": 0}, "red_flags": [f"Cannot read CLAUDE.md: {e}"]}

    lines = content.splitlines()
    total_lines = len(lines)
    sections = _extract_sections(content)
    instruction_count = _count_instructions(content)
    commands = _extract_commands(content)
    paths_ref = _extract_paths(content)

    has_linter, linter_type = _check_linter(root)
    has_formatter, formatter_type = _check_formatter(root)
    has_test, test_framework = _check_test_framework(root)
    available_scripts = _get_available_scripts(root)

    commands_valid = _validate_commands(commands, available_scripts)
    paths_valid = _validate_paths(paths_ref, root)

    sub_files = []
    try:
        for sub_claude in root.rglob("CLAUDE.md"):
            if sub_claude == claude_md_path:
                continue
            try:
                sub_content = sub_claude.read_text(errors="replace")
                sub_files.append(
                    {
                        "path": str(sub_claude.relative_to(root)),
                        "lines": len(sub_content.splitlines()),
                        "purpose": sub_content.splitlines()[0][:80] if sub_content else "",
                    }
                )
            except OSError:
                pass
    except OSError:
        pass

    top_dirs = _get_top_level_dirs(root)
    doc_locations = _check_doc_locations(root)

    red_flags = _check_red_flags(
        content, total_lines, instruction_count, has_linter, commands_valid, paths_valid
    )

    codebase_not_in_doc: list[str] = []
    if has_linter and linter_type and linter_type.lower() not in content.lower():
        codebase_not_in_doc.append(f"Linter config ({linter_type}) exists but not mentioned")
    if (root / ".github" / "workflows").exists() and "workflow" not in content.lower():
        codebase_not_in_doc.append("GitHub Actions workflows not mentioned")

    return {
        "claude_md": {
            "location": str(claude_md_path),
            "total_lines": total_lines,
            "total_sections": len(sections),
            "section_names": sections,
            "code_blocks": _count_code_blocks(content),
            "instruction_count": instruction_count,
            "estimated_tokens": _estimate_tokens(content),
            "commands_referenced": commands,
            "paths_referenced": paths_ref,
            "tools_referenced": [],
            "has_project_summary": bool(re.search(r"^# .+\n\n[^\n#]", content, re.MULTILINE)),
            "has_directory_map": bool(re.search(r"```\n[├└─]", content)),
            "has_commands_section": any("command" in s.lower() for s in sections),
            "has_code_style_section": any(
                any(k in s.lower() for k in ["style", "lint", "format"]) for s in sections
            ),
            "has_workflow_section": any("workflow" in s.lower() for s in sections),
            "has_architecture_section": any(
                any(k in s.lower() for k in ["arch", "structure", "overview"]) for s in sections
            ),
            "has_progressive_disclosure": bool(
                re.search(r"See `|Read `|Refer to `|\[.*\]\(docs/", content)
            ),
        },
        "subdirectory_claude_mds": sub_files,
        "codebase": {
            "language": _detect_language(root),
            "framework": _detect_framework(root),
            "package_manager": _detect_package_manager(root),
            "available_scripts": available_scripts,
            "top_level_dirs": top_dirs,
            "has_linter_config": has_linter,
            "linter_type": linter_type,
            "has_formatter_config": has_formatter,
            "formatter_type": formatter_type,
            "has_ci_config": (root / ".github" / "workflows").exists(),
            "has_test_framework": has_test,
            "test_framework": test_framework,
            "has_hooks_config": (root / ".claude" / "settings.json").exists(),
            "has_mcp_config": (root / ".mcp.json").exists(),
            "has_slash_commands": (root / ".claude" / "commands").exists(),
            "has_existing_docs": bool(doc_locations),
            "doc_locations": doc_locations,
        },
        "cross_reference": {
            "commands_valid": commands_valid,
            "paths_valid": paths_valid,
            "tools_valid": [],
            "codebase_features_not_in_claude_md": codebase_not_in_doc,
            "claude_md_claims_not_in_codebase": [p["path"] for p in paths_valid if not p["exists"]],
        },
        "red_flags": red_flags,
    }
