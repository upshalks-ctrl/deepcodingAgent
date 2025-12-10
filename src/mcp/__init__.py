"""
MCP (Model Context Protocol) 相关功能

这个包包含了 MCP 客户端和 MCP 管理器的实现。
"""

from .mcp_client import MCPServerConfig
from .mcp_manager import MCPManager

__all__ = [
    "MCPServerConfig",
    "MCPManager",
]
