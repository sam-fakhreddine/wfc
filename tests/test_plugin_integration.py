"""
Tests for WFC Plugin Integration features.

Covers all 7 features:
1. Hook Infrastructure (HookState, SecurityHook, RuleEngine, ConfigLoader, PreToolUseDispatcher)
2. Review Enhancements (confidence filtering, ReviewRequest fields)
3. New Personas (SILENT_FAILURE_HUNTER, CODE_SIMPLIFIER)
4. Architecture Designer (multi-approach design phase)
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from wfc.scripts.hooks.config_loader import load_rules
from wfc.scripts.hooks.hook_state import HookState
from wfc.scripts.hooks.rule_engine import evaluate as rule_evaluate
from wfc.scripts.hooks.security_hook import check as security_check
from wfc.scripts.orchestrators.review.agents import AgentReview, AgentType, ReviewComment
from wfc.scripts.orchestrators.review.consensus import ConsensusAlgorithm

_arch_designer_path = (
    Path(__file__).parent.parent / "wfc" / "skills" / "wfc-plan" / "architecture_designer.py"
)
_spec = importlib.util.spec_from_file_location("architecture_designer", _arch_designer_path)
_arch_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_arch_mod)
ArchitectureDesigner = _arch_mod.ArchitectureDesigner
ArchitectureApproach = _arch_mod.ArchitectureApproach


class TestHookState:
    """Test session-scoped hook state."""

    def test_mark_and_check_warned(self):
        """Mark a warning, verify has_warned returns True."""
        state = HookState(session_key="test-mark-warned")
        try:
            state.mark_warned("app.py", "eval-injection")
            assert state.has_warned("app.py", "eval-injection") is True
        finally:
            state.clear()

    def test_not_warned_returns_false(self):
        """Verify has_warned returns False for unseen patterns."""
        state = HookState(session_key="test-not-warned")
        try:
            assert state.has_warned("app.py", "never-seen-pattern") is False
        finally:
            state.clear()

    def test_different_files_different_state(self):
        """Same pattern on different files tracked separately."""
        state = HookState(session_key="test-different-files")
        try:
            state.mark_warned("file_a.py", "eval-injection")

            assert state.has_warned("file_a.py", "eval-injection") is True
            assert state.has_warned("file_b.py", "eval-injection") is False
        finally:
            state.clear()

    def test_clear_resets_state(self):
        """clear() removes all warnings."""
        state = HookState(session_key="test-clear-state")
        state.mark_warned("app.py", "eval-injection")
        state.mark_warned("utils.py", "os-system")

        state.clear()

        assert state.has_warned("app.py", "eval-injection") is False
        assert state.has_warned("utils.py", "os-system") is False


class TestSecurityHook:
    """Test security pattern matching."""

    def test_blocks_eval(self):
        """Write tool with eval() content should return block."""
        result = security_check(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "script.py",
                    "content": "result = eval(user_input)",
                },
            }
        )
        assert result.get("decision") == "block"
        assert "eval" in result.get("reason", "").lower()

    def test_blocks_os_system(self):
        """Write tool with os.system() should return block."""
        result = security_check(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "script.py",
                    "content": "import os\nos.system('ls -la')",
                },
            }
        )
        assert result.get("decision") == "block"
        assert "os.system" in result.get("reason", "").lower()

    def test_warns_innerhtml(self):
        """Write tool with innerHTML should return warn."""
        state = HookState(session_key="test-innerhtml-warn")
        try:
            result = security_check(
                {
                    "tool_name": "Write",
                    "tool_input": {
                        "file_path": "app.js",
                        "content": "element.innerHTML = userContent;",
                    },
                },
                state=state,
            )
            assert result.get("decision") == "warn"
            assert "innerhtml" in result.get("reason", "").lower()
        finally:
            state.clear()

    def test_warns_pickle(self):
        """Write tool with pickle.load should return warn."""
        state = HookState(session_key="test-pickle-warn")
        try:
            result = security_check(
                {
                    "tool_name": "Write",
                    "tool_input": {
                        "file_path": "loader.py",
                        "content": "data = pickle.load(f)",
                    },
                },
                state=state,
            )
            assert result.get("decision") == "warn"
            assert "pickle" in result.get("reason", "").lower()
        finally:
            state.clear()

    def test_blocks_rm_rf_root(self):
        """Bash tool with 'rm -rf /' should return block."""
        result = security_check(
            {
                "tool_name": "Bash",
                "tool_input": {
                    "command": "rm -rf /etc",
                },
            }
        )
        assert result.get("decision") == "block"

    def test_allows_safe_code(self):
        """Write tool with normal Python should return empty dict."""
        result = security_check(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "safe.py",
                    "content": "def hello():\n    return 'world'\n",
                },
            }
        )
        assert result == {}

    def test_blocks_subprocess_shell(self):
        """subprocess with shell=True should block."""
        result = security_check(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "runner.py",
                    "content": "subprocess.run(cmd, shell=True)",
                },
            }
        )
        assert result.get("decision") == "block"

    def test_warns_hardcoded_secret(self):
        """API_KEY='secretvalue' should warn."""
        state = HookState(session_key="test-hardcoded-secret")
        try:
            result = security_check(
                {
                    "tool_name": "Write",
                    "tool_input": {
                        "file_path": "config.py",
                        "content": 'API_KEY="my_super_secret_key_12345"',
                    },
                },
                state=state,
            )
            assert result.get("decision") == "warn"
            assert "secret" in result.get("reason", "").lower()
        finally:
            state.clear()


class TestRuleEngine:
    """Test configurable rule engine."""

    def test_evaluate_no_rules_dir(self):
        """Missing dir returns empty dict."""
        result = rule_evaluate(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": "app.py", "content": "anything"},
            },
            rules_dir=Path("/nonexistent/dir/wfc/rules"),
        )
        assert result == {}

    def test_evaluate_regex_match_rule(self):
        """Create temp rule file, verify it matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_content = """---
name: block-debugger
action: block
event: file
conditions:
  - field: new_text, operator: regex_match, pattern: debugger
---
Do not use debugger statements.
"""
            (rules_dir / "block-debugger.md").write_text(rule_content)

            result = rule_evaluate(
                {
                    "tool_name": "Write",
                    "tool_input": {
                        "file_path": "app.js",
                        "content": "debugger; // left in by mistake",
                    },
                },
                rules_dir=rules_dir,
            )
            assert result.get("decision") == "block"

    def test_evaluate_contains_operator(self):
        """Test contains condition."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_content = """---
