"""
Hook Installer - Install and manage WFC git hooks

Uses non-destructive wrapping to preserve existing hooks.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class HookInstaller:
    """Install and manage WFC git hooks."""

    HOOK_SCRIPTS = {
        "pre-commit": "pre_commit.py",
        "commit-msg": "commit_msg.py",
        "pre-push": "pre_push.py",
    }

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize hook installer.

        Args:
            project_root: Project root directory (defaults to current directory)
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.hooks_dir = self.project_root / ".git" / "hooks"
        self.wfc_hooks_dir = Path(__file__).parent

    def is_git_repo(self) -> bool:
        """Check if current directory is a git repository."""
        return (self.project_root / ".git").exists()

    def get_hook_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all WFC hooks.

        Returns:
            List of hook status dicts with:
                - name: Hook name
                - installed: Whether WFC hook is installed
                - enabled: Whether hook is executable
                - wfc_managed: Whether hook is WFC-managed
        """
        if not self.is_git_repo():
            return []

        status = []
        for hook_name in self.HOOK_SCRIPTS.keys():
            hook_path = self.hooks_dir / hook_name
            installed = hook_path.exists()
            enabled = False
            wfc_managed = False

            if installed:
                enabled = hook_path.stat().st_mode & 0o111 != 0
                try:
                    content = hook_path.read_text()
                    wfc_managed = (
                        "WFC-managed" in content or "wfc/wfc_tools/gitwork/hooks" in content
                    )
                except Exception:
                    pass

            status.append(
                {
                    "name": hook_name,
                    "installed": installed,
                    "enabled": enabled,
                    "wfc_managed": wfc_managed,
                }
            )

        return status

    def install_all(self) -> Dict[str, Any]:
        """
        Install all WFC hooks.

        Returns:
            Dict with:
                - success: bool
                - installed: List of installed hook names
                - failed: List of failed hook names
                - message: str
        """
        if not self.is_git_repo():
            return {
                "success": False,
                "installed": [],
                "failed": [],
                "message": "Not a git repository",
            }

        installed = []
        failed = []

        for hook_name, script_name in self.HOOK_SCRIPTS.items():
            result = self.install_hook(hook_name)
            if result["success"]:
                installed.append(hook_name)
            else:
                failed.append(hook_name)

        success = len(failed) == 0
        message = f"Installed {len(installed)}/{len(self.HOOK_SCRIPTS)} hooks"
        if failed:
            message += f" ({len(failed)} failed: {', '.join(failed)})"

        return {
            "success": success,
            "installed": installed,
            "failed": failed,
            "message": message,
        }

    def install_hook(self, hook_name: str) -> Dict[str, Any]:
        """
        Install a single WFC hook.

        Args:
            hook_name: Hook name (e.g., "pre-commit")

        Returns:
            Dict with success status and message
        """
        if hook_name not in self.HOOK_SCRIPTS:
            return {"success": False, "message": f"Unknown hook: {hook_name}"}

        script_name = self.HOOK_SCRIPTS[hook_name]
        hook_path = self.hooks_dir / hook_name

        try:
            # Create hooks directory if it doesn't exist
            self.hooks_dir.mkdir(parents=True, exist_ok=True)

            # Get Python executable path
            python_path = sys.executable

            # Get absolute path to hook script
            hook_script_path = self.wfc_hooks_dir / script_name

            # Create hook wrapper script
            hook_content = f"""#!/bin/bash
# WFC-managed hook - installed by WFC Hook Installer
# To uninstall: wfc hooks uninstall

# Run WFC hook
"{python_path}" "{hook_script_path}" "$@"
exit_code=$?

# WFC uses soft enforcement - always exit 0 to never block
exit 0
"""

            # Check if existing hook exists
            existing_content = ""
            if hook_path.exists():
                try:
                    existing_content = hook_path.read_text()
                    # Check if it's already WFC-managed
                    if "WFC-managed" in existing_content:
                        # Update existing WFC hook
                        hook_path.write_text(hook_content)
                        hook_path.chmod(0o755)
                        return {
                            "success": True,
                            "message": f"Updated {hook_name} hook",
                        }
                except Exception:
                    pass

                # Preserve existing hook by appending
                hook_content += f"\n# Original hook preserved below\n{existing_content}\n"

            # Write hook
            hook_path.write_text(hook_content)
            hook_path.chmod(0o755)

            return {"success": True, "message": f"Installed {hook_name} hook"}

        except Exception as e:
            return {"success": False, "message": f"Failed to install {hook_name}: {str(e)}"}

    def uninstall_all(self) -> Dict[str, Any]:
        """
        Uninstall all WFC hooks.

        Returns:
            Dict with success status and message
        """
        if not self.is_git_repo():
            return {
                "success": False,
                "uninstalled": [],
                "message": "Not a git repository",
            }

        uninstalled = []
        failed = []

        for hook_name in self.HOOK_SCRIPTS.keys():
            result = self.uninstall_hook(hook_name)
            if result["success"]:
                uninstalled.append(hook_name)
            else:
                failed.append(hook_name)

        success = len(failed) == 0
        message = f"Uninstalled {len(uninstalled)} hooks"
        if failed:
            message += f" ({len(failed)} failed: {', '.join(failed)})"

        return {
            "success": success,
            "uninstalled": uninstalled,
            "failed": failed,
            "message": message,
        }

    def uninstall_hook(self, hook_name: str) -> Dict[str, Any]:
        """
        Uninstall a single WFC hook.

        Args:
            hook_name: Hook name (e.g., "pre-commit")

        Returns:
            Dict with success status and message
        """
        hook_path = self.hooks_dir / hook_name

        if not hook_path.exists():
            return {"success": True, "message": f"{hook_name} hook not installed"}

        try:
            content = hook_path.read_text()

            # Check if it's WFC-managed
            if "WFC-managed" not in content:
                return {
                    "success": False,
                    "message": f"{hook_name} is not WFC-managed (skipped)",
                }

            # Check if there's a preserved original hook
            if "# Original hook preserved below" in content:
                # Extract and restore original hook
                parts = content.split("# Original hook preserved below")
                if len(parts) >= 2:
                    original_hook = parts[1].strip()
                    hook_path.write_text(original_hook)
                    hook_path.chmod(0o755)
                    return {
                        "success": True,
                        "message": f"Uninstalled {hook_name} hook (restored original)",
                    }

            # No original hook - remove completely
            hook_path.unlink()
            return {"success": True, "message": f"Uninstalled {hook_name} hook"}

        except Exception as e:
            return {"success": False, "message": f"Failed to uninstall {hook_name}: {str(e)}"}

    def print_status(self) -> None:
        """Print hook status in human-readable format."""
        if not self.is_git_repo():
            print("❌ Not a git repository")
            return

        status = self.get_hook_status()

        print("\nWFC Git Hooks Status\n" + "=" * 50)
        print()

        for hook in status:
            name = hook["name"]
            installed = "✅" if hook["installed"] else "❌"
            enabled = "✅" if hook["enabled"] else "❌"
            wfc_managed = "✅" if hook["wfc_managed"] else "❌"

            print(f"Hook: {name}")
            print(f"  Installed:    {installed}")
            print(f"  Executable:   {enabled}")
            print(f"  WFC-managed:  {wfc_managed}")
            print()

        # Summary
        total = len(status)
        wfc_count = sum(1 for h in status if h["wfc_managed"])

        print(f"Summary: {wfc_count}/{total} WFC hooks installed")
        print()


def main():
    """CLI entry point for hook installer."""
    import argparse

    parser = argparse.ArgumentParser(description="WFC Git Hooks Installer")
    parser.add_argument(
        "command",
        choices=["install", "uninstall", "status"],
        help="Command to execute",
    )
    parser.add_argument(
        "--hook",
        choices=list(HookInstaller.HOOK_SCRIPTS.keys()),
        help="Specific hook to install/uninstall (default: all)",
    )

    args = parser.parse_args()

    installer = HookInstaller()

    if args.command == "status":
        installer.print_status()
        return

    if args.command == "install":
        if args.hook:
            result = installer.install_hook(args.hook)
        else:
            result = installer.install_all()

        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
            sys.exit(1)

    elif args.command == "uninstall":
        if args.hook:
            result = installer.uninstall_hook(args.hook)
        else:
            result = installer.uninstall_all()

        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
            sys.exit(1)


if __name__ == "__main__":
    main()
