"""
Tests verifying the legacy 56-persona system has been cleanly deleted (TASK-015).

These tests confirm:
1. Persona Python modules are deleted
2. Persona JSONs are archived to .development/archive/personas/
3. No persona imports remain in the codebase
4. The review system works without personas
5. Legacy agents.py and consensus.py are retained (still used by plugin integration tests)
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


class TestPersonaPythonModulesDeleted:
    """Assert all legacy persona Python modules have been removed."""

    PERSONA_MODULES = [
        "wfc/scripts/personas/persona_orchestrator.py",
        "wfc/scripts/personas/persona_executor.py",
        "wfc/scripts/personas/ultra_minimal_prompts.py",
        "wfc/scripts/personas/file_reference_prompts.py",
        "wfc/scripts/personas/progressive_registry.py",
        "wfc/scripts/personas/token_manager.py",
        "wfc/scripts/personas/__init__.py",
    ]

    @pytest.mark.parametrize("module_path", PERSONA_MODULES)
    def test_persona_module_deleted(self, module_path):
        """Each legacy persona Python module must not exist."""
        full_path = REPO_ROOT / module_path
        assert not full_path.exists(), f"Legacy persona module still exists: {full_path}"

    def test_wfc_implement_token_manager_preserved(self):
        """wfc/scripts/token_manager.py (wfc-implement) must NOT be deleted."""
        path = REPO_ROOT / "wfc" / "scripts" / "token_manager.py"
        assert (
            path.exists()
        ), "wfc/scripts/token_manager.py (wfc-implement) was accidentally deleted"


class TestPersonaJsonsRemoved:
    """Assert legacy persona JSONs have been removed from the source tree."""

    def test_source_panels_removed(self):
        """Original persona panels directory must not exist."""
        panels_dir = REPO_ROOT / "wfc" / "references" / "personas" / "panels"
        assert not panels_dir.exists(), f"Persona panels still exist at {panels_dir}"

    def test_source_registry_removed(self):
        """Original registry files must not exist."""
        personas_dir = REPO_ROOT / "wfc" / "references" / "personas"
        assert not (personas_dir / "registry.json").exists(), "registry.json still in source"
        assert not (
            personas_dir / "registry-progressive.json"
        ).exists(), "registry-progressive.json still in source"


class TestNoPersonaImportsInCodebase:
    """Grep for persona imports in all .py files (excluding archive)."""

    def test_no_persona_module_imports(self):
        """No .py file in wfc/ or tests/ should import from wfc.scripts.personas."""
        search_dirs = [REPO_ROOT / "wfc", REPO_ROOT / "tests"]
        this_file = Path(__file__).resolve()
        violations = []

        for search_dir in search_dirs:
            for py_file in search_dir.rglob("*.py"):
                if "__pycache__" in str(py_file) or ".development" in str(py_file):
                    continue
                if py_file.resolve() == this_file:
                    continue
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                for line_num, line in enumerate(content.splitlines(), 1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if "from wfc.scripts.personas" in line or "import wfc.scripts.personas" in line:
                        violations.append(f"{py_file}:{line_num}: {stripped}")

        assert (
            violations == []
        ), f"Found {len(violations)} persona import(s) still in codebase:\n" + "\n".join(violations)

    def test_no_persona_test_files(self):
        """Legacy persona test files must be deleted."""
        assert not (
            REPO_ROOT / "wfc" / "personas" / "tests" / "test_persona_selection.py"
        ).exists(), "test_persona_selection.py still exists"
        assert not (
            REPO_ROOT / "tests" / "test_customer_advocate_persona.py"
        ).exists(), "test_customer_advocate_persona.py still exists"

    def test_no_persona_demo_scripts(self):
        """Legacy persona demo/benchmark scripts must be deleted."""
        assert not (
            REPO_ROOT / "examples" / "token_management_demo.py"
        ).exists(), "token_management_demo.py still exists"
        assert not (
            REPO_ROOT / "scripts" / "benchmark_tokens.py"
        ).exists(), "benchmark_tokens.py still exists"


class TestReviewSystemWorksWithoutPersonas:
    """Verify the review system operates without any persona dependencies."""

    def test_review_orchestrator_imports(self):
        """ReviewOrchestrator should import without persona dependencies."""
        from wfc.scripts.orchestrators.review.orchestrator import ReviewOrchestrator, ReviewRequest

        assert ReviewOrchestrator is not None
        assert ReviewRequest is not None

    def test_review_request_creation(self):
        """ReviewRequest should work without persona fields."""
        from wfc.scripts.orchestrators.review.orchestrator import ReviewRequest

        req = ReviewRequest(
            task_id="TASK-TEST",
            files=["test.py"],
            properties=[],
        )
        assert req.task_id == "TASK-TEST"

    def test_consensus_score_imports(self):
        """ConsensusScore (new system) should import without persona dependencies."""
        from wfc.scripts.orchestrators.review.consensus_score import ConsensusScore

        assert ConsensusScore is not None


class TestLegacyReviewCodeRetained:
    """
    agents.py and consensus.py are still used by test_plugin_integration.py
    for confidence filtering tests. They must be retained until those tests
    are migrated.
    """

    def test_legacy_agents_exists(self):
        """agents.py is retained (still used by plugin integration tests)."""
        path = REPO_ROOT / "wfc" / "scripts" / "orchestrators" / "review" / "agents.py"
        assert (
            path.exists()
        ), "agents.py was deleted but is still needed by test_plugin_integration.py"

    def test_legacy_consensus_exists(self):
        """consensus.py is retained (still used by plugin integration tests)."""
        path = REPO_ROOT / "wfc" / "scripts" / "orchestrators" / "review" / "consensus.py"
        assert (
            path.exists()
        ), "consensus.py was deleted but is still needed by test_plugin_integration.py"
