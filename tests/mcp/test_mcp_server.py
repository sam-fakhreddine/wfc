"""
Phase 2A - TASK-014 Tests
Test MCP server initialization, tools, resources, and multi-tenant support.
"""

import json
import pytest
from unittest.mock import AsyncMock, Mock, patch
from mcp.server import Server
from mcp.types import TextContent

try:
    from wfc.servers.mcp_server import WFCMCPServer
except ImportError:
    WFCMCPServer = None


@pytest.mark.skipif(WFCMCPServer is None, reason="WFCMCPServer not implemented yet")
class TestWFCMCPServer:
    """Test WFC MCP server infrastructure."""

    def test_server_initialization(self):
        """Server should initialize with name and description."""
        server = WFCMCPServer()

        assert server.app is not None
        assert isinstance(server.app, Server)
        assert server.app.name == "wfc-mcp"

    @pytest.mark.asyncio
    async def test_list_tools_returns_review_tool(self):
        """Server should expose review_code tool."""
        server = WFCMCPServer()

        tools = await server.list_tools()

        assert len(tools) >= 1
        review_tool = next((t for t in tools if t.name == "review_code"), None)
        assert review_tool is not None
        assert "review" in review_tool.description.lower()
        assert "inputSchema" in review_tool.model_dump()

    @pytest.mark.asyncio
    async def test_list_resources_returns_review_resources(self):
        """Server should expose review:// resources."""
        server = WFCMCPServer()

        resources = await server.list_resources()

        assert len(resources) >= 1
        review_resource = next((r for r in resources if str(r.uri).startswith("review://")), None)
        assert review_resource is not None

    @pytest.mark.asyncio
    async def test_call_tool_review_code_with_project_context(self, tmp_path):
        """review_code tool should create ProjectContext and run review."""
        server = WFCMCPServer()

        with patch("wfc.servers.mcp_server.ReviewOrchestrator") as mock_orch_class:
            mock_orch = AsyncMock()
            mock_orch.review_code = AsyncMock(
                return_value={"consensus_score": 8.5, "passed": True, "findings": []}
            )
            mock_orch_class.return_value = mock_orch

            result = await server.call_tool(
                name="review_code",
                arguments={
                    "project_id": "test-proj",
                    "developer_id": "alice",
                    "diff_content": "some diff",
                    "files": ["test.py"],
                },
            )

            mock_orch_class.assert_called_once()
            call_kwargs = mock_orch_class.call_args[1]
            assert "project_context" in call_kwargs
            assert call_kwargs["project_context"].project_id == "test-proj"

            assert len(result) == 1
            assert isinstance(result[0], TextContent)

            result_data = json.loads(result[0].text)
            assert result_data["project_id"] == "test-proj"
            assert result_data["developer_id"] == "alice"

    @pytest.mark.asyncio
    async def test_call_tool_review_code_backward_compat(self):
        """review_code should work without project_id (backward compat)."""
        server = WFCMCPServer()

        with patch("wfc.servers.mcp_server.ReviewOrchestrator") as mock_orch_class:
            mock_orch = AsyncMock()
            mock_orch.review_code = AsyncMock(
                return_value={"consensus_score": 7.5, "passed": True, "findings": []}
            )
            mock_orch_class.return_value = mock_orch

            result = await server.call_tool(
                name="review_code", arguments={"diff_content": "some diff", "files": ["test.py"]}
            )

            mock_orch_class.assert_called_once()
            call_kwargs = mock_orch_class.call_args[1]
            assert call_kwargs.get("project_context") is None

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_read_resource_review_latest(self, tmp_path):
        """read_resource should return latest review data."""
        server = WFCMCPServer()

        output_dir = tmp_path / ".wfc" / "output" / "test-proj"
        output_dir.mkdir(parents=True)
        review_file = output_dir / "REVIEW-test-proj.md"
        review_file.write_text("# Review Results\nCS: 8.5")

        with patch("wfc.servers.mcp_server.Path") as mock_path:
            mock_path.return_value = tmp_path

            content = await server.read_resource("review://project/test-proj/latest")

            assert "8.5" in content or "test-proj" in content

    @pytest.mark.asyncio
    async def test_server_handles_rate_limiting(self):
        """Server should enforce rate limits via TokenBucket."""
        with patch("wfc.servers.mcp_server.TokenBucket") as mock_bucket_class:
            mock_bucket = Mock()
            mock_bucket.acquire.side_effect = [True, False]
            mock_bucket_class.return_value = mock_bucket

            server = WFCMCPServer()

            with patch("wfc.servers.mcp_server.ReviewOrchestrator") as mock_orch_class:
                mock_orch = AsyncMock()
                mock_orch.review_code = AsyncMock(return_value={"passed": True})
                mock_orch_class.return_value = mock_orch

                result1 = await server.call_tool("review_code", {"diff_content": "diff1"})
                assert len(result1) == 1
                assert "rate limit" not in result1[0].text.lower()

                result2 = await server.call_tool("review_code", {"diff_content": "diff2"})
                assert len(result2) == 1
                assert "rate limit" in result2[0].text.lower()

    def test_server_creates_worktree_pool(self):
        """Server should initialize WorktreePool for resource management."""
        server = WFCMCPServer()

        assert hasattr(server, "worktree_pool")
        assert server.worktree_pool is not None

    @pytest.mark.asyncio
    async def test_server_cleanup_on_shutdown(self):
        """Server should cleanup resources on shutdown."""
        server = WFCMCPServer()

        server.worktree_pool = Mock()
        server.worktree_pool.cleanup_all = Mock()

        await server.cleanup()

        server.worktree_pool.cleanup_all.assert_called_once()
