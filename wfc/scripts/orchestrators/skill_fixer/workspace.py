"""Workspace management for skill fixer pipeline.

Based on wfc-prompt-fixer workspace pattern.
"""

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class WorkspaceError(Exception):
    """Custom exception for workspace-related errors."""

    pass


@dataclass
class WorkspaceMetadata:
    """Metadata for a skill fixer run."""

    run_id: str
    timestamp: str
    skill_path: str
    skill_name: str
    run_functional_qa: bool = False
    retries: int = 0
    grade: Optional[str] = None
    status: str = "in_progress"


class WorkspaceManager:
    """
    Manages workspace directories for skill fixer runs.

    Workspace structure:
    .development/skill-fixer/<run-id>/
    ├── input/
    │   ├── SKILL.md
    │   ├── scripts/
    │   ├── references/
    │   └── assets/
    ├── 01-cataloger/
    │   └── manifest.json
    ├── 02-analyst/
    │   └── diagnosis.json
    ├── 03-fixer/
    │   ├── SKILL.md
    │   ├── references/
    │   ├── changelog.md
    │   ├── script_issues.md
    │   └── unresolved.md
    ├── 04-structural-qa/
    │   ├── validation.json
    │   └── revision_notes.md
    ├── 05-functional-qa/
    │   └── eval_results.json
    ├── 06-reporter/
    │   └── report.md
    └── metadata.json
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize workspace manager."""
        self.base_dir = base_dir or Path.cwd() / ".development" / "skill-fixer"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create(self, skill_path: Path, run_functional_qa: bool = False) -> Path:
        """
        Create workspace for a skill fixer run.

        Args:
            skill_path: Path to the skill directory
            run_functional_qa: Whether to run functional QA

        Returns:
            Path to the workspace directory
        """
        import uuid

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S%f")
        skill_name = skill_path.name
        unique_suffix = uuid.uuid4().hex[:8]
        run_id = f"{skill_name}-{timestamp}-{unique_suffix}"

        workspace = self.base_dir / run_id
        workspace.mkdir(parents=True, exist_ok=True)

        (workspace / "input").mkdir(exist_ok=True)
        (workspace / "01-cataloger").mkdir(exist_ok=True)
        (workspace / "02-analyst").mkdir(exist_ok=True)
        (workspace / "03-fixer").mkdir(exist_ok=True)
        (workspace / "04-structural-qa").mkdir(exist_ok=True)
        (workspace / "05-functional-qa").mkdir(exist_ok=True)
        (workspace / "06-reporter").mkdir(exist_ok=True)

        if skill_path.exists():
            try:
                skill_md = skill_path / "SKILL.md"
                if skill_md.exists():
                    shutil.copy(skill_md, workspace / "input" / "SKILL.md")

                for subdir in ["scripts", "references", "assets"]:
                    src_dir = skill_path / subdir
                    if src_dir.exists() and src_dir.is_dir():
                        shutil.copytree(src_dir, workspace / "input" / subdir)
            except PermissionError as e:
                raise WorkspaceError(
                    f"Failed to copy skill files: Permission denied. "
                    f"Check file permissions for {skill_path}."
                ) from e
            except OSError as e:
                raise WorkspaceError(
                    f"Failed to copy skill files from {skill_path}: {e}. "
                    f"Check available disk space and file system status."
                ) from e

        metadata = WorkspaceMetadata(
            run_id=run_id,
            timestamp=timestamp,
            skill_path=str(skill_path.absolute()),
            skill_name=skill_name,
            run_functional_qa=run_functional_qa,
        )
        self.write_metadata(workspace, metadata)

        return workspace

    def write_metadata(self, workspace: Path, metadata: WorkspaceMetadata) -> None:
        """Write metadata to workspace."""
        metadata_path = workspace / "metadata.json"
        try:
            with open(metadata_path, "w") as f:
                json.dump(asdict(metadata), f, indent=2)
        except (PermissionError, OSError) as e:
            raise WorkspaceError(f"Failed to write metadata to {metadata_path}: {e}") from e

    def read_metadata(self, workspace: Path) -> WorkspaceMetadata:
        """Read metadata from workspace."""
        metadata_path = workspace / "metadata.json"
        try:
            with open(metadata_path) as f:
                data = json.load(f)
            return WorkspaceMetadata(**data)
        except FileNotFoundError as e:
            raise WorkspaceError(
                f"Metadata file not found at {metadata_path}. "
                f"Workspace may be corrupted or incomplete."
            ) from e
        except json.JSONDecodeError as e:
            raise WorkspaceError(
                f"Invalid JSON in metadata file {metadata_path}: {e}. File may be corrupted."
            ) from e
        except OSError as e:
            raise WorkspaceError(f"Failed to read metadata from {metadata_path}: {e}") from e

    def write_manifest(self, workspace: Path, manifest: Dict) -> None:
        """Write cataloger manifest to workspace."""
        manifest_path = workspace / "01-cataloger" / "manifest.json"
        try:
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
        except (PermissionError, OSError) as e:
            raise WorkspaceError(f"Failed to write manifest to {manifest_path}: {e}") from e

    def read_manifest(self, workspace: Path) -> Dict:
        """Read cataloger manifest from workspace."""
        manifest_path = workspace / "01-cataloger" / "manifest.json"
        try:
            with open(manifest_path) as f:
                return json.load(f)
        except FileNotFoundError as e:
            raise WorkspaceError(
                f"Manifest file not found at {manifest_path}. "
                f"Cataloger may not have completed successfully."
            ) from e
        except json.JSONDecodeError as e:
            raise WorkspaceError(
                f"Invalid JSON in manifest file {manifest_path}: {e}. File may be corrupted."
            ) from e
        except OSError as e:
            raise WorkspaceError(f"Failed to read manifest from {manifest_path}: {e}") from e

    def write_diagnosis(self, workspace: Path, diagnosis: Dict) -> None:
        """Write analyst diagnosis to workspace."""
        diagnosis_path = workspace / "02-analyst" / "diagnosis.json"
        try:
            with open(diagnosis_path, "w") as f:
                json.dump(diagnosis, f, indent=2)
        except (PermissionError, OSError) as e:
            raise WorkspaceError(f"Failed to write diagnosis to {diagnosis_path}: {e}") from e

    def read_diagnosis(self, workspace: Path) -> Dict:
        """Read analyst diagnosis from workspace."""
        diagnosis_path = workspace / "02-analyst" / "diagnosis.json"
        try:
            with open(diagnosis_path) as f:
                return json.load(f)
        except FileNotFoundError as e:
            raise WorkspaceError(
                f"Diagnosis file not found at {diagnosis_path}. "
                f"Analyst may not have completed successfully."
            ) from e
        except json.JSONDecodeError as e:
            raise WorkspaceError(
                f"Invalid JSON in diagnosis file {diagnosis_path}: {e}. File may be corrupted."
            ) from e
        except OSError as e:
            raise WorkspaceError(f"Failed to read diagnosis from {diagnosis_path}: {e}") from e

    def write_fix(
        self,
        workspace: Path,
        rewritten_files: Dict[str, str],
        changelog: List[str],
        script_issues: List[str],
        unresolved: List[str],
    ) -> None:
        """Write fixer results to workspace."""
        fixer_dir = workspace / "03-fixer"

        try:
            if "SKILL.md" in rewritten_files:
                (fixer_dir / "SKILL.md").write_text(rewritten_files["SKILL.md"])

            for path, content in rewritten_files.items():
                if path != "SKILL.md":
                    file_path = fixer_dir / path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content)

            changelog_text = "\n".join(f"{i + 1}. {change}" for i, change in enumerate(changelog))
            (fixer_dir / "changelog.md").write_text(changelog_text)

            if script_issues:
                issues_text = "\n".join(f"- {issue}" for issue in script_issues)
            else:
                issues_text = "No script issues identified."
            (fixer_dir / "script_issues.md").write_text(issues_text)

            if unresolved:
                unresolved_text = "\n".join(f"- {item}" for item in unresolved)
            else:
                unresolved_text = "No unresolved items."
            (fixer_dir / "unresolved.md").write_text(unresolved_text)
        except (PermissionError, OSError) as e:
            raise WorkspaceError(f"Failed to write fix results to {fixer_dir}: {e}") from e

    def read_fix(self, workspace: Path) -> Dict[str, str]:
        """Read fixer results from workspace."""
        fixer_dir = workspace / "03-fixer"
        try:
            skill_md = fixer_dir / "SKILL.md"
            return {
                "SKILL.md": skill_md.read_text() if skill_md.exists() else "",
                "changelog": (fixer_dir / "changelog.md").read_text(),
                "script_issues": (fixer_dir / "script_issues.md").read_text(),
                "unresolved": (fixer_dir / "unresolved.md").read_text(),
            }
        except FileNotFoundError as e:
            raise WorkspaceError(
                f"Fix result files not found in {fixer_dir}. "
                f"Fixer may not have completed successfully."
            ) from e
        except OSError as e:
            raise WorkspaceError(f"Failed to read fix results from {fixer_dir}: {e}") from e

    def write_validation(self, workspace: Path, validation: Dict) -> None:
        """Write structural QA validation to workspace."""
        validation_path = workspace / "04-structural-qa" / "validation.json"
        try:
            with open(validation_path, "w") as f:
                json.dump(validation, f, indent=2)
        except (PermissionError, OSError) as e:
            raise WorkspaceError(f"Failed to write validation to {validation_path}: {e}") from e

    def read_validation(self, workspace: Path) -> Dict:
        """Read structural QA validation from workspace."""
        validation_path = workspace / "04-structural-qa" / "validation.json"
        try:
            with open(validation_path) as f:
                return json.load(f)
        except FileNotFoundError as e:
            raise WorkspaceError(
                f"Validation file not found at {validation_path}. "
                f"Structural QA may not have completed successfully."
            ) from e
        except json.JSONDecodeError as e:
            raise WorkspaceError(
                f"Invalid JSON in validation file {validation_path}: {e}. File may be corrupted."
            ) from e
        except OSError as e:
            raise WorkspaceError(f"Failed to read validation from {validation_path}: {e}") from e

    def write_functional_qa(self, workspace: Path, eval_results: Dict) -> None:
        """Write functional QA results to workspace."""
        eval_path = workspace / "05-functional-qa" / "eval_results.json"
        try:
            with open(eval_path, "w") as f:
                json.dump(eval_results, f, indent=2)
        except (PermissionError, OSError) as e:
            raise WorkspaceError(f"Failed to write functional QA to {eval_path}: {e}") from e

    def read_functional_qa(self, workspace: Path) -> Dict:
        """Read functional QA results from workspace."""
        eval_path = workspace / "05-functional-qa" / "eval_results.json"
        try:
            with open(eval_path) as f:
                return json.load(f)
        except FileNotFoundError as e:
            raise WorkspaceError(
                f"Functional QA file not found at {eval_path}. "
                f"Functional QA may not have completed successfully."
            ) from e
        except json.JSONDecodeError as e:
            raise WorkspaceError(
                f"Invalid JSON in eval_results file {eval_path}: {e}. File may be corrupted."
            ) from e
        except OSError as e:
            raise WorkspaceError(f"Failed to read functional QA from {eval_path}: {e}") from e

    def write_report(self, workspace: Path, report: str) -> Path:
        """Write final report to workspace."""
        report_path = workspace / "06-reporter" / "report.md"
        try:
            report_path.write_text(report)
            return report_path
        except (PermissionError, OSError) as e:
            raise WorkspaceError(f"Failed to write report to {report_path}: {e}") from e

    def read_report(self, workspace: Path) -> Path:
        """Read final report from workspace."""
        report_path = workspace / "06-reporter" / "report.md"
        if not report_path.exists():
            raise WorkspaceError(
                f"Report file not found at {report_path}. "
                f"Reporter may not have completed successfully."
            )
        return report_path

    def list_workspaces(self) -> List[Path]:
        """List all workspace directories."""
        if not self.base_dir.exists():
            return []
        return sorted(self.base_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)

    def cleanup(self, workspace: Path) -> None:
        """Remove workspace directory."""
        if workspace.exists():
            shutil.rmtree(workspace, ignore_errors=True)
