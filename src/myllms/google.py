"""
Google 模型实现
支持 Google AI (Gemini) API 的聊天和流式输出
使用官方 Google AI 客户端库
"""

import asyncio
import json
from typing import List, Optional, AsyncIterator, Dict, Any, Union
import logging

from .base import BaseModel, ModelConfig, ChatResponse, convert_messages

logger = logging.getLogger(__name__)


class GoogleModel(BaseModel):
    """Google 模型 (Gemini)

    基于 Google AI API 的模型实现，支持聊天和流式输出
    使用官方 Google AI 客户端库
    """

    def __init__(self, config: ModelConfig):
        """初始化 Google 模型"""
        super().__init__(config)
        self._configured = False

    def _configure(self):
        """配置客户端（懒加载）"""
        if not self._configured:
            import google.generativeai as genai
            genai.configure(api_key=self.config.api_key)
            self._configured = True

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
            self._configure()

            # 获取最新的用户消息
            user_message = ""
            for msg in reversed(messages):
                if msg["role"] != "system":
                    user_message = msg["content"]
                    break

            # 在事件循环中运行同步代码
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._sync_generate,
                user_message,
                kwargs.get("max_tokens", self.config.max_tokens),
                kwargs.get("temperature", self.config.temperature),
            )

            # 解析响应
            text = response if response else ""

            return ChatResponse(
                content=text,
                tool_calls=None,
                finish_reason="stop",
                usage=None,
                model=self.config.model
            )

        except ImportError:
            raise ImportError(
                "google-generativeai is required. Install it with: pip install google-generativeai"
            )
        except Exception as e:
            logger.error(f"Google AI chat failed: {e}", exc_info=True)
            raise

    def _sync_generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """同步生成内容"""
        import google.generativeai as genai
        model = genai.GenerativeModel(self.config.model)

        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            }
        )

        return response.text if response.text else ""

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
            self._configure()

            # 获取最新的用户消息
            user_message = ""
            for msg in reversed(messages):
                if msg["role"] != "system":
                    user_message = msg["content"]
                    break

            # 在事件循环中运行同步代码
            loop = asyncio.get_event_loop()
            async for chunk in loop.run_in_executor(
                None,
                self._sync_stream_generate,
                user_message,
                kwargs.get("max_tokens", self.config.max_tokens),
                kwargs.get("temperature", self.config.temperature),
            ):
                yield chunk

        except ImportError:
            raise ImportError(
                "google-generativeai is required. Install it with: pip install google-generativeai"
            )
        except Exception as e:
            logger.error(f"Google AI streaming failed: {e}", exc_info=True)
            raise

    def _sync_stream_generate(self, prompt: str, max_tokens: int, temperature: float) -> List[str]:
        """同步流式生成内容"""
        import google.generativeai as genai
        model = genai.GenerativeModel(self.config.model)

        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            },
            stream=True
        )

        chunks = []
        for chunk in response:
            if chunk.text:
                chunks.append(chunk.text)
                yield chunk.text

    async def close(self):
        """关闭连接（异步）"""
        pass

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
            self._configure()

            # 获取最新的用户消息
            user_message = ""
            for msg in reversed(messages):
                if msg["role"] != "system":
                    user_message = msg["content"]
                    break

            # 创建模型实例
            import google.generativeai as genai
            model = genai.GenerativeModel(self.config.model)

            # 发送请求
            logger.debug(f"Sending request to Google AI API")
            response = model.generate_content(
                user_message,
                generation_config={
                    "max_output_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "temperature": kwargs.get("temperature", self.config.temperature),
                }
            )

            logger.debug(f"Received response from Google AI API")

            # 解析响应
            text = response.text if response.text else ""

            return ChatResponse(
                content=text,
                tool_calls=None,
                finish_reason="stop",
                usage=None,
                model=self.config.model
            )

        except ImportError:
            raise ImportError(
                "google-generativeai is required. Install it with: pip install google-generativeai"
            )
        except Exception as e:
            logger.error(f"Google AI chat_sync failed: {e}", exc_info=True)
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
            self._configure()

            # 获取最新的用户消息
            user_message = ""
            for msg in reversed(messages):
                if msg["role"] != "system":
                    user_message = msg["content"]
                    break

            # 创建模型实例
            import google.generativeai as genai
            model = genai.GenerativeModel(self.config.model)

            # 发送请求
            logger.debug(f"Sending sync streaming request to Google AI API")
            response = model.generate_content(
                user_message,
                generation_config={
                    "max_output_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "temperature": kwargs.get("temperature", self.config.temperature),
                },
                stream=True
            )

            # 收集所有文本块
            chunks = []
            for chunk in response:
                if chunk.text:
                    chunks.append(chunk.text)

            return "".join(chunks)

        except ImportError:
            raise ImportError(
                "google-generativeai is required. Install it with: pip install google-generativeai"
            )
        except Exception as e:
            logger.error(f"Google AI streaming_sync failed: {e}", exc_info=True)
            raise

    def close_sync(self):
        """关闭连接（同步）"""
        pass


def create_google_model(
    api_key: str,
    model: str = "gemini-pro",
    base_url: str = "https://generativelanguage.googleapis.com/v1beta",
    **kwargs
) -> GoogleModel:
    """创建 Google 模型的便捷函数

    Args:
        api_key: Google AI API 密钥
        model: 模型名称
        base_url: API 基础 URL
        **kwargs: 其他配置参数

    Returns:
        GoogleModel: 配置好的 Google 模型实例
    """
    config = ModelConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        max_tokens=kwargs.get("max_tokens", 4096),
        temperature=kwargs.get("temperature", 0.7),
        timeout=kwargs.get("timeout", 120.0)
    )

    return GoogleModel(config)
