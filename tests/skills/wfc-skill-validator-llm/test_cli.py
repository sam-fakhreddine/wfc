"""Tests for wfc/skills/wfc-skill-validator-llm/cli.py — thin wrapper entry point."""

from __future__ import annotations


def test_wrapper_main_is_callable() -> None:
    """main() re-exported by the skill wrapper is callable."""
    from wfc.scripts.orchestrators.skill_validator_llm.cli import main

    assert callable(main)


def test_wrapper_main_no_args_returns_nonzero() -> None:
    """Calling main with no args returns a non-zero exit code (prints help)."""
    from wfc.scripts.orchestrators.skill_validator_llm.cli import main

    rc = main([])
    assert rc != 0


def test_wrapper_imports_resolve() -> None:
    """The skill cli module imports without error."""
    import importlib
    import sys

    mod_name = "wfc.scripts.orchestrators.skill_validator_llm.cli"
    if mod_name in sys.modules:
        mod = sys.modules[mod_name]
    else:
        mod = importlib.import_module(mod_name)

    assert hasattr(mod, "main")
