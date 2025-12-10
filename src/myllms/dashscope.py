"""
DashScope 模型实现（阿里云）
使用 dashscope 库进行模型调用
"""

import asyncio
import json
from typing import List, Optional, AsyncIterator, Dict, Any, Union
import logging

from .base import BaseModel, ModelConfig, ChatResponse, convert_messages

logger = logging.getLogger(__name__)


class DashScopeModel(BaseModel):
    """DashScope 模型（阿里云）

    基于 DashScope 库实现的模型，支持聊天和工具调用
    """

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
            from dashscope import Generation

            # 转换消息格式
            converted_messages = convert_messages(messages)

            logger.debug(f"Calling DashScope API with model: {self.config.model}")
            logger.debug(f"Messages: {converted_messages}")

            # 准备参数
            api_params = {
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", 0.8),
                "incremental_output": kwargs.get("incremental_output", True),
            }

            # 如果有工具，添加到参数中
            if tools:
                api_params["tools"] = tools

            # 调用 DashScope API - 使用正确的参数格式
            response = Generation.call(
                model=self.config.model,
                messages=converted_messages,
                parameters=api_params,
                api_key=self.config.api_key,
                results_format="message"
            )

            if response.status_code != 200:
                error_msg = f"DashScope API error: {response.status_code} - {response.message}"
                logger.error(error_msg)
                raise Exception(error_msg)

            logger.debug(f"Received response from DashScope API")

            # 解析响应
            output = response.output
            choices = output.get("choices", [])
            if not choices:
                return ChatResponse(
                    content="",
                    finish_reason="stop",
                    model=self.config.model
                )

            choice = choices[0]
            message = choice.get("message", {})

                # 解析工具调用
            tool_calls = None
            if "tool_calls" in message and message["tool_calls"]:
                tool_calls = []
                for tc in message["tool_calls"]:
                    function = tc.get("function", {})
                    arguments = function.get("arguments", "")

                    # 如果 arguments 是字符串，尝试解析为 JSON
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except json.JSONDecodeError:
                            # 如果解析失败，保持原字符串
                            pass

                    tool_calls.append({
                        "id": tc.get("id", f"call_{len(tool_calls)}"),
                        "name": function.get("name", ""),
                        "arguments": arguments
                    })

            return ChatResponse(
                content=message.get("content", ""),
                tool_calls=tool_calls,
                finish_reason=choice.get("finish_reason", "stop"),
                usage=output.get("usage"),
                model='qwen3-coder'
            )

        except ImportError:
            raise ImportError(
                "dashscope is required. Install it with: pip install dashscope"
            )
        except Exception as e:
            logger.error(f"DashScope ainvoke failed: {e}", exc_info=True)
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
            from dashscope import Generation

            # 转换消息格式
            converted_messages = convert_messages(messages)

            logger.debug(f"Calling DashScope API with streaming for model: {self.config.model}")

            # 准备参数
            api_params = {
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", 0.8),
                "incremental_output": True,  # 启用增量输出
            }

            # 如果有工具，添加到参数中
            if tools:
                api_params["tools"] = tools

            # 调用 DashScope API - 流式模式
            response = Generation.call(
                model=self.config.model,
                messages=converted_messages,
                parameters=api_params,
                api_key=self.config.api_key,
                results_format="message"
            )

            if response.status_code != 200:
                error_msg = f"DashScope API error: {response.status_code} - {response.message}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # 流式输出处理
            output = response.output
            if "choices" in output:
                for choice in output["choices"]:
                    if "message" in choice and "content" in choice["message"]:
                        content = choice["message"]["content"]
                        if content:
                            yield content

        except ImportError:
            raise ImportError(
                "dashscope is required. Install it with: pip install dashscope"
            )
        except Exception as e:
            logger.error(f"DashScope astream failed: {e}", exc_info=True)
            raise

    async def close(self):
        """关闭连接（异步）"""
        # DashScope 客户端无需显式关闭
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
            from dashscope import Generation

            # 转换消息格式
            converted_messages = convert_messages(messages)

            logger.debug(f"Calling DashScope API (sync) with model: {self.config.model}")

            # 准备参数
            api_params = {
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", 0.8),
            }

            # 如果有工具，添加到参数中
            if tools:
                api_params["tools"] = tools

            # 调用 DashScope API（同步）
            response = Generation.call(
                model=self.config.model,
                messages=converted_messages,
                parameters=api_params,
                api_key=self.config.api_key,
                results_format="message"
            )

            if response.status_code != 200:
                error_msg = f"DashScope API error: {response.status_code} - {response.message}"
                logger.error(error_msg)
                raise Exception(error_msg)

            logger.debug(f"Received sync response from DashScope API")

            # 解析响应
            output = response.output
            choices = output.get("choices", [])
            if not choices:
                return ChatResponse(
                    content="",
                    finish_reason="stop",
                    model=self.config.model
                )

            choice = choices[0]
            message = choice.get("message", {})

                # 解析工具调用
            tool_calls = None
            if "tool_calls" in message and message["tool_calls"]:
                tool_calls = []
                for tc in message["tool_calls"]:
                    function = tc.get("function", {})
                    arguments = function.get("arguments", "")

                    # 如果 arguments 是字符串，尝试解析为 JSON
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except json.JSONDecodeError:
                            # 如果解析失败，保持原字符串
                            pass

                    tool_calls.append({
                        "id": tc.get("id", f"call_{len(tool_calls)}"),
                        "name": function.get("name", ""),
                        "arguments": arguments
                    })

            return ChatResponse(
                content=message.get("content", ""),
                tool_calls=tool_calls,
                finish_reason=choice.get("finish_reason", "stop"),
                usage=output.get("usage"),
                model='qwen3-coder'
            )

        except ImportError:
            raise ImportError(
                "dashscope is required. Install it with: pip install dashscope"
            )
        except Exception as e:
            logger.error(f"DashScope invoke failed: {e}", exc_info=True)
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
            from dashscope import Generation

            # 转换消息格式
            converted_messages = convert_messages(messages)

            logger.debug(f"Calling DashScope API with sync streaming for model: {self.config.model}")

            # 准备参数
            api_params = {
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", 0.8),
                "incremental_output": True,  # 启用增量输出
            }

            # 如果有工具，添加到参数中
            if tools:
                api_params["tools"] = tools

            # 调用 DashScope API（同步流式）
            response = Generation.call(
                model=self.config.model,
                messages=converted_messages,
                parameters=api_params,
                api_key=self.config.api_key,
                results_format="message"
            )

            if response.status_code != 200:
                error_msg = f"DashScope API error: {response.status_code} - {response.message}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # 收集流式输出
            chunks = []
            output = response.output
            if "choices" in output:
                for choice in output["choices"]:
                    if "message" in choice and "content" in choice["message"]:
                        content = choice["message"]["content"]
                        if content:
                            chunks.append(content)

            return "".join(chunks)

        except ImportError:
            raise ImportError(
                "dashscope is required. Install it with: pip install dashscope"
            )
        except Exception as e:
            logger.error(f"DashScope stream failed: {e}", exc_info=True)
            raise

    def close_sync(self):
        """关闭连接（同步）"""
        # DashScope 客户端无需显式关闭
        pass


def create_dashscope_model(
    api_key: str,
    model: str = "qwen-turbo",
    base_url: str = "https://dashscope.aliyuncs.com/api/v1",
    **kwargs
) -> DashScopeModel:
    """创建 DashScope 模型的便捷函数

    Args:
        api_key: DashScope API 密钥
        model: 模型名称
        base_url: API 基础 URL
        **kwargs: 其他配置参数

    Returns:
        DashScopeModel: 配置好的 DashScope 模型实例
    """
    config = ModelConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        max_tokens=kwargs.get("max_tokens", 4096),
        temperature=kwargs.get("temperature", 0.7),
        timeout=kwargs.get("timeout", 120.0)
    )

    return DashScopeModel(config)
