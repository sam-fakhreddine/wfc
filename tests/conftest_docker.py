"""Pytest fixtures for Docker-based installer testing."""

import pytest
import subprocess
from pathlib import Path


@pytest.fixture(scope="session")
def docker_installer_image(request):
    """Build Docker image for installer testing once per session."""
    print("\n🔨 Building Docker image for installer tests...")

    dockerfile = Path(__file__).parent / "Dockerfile.installer-test"
    result = subprocess.run(
        ["docker", "build", "-t", "wfc-installer-test", "-f", dockerfile, "."],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        pytest.fail(f"Failed to build Docker image: {result.stderr}")

    print("✅ Docker image built")

    # Store container IDs for cleanup
    container_ids = []

    def cleanup():
        print("\n🧹 Cleaning up Docker resources...")
        # Stop any running containers
        subprocess.run(["docker", "ps", "-aq", "--filter", "name=wfc-test"], capture_output=True)
        # Remove containers
        for cid in container_ids:
            subprocess.run(["docker", "rm", "-f", cid], capture_output=True)
        # Remove image
        subprocess.run(["docker", "rmi", "wfc-installer-test"], capture_output=True)
        print("✅ Cleanup complete")

    request.addfinalizer(cleanup)

    # Return fixture function that builds image
    def build_image():
        return "wfc-installer-test"

    return build_image


@pytest.fixture
def docker_container(docker_installer_image):
    """Create a Docker container for testing."""
    container_name = f"wfc-test-{pytest.root.nodeid}"
    result = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "-v",
            f"{Path.cwd()}:/wfc",
            docker_installer_image(),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        pytest.fail(f"Failed to start container: {result.stderr}")

    return container_name
