"""
WFC Branding Configuration

Provides consistent branding based on user's installation choice.
Supports both SFW (Safe For Work) and NSFW modes.
"""

from pathlib import Path
from typing import Dict, Optional


class WFCBranding:
    """
    WFC Branding manager.

    Reads branding configuration from installation and provides
    consistent messaging across all WFC skills.
    """

    def __init__(self):
        self.mode: str = "nsfw"  # Default
        self.name: str = "World Fucking Class"
        self.acronym: str = "WFC"
        self.tagline: str = "Multi-Agent Framework That Doesn't Fuck Around"
        self._load_config()

    def _load_config(self) -> None:
        """Load branding config from installation"""
        # Possible config locations
        paths = [
            Path.home() / ".wfc" / ".wfc_branding",
            Path.home() / ".claude" / "skills" / "wfc" / ".wfc_branding",
            Path.home() / ".kiro" / "skills" / "wfc" / ".wfc_branding",
        ]

        for path in paths:
            if path.exists():
                try:
                    self._parse_config(path)
                    break
                except Exception:
                    # Fall back to defaults
                    pass

    def _parse_config(self, path: Path) -> None:
        """Parse branding config file"""
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        if key == "mode":
                            self.mode = value
                        elif key == "name":
                            self.name = value
                        elif key == "tagline":
                            self.tagline = value

    @property
    def is_sfw(self) -> bool:
        """Check if SFW mode is enabled"""
        return self.mode == "sfw"

    @property
    def is_nsfw(self) -> bool:
        """Check if NSFW mode is enabled"""
        return self.mode == "nsfw"

    def get_message(self, key: str) -> str:
        """
        Get branding-aware message.

        Args:
            key: Message key (tagline, success, error, etc.)

        Returns:
            Branding-appropriate message
        """
        messages = {
            "tagline": {
                "sfw": "This is Workflow Champion.",
                "nsfw": "This is World Fucking Class."
            },
            "success": {
                "sfw": "Success! Workflow Champion is ready.",
                "nsfw": "Success! World Fucking Class is ready."
            },
            "error": {
                "sfw": "Error: Workflow Champion encountered an issue.",
                "nsfw": "Error: WFC doesn't tolerate failures."
            },
            "complete": {
                "sfw": "Task completed successfully.",
                "nsfw": "Done. No bullshit."
            },
            "quality_fail": {
                "sfw": "Quality checks failed. Please address issues.",
                "nsfw": "Quality checks failed. Fix your shit."
            },
            "review_fail": {
                "sfw": "Review did not approve. Revisions needed.",
                "nsfw": "Review rejected. Back to the drawing board."
            }
        }

        if key in messages:
            return messages[key].get(self.mode, self.name)
        else:
            return self.name

    def format_header(self, title: str) -> str:
        """
        Format a section header with branding.

        Args:
            title: Header title

        Returns:
            Formatted header
        """
        if self.is_sfw:
            return f"# {self.acronym}: {title}"
        else:
            return f"# {self.acronym}: {title}"

    def format_footer(self) -> str:
        """
        Format a document footer with branding.

        Returns:
            Formatted footer
        """
        if self.is_sfw:
            return f"---\n\n**{self.name}** - {self.tagline}\n"
        else:
            return f"---\n\n**{self.get_message('tagline')}**\n\n*{self.tagline}*\n"


# Global instance
_branding: Optional[WFCBranding] = None


def get_branding() -> WFCBranding:
    """Get global branding instance (singleton)"""
    global _branding
    if _branding is None:
        _branding = WFCBranding()
    return _branding


# Convenience functions
def is_sfw() -> bool:
    """Check if SFW mode is enabled"""
    return get_branding().is_sfw


def is_nsfw() -> bool:
    """Check if NSFW mode is enabled"""
    return get_branding().is_nsfw


def get_message(key: str) -> str:
    """Get branding-aware message"""
    return get_branding().get_message(key)


def get_name() -> str:
    """Get WFC name based on branding"""
    return get_branding().name


# Example usage
if __name__ == "__main__":
    branding = get_branding()
    print(f"Mode: {branding.mode}")
    print(f"Name: {branding.name}")
    print(f"Tagline: {branding.tagline}")
    print()
    print(f"Tagline message: {branding.get_message('tagline')}")
    print(f"Success message: {branding.get_message('success')}")
    print(f"Error message: {branding.get_message('error')}")
