"""
MCP 数据模型

定义 MCP 协议相关的数据结构
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    server_id: Optional[str] = None


@dataclass
class ToolResult:
    """工具调用结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None


@dataclass
class ToolCall:
    """工具调用"""
    id: str
    name: str
    arguments: Dict[str, Any]
