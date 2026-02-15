"""Tests for Git Hook Whitelist Constants - VALID_HOOKS completeness.

Focused on verifying the VALID_HOOKS set covers all standard git hooks.
For full security tests (install, wrap, manage), see test_hooks_security.py.

NOTE: Uses importlib to load from hyphenated 'wfc-tools' directory.
"""

import pytest
import importlib.util
from pathlib import Path

_hooks_path = Path(__file__).parent.parent / "wfc" / "wfc-tools" / "gitwork" / "api" / "hooks.py"
_spec = importlib.util.spec_from_file_location("hooks", _hooks_path)
hooks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hooks)


class TestHookWhitelistCompleteness:
    """Verify the VALID_HOOKS set covers expected git hook types."""

    def test_commit_hooks_present(self):
        """All commit-related hooks should be in whitelist."""
        commit_hooks = {"pre-commit", "prepare-commit-msg", "commit-msg", "post-commit"}
        assert commit_hooks.issubset(hooks.VALID_HOOKS)

    def test_merge_hooks_present(self):
        """All merge-related hooks should be in whitelist."""
        merge_hooks = {"pre-merge", "post-merge"}
        assert merge_hooks.issubset(hooks.VALID_HOOKS)

    def test_rebase_hooks_present(self):
        """All rebase-related hooks should be in whitelist."""
        rebase_hooks = {"pre-rebase", "post-rebase"}
        assert rebase_hooks.issubset(hooks.VALID_HOOKS)

    def test_push_hooks_present(self):
        """All push-related hooks should be in whitelist."""
        push_hooks = {"pre-push", "post-push"}
        assert push_hooks.issubset(hooks.VALID_HOOKS)

    def test_checkout_hooks_present(self):
        """All checkout-related hooks should be in whitelist."""
        checkout_hooks = {"pre-checkout", "post-checkout"}
        assert checkout_hooks.issubset(hooks.VALID_HOOKS)

    def test_gc_hooks_present(self):
        """Garbage collection hooks should be in whitelist."""
        gc_hooks = {"pre-auto-gc", "post-auto-gc"}
        assert gc_hooks.issubset(hooks.VALID_HOOKS)

    def test_no_dangerous_entries(self):
        """Whitelist should not contain suspicious entries."""
        for hook in hooks.VALID_HOOKS:
            assert ".." not in hook, f"Path traversal in whitelist: {hook}"
            assert "/" not in hook, f"Directory separator in whitelist: {hook}"
            assert " " not in hook, f"Space in whitelist entry: {hook}"

    def test_whitelist_is_frozen(self):
        """VALID_HOOKS should be a frozenset (immutable at runtime)."""
        assert isinstance(hooks.VALID_HOOKS, frozenset)
        assert len(hooks.VALID_HOOKS) == 14


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
