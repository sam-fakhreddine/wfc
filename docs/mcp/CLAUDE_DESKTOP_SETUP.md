# Claude Desktop MCP Server Setup

This guide explains how to configure Claude Desktop to use the WFC MCP server for multi-tenant code reviews.

## Prerequisites

- Claude Desktop installed
- WFC installed (`uv pip install -e ".[mcp]"`)
- Python 3.12+ with `uv` package manager

## Configuration

### 1. Locate Claude Desktop Config

The Claude Desktop configuration file is located at:

**macOS**:

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows**:

```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux**:

```
~/.config/Claude/claude_desktop_config.json
```

### 2. Add WFC MCP Server

Edit `claude_desktop_config.json` and add the WFC server:

```json
{
  "mcpServers": {
    "wfc": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "wfc.servers.mcp_server"
      ],
      "env": {
        "WFC_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Important**: Replace the `command` path with your actual WFC installation path if needed.

### 3. Restart Claude Desktop

After saving the configuration:

1. Quit Claude Desktop completely
2. Restart Claude Desktop
3. The WFC MCP server should now be available

## Verification

To verify the server is working:

1. Open Claude Desktop
2. Start a new conversation
3. Type: `@wfc` and press Tab
4. You should see WFC tools available:
   - `review_code` - Run 5-agent consensus review

## Usage Examples

### Basic Review (No Multi-Tenancy)

```
@wfc review_code
{
  "diff_content": "your git diff here",
  "files": ["src/auth.py"]
}
```

### Multi-Tenant Review

```
@wfc review_code
{
  "project_id": "auth-service",
  "developer_id": "alice",
  "diff_content": "your git diff here",
  "files": ["src/auth.py"]
}
```

### Read Latest Review

```
@wfc read review://project/auth-service/latest
```

## Multi-Tenant Features

### Project Isolation

When you provide `project_id`, WFC creates isolated namespaces:

- **Worktrees**: `.worktrees/{project_id}/wfc-{task_id}`
- **Reports**: `.wfc/output/{project_id}/REVIEW-{project_id}.md`
- **Metrics**: `~/.wfc/telemetry/{project_id}/`

### Developer Attribution

When you provide `developer_id`, WFC tracks:

- Git commits attributed to developer
- Knowledge entries tagged with developer
- Audit trail of who reviewed what

### Rate Limiting

The server enforces rate limits to prevent API quota exhaustion:

- **Capacity**: 10 requests (burst)
- **Refill Rate**: 10 requests/second
- **Behavior**: Returns error when rate limit exceeded

## Troubleshooting

### Server Not Appearing

1. Check Claude Desktop logs:
   - macOS: `~/Library/Logs/Claude/mcp*.log`
2. Verify `uv` is in PATH:

   ```bash
   which uv
   ```

3. Test server manually:

   ```bash
   uv run python -m wfc.servers.mcp_server
   ```

### Rate Limit Errors

If you see "Rate limit exceeded" errors:

1. Wait a few seconds and retry
2. Reduce concurrent review requests
3. Increase capacity in `wfc/servers/mcp_config.json`:

   ```json
   "rate_limiting": {
     "capacity": 20,
     "refill_rate": 20.0
   }
   ```

### Permission Errors

If you see permission errors accessing worktrees:

1. Check `.worktrees/` directory permissions:

   ```bash
   ls -la .worktrees/
   ```

2. Ensure WFC has write access to project directory

## Configuration Options

You can customize the server by editing `wfc/servers/mcp_config.json`:

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

### Available Options

| Option | Default | Description |
|--------|---------|-------------|
| `max_worktrees` | 10 | Maximum concurrent worktrees |
| `orphan_timeout_hours` | 24 | Hours before orphan cleanup |
| `capacity` | 10 | Token bucket capacity |
| `refill_rate` | 10.0 | Tokens per second |

## Advanced: Custom Server Launch

If you need more control, create a custom launch script:

```bash
#!/bin/bash
# launch-wfc-mcp.sh

export WFC_LOG_LEVEL=DEBUG
export WFC_MAX_WORKTREES=20

cd /path/to/your/wfc
uv run python -m wfc.servers.mcp_server
```

Then update `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "wfc": {
      "command": "/path/to/launch-wfc-mcp.sh"
    }
  }
}
```

## Security Considerations

### Local-Only Access

The MCP server runs locally and only accessible via stdio transport. No network exposure.

### Project Isolation

Each `project_id` gets isolated directories preventing cross-project contamination.

### Developer Attribution

All actions are attributed to `developer_id` for audit trails.

## Next Steps

- See [MCP Interface Documentation](MCP_INTERFACE.md) for full API reference
- See [Multi-Tenant Guide](../architecture/MULTI_TENANT.md) for architecture details
- See [IMPLEMENTATION_SUMMARY.md](../../IMPLEMENTATION_SUMMARY.md) for technical overview