name: warn-todo
action: warn
event: file
conditions:
  - field: new_text, operator: contains, value: TODO
---
Found a TODO comment. Please create a task instead.
"""
            (rules_dir / "warn-todo.md").write_text(rule_content)

            result = rule_evaluate(
                {
                    "tool_name": "Write",
                    "tool_input": {
                        "file_path": "app.py",
                        "content": "# TODO: fix this later",
                    },
                },
                rules_dir=rules_dir,
            )
            assert result.get("decision") == "warn"

    def test_evaluate_disabled_rule_skipped(self):
        """Rule with enabled: false should be skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_content = """---
name: disabled-rule
action: block
enabled: false
event: file
conditions:
  - field: new_text, operator: contains, value: blocked
---
This should not trigger.
"""
            (rules_dir / "disabled-rule.md").write_text(rule_content)

            result = rule_evaluate(
                {
                    "tool_name": "Write",
                    "tool_input": {
                        "file_path": "app.py",
                        "content": "this text contains blocked word",
                    },
                },
                rules_dir=rules_dir,
            )
            assert result == {}


class TestConfigLoader:
    """Test markdown rule file loading."""

    def test_load_rules_empty_dir(self):
        """Empty dir returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules = load_rules(Path(tmpdir))
            assert rules == []

    def test_load_rules_missing_dir(self):
        """Missing dir returns empty list."""
        rules = load_rules(Path("/nonexistent/dir/that/doesnt/exist"))
        assert rules == []

    def test_load_rules_valid_file(self):
        """Create a temp .md file with frontmatter, verify parsed correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rule_file = Path(tmpdir) / "my-rule.md"
            rule_file.write_text(
                """---
name: my-rule
action: warn
event: file
conditions:
  - field: new_text, operator: contains, value: FIXME
---
Please address FIXME comments before committing.
"""
            )
            rules = load_rules(Path(tmpdir))
            assert len(rules) == 1
            assert rules[0]["name"] == "my-rule"
            assert rules[0]["action"] == "warn"
            assert rules[0]["event"] == "file"

    def test_load_rules_body_extracted(self):
        """Verify the body (after frontmatter) is captured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rule_file = Path(tmpdir) / "body-test.md"
            rule_file.write_text(
                """---
