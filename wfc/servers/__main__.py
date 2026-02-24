"""
MCP Server CLI Entry Point.

Run with: python -m wfc.servers.mcp_server
or: uv run python -m wfc.servers.mcp_server
"""

import asyncio
import logging
import sys
from pathlib import Path

import mcp.server.stdio

from wfc.servers.mcp_server import WFCMCPServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def main():
    """Run WFC MCP server via stdio transport."""
    try:
        server = WFCMCPServer(
            pool_dir=Path(".worktrees"),
            max_worktrees=10,
            rate_limit_capacity=10,
            rate_limit_refill=10.0,
        )

        logger.info("Starting WFC MCP server...")

        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.app.run(
                read_stream,
                write_stream,
                server.app.create_initialization_options(),
            )

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
