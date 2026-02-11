"""
Project scanner - detects language, frameworks, tooling
"""

from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass


@dataclass
class ProjectProfile:
    """Detected project profile"""
    project_type: str
    languages: List[str]
    package_manager: str
    frameworks: List[str]
    has_docker: bool
    has_ci: str
    test_command: str
    build_command: str
    directories: Dict[str, List[str]]


class ProjectScanner:
    """Scans project to detect profile"""
    
    def scan(self, project_path: Path = Path.cwd()) -> ProjectProfile:
        """Scan project and return profile"""
        
        languages = self._detect_languages(project_path)
        package_manager = self._detect_package_manager(project_path)
        frameworks = self._detect_frameworks(project_path)
        has_docker = self._detect_docker(project_path)
        has_ci = self._detect_ci(project_path)
        
        # Determine project type
        if "typescript" in languages or "javascript" in languages:
            project_type = "nodejs"
        elif "python" in languages:
            project_type = "python"
        elif "rust" in languages:
            project_type = "rust"
        elif "go" in languages:
            project_type = "go"
        else:
            project_type = "unknown"
        
        return ProjectProfile(
            project_type=project_type,
            languages=languages,
            package_manager=package_manager,
            frameworks=frameworks,
            has_docker=has_docker,
            has_ci=has_ci,
            test_command=self._detect_test_command(project_path, project_type),
            build_command=self._detect_build_command(project_path, project_type),
            directories=self._detect_directories(project_path)
        )
    
    def _detect_languages(self, path: Path) -> List[str]:
        """Detect programming languages"""
        languages = set()
        
        if (path / "package.json").exists():
            languages.add("javascript")
        if (path / "tsconfig.json").exists():
            languages.add("typescript")
        if (path / "pyproject.toml").exists() or (path / "requirements.txt").exists():
            languages.add("python")
        if (path / "Cargo.toml").exists():
            languages.add("rust")
        if (path / "go.mod").exists():
            languages.add("go")
        
        return list(languages)
    
    def _detect_package_manager(self, path: Path) -> str:
        """Detect package manager"""
        if (path / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (path / "yarn.lock").exists():
            return "yarn"
        if (path / "package-lock.json").exists():
            return "npm"
        if (path / "Pipfile").exists():
            return "pipenv"
        if (path / "poetry.lock").exists():
            return "poetry"
        return "unknown"
    
    def _detect_frameworks(self, path: Path) -> List[str]:
        """Detect frameworks"""
        frameworks = []
        
        package_json = path / "package.json"
        if package_json.exists():
            try:
                import json
                data = json.loads(package_json.read_text())
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                
                if "next" in deps:
                    frameworks.append("next.js")
                if "react" in deps:
                    frameworks.append("react")
                if "vue" in deps:
                    frameworks.append("vue")
                if "express" in deps:
                    frameworks.append("express")
                if "jest" in deps:
                    frameworks.append("jest")
                if "vitest" in deps:
                    frameworks.append("vitest")
            except:
                pass
        
        return frameworks
    
    def _detect_docker(self, path: Path) -> bool:
        """Detect Docker usage"""
        return (path / "Dockerfile").exists() or (path / "docker-compose.yml").exists()
    
    def _detect_ci(self, path: Path) -> str:
        """Detect CI/CD"""
        if (path / ".github" / "workflows").exists():
            return "github-actions"
        if (path / ".gitlab-ci.yml").exists():
            return "gitlab-ci"
        if (path / ".circleci").exists():
            return "circleci"
        return "none"
    
    def _detect_test_command(self, path: Path, project_type: str) -> str:
        """Detect test command"""
        if project_type == "nodejs":
            return "npm test"
        elif project_type == "python":
            return "pytest"
        elif project_type == "rust":
            return "cargo test"
        elif project_type == "go":
            return "go test ./..."
        return ""
    
    def _detect_build_command(self, path: Path, project_type: str) -> str:
        """Detect build command"""
        if project_type == "nodejs":
            return "npm run build"
        elif project_type == "rust":
            return "cargo build"
        elif project_type == "go":
            return "go build"
        return ""
    
    def _detect_directories(self, path: Path) -> Dict[str, List[str]]:
        """Detect directory structure"""
        dirs = {
            "source": [],
            "tests": [],
            "config": [],
            "generated": []
        }
        
        for d in path.iterdir():
            if not d.is_dir() or d.name.startswith("."):
                continue
            
            name = d.name
            if name in ["src", "lib", "app"]:
                dirs["source"].append(name + "/")
            elif name in ["tests", "test", "__tests__", "spec"]:
                dirs["tests"].append(name + "/")
            elif name in ["config", ".github", ".vscode"]:
                dirs["config"].append(name + "/")
            elif name in ["dist", "build", "node_modules", "target", "__pycache__"]:
                dirs["generated"].append(name + "/")
        
        return dirs
