"""MCP server exposing vink to Claude Desktop and other MCP clients."""

from vink.interfaces.mcp.server import create_server

__all__ = ["create_server"]
