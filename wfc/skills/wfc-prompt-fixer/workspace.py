"""Workspace management for prompt fixer pipeline."""

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class WorkspaceError(Exception):
    """Custom exception for workspace-related errors.

    Provides actionable error messages for file I/O failures, permission errors,
    and other workspace operations issues.
    """

    pass


@dataclass
class WorkspaceMetadata:
    """Metadata for a prompt fixer run."""

    run_id: str
    timestamp: str
    prompt_path: str
    wfc_mode: bool
    retries: int = 0
    grade: Optional[str] = None
    status: str = "in_progress"


class WorkspaceManager:
    """
    Manages workspace directories for prompt fixer runs.

    Workspace structure:
    .development/prompt-fixer/<run-id>/
    ├── input/
    │   └── prompt.md
    ├── 01-analyzer/
    │   └── analysis.json
    ├── 02-fixer/
    │   ├── fixed_prompt.md
    │   ├── changelog.md
    │   └── unresolved.md
    ├── 03-reporter/
    │   └── report.md
    └── metadata.json
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize workspace manager."""
        self.base_dir = base_dir or Path.cwd() / ".development" / "prompt-fixer"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create(self, prompt_path: Path, wfc_mode: bool = False) -> Path:
        """
        Create workspace for a prompt fixer run.

        Args:
            prompt_path: Path to the prompt file
            wfc_mode: Whether WFC-specific checks are enabled

        Returns:
            Path to the workspace directory
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        prompt_name = prompt_path.stem
        run_id = f"{prompt_name}-{timestamp}"

        workspace = self.base_dir / run_id
        workspace.mkdir(parents=True, exist_ok=True)

        (workspace / "input").mkdir(exist_ok=True)
        (workspace / "01-analyzer").mkdir(exist_ok=True)
        (workspace / "02-fixer").mkdir(exist_ok=True)
        (workspace / "03-reporter").mkdir(exist_ok=True)

        if prompt_path.exists():
            try:
                shutil.copy(prompt_path, workspace / "input" / "prompt.md")
            except PermissionError as e:
                raise WorkspaceError(
                    f"Failed to copy prompt file: Permission denied. "
                    f"Check file permissions for {prompt_path}."
                ) from e
            except OSError as e:
                raise WorkspaceError(
                    f"Failed to copy prompt file from {prompt_path}: {e}. "
                    f"Check available disk space and file system status."
                ) from e

        metadata = WorkspaceMetadata(
            run_id=run_id,
            timestamp=timestamp,
            prompt_path=str(prompt_path.absolute()),
            wfc_mode=wfc_mode,
        )
        self.write_metadata(workspace, metadata)

        return workspace

    def write_metadata(self, workspace: Path, metadata: WorkspaceMetadata) -> None:
        """Write metadata to workspace."""
        metadata_path = workspace / "metadata.json"
        try:
            with open(metadata_path, "w") as f:
                json.dump(asdict(metadata), f, indent=2)
        except PermissionError as e:
            raise WorkspaceError(
                f"Failed to write metadata: Permission denied. "
                f"Check file permissions for {metadata_path}."
            ) from e
        except OSError as e:
            raise WorkspaceError(
                f"Failed to write metadata to {metadata_path}: {e}. "
                f"Check available disk space and file system status."
            ) from e

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
        except PermissionError as e:
            raise WorkspaceError(
                f"Failed to read metadata: Permission denied. "
                f"Check file permissions for {metadata_path}."
            ) from e
        except json.JSONDecodeError as e:
            raise WorkspaceError(
                f"Invalid JSON in metadata file {metadata_path}: {e}. File may be corrupted."
            ) from e
        except OSError as e:
            raise WorkspaceError(f"Failed to read metadata from {metadata_path}: {e}") from e

    def write_analysis(self, workspace: Path, analysis: Dict) -> None:
        """Write analyzer results to workspace."""
        analysis_path = workspace / "01-analyzer" / "analysis.json"
        try:
            with open(analysis_path, "w") as f:
                json.dump(analysis, f, indent=2)
        except PermissionError as e:
            raise WorkspaceError(
                f"Failed to write analysis: Permission denied. "
                f"Check file permissions for {analysis_path}."
            ) from e
        except OSError as e:
            raise WorkspaceError(
                f"Failed to write analysis to {analysis_path}: {e}. "
                f"Check available disk space and file system status."
            ) from e

    def read_analysis(self, workspace: Path) -> Dict:
        """Read analyzer results from workspace."""
        analysis_path = workspace / "01-analyzer" / "analysis.json"
        try:
            with open(analysis_path) as f:
                return json.load(f)
        except FileNotFoundError as e:
            raise WorkspaceError(
                f"Analysis file not found at {analysis_path}. "
                f"Analyzer may not have completed successfully."
            ) from e
        except PermissionError as e:
            raise WorkspaceError(
                f"Failed to read analysis: Permission denied. "
                f"Check file permissions for {analysis_path}."
            ) from e
        except json.JSONDecodeError as e:
            raise WorkspaceError(
                f"Invalid JSON in analysis file {analysis_path}: {e}. File may be corrupted."
            ) from e
        except OSError as e:
            raise WorkspaceError(f"Failed to read analysis from {analysis_path}: {e}") from e

    def write_fix(
        self,
        workspace: Path,
        fixed_prompt: str,
        changelog: List[str],
        unresolved: List[str],
    ) -> None:
        """Write fixer results to workspace."""
        fixer_dir = workspace / "02-fixer"

        try:
            (fixer_dir / "fixed_prompt.md").write_text(fixed_prompt)

            changelog_text = "\n".join(f"{i + 1}. {change}" for i, change in enumerate(changelog))
            (fixer_dir / "changelog.md").write_text(changelog_text)

            if unresolved:
                unresolved_text = "\n".join(f"- {item}" for item in unresolved)
            else:
                unresolved_text = "No unresolved items."
            (fixer_dir / "unresolved.md").write_text(unresolved_text)
        except PermissionError as e:
            raise WorkspaceError(
                f"Failed to write fix results: Permission denied. "
                f"Check file permissions for {fixer_dir}."
            ) from e
        except OSError as e:
            raise WorkspaceError(
                f"Failed to write fix results to {fixer_dir}: {e}. "
                f"Check available disk space and file system status."
            ) from e

    def read_fix(self, workspace: Path) -> Dict[str, str]:
        """Read fixer results from workspace."""
        fixer_dir = workspace / "02-fixer"
        try:
            return {
                "fixed_prompt": (fixer_dir / "fixed_prompt.md").read_text(),
                "changelog": (fixer_dir / "changelog.md").read_text(),
                "unresolved": (fixer_dir / "unresolved.md").read_text(),
            }
        except FileNotFoundError as e:
            raise WorkspaceError(
                f"Fix result files not found in {fixer_dir}. "
                f"Fixer may not have completed successfully."
            ) from e
        except PermissionError as e:
            raise WorkspaceError(
                f"Failed to read fix results: Permission denied. "
                f"Check file permissions for {fixer_dir}."
            ) from e
        except OSError as e:
            raise WorkspaceError(f"Failed to read fix results from {fixer_dir}: {e}") from e

    def write_report(self, workspace: Path, report: str) -> Path:
        """Write final report to workspace."""
        report_path = workspace / "03-reporter" / "report.md"
        try:
            report_path.write_text(report)
            return report_path
        except PermissionError as e:
            raise WorkspaceError(
                f"Failed to write report: Permission denied. "
                f"Check file permissions for {report_path}."
            ) from e
        except OSError as e:
            raise WorkspaceError(
                f"Failed to write report to {report_path}: {e}. "
                f"Check available disk space and file system status."
            ) from e

    def list_workspaces(self) -> List[Path]:
        """List all workspace directories."""
        if not self.base_dir.exists():
            return []
        return sorted(self.base_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)

    def cleanup(self, workspace: Path) -> None:
        """Remove workspace directory.

        Uses ignore_errors=True to ensure cleanup never propagates exceptions,
        satisfying PROP-002 (cleanup on failure) and PROP-004 (liveness).
        """
        if workspace.exists():
            shutil.rmtree(workspace, ignore_errors=True)
