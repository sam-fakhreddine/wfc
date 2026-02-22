"""
WFC MCP Server - Multi-tenant Model Context Protocol server.

Exposes WFC orchestrators via MCP protocol for Claude Code integration.

Security: Issue #64 - Implements authentication via API keys and audit logging.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import Resource, TextContent, Tool

from wfc.scripts.orchestrators.review.orchestrator import ReviewOrchestrator
from wfc.servers.rest_api.audit import AuthAuditor
from wfc.servers.rest_api.auth import APIKeyStore
from wfc.shared.config.wfc_config import ProjectContext
from wfc.shared.resource_pool import TokenBucket, WorktreePool

logger = logging.getLogger(__name__)


class WFCMCPServer:
    """
    WFC MCP Server - exposes WFC tools and resources via Model Context Protocol.

    Provides multi-tenant support with ProjectContext, rate limiting via TokenBucket,
    and resource management via WorktreePool.
    """

    def __init__(
        self,
        pool_dir: Optional[Path] = None,
        max_worktrees: int = 10,
        rate_limit_capacity: int = 10,
        rate_limit_refill: float = 10.0,
        api_keys_path: Optional[Path] = None,
        audit_log_path: Optional[Path] = None,
    ):
        """
        Initialize WFC MCP server.

        Args:
            pool_dir: Directory for worktree pool (default: .worktrees)
            max_worktrees: Maximum concurrent worktrees
            rate_limit_capacity: Token bucket capacity
            rate_limit_refill: Token bucket refill rate (tokens/second)
            api_keys_path: Path to API keys store (Issue #64)
            audit_log_path: Path to audit log (Issue #64)
        """
        self.app = Server("wfc-mcp")
        self.pool_dir = pool_dir or Path(".worktrees")
        self.worktree_pool = WorktreePool(pool_dir=self.pool_dir, max_worktrees=max_worktrees)
        self.rate_limiter = TokenBucket(capacity=rate_limit_capacity, refill_rate=rate_limit_refill)

        self.api_key_store = APIKeyStore(store_path=api_keys_path)
        self.auth_auditor = AuthAuditor(audit_log_path=audit_log_path)

        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self.app.list_tools()
        async def list_tools() -> List[Tool]:
            """List available WFC tools."""
            return await self.list_tools()

        @self.app.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Execute a WFC tool."""
            return await self.call_tool(name, arguments)

        @self.app.list_resources()
        async def list_resources() -> List[Resource]:
            """List available WFC resources."""
            return await self.list_resources()

        @self.app.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a WFC resource."""
            return await self.read_resource(uri)

    async def list_tools(self) -> List[Tool]:
        """
        List available WFC tools.

        Returns:
            List of MCP Tool objects
        """
        return [
            Tool(
                name="review_code",
                description="Run WFC 5-agent consensus review on code changes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "Project identifier for multi-tenant isolation (required for auth)",
                        },
                        "api_key": {
                            "type": "string",
                            "description": "API key for authentication (required, see Issue #64)",
                        },
                        "developer_id": {
                            "type": "string",
                            "description": "Developer identifier for attribution",
                        },
                        "diff_content": {
                            "type": "string",
                            "description": "Git diff content to review",
                        },
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of files to review",
                        },
                    },
                    "required": ["project_id", "api_key", "diff_content"],
                },
            )
        ]

    async def list_resources(self) -> List[Resource]:
        """
        List available WFC resources.

        Returns:
            List of MCP Resource objects
        """
        return [
            Resource(
                uri="review://project/{project_id}/latest",
                name="Latest review for project",
                mimeType="application/json",
                description="Retrieve the most recent review results for a project",
            ),
            Resource(
                uri="review://global/latest",
                name="Latest global review",
                mimeType="application/json",
                description="Retrieve the most recent review (no project isolation)",
            ),
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Execute a WFC tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            List of TextContent results
        """
        if name == "review_code":
            return await self._handle_review_code(arguments)
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    async def _handle_review_code(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Handle review_code tool call.

        Args:
            arguments: Tool arguments containing project_id, developer_id, diff_content, files, api_key

        Returns:
            List containing review result as TextContent

        Security: Issue #64 - Validates API key before processing request
        """
        project_id = arguments.get("project_id")
        api_key = arguments.get("api_key")
        ip_address = arguments.get("_ip_address", "127.0.0.1")

        if not project_id:
            error_msg = "project_id is required for authentication"
            self.auth_auditor.log_auth_attempt(
                project_id="unknown",
                outcome="failure",
                ip_address=ip_address,
                failure_reason="missing_project_id",
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"error": error_msg, "authentication_required": True}),
                )
            ]

        if not api_key:
            error_msg = "API key required. Set 'api_key' in request arguments."
            self.auth_auditor.log_auth_attempt(
                project_id=project_id,
                outcome="failure",
                ip_address=ip_address,
                failure_reason="missing_api_key",
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"error": error_msg, "authentication_required": True}),
                )
            ]

        if not self.api_key_store.validate_api_key(project_id, api_key):
            error_msg = "Authentication failed. Invalid API key for project."
            self.auth_auditor.log_auth_attempt(
                project_id=project_id,
                outcome="failure",
                ip_address=ip_address,
                failure_reason="invalid_api_key",
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"error": error_msg, "authentication_failed": True}),
                )
            ]

        self.auth_auditor.log_auth_attempt(
            project_id=project_id, outcome="success", ip_address=ip_address
        )

        if not self.rate_limiter.acquire(tokens=1, timeout=5.0):
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": "Rate limit exceeded. Please try again later.",
                            "rate_limited": True,
                        }
                    ),
                )
            ]

        developer_id = arguments.get("developer_id")
        diff_content = arguments.get("diff_content", "")
        files = arguments.get("files", [])

        project_context = None
        if project_id:
            repo_path = Path.cwd()
            project_context = ProjectContext(
                project_id=project_id,
                developer_id=developer_id or "unknown",
                repo_path=repo_path,
                worktree_dir=repo_path / ".worktrees" / project_id,
                metrics_dir=Path.home() / ".wfc" / "telemetry" / project_id,
                output_dir=repo_path / ".wfc" / "output" / project_id,
            )

        _orchestrator = ReviewOrchestrator(project_context=project_context)

        try:
            result = {
                "project_id": project_id,
                "developer_id": developer_id,
                "consensus_score": 0.0,
                "passed": False,
                "findings": [],
                "message": f"Review executed successfully (integration pending) - {len(diff_content)} chars, {len(files)} files",
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Review failed: {e}", exc_info=True)
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"error": str(e), "failed": True}, indent=2),
                )
            ]

    async def read_resource(self, uri: str) -> str:
        """
        Read a WFC resource.

        Args:
            uri: Resource URI (e.g., "review://project/myproject/latest")

        Returns:
            Resource content as string
        """
        if uri.startswith("review://project/"):
            parts = uri.split("/")
            if len(parts) >= 4:
                project_id = parts[3]
                return await self._read_latest_review(project_id)

        elif uri == "review://global/latest":
            return await self._read_latest_review(None)

        return json.dumps({"error": f"Unknown resource URI: {uri}"})

    async def _read_latest_review(self, project_id: Optional[str]) -> str:
        """
        Read latest review results.

        Args:
            project_id: Project identifier (None for global)

        Returns:
            Review content as JSON string
        """
        try:
            if project_id:
                output_dir = Path(".wfc") / "output" / project_id
                review_file = output_dir / f"REVIEW-{project_id}.md"
            else:
                output_dir = Path(".wfc") / "output"
                review_file = output_dir / "REVIEW-global.md"

            if review_file.exists():
                content = review_file.read_text()
                return json.dumps({"project_id": project_id, "content": content}, indent=2)
            else:
                return json.dumps({"error": "No review found", "project_id": project_id})

        except Exception as e:
            logger.error(f"Failed to read review: {e}", exc_info=True)
            return json.dumps({"error": str(e)})

    async def cleanup(self) -> None:
        """Cleanup server resources on shutdown."""
        try:
            if hasattr(self.worktree_pool, "cleanup_all"):
                self.worktree_pool.cleanup_all()
            logger.info("WFC MCP server cleanup complete")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
