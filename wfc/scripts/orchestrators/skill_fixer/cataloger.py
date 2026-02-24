"""Cataloger agent - filesystem inventory (local, deterministic).

No LLM required. Pure Python filesystem analysis.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional

import yaml

from .schemas import (
    BodyMetrics,
    CrossReferences,
    FilesystemMetrics,
    FrontmatterMetrics,
    SkillManifest,
)


class SkillCataloger:
    """
    Catalogs skill filesystem structure and content metrics.

    Pure local analysis - no LLM required.
    """

    def catalog(self, skill_path: Path) -> SkillManifest:
        """
        Catalog a skill directory.

        Args:
            skill_path: Path to skill directory

        Returns:
            SkillManifest with complete inventory
        """
        skill_md = skill_path / "SKILL.md"

        if not skill_md.exists():
            raise FileNotFoundError(f"SKILL.md not found in {skill_path}")

        content = skill_md.read_text(errors="replace")

        frontmatter = self._parse_frontmatter(content)

        body = self._parse_body(content)

        filesystem = self._analyze_filesystem(skill_path)

        cross_refs = self._check_cross_references(skill_path, content, filesystem)

        red_flags = self._detect_red_flags(frontmatter, body, filesystem, cross_refs)

        skills_ref_available, skills_ref_output = self._check_skills_ref(skill_md)

        return SkillManifest(
            skill_path=skill_path,
            frontmatter=frontmatter,
            body=body,
            filesystem=filesystem,
            cross_references=cross_refs,
            red_flags=red_flags,
            skills_ref_available=skills_ref_available,
            skills_ref_output=skills_ref_output,
        )

    def _parse_frontmatter(self, content: str) -> FrontmatterMetrics:
        """Parse YAML frontmatter from SKILL.md."""
        frontmatter_errors = []
        frontmatter_valid = False
        name = ""
        description = ""
        description_length = 0
        has_required_fields = False

        try:
            if content.startswith("---\n"):
                end_pos = content.find("\n---\n", 4)
                if end_pos != -1:
                    frontmatter_text = content[4:end_pos]
                    try:
                        data = yaml.safe_load(frontmatter_text)
                        if isinstance(data, dict):
                            name = data.get("name", "")
                            description = data.get("description", "")
                            description_length = len(description)
                            has_required_fields = bool(name and description)
                            frontmatter_valid = True
                    except yaml.YAMLError as e:
                        frontmatter_errors.append(f"YAML parse error: {e}")
                else:
                    frontmatter_errors.append("Frontmatter not properly closed")
            else:
                frontmatter_errors.append("No frontmatter found")
        except Exception as e:
            frontmatter_errors.append(f"Unexpected error: {e}")

        return FrontmatterMetrics(
            name=name,
            description=description,
            description_length=description_length,
            has_required_fields=has_required_fields,
            frontmatter_valid=frontmatter_valid,
            frontmatter_errors=frontmatter_errors,
        )

    def _parse_body(self, content: str) -> BodyMetrics:
        """Parse body content metrics."""
        if content.startswith("---\n"):
            end_pos = content.find("\n---\n", 4)
            if end_pos != -1:
                body = content[end_pos + 5 :]
            else:
                body = content
        else:
            body = content

        lines = body.split("\n")
        total_lines = len(lines)

        sections = [line.strip() for line in lines if line.strip().startswith("#")]
        section_count = len(sections)

        code_block_count = body.count("```") // 2

        file_refs = re.findall(
            r"(?:scripts|references|assets)/[\w\-./]+\.\w+",
            body,
            re.IGNORECASE,
        )
        file_reference_count = len(file_refs)

        return BodyMetrics(
            total_lines=total_lines,
            section_count=section_count,
            code_block_count=code_block_count,
            file_reference_count=file_reference_count,
            sections=sections,
        )

    def _analyze_filesystem(self, skill_path: Path) -> FilesystemMetrics:
        """Analyze filesystem structure."""
        scripts_count = 0
        references_count = 0
        assets_count = 0
        scripts_executable = []
        scripts_non_executable = []
        scripts_missing_shebang = []

        scripts_dir = skill_path / "scripts"
        if scripts_dir.exists() and scripts_dir.is_dir():
            for script in scripts_dir.rglob("*"):
                if script.is_file():
                    scripts_count += 1
                    rel_path = str(script.relative_to(skill_path))

                    if os.access(script, os.X_OK):
                        scripts_executable.append(rel_path)
                    else:
                        scripts_non_executable.append(rel_path)

                    try:
                        first_line = script.read_text(errors="replace").split("\n")[0]
                        if not first_line.startswith("#!"):
                            scripts_missing_shebang.append(rel_path)
                    except Exception:
                        pass

        references_dir = skill_path / "references"
        if references_dir.exists() and references_dir.is_dir():
            references_count = sum(1 for _ in references_dir.rglob("*") if _.is_file())

        assets_dir = skill_path / "assets"
        if assets_dir.exists() and assets_dir.is_dir():
            assets_count = sum(1 for _ in assets_dir.rglob("*") if _.is_file())

        total_files = scripts_count + references_count + assets_count

        return FilesystemMetrics(
            scripts_count=scripts_count,
            references_count=references_count,
            assets_count=assets_count,
            total_files=total_files,
            scripts_executable=scripts_executable,
            scripts_non_executable=scripts_non_executable,
            scripts_missing_shebang=scripts_missing_shebang,
        )

    def _check_cross_references(
        self, skill_path: Path, content: str, filesystem: FilesystemMetrics
    ) -> CrossReferences:
        """Check cross-reference integrity."""
        content_without_code = re.sub(r"```[\s\S]*?```", "", content, flags=re.MULTILINE)

        file_refs = re.findall(
            r"((?:scripts|references|assets)/[\w\-./]+\.\w+)",
            content_without_code,
            re.IGNORECASE,
        )

        present_files = []
        for subdir in ["scripts", "references", "assets"]:
            dir_path = skill_path / subdir
            if dir_path.exists() and dir_path.is_dir():
                for file in dir_path.rglob("*"):
                    if file.is_file():
                        rel_path = str(file.relative_to(skill_path))
                        present_files.append(rel_path)

        referenced_but_missing = []
        for ref in file_refs:
            full_ref = ref if "/" in ref else f"scripts/{ref}"
            if full_ref not in present_files and ref not in present_files:
                referenced_but_missing.append(ref)

        present_but_unreferenced = [
            f
            for f in present_files
            if f not in file_refs and not any(f.endswith(ref) for ref in file_refs)
        ]

        return CrossReferences(
            referenced_but_missing=list(set(referenced_but_missing)),
            present_but_unreferenced=list(set(present_but_unreferenced)),
            all_file_references=list(set(file_refs)),
            all_present_files=present_files,
        )

    def _detect_red_flags(
        self,
        frontmatter: FrontmatterMetrics,
        body: BodyMetrics,
        filesystem: FilesystemMetrics,
        cross_refs: CrossReferences,
    ) -> List[str]:
        """Detect immediate red flags."""
        red_flags = []

        if not frontmatter.frontmatter_valid:
            red_flags.append("Invalid or missing frontmatter")

        if frontmatter.description_length < 10:
            red_flags.append("Description too short (<10 chars)")

        if frontmatter.description_length > 1024:
            red_flags.append("Description too long (>1024 chars)")

        if body.total_lines > 700:
            red_flags.append("SKILL.md too long (>700 lines)")

        if body.section_count < 2:
            red_flags.append("Too few sections (<2)")

        if filesystem.scripts_non_executable:
            red_flags.append(f"{len(filesystem.scripts_non_executable)} non-executable scripts")

        if filesystem.scripts_missing_shebang:
            red_flags.append(f"{len(filesystem.scripts_missing_shebang)} scripts missing shebang")

        if cross_refs.referenced_but_missing:
            red_flags.append(f"{len(cross_refs.referenced_but_missing)} phantom file references")

        return red_flags

    def _check_skills_ref(self, skill_md: Path) -> tuple[bool, Optional[str]]:
        """Check if skills-ref validate is available and run it."""
        try:
            result = subprocess.run(
                ["skills-ref", "validate", str(skill_md)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return (True, result.stdout + result.stderr)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return (False, None)
