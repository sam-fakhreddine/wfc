"""Documentation Gap Auditor.

Analysis-only component that identifies which documentation files may need
updating based on changed source files. Never modifies files, never blocks
review. Follows fail-open pattern.
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_DOCS_ROOT = Path("docs")

_KEY_DOCS = ["CLAUDE.md", "docs/README.md"]


@dataclass
class DocGap:
    """A documentation item that may need updating."""

    doc_file: str
    reason: str
    changed_file: str
    confidence: str


@dataclass
class DocAuditReport:
    """Result of documentation gap analysis."""

    task_id: str
    gaps: list[DocGap]
    missing_docstrings: list[str]
    summary: str
    report_path: Path


class DocAuditor:
    """Analyze changed files to determine which docs need updating.

    Analysis-only: never modifies files, never blocks review.
    """

    def analyze(
        self,
        task_id: str,
        files: list[str],
        diff_content: str,
        output_dir: Path,
        docs_root: Path | None = None,
    ) -> DocAuditReport:
        """Run doc gap analysis. Always returns a result (fail-open)."""
        report_path = output_dir / f"DOC-AUDIT-{task_id}.md"
        try:
            gaps = self._find_doc_gaps(files, diff_content, docs_root=docs_root)
            missing_ds = self._find_missing_docstrings(files, diff_content)
            report_path = self._write_report(task_id, gaps, missing_ds, output_dir)
            summary = self._build_summary(gaps, missing_ds)
        except Exception:
            logger.exception(
                "Doc audit failed for %s -- returning empty result (fail-open)", task_id
            )
            gaps, missing_ds = [], []
            summary = "Doc audit unavailable (fail-open)."
        return DocAuditReport(task_id, gaps, missing_ds, summary, report_path)

    def _find_doc_gaps(
        self,
        files: list[str],
        diff_content: str,
        docs_root: Path | None = None,
    ) -> list[DocGap]:
        """For each changed file, search docs for mentions of its module name."""
        if docs_root is None:
            docs_root = _DEFAULT_DOCS_ROOT

        doc_files: list[Path] = []
        if docs_root.is_dir():
            doc_files.extend(docs_root.rglob("*.md"))

        for key_doc in _KEY_DOCS:
            p = Path(key_doc)
            if p.is_file() and p not in doc_files:
                doc_files.append(p)

        if not doc_files:
            return []

        gaps: list[DocGap] = []
        for changed_file in files:
            file_path = Path(changed_file)
            module_name = file_path.stem

            for doc_path in doc_files:
                try:
                    content = doc_path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue

                doc_str = str(doc_path)

                if changed_file in content:
                    gaps.append(
                        DocGap(
                            doc_file=doc_str,
                            reason=f"Exact path '{changed_file}' found in doc",
                            changed_file=changed_file,
                            confidence="high",
                        )
                    )
                elif (
                    module_name and len(module_name) > 3 and module_name.lower() in content.lower()
                ):
                    gaps.append(
                        DocGap(
                            doc_file=doc_str,
                            reason=f"Module name '{module_name}' mentioned in doc",
                            changed_file=changed_file,
                            confidence="medium",
                        )
                    )

        return gaps

    def _find_missing_docstrings(
        self,
        files: list[str],
        diff_content: str,
    ) -> list[str]:
        """Find functions/classes added in diff without docstrings.

        Returns list of strings like "file:line: def function_name".
        """
        if not diff_content.strip():
            return []

        added_names: set[str] = set()
        for line in diff_content.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                stripped = line[1:].strip()
                m = re.match(r"^(async\s+)?def\s+(\w+)", stripped)
                if m:
                    added_names.add(m.group(2))
                cm = re.match(r"^class\s+(\w+)", stripped)
                if cm:
                    added_names.add(cm.group(1))

        if not added_names:
            return []

        missing: list[str] = []
        for file_path_str in files:
            file_path = Path(file_path_str)
            if file_path.suffix != ".py":
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            try:
                tree = ast.parse(content, filename=file_path_str)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                if node.name not in added_names:
                    continue

                body = node.body
                has_docstring = (
                    body
                    and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)
                )
                if not has_docstring:
                    kind = "class" if isinstance(node, ast.ClassDef) else "def"
                    missing.append(f"{file_path_str}:{node.lineno}: {kind} {node.name}")

        return missing

    def _write_report(
        self,
        task_id: str,
        gaps: list[DocGap],
        missing_docstrings: list[str],
        output_dir: Path,
    ) -> Path:
        """Write DOC-AUDIT-{task_id}.md report and return its path."""
        report_path = output_dir / f"DOC-AUDIT-{task_id}.md"
        lines = [
            f"# Documentation Audit: {task_id}",
            "",
            f"## Documentation Gaps ({len(gaps)} items)",
            "",
        ]

        if gaps:
            lines.extend(
                [
                    "| Doc File | Changed File | Reason | Confidence |",
                    "|----------|-------------|--------|------------|",
                ]
            )
            for gap in gaps:
                lines.append(
                    f"| {gap.doc_file} | {gap.changed_file} | {gap.reason} | {gap.confidence} |"
                )
        else:
            lines.append("No documentation gaps found.")

        lines.extend(
            [
                "",
                f"## Missing Docstrings ({len(missing_docstrings)} items)",
                "",
            ]
        )
        if missing_docstrings:
            for item in missing_docstrings:
                lines.append(f"- {item}")
        else:
            lines.append("No missing docstrings found in changed code.")

        lines.extend(
            [
                "",
                "## Summary",
                "",
                self._build_summary(gaps, missing_docstrings),
                "",
            ]
        )

        output_dir.mkdir(parents=True, exist_ok=True)
        report_path.write_text("\n".join(lines), encoding="utf-8")
        return report_path

    def _build_summary(self, gaps: list[DocGap], missing_docstrings: list[str]) -> str:
        """Build human-readable summary string."""
        parts = []
        if gaps:
            high = sum(1 for g in gaps if g.confidence == "high")
            med = sum(1 for g in gaps if g.confidence == "medium")
            parts.append(
                f"{len(gaps)} doc file(s) may need updating ({high} high, {med} medium confidence)"
            )
        else:
            parts.append("No documentation gaps detected")

        if missing_docstrings:
            parts.append(f"{len(missing_docstrings)} function(s)/class(es) missing docstrings")

        return ". ".join(parts) + "."
