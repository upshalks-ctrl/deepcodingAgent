"""
基础模型抽象
定义所有模型提供商必须实现的接口
支持同步和异步两种模式
"""

from abc import ABC, abstractmethod
from typing import List, Optional, AsyncIterator, Dict, Any, Union
from dataclasses import dataclass
import json


@dataclass
class ModelConfig:
    """模型配置"""
    api_key: str
    base_url: str
    model: str = "default"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: float = 120.0
    stream: bool = False

    def __post_init__(self):
        if not self.api_key:
            raise ValueError("ModelConfig.api_key cannot be empty")
        if not self.base_url:
            raise ValueError("ModelConfig.base_url cannot be empty")


@dataclass
class ChatResponse:
    """聊天响应"""
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: str = "stop"
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None

    def __str__(self) -> str:
        if self.tool_calls:
            return f"ChatResponse(tool_calls={len(self.tool_calls)})"
        else:
            return f"ChatResponse(content={self.content[:50] if self.content else None}...)"


class BaseModel(ABC):
    """基础模型抽象类

    所有模型提供商必须继承此类并实现相应方法
    """

    def __init__(self, config: ModelConfig):
        self.config = config

    # ==================== 异步方法 ====================

    @abstractmethod
    async def ainvoke(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ChatResponse:
        """发送聊天请求（异步）

        Args:
            messages: 消息列表
            tools: 可用工具定义列表
            **kwargs: 其他参数

        Returns:
            ChatResponse: 聊天响应
        """
        pass

    @abstractmethod
    async def astream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """流式聊天（异步）

        Args:
            messages: 消息列表
            tools: 可用工具定义列表
            **kwargs: 其他参数

        Yields:
            str: 流式输出的文本片段
        """
        pass

    @abstractmethod
    async def close(self):
        """关闭模型连接（异步）"""
        pass

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    # ==================== 同步方法 ====================

    @abstractmethod
    def invoke(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ChatResponse:
        """发送聊天请求（同步）

        Args:
            messages: 消息列表
            tools: 可用工具定义列表
            **kwargs: 其他参数

        Returns:
            ChatResponse: 聊天响应
        """
        pass

    @abstractmethod
    def stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Union[str, List[str]]:
        """流式聊天（同步）

        Args:
            messages: 消息列表
            tools: 可用工具定义列表
            **kwargs: 其他参数

        Returns:
            Union[str, List[str]]: 流式输出的文本片段或完整文本
        """
        pass

    @abstractmethod
    def close_sync(self):
        """关闭模型连接（同步）"""
        pass

    def __enter__(self):
        """同步上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器出口"""
        self.close_sync()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"model={self.config.model}, "
            f"base_url={self.config.base_url}"
            f")"
        )


def convert_messages(messages: Any) -> List[Dict[str, Any]]:
    """转换消息格式

    Args:
        messages: 消息（可能是 Message 对象或字典）

    Returns:
        List[Dict[str, Any]]: 字典格式的消息列表
    """
    if not messages:
        return []

    # 如果已经是字典格式，直接返回
    if isinstance(messages, dict):
        return [messages]

    # 如果是列表，递归转换
    if isinstance(messages, list):
        result = []
        for msg in messages:
            if isinstance(msg, dict):
                result.append(msg)
            elif hasattr(msg, 'to_dict'):
                # Message 对象
                result.append(msg.to_dict())
            else:
                # 假设是可字符串化的对象
                result.append({"role": "user", "content": str(msg)})
        return result

    # 单个消息
    if hasattr(messages, 'to_dict'):
        return [messages.to_dict()]
    else:
        return [{"role": "user", "content": str(messages)}]
