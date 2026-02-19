"""AST-based static analysis for Python source files.

Provides ASTAnalyzer which parses Python code using the stdlib ast module and
extracts structural information (functions, classes, imports) as well as
quality metrics (cyclomatic complexity, nesting depth, unreachable code,
unused imports).

For non-Python files the analyzer returns a minimal ASTAnalysis with
parse_error set (tree-sitter fallback is not required at runtime).

All public methods are exception-safe: errors are captured in
``ASTAnalysis.parse_error`` rather than propagated to callers.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field


@dataclass
class FunctionInfo:
    """Metadata extracted from a top-level function definition."""

    name: str
    args: list[str]
    line_start: int
    line_end: int
    cyclomatic_complexity: int
    decorators: list[str] = field(default_factory=list)


@dataclass
class ClassInfo:
    """Metadata extracted from a class definition."""

    name: str
    bases: list[str]
    methods: list[str]
    line_start: int
    line_end: int


@dataclass
class ASTAnalysis:
    """Result of analyzing a single source file."""

    file_path: str
    language: str
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    unused_imports: list[str] = field(default_factory=list)
    unreachable_code: list[int] = field(default_factory=list)
    max_nesting_depth: int = 0
    high_complexity_functions: list[str] = field(default_factory=list)
    deep_nesting_locations: list[int] = field(default_factory=list)
    parse_error: str = ""


_EXT_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "javascript",
    ".jsx": "javascript",
    ".tsx": "javascript",
}


class ASTAnalyzer:
    """Parse source files and return structural + quality analysis."""

    COMPLEXITY_THRESHOLD: int = 15
    NESTING_THRESHOLD: int = 4

    def analyze(self, file_path: str) -> ASTAnalysis:
        """Read *file_path* and return an ASTAnalysis.

        Never raises. On any error (file not found, parse failure, …) the
        returned ``ASTAnalysis.parse_error`` will contain the error message.
        """
        try:
            with open(file_path, encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except Exception as exc:
            return ASTAnalysis(
                file_path=file_path,
                language=self._language_from_path(file_path),
                parse_error=str(exc),
            )
        return self.analyze_content(content, file_path=file_path)

    def analyze_content(self, content: str, file_path: str = "<string>") -> ASTAnalysis:
        """Analyze *content* as source code.

        The optional *file_path* is used to determine the language and to
        populate ``ASTAnalysis.file_path``.  Never raises.

        When the file extension is not recognized (including the default
        ``"<string>"`` sentinel), the content is treated as Python — since
        that is the only language with a built-in parser.
        """
        language = self._language_from_path(file_path)

        if language in ("python", "unknown"):
            return self._analyze_python(content, file_path)

        try:
            import importlib

            mod_name = f"tree_sitter_{language}"
            importlib.import_module(mod_name)
            return ASTAnalysis(
                file_path=file_path,
                language=language,
                parse_error="tree-sitter not available",
            )
        except ImportError:
            return ASTAnalysis(
                file_path=file_path,
                language=language,
                parse_error="tree-sitter not available",
            )
        except Exception as exc:
            return ASTAnalysis(
                file_path=file_path,
                language=language,
                parse_error=str(exc),
            )

    def _analyze_python(self, content: str, file_path: str) -> ASTAnalysis:
        """Full Python analysis using stdlib ast."""
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as exc:
            return ASTAnalysis(
                file_path=file_path,
                language="python",
                parse_error=str(exc),
            )
        except Exception as exc:
            return ASTAnalysis(
                file_path=file_path,
                language="python",
                parse_error=str(exc),
            )

        try:
            functions = self._extract_functions(tree)
            classes = self._extract_classes(tree)
            imports = self._collect_imports(tree)
            unused = self._find_unused_imports(tree)
            unreachable = self._find_unreachable(tree)
            max_depth = self._max_depth(tree)
            deep_locs = self._find_deep_nesting_locations(tree)
            high_cc = [
                f.name for f in functions if f.cyclomatic_complexity > self.COMPLEXITY_THRESHOLD
            ]

            return ASTAnalysis(
                file_path=file_path,
                language="python",
                functions=functions,
                classes=classes,
                imports=imports,
                unused_imports=unused,
                unreachable_code=unreachable,
                max_nesting_depth=max_depth,
                high_complexity_functions=high_cc,
                deep_nesting_locations=deep_locs,
            )
        except Exception as exc:
            return ASTAnalysis(
                file_path=file_path,
                language="python",
                parse_error=str(exc),
            )

    def _extract_functions(self, tree: ast.AST) -> list[FunctionInfo]:
        """Extract top-level function definitions (not methods inside classes)."""
        results: list[FunctionInfo] = []
        module_body: list[ast.stmt] = getattr(tree, "body", [])
        for node in module_body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                info = self._function_info(node)
                results.append(info)
        return results

    def _function_info(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:
        args = [arg.arg for arg in node.args.args]
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(ast.unparse(dec))
            else:
                decorators.append(ast.unparse(dec))

        line_end = getattr(node, "end_lineno", node.lineno)
        cc = self._compute_complexity(node)
        return FunctionInfo(
            name=node.name,
            args=args,
            line_start=node.lineno,
            line_end=line_end,
            cyclomatic_complexity=cc,
            decorators=decorators,
        )

    def _extract_classes(self, tree: ast.AST) -> list[ClassInfo]:
        """Extract top-level class definitions."""
        results: list[ClassInfo] = []
        module_body: list[ast.stmt] = getattr(tree, "body", [])
        for node in module_body:
            if isinstance(node, ast.ClassDef):
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(ast.unparse(base))
                    else:
                        bases.append(ast.unparse(base))

                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(item.name)

                line_end = getattr(node, "end_lineno", node.lineno)
                results.append(
                    ClassInfo(
                        name=node.name,
                        bases=bases,
                        methods=methods,
                        line_start=node.lineno,
                        line_end=line_end,
                    )
                )
        return results

    def _compute_complexity(self, node: ast.AST) -> int:
        """Cyclomatic complexity: 1 + branches.

        Counts: if, elif (each elif clause), for, while, except (each handler),
        with, and (BoolOp), or (BoolOp), assert, and comprehensions.
        """
        count = 1
        for child in ast.walk(node):
            if child is node:
                continue
            if isinstance(child, ast.If):
                count += 1
            elif isinstance(child, (ast.For, ast.AsyncFor)):
                count += 1
            elif isinstance(child, ast.While):
                count += 1
            elif isinstance(child, ast.ExceptHandler):
                count += 1
            elif isinstance(child, ast.With):
                count += 1
            elif isinstance(child, ast.BoolOp):
                count += len(child.values) - 1
            elif isinstance(child, ast.Assert):
                count += 1
            elif isinstance(
                child,
                (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp),
            ):
                count += 1
        return count

    def _collect_imports(self, tree: ast.AST) -> list[str]:
        """Collect all imported names visible at module level."""
        names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_as = alias.asname if alias.asname else alias.name
                    names.append(imported_as)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_as = alias.asname if alias.asname else alias.name
                    names.append(imported_as)
        return names

    def _find_unused_imports(self, tree: ast.AST) -> list[str]:
        """Find imported names never referenced in the module body."""
        imported: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = alias.asname if alias.asname else alias.name
                    imported[local] = local
                    root = local.split(".")[0]
                    if root != local:
                        imported[root] = local
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    local = alias.asname if alias.asname else alias.name
                    imported[local] = local

        if not imported:
            return []

        used: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                pass

        unused = [name for name in imported if name not in used]
        return unused

    def _find_unreachable(self, tree: ast.AST) -> list[int]:
        """Find statements that follow a terminal statement in the same block.

        Terminal statements: Return, Raise, Break, Continue.
        """
        unreachable_lines: list[int] = []
        self._scan_unreachable_in_body(getattr(tree, "body", []), unreachable_lines)
        return unreachable_lines

    def _scan_unreachable_in_body(self, body: list[ast.stmt], out: list[int]) -> None:
        """Scan a list of statements for unreachable code, recursing into blocks.

        Once a terminal statement (Return/Raise/Break/Continue) is encountered,
        ALL subsequent sibling statements in the same block are unreachable.
        """
        terminal_seen = False
        for stmt in body:
            if terminal_seen:
                start = stmt.lineno
                end = getattr(stmt, "end_lineno", start)
                for ln in range(start, end + 1):
                    if ln not in out:
                        out.append(ln)
            else:
                if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                    terminal_seen = True

                for child_body in self._child_bodies(stmt):
                    self._scan_unreachable_in_body(child_body, out)

    @staticmethod
    def _child_bodies(node: ast.stmt) -> list[list[ast.stmt]]:
        """Return all child statement lists for a given statement node."""
        bodies: list[list[ast.stmt]] = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bodies.append(node.body)
        elif isinstance(node, (ast.If,)):
            bodies.append(node.body)
            if node.orelse:
                bodies.append(node.orelse)
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            bodies.append(node.body)
            if node.orelse:
                bodies.append(node.orelse)
        elif isinstance(node, ast.With):
            bodies.append(node.body)
        elif isinstance(node, ast.Try):
            bodies.append(node.body)
            for handler in node.handlers:
                bodies.append(handler.body)
            if node.orelse:
                bodies.append(node.orelse)
            if node.finalbody:
                bodies.append(node.finalbody)
        return bodies

    _NESTING_TYPES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.Try)

    def _max_depth(self, tree: ast.AST) -> int:
        """Compute the maximum nesting depth of control-flow constructs."""
        return self._depth_of(tree, 0)

    def _depth_of(self, node: ast.AST, current: int) -> int:
        max_seen = current
        for child in ast.iter_child_nodes(node):
            if isinstance(child, self._NESTING_TYPES):
                child_depth = self._depth_of(child, current + 1)
            else:
                child_depth = self._depth_of(child, current)
            if child_depth > max_seen:
                max_seen = child_depth
        return max_seen

    def _find_deep_nesting_locations(self, tree: ast.AST) -> list[int]:
        """Return line numbers where nesting depth exceeds NESTING_THRESHOLD."""
        locations: list[int] = []
        self._collect_deep_nodes(tree, 0, locations)
        return sorted(set(locations))

    def _collect_deep_nodes(self, node: ast.AST, current_depth: int, out: list[int]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, self._NESTING_TYPES):
                new_depth = current_depth + 1
                if new_depth > self.NESTING_THRESHOLD:
                    lineno = getattr(child, "lineno", None)
                    if lineno is not None:
                        out.append(lineno)
                self._collect_deep_nodes(child, new_depth, out)
            else:
                self._collect_deep_nodes(child, current_depth, out)

    def generate_findings(self, analysis: "ASTAnalysis") -> list[dict]:
        """Convert an ASTAnalysis into a list of finding dicts.

        The returned dicts are compatible with ``Fingerprinter.deduplicate()``.
        Each finding has: file, line_start, line_end, category, severity,
        confidence, description, validation_status, reviewer_id.

        Finding types and severities:
        - unused-import     → severity 3.0
        - unreachable-code  → severity 8.0
        - high-complexity   → severity 5.0  (cyclomatic complexity > 15)
        - deep-nesting      → severity 5.0  (nesting depth > 4)

        All findings have confidence=8.0, validation_status="VERIFIED",
        reviewer_id="ast-analyzer".

        Returns an empty list when there are no structural issues or when the
        analysis contains a parse error.
        """
        if analysis.parse_error:
            return []

        findings: list[dict] = []
        file_path = analysis.file_path

        for name in analysis.unused_imports:
            findings.append(
                {
                    "file": file_path,
                    "line_start": 1,
                    "line_end": 1,
                    "category": "unused-import",
                    "severity": 3.0,
                    "confidence": 8.0,
                    "description": f"Unused import: '{name}' is imported but never referenced.",
                    "validation_status": "VERIFIED",
                    "reviewer_id": "ast-analyzer",
                }
            )

        if analysis.unreachable_code:
            lines = sorted(analysis.unreachable_code)
            ranges: list[tuple[int, int]] = []
            start = end = lines[0]
            for ln in lines[1:]:
                if ln == end + 1:
                    end = ln
                else:
                    ranges.append((start, end))
                    start = end = ln
            ranges.append((start, end))

            for rng_start, rng_end in ranges:
                findings.append(
                    {
                        "file": file_path,
                        "line_start": rng_start,
                        "line_end": rng_end,
                        "category": "unreachable-code",
                        "severity": 8.0,
                        "confidence": 8.0,
                        "description": (
                            f"Unreachable code detected at line {rng_start}"
                            + (f"-{rng_end}" if rng_end != rng_start else "")
                            + " (follows a terminal statement)."
                        ),
                        "validation_status": "VERIFIED",
                        "reviewer_id": "ast-analyzer",
                    }
                )

        for func in analysis.functions:
            if func.cyclomatic_complexity > self.COMPLEXITY_THRESHOLD:
                findings.append(
                    {
                        "file": file_path,
                        "line_start": func.line_start,
                        "line_end": func.line_end,
                        "category": "high-complexity",
                        "severity": 5.0,
                        "confidence": 8.0,
                        "description": (
                            f"Function '{func.name}' has cyclomatic complexity "
                            f"{func.cyclomatic_complexity} (threshold: {self.COMPLEXITY_THRESHOLD})."
                        ),
                        "validation_status": "VERIFIED",
                        "reviewer_id": "ast-analyzer",
                    }
                )

        for line_no in analysis.deep_nesting_locations:
            findings.append(
                {
                    "file": file_path,
                    "line_start": line_no,
                    "line_end": line_no,
                    "category": "deep-nesting",
                    "severity": 5.0,
                    "confidence": 8.0,
                    "description": (
                        f"Nesting depth exceeds threshold of {self.NESTING_THRESHOLD} "
                        f"at line {line_no}."
                    ),
                    "validation_status": "VERIFIED",
                    "reviewer_id": "ast-analyzer",
                }
            )

        return findings

    @staticmethod
    def _language_from_path(file_path: str) -> str:
        _, ext = os.path.splitext(file_path)
        return _EXT_LANGUAGE.get(ext.lower(), "unknown")
