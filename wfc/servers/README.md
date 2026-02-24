# WFC MCP Server

Model Context Protocol server exposing WFC code review capabilities to Claude Desktop.

## Quick Start

### Installation

```bash
# Install WFC with MCP support
uv pip install -e ".[mcp]"
```

### Running the Server

```bash
# Run standalone
uv run python -m wfc.servers.mcp_server

# Or via configured Claude Desktop
# (see docs/mcp/CLAUDE_DESKTOP_SETUP.md)
```

## Architecture

```
WFCMCPServer
├── Tools
│   └── review_code - Run 5-agent consensus review
├── Resources
│   ├── review://project/{id}/latest - Latest project review
│   └── review://global/latest - Latest global review
├── Rate Limiting
│   └── TokenBucket (10 req/sec)
└── Resource Pooling
    └── WorktreePool (max 10 concurrent)
```

## Multi-Tenant Features

### Project Isolation

```python
{
  "project_id": "auth-service",
  "developer_id": "alice",
  "diff_content": "...",
  "files": ["src/auth.py"]
}
```

**Result**:

- Worktree: `.worktrees/auth-service/wfc-{task_id}`
- Report: `.wfc/output/auth-service/REVIEW-auth-service.md`
- Metrics: `~/.wfc/telemetry/auth-service/`

### Backward Compatible

Omit `project_id` for legacy single-tenant mode:

```python
{
  "diff_content": "...",
  "files": ["src/auth.py"]
}
```

## Files

- `mcp_server.py` - Main server implementation (285 lines)
- `__init__.py` - Package exports
- `__main__.py` - CLI entry point
- `mcp_config.json` - Configuration
- `README.md` - This file

## Testing

```bash
# Run MCP tests
uv run pytest tests/mcp/ -v

# Expected: 9 tests passing
```

## Configuration

Edit `mcp_config.json`:

```json
{
  "server": {
    "worktree_pool": {
      "max_worktrees": 10,
      "orphan_timeout_hours": 24
    },
    "rate_limiting": {
      "capacity": 10,
      "refill_rate": 10.0
    }
  }
}
```

## Documentation

- [Claude Desktop Setup Guide](../../docs/mcp/CLAUDE_DESKTOP_SETUP.md)
- [Implementation Summary](../../IMPLEMENTATION_SUMMARY.md)
- [Multi-Tenant Architecture](../../plans/plan_multi_tenant_wfc_20260221_094944/)

## Test Coverage

| Test | Description |
|------|-------------|
| `test_server_initialization` | Server creates with name "wfc-mcp" |
| `test_list_tools_returns_review_tool` | Exposes review_code tool |
| `test_list_resources_returns_review_resources` | Exposes review:// resources |
| `test_call_tool_review_code_with_project_context` | Multi-tenant review works |
| `test_call_tool_review_code_backward_compat` | Legacy mode works |
| `test_read_resource_review_latest` | Can read review results |
| `test_server_handles_rate_limiting` | Rate limits enforced |
| `test_server_creates_worktree_pool` | Resource pool initialized |
| `test_server_cleanup_on_shutdown` | Cleanup runs on exit |

**Status**: ✅ 9/9 passing (100%)
