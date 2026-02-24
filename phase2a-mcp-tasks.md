---
title: Multi-Tenant WFC - Phase 2A: MCP Interface
status: active
created: 2026-02-21T14:00:00Z
phase1_complete: 2026-02-21 (94/94 tests passing)
tasks_total: 8
tasks_completed: 0
complexity: M
---

# Phase 2A: MCP Interface for Multi-Tenant Reviews

**Context**: Phase 1 complete (all resource pooling and integration done). Core multi-tenant primitives working perfectly.

**Goal**: Create MCP server that exposes WFC review capabilities with multi-tenant isolation, resource pooling, and rate limiting.

**Timeline**: 1-2 days (8 tasks × 45min avg = 6 hours)

**Why MCP?**

- Lighter than REST API
- Native integration with Claude Desktop, IDEs, and AI tools
- Standardized protocol (maintained by Anthropic)
- Perfect for local/team development workflows

---

## TASK-014: Create MCP Server Infrastructure

**File**: `wfc/servers/mcp_server.py` (new file)
**Complexity**: M (100-200 lines)
**Dependencies**: [Phase 1 complete]
**Properties**: [M1-Project-Isolation]
**Estimated Time**: 60min
**Agent Level**: Sonnet

### Description

Create basic MCP server with health check and initialization. Uses `mcp` Python library.

### Code Pattern Example

```python
"""
WFC MCP Server

Exposes WFC review capabilities via Model Context Protocol.
Supports multi-tenant isolation, resource pooling, and rate limiting.
"""

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from wfc.shared.config.wfc_config import WFCConfig
from wfc.shared.resource_pool import WorktreePool, TokenBucket
from wfc.scripts.orchestrators.review.orchestrator import ReviewOrchestrator

logger = logging.getLogger(__name__)


class WFCMCPServer:
    """
    WFC MCP Server.

    Exposes review tools with multi-tenant support.
    """

    def __init__(
        self,
        pool_dir: str = ".worktrees",
        max_worktrees: int = 10,
        rate_limit_capacity: int = 10,
        rate_limit_refill: float = 10.0,
    ):
        """
        Initialize WFC MCP server.

        Args:
            pool_dir: Worktree pool directory
            max_worktrees: Max concurrent worktrees
            rate_limit_capacity: Token bucket capacity
            rate_limit_refill: Tokens per second
        """
        self.config = WFCConfig()
        self.worktree_pool = WorktreePool(
            pool_dir=pool_dir,
            max_worktrees=max_worktrees,
        )
        self.rate_limiter = TokenBucket(
            capacity=rate_limit_capacity,
            refill_rate=rate_limit_refill,
        )
        self.server = Server("wfc-review")

        # Register handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP tool handlers."""
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="wfc_review",
                    description=(
                        "Multi-tenant code review with 5 expert reviewers. "
                        "Returns consensus score and findings. "
                        "Supports project and developer isolation."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "files": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Files to review",
                            },
                            "project_id": {
                                "type": "string",
                                "description": "Project identifier for isolation",
                            },
                            "developer_id": {
                                "type": "string",
                                "description": "Developer identifier for attribution",
                            },
                            "properties": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Property IDs to validate",
                            },
                        },
                        "required": ["files"],
                    },
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool calls."""
            if name == "wfc_review":
                return await self._handle_review(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

    async def _handle_review(self, arguments: dict) -> list[TextContent]:
        """
        Handle review tool call.

        Args:
            arguments: Tool arguments (files, project_id, developer_id, properties)

        Returns:
            Review results as TextContent
        """
        # Rate limiting
        if not self.rate_limiter.acquire(tokens=1, timeout=5.0):
            return [
                TextContent(
                    type="text",
                    text="Rate limit exceeded. Please try again later.",
                )
            ]

        # Extract arguments
        files = arguments.get("files", [])
        project_id = arguments.get("project_id")
        developer_id = arguments.get("developer_id")
        properties = arguments.get("properties", [])

        # Validate project and developer IDs are both provided or both omitted
        if (project_id is None) != (developer_id is None):
            return [
                TextContent(
                    type="text",
                    text="Error: project_id and developer_id must both be provided or both omitted.",
                )
            ]

        # Create project context if multi-tenant
        project_context = None
        if project_id and developer_id:
            try:
                project_context = self.config.create_project_context(
                    project_id=project_id,
                    developer_id=developer_id,
                )
            except ValueError as e:
                return [TextContent(type="text", text=f"Error: {e}")]

        # Create orchestrator
        orchestrator = ReviewOrchestrator(
            config=self.config,
            project_context=project_context,
        )

        # Run review (placeholder - would integrate with actual review logic)
        try:
            # TODO: Integrate with actual review orchestrator workflow
            result_text = f"Review initiated for {len(files)} files"
            if project_context:
                result_text += f"\nProject: {project_id}, Developer: {developer_id}"

            return [TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Review failed: {e}", exc_info=True)
            return [TextContent(type="text", text=f"Review failed: {e}")]

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


async def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    server = WFCMCPServer(
        pool_dir=".worktrees",
        max_worktrees=10,
        rate_limit_capacity=10,
        rate_limit_refill=10.0,
    )

    logger.info("Starting WFC MCP server...")
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
```

