"""
MCP 客户端配置
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class MCPServerConfig:
    """MCP 服务器配置"""
    id: str
    command: List[str]
    name: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    args: Optional[List[str]] = None
    cwd: Optional[str] = None

    def __post_init__(self):
        if not self.id:
            raise ValueError("MCP server id is required")
        if not self.command:
            raise ValueError("MCP server command is required")
