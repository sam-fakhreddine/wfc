"""Test suite for WFC Universal Installer using Docker."""

import subprocess
import pytest


class TestInstaller:
    """Test suite for WFC installer."""

    @pytest.fixture(scope="class")
    def docker_container(self, request):
        """Build and create a Docker container for testing."""
        container_id = None

        def cleanup():
            if container_id:
                subprocess.run(
                    ["docker", "rm", "-f", container_id],
                    capture_output=True,
                    stderr=subprocess.DEVNULL,
                )

        request.addfinalizer(cleanup)

        # Build image first
        result = subprocess.run(
            [
                "docker",
                "build",
                "-t",
                "wfc-installer-test",
                "-f",
                "tests/Dockerfile.installer-test",
                ".",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.fail(f"Failed to build Docker image: {result.stderr}")

        return "wfc-installer-test"

    def test_installer_executable(self, docker_container):
        """Test that install-universal.sh is executable."""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                docker_container,
                "bash",
                "-c",
                "test -x /wfc/install-universal.sh",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "install-universal.sh not executable"
        print("✓ Installer is executable")

    def test_help_flag(self, docker_container):
        """Test --help flag works."""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                docker_container,
                "bash",
                "-c",
                "cd /wfc && ./install-universal.sh --help | grep WFC",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "Help flag failed"
        assert "WFC Universal" in result.stdout, "Help output incorrect"
        print("✓ Help flag works")

    def test_version_defined(self, docker_container):
        """Test VERSION is defined in installer."""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                docker_container,
                "bash",
                "-c",
                "grep 'VERSION=' /wfc/install-universal.sh | cut -d'\"' -f2",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "Version check failed"
        version = result.stdout.strip()
        assert version, "Version not defined"
        print(f"✓ Version defined: {version}")

    def test_skills_source_path(self, docker_container):
        """Test skills source path is wfc/skills."""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                docker_container,
                "bash",
                "-c",
                "grep -q 'wfc/skills.*wfc-' /wfc/install-universal.sh",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "Skills source path incorrect"
        print("✓ Skills source path is wfc/skills")

    def test_ci_mode_logic(self, docker_container):
        """Test CI mode logic exists in installer."""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                docker_container,
                "bash",
                "-c",
                "grep -q '\\[ \"\\$CI_MODE\" = true \\]' /wfc/install-universal.sh",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "CI mode logic missing"
        print("✓ CI mode logic present")

    def test_docker_ci_install(self, docker_container):
        """Test CI mode installation in Docker."""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                docker_container,
                "bash",
                "-c",
                "cd /wfc && ./install-universal.sh --ci",
            ],
            capture_output=True,
            text=True,
        )

        # Check for "Installation complete" message
        assert result.returncode == 0, f"CI install failed: {result.stderr}"
        assert (
            "Installation complete" in result.stdout or "✓ Installation complete" in result.stdout
        ), "Installation completion message missing"
        print("✓ CI mode installation successful")

    def test_skills_installed(self, docker_container):
        """Test skills are installed to correct location."""
        skills = [
            "wfc-review",
            "wfc-implement",
            "wfc-plan",
            "wfc-architecture",
            "wfc-test",
            "wfc-security",
            "wfc-observe",
        ]

        missing_skills = []
        for skill in skills:
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    docker_container,
                    "bash",
                    "-c",
                    f"[ -d /root/.claude/skills/{skill} ] && echo 'exists'",
                ],
                capture_output=True,
                text=True,
            )

            if result.stdout.strip() != "exists":
                missing_skills.append(skill)
            else:
                print(f"  ✓ {skill} installed")

        assert not missing_skills, f"Missing skills: {', '.join(missing_skills)}"
        print(f"✓ All {len(skills)} core skills installed")

    def test_no_nested_structure(self, docker_container):
        """Test that skills are not nested in wfc/skills/."""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                docker_container,
                "bash",
                "-c",
                "[ ! -d /root/.claude/skills/wfc/skills ] && echo 'no-nested' || echo 'nested'",
            ],
            capture_output=True,
            text=True,
        )

        assert result.stdout.strip() == "no-nested", "Nested structure bug found!"
        print("✓ No incorrect nested wfc/skills/ directory")

    def test_shared_personas(self, docker_container):
        """Test shared personas directory exists."""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                docker_container,
                "bash",
                "-c",
                "[ -d /root/.claude/skills/wfc/personas ] && echo 'exists' || echo 'missing'",
            ],
            capture_output=True,
            text=True,
        )

        assert result.stdout.strip() == "exists", "Shared personas missing"
        print("✓ Shared personas directory exists")

    def test_branding_config(self, docker_container):
        """Test branding config file is created."""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                docker_container,
                "bash",
                "-c",
                "[ -f /root/.claude/skills/.wfc_branding ] && grep -q 'mode=' /root/.claude/skills/.wfc_branding",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "Branding config not created"
        print("✓ Branding config created with mode=")

    def test_skill_count(self, docker_container):
        """Test all 12 skills are installed."""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                docker_container,
                "bash",
                "-c",
                "find /root/.claude/skills/wfc-*/SKILL.md -type f | wc -l",
            ],
            capture_output=True,
            text=True,
        )

        skill_count = int(result.stdout.strip())
        assert skill_count >= 12, f"Only {skill_count} skills found (expected >= 12)"
        print(f"✓ Found {skill_count} skill markdown files")
