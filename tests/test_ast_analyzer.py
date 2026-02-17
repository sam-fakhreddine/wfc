"""Tests for ASTAnalyzer - AST-based code analysis for Python files.

TDD: tests written before implementation.
"""
from __future__ import annotations

import textwrap

import pytest

from wfc.scripts.skills.review.ast_analyzer import ASTAnalysis, ASTAnalyzer, FunctionInfo, ClassInfo



SIMPLE_FIXTURE = """
import os
import sys

def greet(name):
    return f"Hello {name}"

class Greeter:
    def __init__(self):
        pass
    def greet(self):
        return "hi"
"""

UNUSED_IMPORT_FIXTURE = """
import os
import sys

def hello():
    return sys.version
"""

UNREACHABLE_FIXTURE = """
def foo():
    return 42
    x = 1
"""

HIGH_COMPLEXITY_FIXTURE = """
def complex_func(a, b, c, d, e, f):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        if f:
                            if a and b:
                                if c or d:
                                    pass
    for i in range(10):
        while a:
            if b or c:
                if d and e and f:
                    pass
    try:
        pass
    except ValueError:
        pass
    except TypeError:
        pass
"""

DEEP_NESTING_FIXTURE = """
def deeply_nested():
    if True:
        for i in range(10):
            while True:
                with open("f") as fh:
                    try:
                        pass
                    except Exception:
                        pass
"""

FROM_IMPORT_FIXTURE = """
from os.path import join, exists
from sys import version

def use_join():
    return join("a", "b")
"""

ALIAS_IMPORT_FIXTURE = """
import os as operating_system
import sys

def use_os():
    return operating_system.getcwd()
"""

MULTI_FUNCTION_FIXTURE = """
def func_a(x):
    return x + 1

def func_b(x, y):
    if x:
        return y
    return x

def func_c():
    for i in range(10):
        if i > 5:
            pass
"""

PARSE_ERROR_FIXTURE = "def foo(:\n    pass"

NO_IMPORTS_FIXTURE = """
def add(a, b):
    return a + b
"""

MULTIPLE_UNREACHABLE_FIXTURE = """
def bar():
    x = 1
    raise ValueError("oops")
    y = 2
    z = 3
"""



@pytest.fixture
def analyzer() -> ASTAnalyzer:
    return ASTAnalyzer()


def dedent(src: str) -> str:
    return textwrap.dedent(src).strip()