### Acceptance Criteria

- [ ] WFCMCPServer class implemented
- [ ] Initializes with WorktreePool and TokenBucket
- [ ] Registers `wfc_review` tool
- [ ] Tool schema includes project_id and developer_id
- [ ] Rate limiting applied to tool calls
- [ ] Creates ProjectContext when IDs provided
- [ ] Validates both IDs present or both absent
- [ ] CLI entry point works
- [ ] Unit tests:
  - [ ] `test_server_initialization`
  - [ ] `test_tool_registration`
  - [ ] `test_rate_limiting`
  - [ ] `test_project_context_creation`

---

## TASK-015: Add MCP Server Dependencies

**File**: `pyproject.toml`
**Complexity**: XS (<10 lines)
**Dependencies**: []
**Properties**: []
**Estimated Time**: 5min
**Agent Level**: Haiku

### Description

Add MCP Python library to dependencies.

### Code Pattern Example

```toml
[project]
dependencies = [
    # ... existing dependencies
    "mcp>=1.0.0",
]
```

### Acceptance Criteria

- [ ] `mcp>=1.0.0` added to dependencies
- [ ] `uv pip install -e .` works

---

## TASK-016: Create MCP Server Configuration

**File**: `wfc/servers/mcp_config.json` (new file)
**Complexity**: XS (<10 lines)
**Dependencies**: [TASK-014]
**Properties**: []
**Estimated Time**: 10min
**Agent Level**: Haiku

### Description

Create default configuration for MCP server.

### Code Pattern Example

```json
{
  "server_name": "wfc-review",
  "worktree_pool": {
    "directory": ".worktrees",
    "max_worktrees": 10,
    "orphan_timeout_hours": 24
  },
  "rate_limiting": {
    "capacity": 10,
    "refill_rate": 10.0
  },
  "logging": {
    "level": "INFO",
    "file": ".wfc/logs/mcp_server.log"
  }
}
```

### Acceptance Criteria

- [ ] JSON configuration file created
- [ ] All server settings configurable
- [ ] Valid JSON syntax

---

## TASK-017: Add MCP Server to Claude Desktop Config

**File**: `docs/mcp/CLAUDE_DESKTOP_SETUP.md` (new file)
**Complexity**: S (10-50 lines)
**Dependencies**: [TASK-014]
**Properties**: []
**Estimated Time**: 15min
**Agent Level**: Haiku

### Description

Document how to add WFC MCP server to Claude Desktop.

### Code Pattern Example

