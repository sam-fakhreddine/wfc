"""
Settings generator - creates .claude/settings.local.json
"""

import json
from pathlib import Path
from typing import Dict

from .allowlist import AllowlistCategories


class SettingsGenerator:
    """Generates Claude Code settings file"""

    def generate(self, allowlist: AllowlistCategories) -> Dict:
        """Generate settings.local.json content"""

        # Convert allowlist to Claude Code format
        allowed_commands = []

        # Universal commands
        allowed_commands.extend(allowlist.universal)

        # Git commands
        allowed_commands.extend(allowlist.git_read)
        allowed_commands.extend(allowlist.git_write)

        # Language-specific
        allowed_commands.extend(allowlist.language_specific)

        # Build/CI
        allowed_commands.extend(allowlist.build_ci)

        settings = {
            "allowedCommands": allowed_commands,
            "filePatterns": {
                "allowed": [p for p in allowlist.file_patterns if "read-only" not in p],
                "readonly": [
                    p.replace(" (read-only)", "")
                    for p in allowlist.file_patterns
                    if "read-only" in p
                ],
            },
            "generated_by": "wfc-safeclaude",
            "version": "1.0.0",
        }

        return settings

    def save(self, settings: Dict, project_path: Path = Path.cwd()) -> Path:
        """Save settings to .claude/settings.local.json"""

        claude_dir = project_path / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "settings.local.json"
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)

        return settings_file
