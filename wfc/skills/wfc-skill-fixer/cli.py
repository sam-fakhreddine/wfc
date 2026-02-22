#!/usr/bin/env python3
"""CLI wrapper for wfc-skill-fixer skill."""

import sys

from wfc.scripts.orchestrators.skill_fixer.cli import main

if __name__ == "__main__":
    sys.exit(main())
