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


def main() -> None:
    """Main entry point for the PreToolUse hook."""
    try:
        _run()
    except Exception as e:
        try:
            from wfc.observability.instrument import emit_event, incr

            incr("hook.bypass_count", labels={"hook": "pretooluse"})
            emit_event(
                "hook.bypass",
                source="pretooluse_hook",
                payload={"error_type": type(e).__name__},
                level="warning",
            )
        except Exception:
            pass
        logger.warning(
            "Hook bypass: pretooluse_hook exception=%s time=%s",
            type(e).__name__,
            time.strftime("%Y-%m-%dT%H:%M:%S"),
        )
        sys.exit(0)


def _run() -> None:
    """Internal hook logic."""
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        input_data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    if not isinstance(input_data, dict):
        sys.exit(0)

    try:
        from wfc.scripts.hooks.rule_engine import evaluate as rule_evaluate
        from wfc.scripts.hooks.security_hook import check as security_check
    except ImportError:
        sys.exit(0)

    security_result = security_check(input_data)

    if security_result.get("decision") == "block":
        try:
            from wfc.scripts.security.refusal_agent import emit_and_exit

            reason = security_result["reason"]
            pattern_id = ""
            if "[" in reason and "]" in reason:
                pattern_id = reason[reason.index("[") + 1 : reason.index("]")]
            emit_and_exit(
                reason=reason,
                pattern_id=pattern_id,
                tool_name=input_data.get("tool_name", ""),
            )
        except SystemExit:
            raise
        except Exception:
            print(security_result["reason"], file=sys.stderr)
            sys.exit(2)

    if security_result.get("decision") == "warn":
        print(security_result["reason"], file=sys.stderr)

    rule_result = rule_evaluate(input_data)

    if rule_result.get("decision") == "block":
        try:
            from wfc.scripts.security.refusal_agent import emit_and_exit

            reason = rule_result["reason"]
            pattern_id = ""
            if "[" in reason and "]" in reason:
                pattern_id = reason[reason.index("[") + 1 : reason.index("]")]
            emit_and_exit(
                reason=reason,
                pattern_id=pattern_id,
                tool_name=input_data.get("tool_name", ""),
            )
        except SystemExit:
            raise
        except Exception:
            print(rule_result["reason"], file=sys.stderr)
            sys.exit(2)

    if rule_result.get("decision") == "warn":
        print(rule_result["reason"], file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
