"""
Allow running the hook as: uv run python -m wfc.scripts.hooks

This delegates to pretooluse_hook.main() which is the unified dispatcher.
"""

from wfc.scripts.hooks.pretooluse_hook import main

main()
