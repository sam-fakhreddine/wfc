"""Tests for register_hooks upsert logic."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wfc" / "scripts" / "hooks"))

from register_hooks import is_wfc_hook_entry, upsert_hooks


class TestIsWfcHookEntry:
    """Test WFC hook detection."""

    def test_detects_wfc_hook(self):
        entry = {
            "matcher": "Write|Edit",
            "hooks": [
                {"type": "command", "command": "python ~/.wfc/scripts/hooks/file_checker.py"}
            ],
        }
        assert is_wfc_hook_entry(entry) is True

    def test_ignores_non_wfc_hook(self):
        entry = {
            "matcher": "Write|Edit",
            "hooks": [
                {"type": "command", "command": "my-custom-linter"}
            ],
        }
        assert is_wfc_hook_entry(entry) is False

    def test_empty_hooks_list(self):
        entry = {"matcher": "Write|Edit", "hooks": []}
        assert is_wfc_hook_entry(entry) is False

    def test_no_hooks_key(self):
        entry = {"matcher": "Write|Edit"}
        assert is_wfc_hook_entry(entry) is False


class TestUpsertHooks:
    """Test settings.json upsert logic."""

    def test_creates_new_settings_file(self, tmp_path):
        settings = tmp_path / ".claude" / "settings.json"
        assert not settings.exists()

        changed = upsert_hooks(settings)

        assert changed is True
        assert settings.exists()
        data = json.loads(settings.read_text())
        assert "hooks" in data
        assert "PostToolUse" in data["hooks"]
        post_hooks = data["hooks"]["PostToolUse"]
        assert len(post_hooks) == 2
        assert any("file_checker" in str(h) for h in post_hooks)
        assert any("context_monitor" in str(h) for h in post_hooks)

    def test_preserves_existing_settings(self, tmp_path):
        settings = tmp_path / "settings.json"
        existing = {
            "permissions": {"allow": ["Bash(*)"]},
            "env": {"MY_VAR": "hello"},
        }
        settings.write_text(json.dumps(existing))

        upsert_hooks(settings)

        data = json.loads(settings.read_text())
        assert data["permissions"] == {"allow": ["Bash(*)"]}
        assert data["env"] == {"MY_VAR": "hello"}
        assert "PostToolUse" in data["hooks"]

    def test_preserves_existing_hooks(self, tmp_path):
        settings = tmp_path / "settings.json"
        existing = {
            "hooks": {
                "PreToolUse": [
                    {"matcher": "Bash", "hooks": [{"type": "command", "command": "my-guard"}]}
                ],
                "PostToolUse": [
                    {"matcher": "Task", "hooks": [{"type": "command", "command": "my-task-hook"}]}
                ],
            }
        }
        settings.write_text(json.dumps(existing))

        upsert_hooks(settings)

        data = json.loads(settings.read_text())
        assert len(data["hooks"]["PreToolUse"]) == 1
        assert data["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == "my-guard"
        post_hooks = data["hooks"]["PostToolUse"]
        commands = []
        for entry in post_hooks:
            for hook in entry.get("hooks", []):
                commands.append(hook.get("command", ""))
        assert "my-task-hook" in commands
        assert any("file_checker" in c for c in commands)

    def test_idempotent(self, tmp_path):
        settings = tmp_path / "settings.json"
        settings.write_text("{}")

        upsert_hooks(settings)
        first_content = settings.read_text()

        upsert_hooks(settings)
        second_content = settings.read_text()

        assert first_content == second_content

    def test_replaces_old_wfc_hooks(self, tmp_path):
        settings = tmp_path / "settings.json"
        old_data = {
            "hooks": {
                "PostToolUse": [
                    {"matcher": "Task", "hooks": [{"type": "command", "command": "user-hook"}]},
                    {
                        "matcher": "Write|Edit",
                        "hooks": [
                            {"type": "command", "command": "python ~/.wfc/scripts/hooks/old_checker.py"}
                        ],
                    },
                ]
            }
        }
        settings.write_text(json.dumps(old_data))

        upsert_hooks(settings)

        data = json.loads(settings.read_text())
        post_hooks = data["hooks"]["PostToolUse"]
        commands = []
        for entry in post_hooks:
            for hook in entry.get("hooks", []):
                commands.append(hook.get("command", ""))
        assert "python ~/.wfc/scripts/hooks/old_checker.py" not in commands
        assert "user-hook" in commands
        assert any("file_checker" in c for c in commands)

    def test_handles_corrupt_json(self, tmp_path):
        settings = tmp_path / "settings.json"
        settings.write_text("not valid json{{{")

        changed = upsert_hooks(settings)

        assert changed is True
        data = json.loads(settings.read_text())
        assert "PostToolUse" in data["hooks"]

    def test_handles_non_dict_json(self, tmp_path):
        settings = tmp_path / "settings.json"
        settings.write_text('"just a string"')

        changed = upsert_hooks(settings)

        assert changed is True
        data = json.loads(settings.read_text())
        assert "PostToolUse" in data["hooks"]

    def test_session_start_not_clobbered(self, tmp_path):
        settings = tmp_path / "settings.json"
        existing = {
            "hooks": {
                "SessionStart": [
                    {"matcher": "", "hooks": [{"type": "command", "command": "my-init"}]}
                ]
            }
        }
        settings.write_text(json.dumps(existing))

        upsert_hooks(settings)

        data = json.loads(settings.read_text())
        assert data["hooks"]["SessionStart"][0]["hooks"][0]["command"] == "my-init"
