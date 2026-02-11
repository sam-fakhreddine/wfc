"""
Branch operations API

Conservative type classification: chore by default, feat only for new user-facing capability.
"""

import subprocess
import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class BranchResult:
    """Result of branch operation"""
    branch_name: str
    created_from: str
    type_classified: str
    success: bool
    message: str


class BranchOperations:
    """Branch operations for WFC"""
    
    PROTECTED_BRANCHES = ["main", "master", "develop", "production"]
    
    def create(self, task_id: str, title: str, base_ref: str = "main", 
               type_override: Optional[str] = None) -> BranchResult:
        """
        Create branch for task.
        
        Conservative type classification:
        - chore: default for everything internal/plumbing
        - feat: only for NEW user-facing features
        - fix: bug fixes
        - refactor: code restructuring
        - test: test additions
        - security: security fixes
        """
        # Classify type (conservative)
        if type_override:
            branch_type = type_override
        else:
            branch_type = self._classify_type(title)
        
        # Create slug from title
        slug = self._slugify(title)
        
        # Format branch name
        branch_name = f"{branch_type}/{task_id}-{slug}"
        
        try:
            # Create branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name, base_ref],
                check=True,
                capture_output=True
            )
            
            return BranchResult(
                branch_name=branch_name,
                created_from=base_ref,
                type_classified=branch_type,
                success=True,
                message=f"Created branch {branch_name} from {base_ref}"
            )
        except subprocess.CalledProcessError as e:
            return BranchResult(
                branch_name=branch_name,
                created_from=base_ref,
                type_classified=branch_type,
                success=False,
                message=f"Failed to create branch: {e.stderr.decode()}"
            )
    
    def delete(self, branch_name: str, force: bool = False) -> Dict:
        """Delete branch with safety checks"""
        # Never delete protected branches
        if branch_name in self.PROTECTED_BRANCHES:
            return {
                "success": False,
                "message": f"Cannot delete protected branch: {branch_name}"
            }
        
        try:
            flag = "-D" if force else "-d"
            subprocess.run(
                ["git", "branch", flag, branch_name],
                check=True,
                capture_output=True
            )
            return {
                "success": True,
                "message": f"Deleted branch {branch_name}"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": f"Failed to delete: {e.stderr.decode()}"
            }
    
    def list(self, filter_type: str = "all") -> List[Dict]:
        """List branches"""
        try:
            result = subprocess.run(
                ["git", "branch", "-a"],
                check=True,
                capture_output=True,
                text=True
            )
            branches = [b.strip().replace("* ", "") for b in result.stdout.split("\n") if b.strip()]
            
            if filter_type == "wfc":
                branches = [b for b in branches if "/TASK-" in b]
            elif filter_type == "human":
                branches = [b for b in branches if "/TASK-" not in b]
            
            return [{"name": b} for b in branches]
        except subprocess.CalledProcessError:
            return []
    
    def validate_name(self, name: str) -> Dict:
        """Validate branch name against convention"""
        pattern = r'^(feat|fix|chore|refactor|test|security|hotfix)/TASK-\d{3}-.+$'
        valid = bool(re.match(pattern, name))
        
        violations = []
        if not valid:
            violations.append(f"Branch name must match pattern: {pattern}")
        
        return {
            "valid": valid,
            "violations": violations
        }
    
    def _classify_type(self, title: str) -> str:
        """
        Conservative type classification.
        
        Default: chore (infrastructure, plumbing, internal)
        feat: ONLY for NEW user-facing features
        """
        title_lower = title.lower()
        
        # Explicit feature indicators
        if any(word in title_lower for word in ["add new", "new feature", "user can"]):
            return "feat"
        
        # Bug fixes
        if any(word in title_lower for word in ["fix", "bug", "issue", "error"]):
            return "fix"
        
        # Security
        if any(word in title_lower for word in ["security", "vulnerability", "cve"]):
            return "security"
        
        # Tests
        if any(word in title_lower for word in ["test", "spec", "coverage"]):
            return "test"
        
        # Refactoring
        if any(word in title_lower for word in ["refactor", "restructure", "cleanup"]):
            return "refactor"
        
        # Default: chore (conservative)
        return "chore"
    
    def _slugify(self, text: str, max_length: int = 40) -> str:
        """Convert title to slug"""
        slug = text.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = slug[:max_length].strip('-')
        return slug


# Singleton instance
_instance = BranchOperations()

def create(task_id: str, title: str, base_ref: str = "main", 
           type_override: Optional[str] = None) -> BranchResult:
    """Create branch"""
    return _instance.create(task_id, title, base_ref, type_override)

def delete(branch_name: str, force: bool = False) -> Dict:
    """Delete branch"""
    return _instance.delete(branch_name, force)

def list(filter_type: str = "all") -> List[Dict]:
    """List branches"""
    return _instance.list(filter_type)

def validate_name(name: str) -> Dict:
    """Validate branch name"""
    return _instance.validate_name(name)
