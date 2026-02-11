#!/usr/bin/env python3
"""
Update all persona JSON files to use model aliases instead of hardcoded IDs.

This script:
1. Reads all persona JSON files
2. Replaces hardcoded model IDs with aliases (opus, sonnet, haiku)
3. Writes back the updated files

Run after model releases to standardize on aliases.
"""

import json
from pathlib import Path

# Model ID to alias mapping
MODEL_TO_ALIAS = {
    "claude-opus-4-20250514": "opus",
    "claude-opus-4-6": "opus",
    "claude-sonnet-4-20250514": "sonnet",
    "claude-sonnet-4-5-20250929": "sonnet",
    "claude-haiku-4-5-20251001": "haiku",
    "claude-haiku-4-20250514": "haiku",
}


def update_persona_file(file_path: Path):
    """Update a single persona file to use aliases"""
    try:
        with open(file_path, 'r') as f:
            persona = json.load(f)

        # Update model_preference
        if "model_preference" in persona:
            default = persona["model_preference"].get("default", "")
            fallback = persona["model_preference"].get("fallback", "")

            # Replace with alias if found
            if default in MODEL_TO_ALIAS:
                persona["model_preference"]["default"] = MODEL_TO_ALIAS[default]
                print(f"  ✓ {file_path.stem}: {default} → {MODEL_TO_ALIAS[default]}")

            if fallback and fallback in MODEL_TO_ALIAS:
                persona["model_preference"]["fallback"] = MODEL_TO_ALIAS[fallback]

        # Write back
        with open(file_path, 'w') as f:
            json.dump(persona, f, indent=2)

        return True

    except Exception as e:
        print(f"  ✗ Error updating {file_path}: {e}")
        return False


def main():
    """Update all persona files"""
    personas_dir = Path.home() / ".claude/skills/wfc/personas/panels"

    if not personas_dir.exists():
        print(f"Personas directory not found: {personas_dir}")
        return

    print("Updating persona files to use model aliases...\n")

    count = 0
    for panel_dir in personas_dir.iterdir():
        if not panel_dir.is_dir():
            continue

        for persona_file in panel_dir.glob("*.json"):
            if update_persona_file(persona_file):
                count += 1

    print(f"\n✅ Updated {count} persona files")
    print("\nModel aliases used:")
    print("  opus   → Latest Opus model")
    print("  sonnet → Latest Sonnet model")
    print("  haiku  → Latest Haiku model")
    print("\nUpdate shared/config/wfc_config.py to change actual model IDs.")


if __name__ == "__main__":
    main()