name: body-test
action: block
---
This is the body message.
It spans multiple lines.
"""
            )
            rules = load_rules(Path(tmpdir))
            assert len(rules) == 1
            body = rules[0]["body"]
            assert "This is the body message." in body
            assert "It spans multiple lines." in body


class TestPreToolUseDispatcher:
    """Test unified hook dispatcher."""

    def _run_dispatcher(self, input_data: dict) -> subprocess.CompletedProcess:
        """Helper to run the pretooluse hook dispatcher as a subprocess."""
        input_json = json.dumps(input_data)
        return subprocess.run(
            [sys.executable, "-m", "wfc.scripts.hooks"],
            input=input_json,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_security_block_exits_2(self):
        """Pipe eval() JSON to dispatcher, verify exit code 2."""
        result = self._run_dispatcher(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "evil.py",
                    "content": "result = eval(user_input)",
                },
            }
        )
        assert result.returncode == 2

    def test_safe_code_exits_0(self):
        """Pipe safe code JSON, verify exit code 0."""
        result = self._run_dispatcher(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "safe.py",
                    "content": "def hello():\n    return 'world'\n",
                },
            }
        )
        assert result.returncode == 0


class TestConfidenceFiltering:
    """Test confidence-based false positive filtering."""

    def test_review_comment_default_confidence(self):
        """ReviewComment() has confidence=80."""
        rc = ReviewComment(
            file="test.py",
            line=1,
            severity="medium",
            message="test",
            suggestion="fix",
        )
        assert rc.confidence == 80

    def test_review_comment_custom_confidence(self):
        """Can set confidence=50."""
        rc = ReviewComment(
            file="test.py",
            line=1,
            severity="medium",
            message="test",
            suggestion="fix",
            confidence=50,
        )
        assert rc.confidence == 50

    def test_consensus_filters_low_confidence(self):
        """Comments below threshold excluded from consensus."""
        low_conf_comment = ReviewComment(
            file="test.py",
            line=10,
            severity="medium",
            message="Maybe an issue",
            suggestion="Check this",
            confidence=30,
        )
        high_conf_comment = ReviewComment(
            file="test.py",
            line=20,
            severity="high",
            message="Definite issue",
            suggestion="Fix this",
            confidence=90,
        )

        reviews = [
            AgentReview(
                agent=AgentType.CR,
                score=8.0,
                passed=True,
                comments=[low_conf_comment, high_conf_comment],
                summary="Some issues found",
            ),
            AgentReview(
                agent=AgentType.SEC,
                score=9.0,
                passed=True,
                comments=[],
                summary="No issues",
            ),
            AgentReview(
                agent=AgentType.PERF,
                score=8.5,
                passed=True,
                comments=[],
                summary="OK",
            ),
            AgentReview(
                agent=AgentType.COMP,
                score=9.0,
                passed=True,
                comments=[],
                summary="Good",
            ),
        ]

        algo = ConsensusAlgorithm()
        result = algo.calculate(reviews, confidence_threshold=80)

        assert len(result.all_comments) == 1
        assert result.all_comments[0].message == "Definite issue"

    def test_consensus_critical_bypasses_filter(self):
        """Critical severity always included regardless of confidence."""
        critical_low_conf = ReviewComment(
            file="test.py",
            line=1,
            severity="critical",
            message="SQL injection vulnerability",
            suggestion="Use parameterized queries",
            confidence=10,
        )

        reviews = [
            AgentReview(
                agent=AgentType.CR,
                score=8.0,
                passed=True,
                comments=[critical_low_conf],
                summary="Critical issue",
            ),
            AgentReview(
                agent=AgentType.SEC,
                score=9.0,
                passed=True,
                comments=[],
                summary="No issues",
            ),
            AgentReview(
                agent=AgentType.PERF,
                score=8.5,
                passed=True,
                comments=[],
                summary="OK",
            ),
            AgentReview(
                agent=AgentType.COMP,
                score=9.0,
                passed=True,
                comments=[],
                summary="Good",
            ),
        ]

        algo = ConsensusAlgorithm()
        result = algo.calculate(reviews, confidence_threshold=80)

        assert len(result.all_comments) == 1
        assert result.all_comments[0].severity == "critical"

    def test_consensus_filtered_count_tracked(self):
        """filtered_count is correct."""
        comments = [
            ReviewComment(
                file="a.py",
                line=1,
                severity="low",
                message="m1",
                suggestion="s1",
                confidence=10,
            ),
            ReviewComment(
                file="b.py",
                line=2,
                severity="medium",
                message="m2",
                suggestion="s2",
                confidence=20,
            ),
            ReviewComment(
                file="c.py",
                line=3,
                severity="high",
                message="m3",
                suggestion="s3",
                confidence=90,
            ),
        ]

        reviews = [
            AgentReview(
                agent=AgentType.CR,
                score=8.0,
                passed=True,
                comments=comments,
                summary="Issues",
            ),
            AgentReview(
                agent=AgentType.SEC,
                score=9.0,
                passed=True,
                comments=[],
                summary="OK",
            ),
            AgentReview(
                agent=AgentType.PERF,
                score=8.5,
                passed=True,
                comments=[],
                summary="OK",
            ),
            AgentReview(
                agent=AgentType.COMP,
                score=9.0,
                passed=True,
                comments=[],
                summary="OK",
            ),
        ]

        algo = ConsensusAlgorithm()
        result = algo.calculate(reviews, confidence_threshold=80)

        assert result.filtered_count == 2
        assert len(result.all_comments) == 1

    def test_consensus_result_to_dict_includes_filtered(self):
        """to_dict has filtered_count."""
        reviews = [
            AgentReview(
                agent=AgentType.CR,
                score=8.0,
                passed=True,
                comments=[],
                summary="OK",
            ),
            AgentReview(
                agent=AgentType.SEC,
                score=9.0,
                passed=True,
                comments=[],
                summary="OK",
            ),
            AgentReview(
                agent=AgentType.PERF,
                score=8.5,
                passed=True,
                comments=[],
                summary="OK",
            ),
            AgentReview(
                agent=AgentType.COMP,
                score=9.0,
                passed=True,
                comments=[],
                summary="OK",
            ),
        ]

        algo = ConsensusAlgorithm()
        result = algo.calculate(reviews, confidence_threshold=80)
        result_dict = result.to_dict()

        assert "filtered_count" in result_dict
        assert result_dict["filtered_count"] == 0


class TestReviewRequestFields:
    """Test ReviewRequest fields after v2.0 rewrite."""

    def test_review_request_defaults(self):
        """ReviewRequest has sensible defaults for optional fields."""
        from wfc.scripts.orchestrators.review.orchestrator import ReviewRequest

        req = ReviewRequest(
            task_id="TASK-001",
            files=["test.py"],
        )
        assert req.diff_content == ""
        assert req.properties == []

    def test_review_request_with_all_fields(self):
        """ReviewRequest accepts all fields."""
        from wfc.scripts.orchestrators.review.orchestrator import ReviewRequest

        req = ReviewRequest(
            task_id="TASK-001",
            files=["test.py"],
            diff_content="diff --git a/test.py",
            properties=[{"name": "SAFETY"}],
        )
        assert req.task_id == "TASK-001"
        assert req.diff_content == "diff --git a/test.py"


class TestArchitectureDesigner:
    """Test multi-architecture design phase."""

    def test_design_returns_three_approaches(self):
        """design() returns 3 approaches."""
        designer = ArchitectureDesigner()
        approaches = designer.design(goal="add caching", context="performance improvement")
        assert len(approaches) == 3

    def test_approach_names(self):
        """Approaches are Minimal Changes, Clean Architecture, Pragmatic Balance."""
        designer = ArchitectureDesigner()
        approaches = designer.design(goal="test", context="test")
        names = [a.name for a in approaches]
        assert "Minimal Changes" in names
        assert "Clean Architecture" in names
        assert "Pragmatic Balance" in names

    def test_format_comparison_markdown(self):
        """format_comparison returns valid markdown with all sections."""
        designer = ArchitectureDesigner()
        approaches = designer.design(goal="add API", context="new feature")
        md = designer.format_comparison(approaches)

        assert "## Architecture Approaches" in md
        assert "### Option 1:" in md
        assert "### Option 2:" in md
        assert "### Option 3:" in md
        assert "**Pros:**" in md
        assert "**Cons:**" in md
        assert "| Effort |" in md
        assert "| Risk |" in md

    def test_approach_has_pros_and_cons(self):
        """Each approach has non-empty pros and cons."""
        designer = ArchitectureDesigner()
        approaches = designer.design(goal="test", context="test")

        for approach in approaches:
            assert len(approach.pros) > 0, f"{approach.name} has no pros"
            assert len(approach.cons) > 0, f"{approach.name} has no cons"
            assert isinstance(approach.effort, str)
            assert isinstance(approach.risk, str)
