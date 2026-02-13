#!/usr/bin/env python3
"""
WFC Language Detector

Detects project languages and recommends appropriate quality tools.
"""

from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
import json


@dataclass
class LanguageConfig:
    """Configuration for a detected language."""

    language: str
    files_found: int
    formatter: str
    linter: str
    test_framework: str
    install_command: str


class LanguageDetector:
    """Detect languages and recommend tools."""

    LANGUAGE_PATTERNS = {
        "python": {
            "extensions": [".py"],
            "config_files": ["pyproject.toml", "setup.py", "requirements.txt"],
            "formatter": "black",
            "linter": "ruff",  # Ruff is Python-specific
            "test_framework": "pytest",
            "install": "uv pip install black ruff pytest",
        },
        "javascript": {
            "extensions": [".js", ".jsx"],
            "config_files": ["package.json", ".eslintrc", ".eslintrc.json"],
            "formatter": "prettier",
            "linter": "eslint",
            "test_framework": "jest",
            "install": "npm install --save-dev prettier eslint jest",
        },
        "typescript": {
            "extensions": [".ts", ".tsx"],
            "config_files": ["tsconfig.json", "package.json"],
            "formatter": "prettier",
            "linter": "eslint",
            "test_framework": "jest",
            "install": "npm install --save-dev prettier @typescript-eslint/parser @typescript-eslint/eslint-plugin jest",
        },
        "go": {
            "extensions": [".go"],
            "config_files": ["go.mod", "go.sum"],
            "formatter": "gofmt",
            "linter": "golangci-lint",
            "test_framework": "go test",
            "install": "go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest",
        },
        "rust": {
            "extensions": [".rs"],
            "config_files": ["Cargo.toml", "Cargo.lock"],
            "formatter": "rustfmt",
            "linter": "clippy",
            "test_framework": "cargo test",
            "install": "rustup component add rustfmt clippy",
        },
        "java": {
            "extensions": [".java"],
            "config_files": ["pom.xml", "build.gradle"],
            "formatter": "google-java-format",
            "linter": "checkstyle",
            "test_framework": "junit",
            "install": "# Maven/Gradle managed",
        },
        "ruby": {
            "extensions": [".rb"],
            "config_files": ["Gemfile", ".rubocop.yml"],
            "formatter": "rubocop",
            "linter": "rubocop",
            "test_framework": "rspec",
            "install": "gem install rubocop rspec",
        },
        "csharp": {
            "extensions": [".cs"],
            "config_files": [".csproj", ".sln"],
            "formatter": "dotnet format",
            "linter": "dotnet analyze",
            "test_framework": "dotnet test",
            "install": "# .NET SDK included",
        },
    }

    def __init__(self, project_root: Path = None):
        """Initialize detector."""
        self.project_root = project_root or Path.cwd()

    def detect_languages(self) -> List[LanguageConfig]:
        """
        Detect all languages used in project.

        Returns:
            List of LanguageConfig for detected languages
        """
        detected = {}

        # Scan for files
        for lang_name, lang_info in self.LANGUAGE_PATTERNS.items():
            files_found = 0

            # Count files with matching extensions
            for ext in lang_info["extensions"]:
                files_found += len(list(self.project_root.rglob(f"*{ext}")))

            # Check for config files
            has_config = any((self.project_root / cf).exists() for cf in lang_info["config_files"])

            if files_found > 0 or has_config:
                detected[lang_name] = LanguageConfig(
                    language=lang_name,
                    files_found=files_found,
                    formatter=lang_info["formatter"],
                    linter=lang_info["linter"],
                    test_framework=lang_info["test_framework"],
                    install_command=lang_info["install"],
                )

        # Sort by file count (most files first)
        return sorted(detected.values(), key=lambda x: x.files_found, reverse=True)

    def generate_config(self, languages: List[LanguageConfig]) -> Dict:
        """Generate quality check configuration."""
        return {
            "languages": [
                {
                    "name": lang.language,
                    "formatter": lang.formatter,
                    "linter": lang.linter,
                    "test_framework": lang.test_framework,
                }
                for lang in languages
            ],
            "install_commands": [lang.install_command for lang in languages],
        }


def main():
    """CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Detect project languages")
    parser.add_argument("--path", default=".", help="Project root")
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()

    detector = LanguageDetector(Path(args.path))
    languages = detector.detect_languages()

    if args.json:
        config = detector.generate_config(languages)
        print(json.dumps(config, indent=2))
    else:
        print("Detected Languages:")
        for lang in languages:
            print(f"\n{lang.language.upper()}:")
            print(f"  Files: {lang.files_found}")
            print(f"  Formatter: {lang.formatter}")
            print(f"  Linter: {lang.linter}")
            print(f"  Tests: {lang.test_framework}")
            print(f"  Install: {lang.install_command}")


if __name__ == "__main__":
    main()
