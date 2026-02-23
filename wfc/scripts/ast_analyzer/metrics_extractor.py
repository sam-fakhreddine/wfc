"""
Extract reviewer-relevant metrics from Python AST.

Focus on actionable insights:
1. Cyclomatic complexity (all reviewers)
2. Data flow: input → dangerous sinks (security)
3. Nesting depth (correctness, performance)
4. Exception handling coverage (reliability)
5. Dead code detection (maintainability)
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path

MAX_LINES = 5000
MAX_FILE_BYTES = 512_000

DANGEROUS_NAMESPACES = {"os", "subprocess", "pickle", "yaml"}

# Note: 'eval' is intentionally excluded — it is a builtin, not a module name.
DANGEROUS_MODULES = {"subprocess", "os", "pickle", "yaml"}


@dataclass
class FunctionMetrics:
    """Per-function metrics."""

    name: str
    line: int
    complexity: int
    max_nesting: int
    has_try_except: bool
    has_returns: bool
    has_io_calls: bool = False
    dangerous_calls: list[str] = field(default_factory=list)
    params: list[str] = field(default_factory=list)


@dataclass
class FileMetrics:
    """File-level metrics for reviewers."""

    file_path: str
    lines: int
    functions: int
    classes: int
    imports: list[str] = field(default_factory=list)
    dangerous_imports: list[str] = field(default_factory=list)
    hotspots: list[dict] = field(default_factory=list)
    function_details: list[FunctionMetrics] = field(default_factory=list)


class UnifiedFunctionVisitor(ast.NodeVisitor):
    """Single-pass visitor computing all per-function metrics."""

    DANGEROUS_CALLS = {
        "eval",
        "exec",
        "compile",
        "__import__",
        "execfile",
        "input",
        "system",
        "popen",
        "spawn",
    }

    IO_CALLS = {"open", "read", "write", "request", "get", "post", "urlopen", "urlretrieve"}

    def __init__(self):
        self.complexity = 1
        self.max_depth = 0
        self.current_depth = 0
        self.dangerous: list[str] = []
        self.has_try_except = False
        self.has_return = False
        self.has_io_calls = False
        self._root_visited = False

    def visit_If(self, node):
        self.complexity += 1
        self._enter_block(node)

    def visit_For(self, node):
        self.complexity += 1
        self._enter_block(node)

    def visit_While(self, node):
        self.complexity += 1
        self._enter_block(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.complexity += 1
        self._enter_block(node)

    def visit_BoolOp(self, node):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def _enter_block(self, node):
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1

    def visit_Try(self, node):
        self.has_try_except = True
        self._enter_block(node)

    def visit_Call(self, node):
        call_name = self._get_call_name(node.func)
        if call_name:
            if len(call_name) > 256:
                call_name = call_name[:256]
            parts = call_name.split(".")
            leaf = parts[-1]
            if leaf in self.DANGEROUS_CALLS:
                if len(parts) == 1 or parts[0] in DANGEROUS_NAMESPACES:
                    self.dangerous.append(call_name)
            if leaf in self.IO_CALLS:
                self.has_io_calls = True
        self.generic_visit(node)

    def _get_call_name(self, node) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_call_name(node.value)
            if value:
                return f"{value}.{node.attr}"
            return node.attr
        return None

    def visit_Return(self, node):
        self.has_return = True
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if not self._root_visited:
            self._root_visited = True
            self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if not self._root_visited:
            self._root_visited = True
            self.generic_visit(node)


class FileAnalysisVisitor(ast.NodeVisitor):
    """Single-pass visitor collecting file-level structure.

    Descends into function bodies so that nested functions each receive their
    own entry in func_nodes (each node appears exactly once).  Complexity for
    each function is computed independently by UnifiedFunctionVisitor, which
    already guards against counting nested function branches.
    """

    def __init__(self):
        self.func_nodes: list[ast.AST] = []
        self.class_nodes: list[ast.ClassDef] = []
        self.imports: list[str] = []
        self.dangerous_imports: list[str] = []

    def visit_FunctionDef(self, node):
        self.func_nodes.append(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.func_nodes.append(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.class_nodes.append(node)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
            parts = alias.name.split(".")
            if any(part in DANGEROUS_MODULES for part in parts):
                self.dangerous_imports.append(alias.name)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        if module:
            self.imports.append(module)
        for alias in node.names:
            full_name = f"{module}.{alias.name}" if module else alias.name
            if full_name not in self.imports:
                self.imports.append(full_name)
        parts = module.split(".")
        if any(part in DANGEROUS_MODULES for part in parts):
            self.dangerous_imports.append(module)


def analyze_function(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionMetrics:
    """Extract metrics for a single function."""
    visitor = UnifiedFunctionVisitor()
    visitor.visit(func_node)

    args = func_node.args
    params = (
        [arg.arg for arg in args.posonlyargs]
        + [arg.arg for arg in args.args]
        + ([args.vararg.arg] if args.vararg else [])
        + [arg.arg for arg in args.kwonlyargs]
        + ([args.kwarg.arg] if args.kwarg else [])
    )

    return FunctionMetrics(
        name=func_node.name,
        line=func_node.lineno,
        complexity=visitor.complexity,
        max_nesting=visitor.max_depth,
        has_try_except=visitor.has_try_except,
        has_returns=visitor.has_return,
        has_io_calls=visitor.has_io_calls,
        dangerous_calls=visitor.dangerous,
        params=params,
    )


def analyze_file(file_path: Path) -> FileMetrics:
    """Extract reviewer-relevant metrics from a Python file."""
    if file_path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(
            f"File too large for AST analysis: {file_path.stat().st_size} bytes (max {MAX_FILE_BYTES})"
        )

    content = file_path.read_text(encoding="utf-8", errors="replace")
    lines = len(content.splitlines())

    if lines > MAX_LINES:
        raise ValueError(f"File too large for AST analysis: {lines} lines (max {MAX_LINES})")

    tree = ast.parse(content, filename=str(file_path))

    file_visitor = FileAnalysisVisitor()
    file_visitor.visit(tree)

    function_metrics = []
    hotspots = []

    for func in file_visitor.func_nodes:
        metrics = analyze_function(func)
        function_metrics.append(metrics)

        issues = []
        if metrics.complexity > 10:
            issues.append(f"high_complexity:{metrics.complexity}")
        if metrics.max_nesting > 4:
            issues.append(f"deep_nesting:{metrics.max_nesting}")
        if metrics.dangerous_calls:
            issues.append(f"dangerous_calls:{','.join(metrics.dangerous_calls)}")
        if metrics.has_io_calls and not metrics.has_try_except:
            issues.append("missing_error_handling")

        if issues:
            hotspots.append({"line": metrics.line, "function": metrics.name, "issues": issues})

    try:
        relative_path = str(file_path.relative_to(Path.cwd()))
    except ValueError:
        relative_path = (
            "/".join(file_path.parts[-2:]) if len(file_path.parts) >= 2 else file_path.name
        )

    return FileMetrics(
        file_path=relative_path,
        lines=lines,
        functions=len(file_visitor.func_nodes),
        classes=len(file_visitor.class_nodes),
        imports=file_visitor.imports,
        dangerous_imports=file_visitor.dangerous_imports,
        hotspots=hotspots,
        function_details=function_metrics,
    )


def summarize_for_reviewer(metrics: FileMetrics) -> dict:
    """
    Create compact summary optimized for reviewer context.

    Token budget: ~50-100 tokens per file (vs 1000+ for full file content).

    IMPORTANT: This is SUPPLEMENTAL CONTEXT, not a directive.
    Reviewers should use this as guidance, not gospel.
    """
    summary = {
        "file": metrics.file_path,
        "lines": metrics.lines,
        "complexity_budget": sum(f.complexity for f in metrics.function_details),
        "_note": "Supplemental hints only. Review the full code, not just these flags.",
    }

    if metrics.dangerous_imports:
        summary["dangerous_imports"] = list(set(metrics.dangerous_imports))
        summary["_imports_note"] = "Verify actual usage. Presence != vulnerability."

    if metrics.hotspots:
        summary["hotspots"] = metrics.hotspots
        summary["_hotspots_note"] = "Suggested focus areas. Not exhaustive."

    complex_funcs = sorted(metrics.function_details, key=lambda f: f.complexity, reverse=True)[:3]
    if complex_funcs and complex_funcs[0].complexity > 5:
        summary["complex_functions"] = [
            {"name": f.name, "line": f.line, "complexity": f.complexity} for f in complex_funcs
        ]
        summary["_complexity_note"] = "High complexity warrants deeper review."

    return summary