class TestAnalyzeContent:
    """analyze_content returns ASTAnalysis without raising."""

    def test_returns_ast_analysis(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        assert isinstance(result, ASTAnalysis)

    def test_language_is_python_for_py_path(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE, file_path="app.py")
        assert result.language == "python"

    def test_default_file_path(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        assert result.file_path == "<string>"

    def test_no_parse_error_on_valid_code(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        assert result.parse_error == ""



class TestAnalyzeFunctions:
    """Function extraction."""

    def test_single_function_extracted(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        names = [f.name for f in result.functions]
        assert "greet" in names

    def test_function_args_extracted(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        greet = next(f for f in result.functions if f.name == "greet")
        assert greet.args == ["name"]

    def test_function_line_numbers_extracted(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        greet = next(f for f in result.functions if f.name == "greet")
        assert greet.line_start >= 1
        assert greet.line_end >= greet.line_start

    def test_function_info_type(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        assert all(isinstance(f, FunctionInfo) for f in result.functions)

    def test_multiple_functions_extracted(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(MULTI_FUNCTION_FIXTURE)
        names = {f.name for f in result.functions}
        assert {"func_a", "func_b", "func_c"} == names

    def test_no_functions_when_none_defined(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content("x = 1\n")
        assert result.functions == []

    def test_method_not_in_top_level_functions(self, analyzer: ASTAnalyzer):
        """Methods inside classes should NOT appear as top-level functions."""
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        names = [f.name for f in result.functions]
        assert "__init__" not in names



class TestAnalyzeClasses:
    """Class extraction."""

    def test_single_class_extracted(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        names = [c.name for c in result.classes]
        assert "Greeter" in names

    def test_class_methods_extracted(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        greeter = next(c for c in result.classes if c.name == "Greeter")
        assert "__init__" in greeter.methods
        assert "greet" in greeter.methods

    def test_class_line_numbers(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        greeter = next(c for c in result.classes if c.name == "Greeter")
        assert greeter.line_start >= 1
        assert greeter.line_end >= greeter.line_start

    def test_class_info_type(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        assert all(isinstance(c, ClassInfo) for c in result.classes)

    def test_no_classes_when_none_defined(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(NO_IMPORTS_FIXTURE)
        assert result.classes == []

    def test_class_bases_extracted(self, analyzer: ASTAnalyzer):
        src = "class Child(Base):\n    pass\n"
        result = analyzer.analyze_content(src)
        child = next(c for c in result.classes if c.name == "Child")
        assert "Base" in child.bases

    def test_class_no_bases(self, analyzer: ASTAnalyzer):
        src = "class Plain:\n    pass\n"
        result = analyzer.analyze_content(src)
        plain = next(c for c in result.classes if c.name == "Plain")
        assert plain.bases == []



class TestAnalyzeImports:
    """Import collection."""

    def test_simple_imports_collected(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        assert "os" in result.imports
        assert "sys" in result.imports

    def test_no_imports_is_empty_list(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(NO_IMPORTS_FIXTURE)
        assert result.imports == []

    def test_from_import_names_collected(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(FROM_IMPORT_FIXTURE)
        assert "join" in result.imports
        assert "exists" in result.imports

    def test_alias_import_collected(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(ALIAS_IMPORT_FIXTURE)
        assert "operating_system" in result.imports



class TestUnusedImports:
    """Unused import detection."""

    def test_unused_import_detected(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(UNUSED_IMPORT_FIXTURE)
        assert "os" in result.unused_imports

    def test_used_import_not_marked_unused(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(UNUSED_IMPORT_FIXTURE)
        assert "sys" not in result.unused_imports

    def test_no_imports_means_no_unused(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(NO_IMPORTS_FIXTURE)
        assert result.unused_imports == []

    def test_from_import_unused_detected(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(FROM_IMPORT_FIXTURE)
        assert "exists" in result.unused_imports

    def test_from_import_used_not_unused(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(FROM_IMPORT_FIXTURE)
        assert "join" not in result.unused_imports

    def test_alias_unused_import(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(ALIAS_IMPORT_FIXTURE)
        assert "sys" in result.unused_imports

    def test_alias_used_not_unused(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(ALIAS_IMPORT_FIXTURE)
        assert "operating_system" not in result.unused_imports



class TestUnreachableCode:
    """Unreachable statement detection."""

    def test_statement_after_return_is_unreachable(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(UNREACHABLE_FIXTURE)
        assert len(result.unreachable_code) >= 1

    def test_correct_line_flagged(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(UNREACHABLE_FIXTURE)
        assert result.unreachable_code

    def test_multiple_unreachable_statements(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(MULTIPLE_UNREACHABLE_FIXTURE)
        assert len(result.unreachable_code) >= 2

    def test_reachable_code_not_flagged(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        assert result.unreachable_code == []

    def test_unreachable_after_raise(self, analyzer: ASTAnalyzer):
        src = "def f():\n    raise ValueError\n    x = 1\n"
        result = analyzer.analyze_content(src)
        assert len(result.unreachable_code) >= 1



class TestCyclomaticComplexity:
    """Cyclomatic complexity computation."""

    def test_simple_function_low_complexity(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        greet = next(f for f in result.functions if f.name == "greet")
        assert greet.cyclomatic_complexity == 1

    def test_high_complexity_function_detected(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(HIGH_COMPLEXITY_FIXTURE)
        assert "complex_func" in result.high_complexity_functions

    def test_low_complexity_not_in_high_list(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        assert "greet" not in result.high_complexity_functions

    def test_complexity_threshold_is_15(self):
        assert ASTAnalyzer.COMPLEXITY_THRESHOLD == 15

    def test_function_with_if_has_complexity_2(self, analyzer: ASTAnalyzer):
        src = "def f(x):\n    if x:\n        return 1\n    return 0\n"
        result = analyzer.analyze_content(src)
        f = next(fn for fn in result.functions if fn.name == "f")
        assert f.cyclomatic_complexity == 2

    def test_function_with_for_loop_has_complexity_2(self, analyzer: ASTAnalyzer):
        src = "def f(items):\n    for x in items:\n        pass\n"
        result = analyzer.analyze_content(src)
        f = next(fn for fn in result.functions if fn.name == "f")
        assert f.cyclomatic_complexity == 2

    def test_and_or_add_complexity(self, analyzer: ASTAnalyzer):
        src = "def f(a, b, c):\n    if a and b or c:\n        pass\n"
        result = analyzer.analyze_content(src)
        f = next(fn for fn in result.functions if fn.name == "f")
        assert f.cyclomatic_complexity >= 3



class TestNestingDepth:
    """Max nesting depth tracking."""

    def test_flat_code_has_depth_zero(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content("x = 1\n")
        assert result.max_nesting_depth == 0

    def test_single_if_has_depth_one(self, analyzer: ASTAnalyzer):
        src = "if True:\n    pass\n"
        result = analyzer.analyze_content(src)
        assert result.max_nesting_depth == 1

    def test_deeply_nested_code(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(DEEP_NESTING_FIXTURE)
        assert result.max_nesting_depth >= 4

    def test_nesting_threshold_is_4(self):
        assert ASTAnalyzer.NESTING_THRESHOLD == 4

    def test_deep_nesting_locations_populated(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(DEEP_NESTING_FIXTURE)
        assert len(result.deep_nesting_locations) >= 1

    def test_no_deep_nesting_on_flat_code(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(NO_IMPORTS_FIXTURE)
        assert result.deep_nesting_locations == []



class TestErrorHandling:
    """Never raises; returns ASTAnalysis with parse_error on failure."""

    def test_parse_error_returns_ast_analysis(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(PARSE_ERROR_FIXTURE)
        assert isinstance(result, ASTAnalysis)

    def test_parse_error_message_set(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(PARSE_ERROR_FIXTURE)
        assert result.parse_error != ""

    def test_parse_error_no_exception_raised(self, analyzer: ASTAnalyzer):
        try:
            analyzer.analyze_content(PARSE_ERROR_FIXTURE)
        except Exception as e:
            pytest.fail(f"analyze_content raised {type(e).__name__}: {e}")

    def test_analyze_file_not_found(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze("/nonexistent/path/to/file.py")
        assert isinstance(result, ASTAnalysis)
        assert result.parse_error != ""

    def test_analyze_file_not_found_no_exception(self, analyzer: ASTAnalyzer):
        try:
            analyzer.analyze("/nonexistent/path/to/file.py")
        except Exception as e:
            pytest.fail(f"analyze raised {type(e).__name__}: {e}")

    def test_analyze_file_path_preserved_on_error(self, analyzer: ASTAnalyzer):
        path = "/nonexistent/path/to/file.py"
        result = analyzer.analyze(path)
        assert result.file_path == path

    def test_empty_string_content_no_exception(self, analyzer: ASTAnalyzer):
        try:
            result = analyzer.analyze_content("")
        except Exception as e:
            pytest.fail(f"raised {type(e).__name__}: {e}")

    def test_empty_string_returns_analysis(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content("")
        assert isinstance(result, ASTAnalysis)



class TestAnalyzeFile:
    """File-based analysis using analyze()."""

    def test_analyze_real_file(self, analyzer: ASTAnalyzer, tmp_path):
        f = tmp_path / "sample.py"
        f.write_text(SIMPLE_FIXTURE)
        result = analyzer.analyze(str(f))
        assert isinstance(result, ASTAnalysis)
        assert result.parse_error == ""

    def test_analyze_file_path_stored(self, analyzer: ASTAnalyzer, tmp_path):
        f = tmp_path / "sample.py"
        f.write_text(SIMPLE_FIXTURE)
        result = analyzer.analyze(str(f))
        assert result.file_path == str(f)

    def test_analyze_file_extracts_functions(self, analyzer: ASTAnalyzer, tmp_path):
        f = tmp_path / "sample.py"
        f.write_text(SIMPLE_FIXTURE)
        result = analyzer.analyze(str(f))
        names = [fn.name for fn in result.functions]
        assert "greet" in names

    def test_analyze_non_python_file(self, analyzer: ASTAnalyzer, tmp_path):
        f = tmp_path / "sample.js"
        f.write_text("function hello() { return 'hi'; }")
        result = analyzer.analyze(str(f))
        assert isinstance(result, ASTAnalysis)



class TestDataStructures:
    """ASTAnalysis dataclass field defaults."""

    def test_default_empty_lists(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content("x = 1\n")
        assert isinstance(result.functions, list)
        assert isinstance(result.classes, list)
        assert isinstance(result.imports, list)
        assert isinstance(result.unused_imports, list)
        assert isinstance(result.unreachable_code, list)
        assert isinstance(result.high_complexity_functions, list)
        assert isinstance(result.deep_nesting_locations, list)

    def test_function_info_fields(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        greet = next(f for f in result.functions if f.name == "greet")
        assert isinstance(greet.name, str)
        assert isinstance(greet.args, list)
        assert isinstance(greet.line_start, int)
        assert isinstance(greet.line_end, int)
        assert isinstance(greet.cyclomatic_complexity, int)
        assert isinstance(greet.decorators, list)

    def test_class_info_fields(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        greeter = next(c for c in result.classes if c.name == "Greeter")
        assert isinstance(greeter.name, str)
        assert isinstance(greeter.bases, list)
        assert isinstance(greeter.methods, list)
        assert isinstance(greeter.line_start, int)
        assert isinstance(greeter.line_end, int)

    def test_max_nesting_depth_is_int(self, analyzer: ASTAnalyzer):
        result = analyzer.analyze_content(SIMPLE_FIXTURE)
        assert isinstance(result.max_nesting_depth, int)


# ---------------------------------------------------------------------------
# TASK-007: TestGenerateFindings
# ---------------------------------------------------------------------------

_UNUSED_IMPORT_FINDINGS_FIXTURE = """
import os
import sys

def hello():
    return sys.version
"""

_UNREACHABLE_CODE_FINDINGS_FIXTURE = """
def foo():
    return 42
    x = 1
"""

_HIGH_COMPLEXITY_FINDINGS_FIXTURE = """
def complex_func(a, b, c, d, e, f):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        if f:
                            if a and b:
                                if c or d:
                                    pass
    for i in range(10):
        while a:
            if b or c:
                if d and e and f:
                    pass
    try:
        pass
    except ValueError:
        pass
    except TypeError:
        pass
"""

_DEEP_NESTING_FINDINGS_FIXTURE = """
def deeply_nested():
    if True:
        for i in range(10):
            while True:
                with open("f") as fh:
                    try:
                        pass
                    except Exception:
                        pass
"""


class TestGenerateFindings:
    """Tests for ASTAnalyzer.generate_findings(analysis)."""

    @pytest.fixture
    def analyzer(self) -> ASTAnalyzer:
        return ASTAnalyzer()

    def test_generate_findings_returns_list(self, analyzer):
        analysis = analyzer.analyze_content("x = 1\n")
        result = analyzer.generate_findings(analysis)
        assert isinstance(result, list)

    def test_empty_analysis_returns_empty_list(self, analyzer):
        analysis = analyzer.analyze_content("x = 1\n")
        result = analyzer.generate_findings(analysis)
        assert result == []

    def test_each_finding_has_required_fields(self, analyzer):
        analysis = analyzer.analyze_content(_UNUSED_IMPORT_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        assert len(findings) > 0
        required = {
            "file", "line_start", "line_end", "category",
            "severity", "confidence", "description",
            "validation_status", "reviewer_id",
        }
        for finding in findings:
            missing = required - finding.keys()
            assert missing == set(), f"Finding missing fields: {missing}"

    def test_reviewer_id_is_ast_analyzer(self, analyzer):
        analysis = analyzer.analyze_content(_UNUSED_IMPORT_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        for finding in findings:
            assert finding["reviewer_id"] == "ast-analyzer"

    def test_validation_status_is_verified(self, analyzer):
        analysis = analyzer.analyze_content(_UNUSED_IMPORT_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        for finding in findings:
            assert finding["validation_status"] == "VERIFIED"

    def test_unused_import_generates_finding(self, analyzer):
        analysis = analyzer.analyze_content(_UNUSED_IMPORT_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        categories = [f["category"] for f in findings]
        assert "unused-import" in categories

    def test_unused_import_severity(self, analyzer):
        analysis = analyzer.analyze_content(_UNUSED_IMPORT_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        ui = [f for f in findings if f["category"] == "unused-import"]
        assert len(ui) > 0
        for finding in ui:
            assert finding["severity"] == 3.0

    def test_unused_import_confidence(self, analyzer):
        analysis = analyzer.analyze_content(_UNUSED_IMPORT_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        ui = [f for f in findings if f["category"] == "unused-import"]
        for finding in ui:
            assert finding["confidence"] == 8.0

    def test_unused_import_file_matches_analysis(self, analyzer):
        analysis = analyzer.analyze_content(_UNUSED_IMPORT_FINDINGS_FIXTURE, file_path="myfile.py")
        findings = analyzer.generate_findings(analysis)
        ui = [f for f in findings if f["category"] == "unused-import"]
        for finding in ui:
            assert finding["file"] == "myfile.py"

    def test_unused_import_description_mentions_name(self, analyzer):
        analysis = analyzer.analyze_content(_UNUSED_IMPORT_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        ui = [f for f in findings if f["category"] == "unused-import"]
        for finding in ui:
            assert "os" in finding["description"] or "import" in finding["description"].lower()

    def test_no_finding_for_used_imports(self, analyzer):
        code = "import os\ndef f():\n    return os.getcwd()\n"
        analysis = analyzer.analyze_content(code)
        findings = analyzer.generate_findings(analysis)
        assert not any(f["category"] == "unused-import" for f in findings)

    def test_unreachable_code_generates_finding(self, analyzer):
        analysis = analyzer.analyze_content(_UNREACHABLE_CODE_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        categories = [f["category"] for f in findings]
        assert "unreachable-code" in categories

    def test_unreachable_code_severity(self, analyzer):
        analysis = analyzer.analyze_content(_UNREACHABLE_CODE_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        ur = [f for f in findings if f["category"] == "unreachable-code"]
        assert len(ur) > 0
        for finding in ur:
            assert finding["severity"] == 8.0

    def test_unreachable_code_confidence(self, analyzer):
        analysis = analyzer.analyze_content(_UNREACHABLE_CODE_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        ur = [f for f in findings if f["category"] == "unreachable-code"]
        for finding in ur:
            assert finding["confidence"] == 8.0

    def test_unreachable_code_line_numbers_valid(self, analyzer):
        analysis = analyzer.analyze_content(_UNREACHABLE_CODE_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        ur = [f for f in findings if f["category"] == "unreachable-code"]
        for finding in ur:
            assert isinstance(finding["line_start"], int)
            assert finding["line_start"] >= 1
            assert finding["line_end"] >= finding["line_start"]

    def test_no_unreachable_finding_for_clean_code(self, analyzer):
        code = "def f(x):\n    return x\n"
        analysis = analyzer.analyze_content(code)
        findings = analyzer.generate_findings(analysis)
        assert not any(f["category"] == "unreachable-code" for f in findings)

    def test_high_complexity_generates_finding(self, analyzer):
        analysis = analyzer.analyze_content(_HIGH_COMPLEXITY_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        categories = [f["category"] for f in findings]
        assert "high-complexity" in categories

    def test_high_complexity_severity(self, analyzer):
        analysis = analyzer.analyze_content(_HIGH_COMPLEXITY_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        hc = [f for f in findings if f["category"] == "high-complexity"]
        assert len(hc) > 0
        for finding in hc:
            assert finding["severity"] == 5.0

    def test_high_complexity_confidence(self, analyzer):
        analysis = analyzer.analyze_content(_HIGH_COMPLEXITY_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        hc = [f for f in findings if f["category"] == "high-complexity"]
        for finding in hc:
            assert finding["confidence"] == 8.0

    def test_high_complexity_description_mentions_function(self, analyzer):
        analysis = analyzer.analyze_content(_HIGH_COMPLEXITY_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        hc = [f for f in findings if f["category"] == "high-complexity"]
        for finding in hc:
            assert "complex_func" in finding["description"] or "complexity" in finding["description"].lower()

    def test_no_high_complexity_for_simple_function(self, analyzer):
        code = "def f(x):\n    if x:\n        return 1\n    return 0\n"
        analysis = analyzer.analyze_content(code)
        findings = analyzer.generate_findings(analysis)
        assert not any(f["category"] == "high-complexity" for f in findings)

    def test_high_complexity_line_start_valid(self, analyzer):
        analysis = analyzer.analyze_content(_HIGH_COMPLEXITY_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        hc = [f for f in findings if f["category"] == "high-complexity"]
        for finding in hc:
            assert isinstance(finding["line_start"], int)
            assert finding["line_start"] >= 1

    def test_deep_nesting_generates_finding(self, analyzer):
        analysis = analyzer.analyze_content(_DEEP_NESTING_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        categories = [f["category"] for f in findings]
        assert "deep-nesting" in categories

    def test_deep_nesting_severity(self, analyzer):
        analysis = analyzer.analyze_content(_DEEP_NESTING_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        dn = [f for f in findings if f["category"] == "deep-nesting"]
        assert len(dn) > 0
        for finding in dn:
            assert finding["severity"] == 5.0

    def test_deep_nesting_confidence(self, analyzer):
        analysis = analyzer.analyze_content(_DEEP_NESTING_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        dn = [f for f in findings if f["category"] == "deep-nesting"]
        for finding in dn:
            assert finding["confidence"] == 8.0

    def test_deep_nesting_line_numbers_valid(self, analyzer):
        analysis = analyzer.analyze_content(_DEEP_NESTING_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        dn = [f for f in findings if f["category"] == "deep-nesting"]
        for finding in dn:
            assert isinstance(finding["line_start"], int)
            assert finding["line_start"] >= 1
            assert finding["line_end"] >= finding["line_start"]

    def test_no_deep_nesting_for_shallow_code(self, analyzer):
        code = "def f(x):\n    if x:\n        return 1\n    return 0\n"
        analysis = analyzer.analyze_content(code)
        findings = analyzer.generate_findings(analysis)
        assert not any(f["category"] == "deep-nesting" for f in findings)

    def test_findings_compatible_with_fingerprinter(self, analyzer):
        from wfc.scripts.skills.review.fingerprint import Fingerprinter
        analysis = analyzer.analyze_content(_UNUSED_IMPORT_FINDINGS_FIXTURE)
        findings = analyzer.generate_findings(analysis)
        if findings:
            fp = Fingerprinter()
            try:
                result = fp.deduplicate(findings)
                assert isinstance(result, list)
            except Exception as e:
                pytest.fail(f"Fingerprinter.deduplicate raised: {e}")

    def test_empty_analysis_compatible_with_fingerprinter(self, analyzer):
        from wfc.scripts.skills.review.fingerprint import Fingerprinter
        analysis = analyzer.analyze_content("x = 1\n")
        findings = analyzer.generate_findings(analysis)
        assert findings == []
        fp = Fingerprinter()
        result = fp.deduplicate(findings)
        assert result == []

    def test_combined_findings_unused_and_unreachable(self, analyzer):
        code = (
            "import os\nimport sys\n\n"
            "def foo():\n"
            "    return 42\n"
            "    x = 1\n"
            "\ndef use_sys():\n"
            "    return sys.version\n"
        )
        analysis = analyzer.analyze_content(code)
        findings = analyzer.generate_findings(analysis)
        categories = {f["category"] for f in findings}
        assert "unused-import" in categories
        assert "unreachable-code" in categories

    def test_validation_status_verified_for_all_types(self, analyzer):
        for fixture in [
            _UNUSED_IMPORT_FINDINGS_FIXTURE,
            _UNREACHABLE_CODE_FINDINGS_FIXTURE,
            _HIGH_COMPLEXITY_FINDINGS_FIXTURE,
            _DEEP_NESTING_FINDINGS_FIXTURE,
        ]:
            analysis = analyzer.analyze_content(fixture)
            findings = analyzer.generate_findings(analysis)
            for finding in findings:
                assert finding["validation_status"] == "VERIFIED", (
                    f"Expected VERIFIED, got {finding['validation_status']} "
                    f"for category {finding['category']}"
                )
