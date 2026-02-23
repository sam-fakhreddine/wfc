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
from typing import Dict, List, Optional

DANGEROUS_NAMESPACES = {"os", "subprocess", "pickle", "yaml"}


@dataclass
class FunctionMetrics:
    """Per-function metrics."""

    name: str
    line: int
    complexity: int
    max_nesting: int
    has_try_except: bool
    has_returns: bool
    calls: List[str] = field(default_factory=list)
    dangerous_calls: List[str] = field(default_factory=list)
    params: List[str] = field(default_factory=list)


@dataclass
class FileMetrics:
    """File-level metrics for reviewers."""

    file_path: str
    lines: int
    functions: int
    classes: int
    imports: List[str] = field(default_factory=list)
    dangerous_imports: List[str] = field(default_factory=list)
    hotspots: List[Dict] = field(default_factory=list)
    function_details: List[FunctionMetrics] = field(default_factory=list)


class ComplexityVisitor(ast.NodeVisitor):
    """Calculate cyclomatic complexity."""

    def __init__(self):
        self.complexity = 1
        self._root_visited = False

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if not self._root_visited:
            self._root_visited = True
            self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if not self._root_visited:
            self._root_visited = True
            self.generic_visit(node)


class NestingVisitor(ast.NodeVisitor):
    """Calculate maximum nesting depth."""

    def __init__(self):
        self.max_depth = 0
        self.current_depth = 0
        self._root_visited = False

    def _enter_block(self, node):
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1

    def visit_If(self, node):
        self._enter_block(node)

    def visit_For(self, node):
        self._enter_block(node)

    def visit_While(self, node):
        self._enter_block(node)

    def visit_With(self, node):
        self._enter_block(node)

    def visit_Try(self, node):
        self._enter_block(node)

    def visit_FunctionDef(self, node):
        if not self._root_visited:
            self._root_visited = True
            self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if not self._root_visited:
            self._root_visited = True
            self.generic_visit(node)


class CallVisitor(ast.NodeVisitor):
    """Extract function calls and identify dangerous patterns."""

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

    def __init__(self):
        self.calls: List[str] = []
        self.dangerous: List[str] = []

    def visit_Call(self, node):
        call_name = self._get_call_name(node.func)
        if call_name:
            if len(call_name) > 256:
                call_name = call_name[:256]
            self.calls.append(call_name)
            parts = call_name.split(".")
            leaf = parts[-1]
            if leaf in self.DANGEROUS_CALLS:
                if len(parts) == 1 or parts[0] in DANGEROUS_NAMESPACES:
                    self.dangerous.append(call_name)
        self.generic_visit(node)

    def _get_call_name(self, node) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_call_name(node.value)
            if value:
                return f"{value}.{node.attr}"
            return node.attr
        return None


def analyze_function(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionMetrics:
    """Extract metrics for a single function."""
    complexity_visitor = ComplexityVisitor()
    complexity_visitor.visit(func_node)

    nesting_visitor = NestingVisitor()
    nesting_visitor.visit(func_node)

    call_visitor = CallVisitor()
    call_visitor.visit(func_node)

    has_try = any(isinstance(n, ast.Try) for n in ast.walk(func_node))

    has_return = any(isinstance(n, ast.Return) for n in ast.walk(func_node))

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
        complexity=complexity_visitor.complexity,
        max_nesting=nesting_visitor.max_depth,
        has_try_except=has_try,
        has_returns=has_return,
        calls=call_visitor.calls,
        dangerous_calls=call_visitor.dangerous,
        params=params,
    )


def analyze_file(file_path: Path) -> FileMetrics:
    """Extract reviewer-relevant metrics from a Python file."""
    content = file_path.read_text()
    tree = ast.parse(content, filename=str(file_path))

    lines = content.count("\n")
    functions = [
        n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

    imports = []
    dangerous_imports = []
    DANGEROUS_MODULES = {"subprocess", "os", "pickle", "yaml", "eval"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
                if any(part in DANGEROUS_MODULES for part in alias.name.split(".")):
                    dangerous_imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(module)
            if any(part in DANGEROUS_MODULES for part in module.split(".")):
                dangerous_imports.append(module)

    function_metrics = []
    hotspots = []

    for func in functions:
        metrics = analyze_function(func)
        function_metrics.append(metrics)

        issues = []
        if metrics.complexity > 10:
            issues.append(f"high_complexity:{metrics.complexity}")
        if metrics.max_nesting > 4:
            issues.append(f"deep_nesting:{metrics.max_nesting}")
        if metrics.dangerous_calls:
            issues.append(f"dangerous_calls:{','.join(metrics.dangerous_calls)}")
        if not metrics.has_try_except and any("open" in c or "request" in c for c in metrics.calls):
            issues.append("missing_error_handling")

        if issues:
            hotspots.append({"line": metrics.line, "function": metrics.name, "issues": issues})

    return FileMetrics(
        file_path=str(file_path),
        lines=lines,
        functions=len(functions),
        classes=len(classes),
        imports=imports,
        dangerous_imports=dangerous_imports,
        hotspots=hotspots,
        function_details=function_metrics,
    )


def summarize_for_reviewer(metrics: FileMetrics) -> Dict:
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
