"""
Performance tests for parallel batch processing (TASK-006).

Verifies that batch processing with ThreadPoolExecutor achieves
near-constant time complexity O(1) instead of linear O(N).
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from wfc_prompt_fixer.orchestrator import PromptFixerOrchestrator
from wfc_prompt_fixer.workspace import WorkspaceManager


class TestBatchPerformance:
    """Test parallel batch processing performance (PROP-008)."""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator with temp workspace."""
        workspace_mgr = WorkspaceManager(base_dir=tmp_path / ".development" / "prompt-fixer")
        orch = PromptFixerOrchestrator(cwd=tmp_path)
        orch.workspace_manager = workspace_mgr
        return orch

    @pytest.fixture
    def mock_prompts(self, tmp_path):
        """Create 4 test prompt files."""
        prompts = []
        for i in range(4):
            prompt = tmp_path / f"test_prompt_{i}.md"
            prompt.write_text(f"# Test Prompt {i}\n\nContent here.")
            prompts.append(prompt)
        return prompts

    def test_parallel_batch_execution_time(self, orchestrator, mock_prompts, tmp_path, monkeypatch):
        """
        Verify parallel batch processes 4 prompts in ~1x time, not 4x.

        PROP-008: Batch processing must use parallel execution.
        Expected: 4 prompts with 1s delay each = ~1.5s total (not 4s)
        Tolerance: Allow up to 2.5s to account for overhead
        """
        monkeypatch.chdir(tmp_path)

        def mock_fix_prompt_with_delay(prompt_path, **kwargs):
            """Simulate 1 second processing time per prompt."""
            time.sleep(1.0)
            return MagicMock(
                prompt_name=prompt_path.name,
                grade_before="C",
                grade_after="A",
                report_path=tmp_path / "report.md",
                workspace=tmp_path / "workspace",
            )

        with patch.object(
            orchestrator, "fix_prompt", side_effect=mock_fix_prompt_with_delay
        ) as mock_fix:
            start_time = time.time()

            pattern = "./test_prompt_*.md"
            results = orchestrator.fix_batch(
                pattern=pattern, wfc_mode=False, auto_pr=False, keep_workspace=False
            )

            elapsed = time.time() - start_time

            assert len(results) == 4
            assert mock_fix.call_count == 4

            assert (
                elapsed < 2.5
            ), f"Batch took {elapsed:.2f}s (expected <2.5s). Parallel execution failed."
            print(f"✓ Parallel batch completed in {elapsed:.2f}s (4 prompts @ 1s each)")

    def test_workspace_naming_uniqueness(self, orchestrator, tmp_path):
        """
        Verify workspace names include microseconds + UUID for uniqueness.

        TASK-006: Workspace naming must prevent collisions in parallel execution.
        Format: {prompt_name}-{timestamp_with_microseconds}-{uuid8}
        """
        prompt = tmp_path / "test.md"
        prompt.write_text("# Test")

        workspaces = []
        for _ in range(10):
            workspace = orchestrator.workspace_manager.create(prompt, wfc_mode=False)
            workspaces.append(workspace.name)

        assert len(workspaces) == len(set(workspaces)), "Workspace name collision detected"

        for ws_name in workspaces:
            parts = ws_name.split("-")
            assert len(parts) >= 4, f"Invalid format: {ws_name}"

            timestamp_part = parts[1] + parts[2]
            assert len(timestamp_part) >= 20, f"Timestamp missing microseconds: {ws_name}"

            uuid_part = parts[-1]
            assert len(uuid_part) == 8, f"UUID suffix not 8 chars: {ws_name}"
            assert all(c in "0123456789abcdef" for c in uuid_part), f"UUID not hex: {ws_name}"

    def test_partial_results_on_batch_failure(
        self, orchestrator, mock_prompts, tmp_path, monkeypatch
    ):
        """
        Verify batch returns partial results when some prompts fail.

        TASK-006: Error handling must preserve partial results.
        If 2/4 prompts fail, should return 2 successful results (not fail entire batch).
        """
        monkeypatch.chdir(tmp_path)

        call_count = [0]

        def mock_fix_with_failures(prompt_path, **kwargs):
            """Fail every other prompt."""
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                raise RuntimeError(f"Simulated failure for {prompt_path.name}")

            return MagicMock(
                prompt_name=prompt_path.name,
                grade_before="D",
                grade_after="B",
                report_path=tmp_path / "report.md",
                workspace=tmp_path / "workspace",
            )

        with patch.object(orchestrator, "fix_prompt", side_effect=mock_fix_with_failures):
            pattern = "./test_prompt_*.md"
            results = orchestrator.fix_batch(
                pattern=pattern, wfc_mode=False, auto_pr=False, keep_workspace=False
            )

            assert len(results) == 2, f"Expected 2 partial results, got {len(results)}"
            assert all(r.grade_after == "B" for r in results)

    def test_batch_size_limits_concurrency(self, orchestrator, tmp_path, monkeypatch):
        """
        Verify batch_size=4 limits concurrent execution to 4 workers.

        TASK-006: ThreadPoolExecutor should use max_workers=4 (batch_size).
        """
        monkeypatch.chdir(tmp_path)

        prompts = []
        for i in range(8):
            prompt = tmp_path / f"prompt_{i}.md"
            prompt.write_text(f"# Prompt {i}")
            prompts.append(prompt)

        active_workers = []
        max_concurrent = [0]

        def mock_fix_tracking_concurrency(prompt_path, **kwargs):
            """Track maximum concurrent executions."""
            active_workers.append(1)
            current_count = len(active_workers)
            max_concurrent[0] = max(max_concurrent[0], current_count)

            time.sleep(0.1)

            active_workers.pop()
            return MagicMock(
                prompt_name=prompt_path.name,
                grade_before="F",
                grade_after="A",
                report_path=tmp_path / "report.md",
                workspace=tmp_path / "workspace",
            )

        with patch.object(orchestrator, "fix_prompt", side_effect=mock_fix_tracking_concurrency):
            pattern = "./prompt_*.md"
            results = orchestrator.fix_batch(
                pattern=pattern, wfc_mode=False, auto_pr=False, keep_workspace=False
            )

            assert len(results) == 8
            assert (
                max_concurrent[0] <= 4
            ), f"Too many concurrent workers: {max_concurrent[0]} (expected ≤4)"
            print(f"✓ Max concurrent workers: {max_concurrent[0]} (limit: 4)")