```markdown
# WFC MCP Server - Claude Desktop Setup

Add WFC review capabilities to Claude Desktop via MCP.

## Installation

1. **Install WFC MCP server**:
   ```bash
   cd /path/to/wfc
   uv pip install -e ".[mcp]"
   ```

2. **Add to Claude Desktop config**:

   Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

   ```json
   {
     "mcpServers": {
       "wfc-review": {
         "command": "uv",
         "args": [
           "run",
           "python",
           "-m",
           "wfc.servers.mcp_server"
         ],
         "cwd": "/path/to/wfc"
       }
     }
   }
   ```

3. **Restart Claude Desktop**

## Usage

In Claude Desktop:

```
Can you review these files using wfc_review?
- project_id: my-web-app
- developer_id: alice
- files: [src/auth.py, src/api.py]
```

Claude will call the MCP tool with proper isolation.

## Multi-Tenant Example

```
Review the API endpoints:
Project: backend-api
Developer: bob
Files: api/routes/*.py
```

This creates isolated review with:

- Worktree: `.worktrees/backend-api/wfc-review-001`
- Output: `.wfc/output/backend-api/REVIEW-backend-api.md`
- Attribution: Knowledge entries tagged with "bob"

```

### Acceptance Criteria

- [ ] Installation steps documented
- [ ] Claude Desktop config example provided
- [ ] Usage examples with multi-tenant flags
- [ ] Clear and actionable

---

## TASK-018: Add Integration Tests for MCP Server

**File**: `tests/mcp/test_mcp_server.py` (new file)
**Complexity**: M (50-200 lines)
**Dependencies**: [TASK-014]
**Properties**: [M1, M2]
**Estimated Time**: 45min
**Agent Level**: Sonnet

### Description

Integration tests for MCP server functionality.

### Code Pattern Example

```python
"""
Integration tests for WFC MCP server.
"""

import pytest
from wfc.servers.mcp_server import WFCMCPServer


class TestWFCMCPServer:
    """Test WFC MCP server."""

    def test_server_initialization(self):
        """Server should initialize with resource pools."""
        server = WFCMCPServer(
            pool_dir=".worktrees",
            max_worktrees=10,
            rate_limit_capacity=10,
            rate_limit_refill=5.0,
        )

        assert server.worktree_pool.max_worktrees == 10
        assert server.rate_limiter.capacity == 10
        assert server.rate_limiter.refill_rate == 5.0

    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Server should register wfc_review tool."""
        server = WFCMCPServer()

        # Get tools list
        @server.server.list_tools()
        async def get_tools():
            pass

        tools = await get_tools()

        assert len(tools) == 1
        assert tools[0].name == "wfc_review"
        assert "project_id" in tools[0].inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_rate_limiting_enforced(self):
        """Server should enforce rate limits."""
        server = WFCMCPServer(
            rate_limit_capacity=2,  # Only 2 requests
            rate_limit_refill=0.0,  # No refill
        )

        # First 2 should succeed
        result1 = await server._handle_review({"files": ["test1.py"]})
        result2 = await server._handle_review({"files": ["test2.py"]})

        assert "Rate limit exceeded" not in result1[0].text
        assert "Rate limit exceeded" not in result2[0].text

        # Third should be rate limited
        result3 = await server._handle_review({"files": ["test3.py"]})
        assert "Rate limit exceeded" in result3[0].text

    @pytest.mark.asyncio
    async def test_project_context_created_when_ids_provided(self, tmp_path):
        """Server should create ProjectContext when project_id and developer_id provided."""
        server = WFCMCPServer()

        result = await server._handle_review({
            "files": ["test.py"],
            "project_id": "web-app",
            "developer_id": "alice",
        })

        # Should succeed (not error)
        assert "Error" not in result[0].text
        assert "web-app" in result[0].text
        assert "alice" in result[0].text

    @pytest.mark.asyncio
    async def test_validates_ids_both_present_or_absent(self):
        """Server should require both IDs or neither."""
        server = WFCMCPServer()

        # Only project_id - should error
        result1 = await server._handle_review({
            "files": ["test.py"],
            "project_id": "web-app",
        })
        assert "Error" in result1[0].text
        assert "both be provided" in result1[0].text

        # Only developer_id - should error
        result2 = await server._handle_review({
            "files": ["test.py"],
            "developer_id": "alice",
        })
        assert "Error" in result2[0].text

        # Neither - should succeed
        result3 = await server._handle_review({
            "files": ["test.py"],
        })
        assert "Error" not in result3[0].text

        # Both - should succeed
        result4 = await server._handle_review({
            "files": ["test.py"],
            "project_id": "web-app",
            "developer_id": "alice",
        })
        assert "Error" not in result4[0].text
```

### Acceptance Criteria

- [ ] Server initialization test
- [ ] Tool registration test
- [ ] Rate limiting test
- [ ] ProjectContext creation test
- [ ] ID validation test
- [ ] All tests pass

---

## TASK-019: Add MCP Server CLI Script

**File**: `scripts/run-mcp-server.sh` (new file)
**Complexity**: S (10-50 lines)
**Dependencies**: [TASK-014]
**Properties**: []
**Estimated Time**: 15min
**Agent Level**: Haiku

### Description

Create convenient CLI script to run MCP server with options.

### Code Pattern Example

```bash
#!/usr/bin/env bash
#
# Run WFC MCP Server
#
# Usage:
#   bash scripts/run-mcp-server.sh [OPTIONS]
#
# Options:
#   --pool-dir DIR          Worktree pool directory (default: .worktrees)
#   --max-worktrees N       Max concurrent worktrees (default: 10)
#   --rate-limit N          Rate limit capacity (default: 10)
#   --log-level LEVEL       Logging level (default: INFO)
#   --help                  Show this help

set -euo pipefail

POOL_DIR=".worktrees"
MAX_WORKTREES=10
RATE_LIMIT=10
LOG_LEVEL="INFO"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --pool-dir)
      POOL_DIR="$2"
      shift 2
      ;;
    --max-worktrees)
      MAX_WORKTREES="$2"
      shift 2
      ;;
    --rate-limit)
      RATE_LIMIT="$2"
      shift 2
      ;;
    --log-level)
      LOG_LEVEL="$2"
      shift 2
      ;;
    --help)
      grep "^#" "$0" | sed 's/^# //'
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage"
      exit 1
      ;;
  esac
done

# Export environment variables
export WFC_POOL_DIR="$POOL_DIR"
export WFC_MAX_WORKTREES="$MAX_WORKTREES"
export WFC_RATE_LIMIT="$RATE_LIMIT"
export WFC_LOG_LEVEL="$LOG_LEVEL"

# Run server
echo "Starting WFC MCP Server..."
echo "  Pool dir: $POOL_DIR"
echo "  Max worktrees: $MAX_WORKTREES"
echo "  Rate limit: $RATE_LIMIT"
echo "  Log level: $LOG_LEVEL"
echo

uv run python -m wfc.servers.mcp_server
```

### Acceptance Criteria

- [ ] Bash script with argument parsing
- [ ] Default values for all options
- [ ] Help text
- [ ] Exports environment variables
- [ ] Runs MCP server
- [ ] Executable permissions

---

## TASK-020: Update Main Documentation

**File**: `README.md`
**Complexity**: S (10-50 lines)
**Dependencies**: [TASK-014, TASK-017]
**Properties**: []
**Estimated Time**: 15min
**Agent Level**: Haiku

### Description

Update main README to mention MCP server support.

### Code Pattern Example

```markdown
## MCP Server Support 🔌

WFC now includes an MCP (Model Context Protocol) server for integration with Claude Desktop and other AI tools.

### Quick Start

1. **Install with MCP support**:
   ```bash
   uv pip install -e ".[mcp]"
   ```

2. **Run MCP server**:

   ```bash
   bash scripts/run-mcp-server.sh
   ```

3. **Add to Claude Desktop** (see [docs/mcp/CLAUDE_DESKTOP_SETUP.md](docs/mcp/CLAUDE_DESKTOP_SETUP.md)):

   ```json
   {
     "mcpServers": {
       "wfc-review": {
         "command": "uv",
         "args": ["run", "python", "-m", "wfc.servers.mcp_server"]
       }
     }
   }
   ```

### Features

- ✅ Multi-tenant isolation (project_id + developer_id)
- ✅ Resource pooling (WorktreePool with LRU eviction)
- ✅ Rate limiting (TokenBucket)
- ✅ Developer attribution in knowledge base
- ✅ Native Claude Desktop integration

```

### Acceptance Criteria

- [ ] MCP section added to README
- [ ] Quick start guide
- [ ] Features listed
- [ ] Link to detailed setup docs

---

## TASK-021: Create MCP Server Package Marker

**File**: `wfc/servers/__init__.py` (new file)
**Complexity**: XS (<10 lines)
**Dependencies**: []
**Properties**: []
**Estimated Time**: 2min
**Agent Level**: Haiku

### Description

Create package marker for servers module.

### Code Pattern Example

```python
"""
WFC Servers

MCP and REST API servers for multi-tenant WFC.
"""

from .mcp_server import WFCMCPServer

__all__ = ["WFCMCPServer"]
```

### Acceptance Criteria

- [ ] Package marker created
- [ ] Exports WFCMCPServer
- [ ] Valid Python syntax

---

## Success Criteria (Phase 2A)

1. ✅ MCP server runs and accepts connections
2. ✅ `wfc_review` tool registered with proper schema
3. ✅ Multi-tenant flags (project_id, developer_id) work
4. ✅ Rate limiting enforced (TokenBucket)
5. ✅ Resource pooling active (WorktreePool)
6. ✅ Claude Desktop integration documented
7. ✅ All integration tests pass (6+ new tests)
8. ✅ Documentation updated

---

## Testing Strategy

### Unit Tests (TASK-018)

- Server initialization
- Tool registration
- Rate limiting
- ProjectContext creation
- Input validation

### Integration Tests

- End-to-end review via MCP
- Concurrent reviews from multiple "projects"
- Rate limit enforcement
- Orphan cleanup interaction

### Manual Testing

1. Run MCP server locally
2. Add to Claude Desktop config
3. Trigger review via Claude Desktop
4. Verify multi-tenant isolation
5. Check resource limits

---

## What This Enables

**Claude Desktop Users**:

```
User: "Review my authentication code with project=api, developer=alice"

Claude: [Calls wfc_review tool via MCP]

        ✅ Review complete!
        - Consensus Score: 6.2/10
        - 3 security findings
        - Report: .wfc/output/api/REVIEW-api.md
        - Developer: alice (attributed in knowledge base)
```

**IDE Integration** (future):

- VS Code extension calling MCP server
- IntelliJ plugin using MCP
- Neovim integration via MCP client

**Team Workflows**:

- Shared MCP server on team network
- Each developer gets isolated namespace
- Central knowledge base with attribution
- Resource limits prevent overload

---

## Stop/Go Decision Gate

After completing Phase 2A (8 tasks):

**Question**: Does MCP server meet your integration needs?

**Tests to validate**:

- Claude Desktop can trigger reviews
- Multi-tenant isolation works via MCP
- Rate limiting prevents abuse
- Resource pooling efficient

**Decision**:

- **STOP** if MCP integration sufficient
- **GO to REST API** if you need HTTP endpoints for web/CI integration
