"""
Anthropic 模型实现
支持 Anthropic API 的聊天和流式输出
使用官方 Anthropic 客户端库
"""

import asyncio
import json
from typing import List, Optional, AsyncIterator, Dict, Any, Union
import logging

from .base import BaseModel, ModelConfig, ChatResponse, convert_messages

logger = logging.getLogger(__name__)


class AnthropicModel(BaseModel):
    """Anthropic 模型

    基于 Anthropic API 的模型实现，支持聊天和工具调用
    使用官方 Anthropic 客户端库
    """

    def __init__(self, config: ModelConfig):
        """初始化 Anthropic 模型"""
        super().__init__(config)
        self.client = None
        self.sync_client = None

    def _get_client(self):
        """获取异步客户端（懒加载）"""
        if self.client is None:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
            )
        return self.client

    def _get_sync_client(self):
        """获取同步客户端（懒加载）"""
        if self.sync_client is None:
            from anthropic import Anthropic
            self.sync_client = Anthropic(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
            )
        return self.sync_client

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
        try:
            # Anthropic 需要不同的消息格式
            system_message = ""
            anthropic_messages = []

            for msg in convert_messages(messages):
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # 准备参数
            params = {
                "model": self.config.model,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "messages": anthropic_messages,
            }

            if system_message:
                params["system"] = system_message

            # 添加工具定义
            if tools:
                # Anthropic 的工具格式略有不同
                params["tools"] = [
                    {
                        "name": tool.get("function", {}).get("name"),
                        "description": tool.get("function", {}).get("description"),
                        "input_schema": tool.get("function", {}).get("parameters", {})
                    }
                    for tool in tools
                ]

            client = self._get_client()
            logger.debug(f"Sending request to Anthropic API: {self.config.base_url}")

            response = await client.messages.create(**params)
            logger.debug(f"Received response from Anthropic API")

            # 解析响应
            content = response.content[0] if response.content else None
            text = content.text if content and hasattr(content, 'text') else ""

            # 解析工具调用（Anthropic 使用不同的格式）
            tool_calls = None
            if content and hasattr(content, 'type') and content.type == "tool_use":
                tool_calls = [
                    {
                        "id": content.id,
                        "name": getattr(content, 'name', None),
                        "arguments": getattr(content, 'input', {})
                    }
                ]

            return ChatResponse(
                content=text,
                tool_calls=tool_calls,
                finish_reason=response.stop_reason,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                model=response.model
            )

        except ImportError:
            raise ImportError(
                "anthropic is required. Install it with: pip install anthropic"
            )
        except Exception as e:
            logger.error(f"Anthropic chat failed: {e}", exc_info=True)
            raise

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
        try:
            # Anthropic 需要不同的消息格式
            system_message = ""
            anthropic_messages = []

            for msg in convert_messages(messages):
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # 准备参数
            params = {
                "model": self.config.model,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "messages": anthropic_messages,
                "stream": True
            }

            if system_message:
                params["system"] = system_message

            # 添加工具定义
            if tools:
                params["tools"] = [
                    {
                        "name": tool.get("function", {}).get("name"),
                        "description": tool.get("function", {}).get("description"),
                        "input_schema": tool.get("function", {}).get("parameters", {})
                    }
                    for tool in tools
                ]

            client = self._get_client()
            logger.debug(f"Sending streaming request to Anthropic API: {self.config.base_url}")

            async with client.messages.create(**params) as stream:
                async for chunk in stream:
                    if chunk.type == "content_block_delta":
                        if hasattr(chunk.delta, 'text'):
                            yield chunk.delta.text

        except ImportError:
            raise ImportError(
                "anthropic is required. Install it with: pip install anthropic"
            )
        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}", exc_info=True)
            raise

    async def close(self):
        """关闭连接（异步）"""
        if self.client:
            await self.client.close()
            self.client = None

    def close_sync(self):
        """关闭连接（同步）"""
        if self.sync_client:
            self.sync_client.close()
            self.sync_client = None

    # ==================== 同步方法 ====================

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
        try:
            # Anthropic 需要不同的消息格式
            system_message = ""
            anthropic_messages = []

            for msg in convert_messages(messages):
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # 准备参数
            params = {
                "model": self.config.model,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "messages": anthropic_messages,
            }

            if system_message:
                params["system"] = system_message

            # 添加工具定义
            if tools:
                params["tools"] = [
                    {
                        "name": tool.get("function", {}).get("name"),
                        "description": tool.get("function", {}).get("description"),
                        "input_schema": tool.get("function", {}).get("parameters", {})
                    }
                    for tool in tools
                ]

            client = self._get_sync_client()
            logger.debug(f"Sending sync request to Anthropic API: {self.config.base_url}")

            response = client.messages.create(**params)
            logger.debug(f"Received sync response from Anthropic API")

            # 解析响应
            content = response.content[0] if response.content else None
            text = content.text if content and hasattr(content, 'text') else ""

            # 解析工具调用（Anthropic 使用不同的格式）
            tool_calls = None
            if content and hasattr(content, 'type') and content.type == "tool_use":
                tool_calls = [
                    {
                        "id": content.id,
                        "name": getattr(content, 'name', None),
                        "arguments": getattr(content, 'input', {})
                    }
                ]

            return ChatResponse(
                content=text,
                tool_calls=tool_calls,
                finish_reason=response.stop_reason,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                model=response.model
            )

        except ImportError:
            raise ImportError(
                "anthropic is required. Install it with: pip install anthropic"
            )
        except Exception as e:
            logger.error(f"Anthropic chat_sync failed: {e}", exc_info=True)
            raise

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
        try:
            # Anthropic 需要不同的消息格式
            system_message = ""
            anthropic_messages = []

            for msg in convert_messages(messages):
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # 准备参数
            params = {
                "model": self.config.model,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "messages": anthropic_messages,
                "stream": True
            }

            if system_message:
                params["system"] = system_message

            # 添加工具定义
            if tools:
                params["tools"] = [
                    {
                        "name": tool.get("function", {}).get("name"),
                        "description": tool.get("function", {}).get("description"),
                        "input_schema": tool.get("function", {}).get("parameters", {})
                    }
                    for tool in tools
                ]

            client = self._get_sync_client()
            logger.debug(f"Sending sync streaming request to Anthropic API: {self.config.base_url}")

            with client.messages.create(**params) as stream:
                chunks = []
                for chunk in stream:
                    if chunk.type == "content_block_delta":
                        if hasattr(chunk.delta, 'text'):
                            chunks.append(chunk.delta.text)

                return "".join(chunks)

        except ImportError:
            raise ImportError(
                "anthropic is required. Install it with: pip install anthropic"
            )
        except Exception as e:
            logger.error(f"Anthropic streaming_sync failed: {e}", exc_info=True)
            raise


def create_anthropic_model(
    api_key: str,
    model: str = "claude-3-5-sonnet-20241022",
    base_url: str = "https://api.anthropic.com/v1",
    **kwargs
) -> AnthropicModel:
    """创建 Anthropic 模型的便捷函数

    Args:
        api_key: Anthropic API 密钥
        model: 模型名称
        base_url: API 基础 URL
        **kwargs: 其他配置参数

    Returns:
        AnthropicModel: 配置好的 Anthropic 模型实例
    """
    config = ModelConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        max_tokens=kwargs.get("max_tokens", 4096),
        temperature=kwargs.get("temperature", 0.7),
        timeout=kwargs.get("timeout", 120.0)
    )

    return AnthropicModel(config)
