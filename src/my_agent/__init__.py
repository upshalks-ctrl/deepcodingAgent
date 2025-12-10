"""
my_agent - 独立的 Agent 框架

一个类似 langchain create_agent 的独立实现，额外支持 MCP 工具访问能力。

主要特性：
- 零依赖框架（仅使用 Python 标准库 + asyncio）
- 原生支持 MCP (Model Context Protocol) 多服务器工具
- 异步消息处理循环
- 灵活的 LLM 提供者抽象层
- 简单的工具注册和调用机制
- 中间件管道处理
- 人在环中模式

使用示例：
```python
import asyncio
from src.my_agent import create_my_agent

async def main():
    # 创建 Agent
    agent = create_my_agent(
        name="CodeAssistant",
        model_provider="deepseek",
        api_key="your-api-key"
    )

    # 添加 MCP 服务器
    await agent.add_mcp_server(
        "file-bash",
        ["python", "src/mcp/file_bash_server.py"]
    )

    # 运行 Agent
    response = await agent.run("请帮我读取 README.md 文件")
    print(response)

    await agent.shutdown()

asyncio.run(main())
```
"""

from typing import Optional

# 核心类和函数
from .models import (
    Message,
    ToolDefinition,
    ToolResult,
    AgentInfo,
)


from src.human_in_the_loop import HumanInTheLoop, FunctionHumanInTheLoop

from .agent import (
    MyAgent,
    AgentConfig,
    AgentState,
    create_my_agent,
)

# 包版本
__version__ = "1.0.0"
__author__ = "Claude Code"
__description__ = "Independent Agent framework with MCP support"

# 公共 API
__all__ = [
    # 数据模型
    "Role",
    "Message",
    "ToolDefinition",
    "ToolResult",
    "AgentInfo",

    # LLM 相关
    "BaseLLMProvider",
    "HTTPLLMProvider",
    "LLMConfig",
    "LLMResponse",
    "create_llm_provider",

    # 中间件
    "Middleware",
    "MiddlewareContext",
    "MiddlewareChain",
    "LoggingMiddleware",
    "ValidationMiddleware",
    "TimingMiddleware",

    # 人在环中
    "HumanInTheLoop",
    "FunctionHumanInTheLoop",
    "ConsoleHumanInTheLoop",

    # Agent 核心
    "MyAgent",
    "AgentConfig",
    "AgentState",
    "create_my_agent",
]


# 快捷方式
create = create_my_agent
agent = create_my_agent

# 日志配置
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
