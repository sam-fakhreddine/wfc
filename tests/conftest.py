#!/usr/bin/env python3
"""
PyTest configuration and shared fixtures for WFC tests.
"""

import sys
from pathlib import Path

import pytest

# Add WFC to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def wfc_scripts_dir(project_root):
    """Get WFC scripts directory."""
    return project_root / "wfc" / "scripts"


@pytest.fixture(scope="session")
def wfc_skills_dir(project_root):
    """Get WFC skills directory."""
    return project_root / "wfc" / "skills"


@pytest.fixture
def sample_task_simple():
    """Sample simple task for testing."""
    return {
        "id": "TASK-SIMPLE",
        "description": "Add logging to existing function",
        "acceptance_criteria": [
            "Logs function entry",
            "Logs function exit",
            "Uses Python logging module",
        ],
        "complexity": "S",
        "files_likely_affected": ["src/utils.py"],
        "test_requirements": ["Test logging output"],
        "dependencies": [],
    }


@pytest.fixture
def sample_task_complex():
    """Sample complex task for testing."""
    return {
        "id": "TASK-COMPLEX",
        "description": "Implement distributed caching layer with Redis",
        "acceptance_criteria": [
            "Redis client configured",
            "Cache hit/miss metrics tracked",
            "Supports TTL configuration",
            "Handles connection failures gracefully",
        ],
        "complexity": "XL",
        "files_likely_affected": [
            "src/cache/redis.py",
            "src/cache/metrics.py",
            "tests/test_cache.py",
        ],
        "test_requirements": [
            "Test cache operations",
            "Test TTL expiration",
            "Test connection failure handling",
        ],
        "dependencies": ["TASK-001", "TASK-002"],
    }


@pytest.fixture
def sample_task_vague():
    """Sample vague task (should have low confidence)."""
    return {
        "id": "TASK-VAGUE",
        "description": "Make it better",
        "acceptance_criteria": [],
        "complexity": "M",
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "slow: Slow tests (> 1 second)")
