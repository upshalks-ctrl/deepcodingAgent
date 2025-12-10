"""
OpenAI 模型实现
使用官方 OpenAI 客户端库，支持 OpenAI API 的聊天和流式输出
"""

import asyncio
import json
from typing import List, Optional, AsyncIterator, Dict, Any, Union
import logging

from .base import BaseModel, ModelConfig, ChatResponse, convert_messages

logger = logging.getLogger(__name__)


class OpenAIModel(BaseModel):
    """OpenAI 模型

    基于官方 OpenAI 客户端库的模型实现，支持聊天和工具调用
    """

    def __init__(self, config: ModelConfig):
        """初始化 OpenAI 模型

        Args:
            config: 模型配置
        """
        super().__init__(config)
        self.client = None
        self.async_client = None

    def _get_client(self):
        """获取同步客户端"""
        if self.client is None:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                )
            except ImportError:
                raise ImportError(
                    "openai is required. Install it with: pip install openai"
                )
        return self.client

    async def _get_async_client(self):
        """获取异步客户端"""
        if self.async_client is None:
            try:
                from openai import AsyncOpenAI
                self.async_client = AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                )
            except ImportError:
                raise ImportError(
                    "openai is required. Install it with: pip install openai"
                )
        return self.async_client

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
            client = await self._get_async_client()

            # 准备参数
            params = {
                "model": self.config.model,
                "messages": convert_messages(messages),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
            }

            # 添加工具定义
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            logger.debug(f"Sending async request to OpenAI API: {self.config.base_url}")

            response = await client.chat.completions.create(**params)

            logger.debug(f"Received async response from OpenAI API")

            # 解析响应
            choice = response.choices[0]
            message = choice.message

            # 解析工具调用
            tool_calls = None
            if message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments)
                    }
                    for tc in message.tool_calls
                ]

            return ChatResponse(
                content=message.content,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason,
                usage=response.usage.dict() if response.usage else None,
                model=response.model
            )

        except Exception as e:
            logger.error(f"OpenAI chat failed: {e}", exc_info=True)
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
            client = await self._get_async_client()

            # 准备参数
            params = {
                "model": self.config.model,
                "messages": convert_messages(messages),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "stream": True,
            }

            # 添加工具定义
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            logger.debug(f"Sending async stream request to OpenAI API: {self.config.base_url}")

            response = await client.chat.completions.create(**params)

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}", exc_info=True)
            raise

    async def close(self):
        """关闭连接（异步）"""
        if self.async_client:
            await self.async_client.close()
        self.async_client = None

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
            client = self._get_client()

            # 准备参数
            params = {
                "model": self.config.model,
                "messages": convert_messages(messages),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
            }

            # 添加工具定义
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            logger.debug(f"Sending sync request to OpenAI API: {self.config.base_url}")

            response = client.chat.completions.create(**params)

            logger.debug(f"Received sync response from OpenAI API")

            # 解析响应
            choice = response.choices[0]
            message = choice.message

            # 解析工具调用
            tool_calls = None
            if message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments)
                    }
                    for tc in message.tool_calls
                ]

            return ChatResponse(
                content=message.content,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason,
                usage=response.usage.dict() if response.usage else None,
                model=response.model
            )

        except Exception as e:
            logger.error(f"OpenAI chat_sync failed: {e}", exc_info=True)
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
            client = self._get_client()

            # 准备参数
            params = {
                "model": self.config.model,
                "messages": convert_messages(messages),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "stream": True,
            }

            # 添加工具定义
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            logger.debug(f"Sending sync stream request to OpenAI API: {self.config.base_url}")

            response = client.chat.completions.create(**params)

            chunks = []
            for chunk in response:
                if chunk.choices[0].delta.content:
                    chunks.append(chunk.choices[0].delta.content)

            return "".join(chunks)

        except Exception as e:
            logger.error(f"OpenAI streaming_sync failed: {e}", exc_info=True)
            raise

    def close_sync(self):
        """关闭连接（同步）"""
        if self.client:
            self.client.close()
        self.client = None


def create_openai_model(
    api_key: str,
    model: str = "gpt-4o-mini",
    base_url: str = "https://api.openai.com/v1",
    **kwargs
) -> OpenAIModel:
    """创建 OpenAI 模型的便捷函数

    Args:
        api_key: OpenAI API 密钥
        model: 模型名称
        base_url: API 基础 URL
        **kwargs: 其他配置参数

    Returns:
        OpenAIModel: 配置好的 OpenAI 模型实例
    """
    config = ModelConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        max_tokens=kwargs.get("max_tokens", 8192),
        temperature=kwargs.get("temperature", 0.7),
        timeout=kwargs.get("timeout", 120.0)
    )

    return OpenAIModel(config)
