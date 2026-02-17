#!/usr/bin/env python3
"""
Unified PreToolUse hook dispatcher for WFC.

This is the MAIN entry point called by Claude Code's hook system.
It reads JSON from stdin, runs security checks and rule evaluation,
and exits with the appropriate code:

  - Exit 0: Allow (no issues, or warning issued)
  - Exit 2: Block (security violation or rule block)

CRITICAL: Always exits 0 on internal errors. A hook bug must never
block the user's workflow.

Protocol:
  - Claude Code sends JSON on stdin: {"tool_name": "...", "tool_input": {...}}
  - Block: exit code 2, reason on stderr
  - Warn: reason on stderr, exit code 0
  - Pass: exit code 0, no output
"""

from __future__ import annotations

import json
import logging
import sys
import time

logger = logging.getLogger("wfc.hooks.pretooluse")
_bypass_count = 0


def main() -> None:
    """Main entry point for the PreToolUse hook."""
    global _bypass_count
    try:
        _run()
    except Exception as e:
        _bypass_count += 1
        logger.warning(
            "Hook bypass: pretooluse_hook exception=%s time=%s bypass_count=%d",
            type(e).__name__,
            time.strftime("%Y-%m-%dT%H:%M:%S"),
            _bypass_count,
        )
        # CRITICAL: Never block due to hook bugs
        sys.exit(0)


def _run() -> None:
    """Internal hook logic."""
    # Read input from stdin
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        input_data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    if not isinstance(input_data, dict):
        sys.exit(0)

    # Import here to avoid import errors blocking the hook
    try:
        from wfc.scripts.hooks.rule_engine import evaluate as rule_evaluate
        from wfc.scripts.hooks.security_hook import check as security_check
    except ImportError:
        sys.exit(0)

    # Phase 1: Security patterns (highest priority)
    security_result = security_check(input_data)

    if security_result.get("decision") == "block":
        print(security_result["reason"], file=sys.stderr)
        sys.exit(2)

    if security_result.get("decision") == "warn":
        print(security_result["reason"], file=sys.stderr)
        # Don't exit yet - still check rules

    # Phase 2: Custom rules
    rule_result = rule_evaluate(input_data)

    if rule_result.get("decision") == "block":
        print(rule_result["reason"], file=sys.stderr)
        sys.exit(2)

    if rule_result.get("decision") == "warn":
        print(rule_result["reason"], file=sys.stderr)

    # All clear (or warnings only)
    sys.exit(0)


if __name__ == "__main__":
    main()
