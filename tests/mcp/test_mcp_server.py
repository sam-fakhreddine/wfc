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
        api_keys_path = tmp_path / "api_keys.json"
        server = WFCMCPServer(api_keys_path=api_keys_path)

        api_key = server.api_key_store.create_api_key("test-proj", "alice")

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
                    "api_key": api_key,
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
        """review_code should reject requests without authentication (no backward compat)."""
        server = WFCMCPServer()

        result = await server.call_tool(
            name="review_code", arguments={"diff_content": "some diff", "files": ["test.py"]}
        )

        assert len(result) == 1
        result_data = json.loads(result[0].text)
        assert "error" in result_data
        assert (
            "project_id" in result_data["error"].lower()
            or "authentication" in result_data["error"].lower()
        )

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
    async def test_server_handles_rate_limiting(self, tmp_path):
        """Server should enforce rate limits via TokenBucket."""
        api_keys_path = tmp_path / "api_keys.json"

        with patch("wfc.servers.mcp_server.TokenBucket") as mock_bucket_class:
            mock_bucket = Mock()
            mock_bucket.acquire.side_effect = [True, False]
            mock_bucket_class.return_value = mock_bucket

            server = WFCMCPServer(api_keys_path=api_keys_path)
            api_key = server.api_key_store.create_api_key("test-proj", "alice")

            with patch("wfc.servers.mcp_server.ReviewOrchestrator") as mock_orch_class:
                mock_orch = AsyncMock()
                mock_orch.review_code = AsyncMock(return_value={"passed": True})
                mock_orch_class.return_value = mock_orch

                result1 = await server.call_tool(
                    "review_code",
                    {"project_id": "test-proj", "api_key": api_key, "diff_content": "diff1"},
                )
                assert len(result1) == 1
                assert "rate limit" not in result1[0].text.lower()

                result2 = await server.call_tool(
                    "review_code",
                    {"project_id": "test-proj", "api_key": api_key, "diff_content": "diff2"},
                )
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


@pytest.mark.skipif(WFCMCPServer is None, reason="WFCMCPServer not implemented yet")
class TestMCPAuthentication:
    """Test MCP server authentication (Issue #64)."""

    def test_server_initializes_with_api_key_store(self, tmp_path):
        """Server should initialize with APIKeyStore for authentication."""
        api_keys_path = tmp_path / "api_keys.json"
        server = WFCMCPServer(api_keys_path=api_keys_path)

        assert hasattr(server, "api_key_store")
        assert server.api_key_store is not None

    @pytest.mark.asyncio
    async def test_call_tool_rejects_missing_api_key(self):
        """Tool calls without API key should be rejected."""
        server = WFCMCPServer()

        result = await server.call_tool(
            name="review_code",
            arguments={
                "project_id": "test-proj",
                "diff_content": "some diff",
            },
        )

        assert len(result) == 1
        result_data = json.loads(result[0].text)
        assert "error" in result_data
        assert (
            "authentication" in result_data["error"].lower()
            or "api key" in result_data["error"].lower()
        )

    @pytest.mark.asyncio
    async def test_call_tool_rejects_invalid_api_key(self, tmp_path):
        """Tool calls with invalid API key should be rejected."""
        api_keys_path = tmp_path / "api_keys.json"
        server = WFCMCPServer(api_keys_path=api_keys_path)

        server.api_key_store.create_api_key("test-proj", "alice")

        result = await server.call_tool(
            name="review_code",
            arguments={
                "project_id": "test-proj",
                "api_key": "invalid-key",  # pragma: allowlist secret
                "diff_content": "some diff",
            },
        )

        assert len(result) == 1
        result_data = json.loads(result[0].text)
        assert "error" in result_data
        assert (
            "authentication" in result_data["error"].lower()
            or "invalid" in result_data["error"].lower()
        )

    @pytest.mark.asyncio
    async def test_call_tool_accepts_valid_api_key(self, tmp_path):
        """Tool calls with valid API key should be accepted."""
        api_keys_path = tmp_path / "api_keys.json"
        server = WFCMCPServer(api_keys_path=api_keys_path)

        api_key = server.api_key_store.create_api_key("test-proj", "alice")

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
                    "api_key": api_key,
                    "diff_content": "some diff",
                    "files": ["test.py"],
                },
            )

            assert len(result) == 1
            result_data = json.loads(result[0].text)
            assert "error" not in result_data or result_data.get("failed") is not True
            assert result_data["project_id"] == "test-proj"

    @pytest.mark.asyncio
    async def test_authentication_failures_logged_to_audit(self, tmp_path):
        """Failed authentication attempts should be logged to audit trail."""
        api_keys_path = tmp_path / "api_keys.json"
        audit_path = tmp_path / "audit" / "auth.jsonl"
        server = WFCMCPServer(api_keys_path=api_keys_path, audit_log_path=audit_path)

        server.api_key_store.create_api_key("test-proj", "alice")

        await server.call_tool(
            name="review_code",
            arguments={
                "project_id": "test-proj",
                "api_key": "invalid-key",  # pragma: allowlist secret
                "diff_content": "some diff",
            },
        )

        assert audit_path.exists()
        audit_content = audit_path.read_text()
        assert "failure" in audit_content
        assert "test-proj" in audit_content

    @pytest.mark.asyncio
    async def test_authentication_success_logged_to_audit(self, tmp_path):
        """Successful authentication attempts should be logged to audit trail."""
        api_keys_path = tmp_path / "api_keys.json"
        audit_path = tmp_path / "audit" / "auth.jsonl"
        server = WFCMCPServer(api_keys_path=api_keys_path, audit_log_path=audit_path)

        api_key = server.api_key_store.create_api_key("test-proj", "alice")

        with patch("wfc.servers.mcp_server.ReviewOrchestrator") as mock_orch_class:
            mock_orch = AsyncMock()
            mock_orch.review_code = AsyncMock(
                return_value={"consensus_score": 8.5, "passed": True, "findings": []}
            )
            mock_orch_class.return_value = mock_orch

            await server.call_tool(
                name="review_code",
                arguments={
                    "project_id": "test-proj",
                    "api_key": api_key,
                    "diff_content": "some diff",
                },
            )

        assert audit_path.exists()
        audit_content = audit_path.read_text()
        assert "success" in audit_content
        assert "test-proj" in audit_content
