"""
Hooks operations API

Install and manage git hooks without replacing existing ones.
"""

import subprocess
from pathlib import Path
from typing import Dict, List


def install(hook_type: str, script: str) -> Dict:
    """Install git hook"""
    hook_path = Path(".git/hooks") / hook_type
    
    try:
        # Create hook file
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text(script)
        hook_path.chmod(0o755)
        
        return {
            "success": True,
            "message": f"Installed {hook_type} hook"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to install: {str(e)}"
        }


def manage() -> List[Dict]:
    """List installed hooks"""
    hooks_dir = Path(".git/hooks")
    if not hooks_dir.exists():
        return []
    
    hooks = []
    for hook_file in hooks_dir.glob("*"):
        if hook_file.is_file() and not hook_file.name.endswith(".sample"):
            hooks.append({
                "name": hook_file.name,
                "enabled": hook_file.stat().st_mode & 0o111 != 0
            })
    
    return hooks


def wrap(hook_type: str, new_script: str) -> Dict:
    """Wrap existing hook (never replace)"""
    hook_path = Path(".git/hooks") / hook_type
    
    try:
        existing = ""
        if hook_path.exists():
            existing = hook_path.read_text()
        
        # Combine scripts
        wrapped = f"""#!/bin/bash
# WFC-managed hook
{new_script}

# Original hook
{existing}
"""
        hook_path.write_text(wrapped)
        hook_path.chmod(0o755)
        
        return {
            "success": True,
            "message": f"Wrapped {hook_type} hook"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to wrap: {str(e)}"
        }
