"""
数据模型定义
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import uuid


@dataclass
class Message:
    """消息模型"""
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "role": self.role,
            "content": self.content
        }

        # 如果是工具消息，添加工具调用 ID
        if self.role == "tool" and self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id

        # 如果是助手消息且有工具调用
        if self.role == "assistant" and self.tool_calls:
            # 转换为 OpenAI 格式
            result["tool_calls"] = [
                {
                    "id": tc.get("id", ""),
                    "type": "function",
                    "function": {
                        "name": tc.get("name", ""),
                        "arguments": json.dumps(tc.get("arguments", {}))
                    }
                }
                for tc in self.tool_calls
            ]

        return result


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    server_id: Optional[str] = None  # 所属 MCP 服务器 ID


@dataclass
class ToolResult:
    """工具调用结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None


@dataclass
class AgentInfo:
    """Agent 信息"""
    name: str
    tools_count: int
    mcp_servers: List[str]
    model: Optional[str] = None
    version: str = "1.0.0"
