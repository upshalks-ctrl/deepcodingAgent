# my_agent 使用指南

完整的 `create_my_agent` 使用指南，展示所有功能。

## 目录
- [基础使用](#基础使用)
- [模型配置](#模型配置)
- [MCP 工具集成](#mcp-工具集成)
- [本地工具](#本地工具)
- [中间件系统](#中间件系统)
- [人在环中](#人在环中)
- [完整示例](#完整示例)

---

## 基础使用

### 1. 创建简单 Agent

```python
import asyncio
from src.my_agent import create_my_agent

async def main():
    # 创建 Agent（使用 DeepSeek 模型）
    agent = create_my_agent(
        name="MyAgent",
        model_provider="deepseek",
        api_key="your-api-key",
        model_name="deepseek-chat"
    )

    # 简单对话
    response = await agent.chat("你好，请介绍一下你自己")
    print(response)

    await agent.shutdown()

asyncio.run(main())
```

### 2. 使用环境变量

```python
# 设置环境变量
# export DEEPSEEK_API_KEY="your-api-key"

agent = create_my_agent(
    name="EnvAgent",
    model_provider="deepseek",
    model_name="deepseek-chat"
)
```

---

## 模型配置

支持多种模型提供商：

### DeepSeek（默认）
```python
agent = create_my_agent(
    model_provider="deepseek",
    api_key="your-key",
    model_name="deepseek-chat",  # 或 deepseek-coder
    base_url="https://api.deepseek.com/v1"
)
```

### OpenAI
```python
agent = create_my_agent(
    model_provider="openai",
    api_key="your-key",
    model_name="gpt-4",
    base_url="https://api.openai.com/v1"
)
```

### Anyscale
```python
agent = create_my_agent(
    model_provider="anyscale",
    api_key="your-key",
    model_name="meta-llama/Llama-2-70b-chat-hf",
    base_url="https://api.endpoints.anyscale.com/v1"
)
```

### 自定义模型实例
```python
from src.myllms import create_model

# 创建模型实例
model = create_model(
    provider="deepseek",
    api_key="your-key",
    model_name="deepseek-chat"
)

# 使用自定义模型
agent = create_my_agent(
    name="CustomAgent",
    model=model
)
```

---

## MCP 工具集成

### 1. 添加 MCP 服务器

```python
agent = create_my_agent(
    name="MCPAgent",
    model_provider="deepseek",
    api_key="your-key"
)

# 添加 MCP 服务器
await agent.add_mcp_server(
    server_id="file-bash",
    command=["python", "src/mcp/file_bash_server.py"],
    name="File System Server"
)

# 使用 MCP 工具
response = await agent.run("请列出当前目录的文件")
```

### 2. 使用工厂函数

```python
agent = create_my_agent(
    name="MCPAgent",
    model_provider="deepseek",
    api_key="your-key",
    mcp_servers=[
        {
            "id": "file-bash",
            "command": ["python", "src/mcp/file_bash_server.py"],
            "name": "File System Server"
        }
    ]
)
```

### 3. 多个 MCP 服务器

```python
agent = create_my_agent(
    name="MultiServerAgent",
    model_provider="deepseek",
    api_key="your-key",
    mcp_servers=[
        {
            "id": "file-ops",
            "command": ["python", "file_server.py"],
            "name": "File Operations"
        },
        {
            "id": "web-search",
            "command": ["python", "search_server.py"],
            "name": "Web Search"
        },
        {
            "id": "database",
            "command": ["python", "db_server.py"],
            "name": "Database"
        }
    ]
)
```

---

## 本地工具

### 1. 使用装饰器

```python
agent = create_my_agent(
    name="ToolAgent",
    model_provider="deepseek",
    api_key="your-key"
)

# 注册本地工具
@agent.tool(
    name="calculate",
    description="计算数学表达式",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "要计算的数学表达式"
            }
        },
        "required": ["expression"]
    }
)
def calculate(expression: str) -> str:
    return str(eval(expression))

# 使用本地工具
response = await agent.run("请计算 15 * 23 + 7")
```

### 2. 手动注册

```python
def get_current_time() -> dict:
    from datetime import datetime
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S")
    }

agent.register_tool(
    name="get_time",
    description="获取当前时间",
    parameters={"type": "object", "properties": {}},
    handler=get_current_time
)
```

### 3. 异步工具

```python
@agent.tool(
    name="fetch_data",
    description="异步获取数据",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string"}
        },
        "required": ["url"]
    }
)
async def fetch_data(url: str) -> dict:
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return {"status": response.status, "data": await response.text()}
```

---

## 中间件系统

中间件可以拦截"输入 -> 处理 -> 输出"管道中的数据。

### 1. 函数式中间件

```python
import logging

# 日志中间件
def logging_middleware(context):
    logging.info(f"Processing: {context.data}")
    return context

# 验证中间件
def validation_middleware(context):
    if not context.data:
        context.add_error("Empty input")
    return context

agent = create_my_agent(
    name="LoggingAgent",
    model_provider="deepseek",
    api_key="your-key",
    middlewares=[
        logging_middleware,
        validation_middleware
    ]
)
```

### 2. 预定义中间件

```python
from src.my_agent import LoggingMiddleware, ValidationMiddleware, TimingMiddleware

agent = create_my_agent(
    name="AdvancedAgent",
    model_provider="deepseek",
    api_key="your-key",
    middlewares=[
        LoggingMiddleware(),
        ValidationMiddleware(required_fields=["user_input"]),
        TimingMiddleware()
    ]
)
```

### 3. 自定义中间件类

```python
from src.my_agent import Middleware, MiddlewareContext

class CustomMiddleware(Middleware):
    async def process(self, context: MiddlewareContext, **kwargs):
        # 处理逻辑
        context.data = context.data.upper()  # 示例：转大写
        return context

    def get_name(self):
        return "CustomMiddleware"

agent = create_my_agent(
    name="CustomMiddlewareAgent",
    model_provider="deepseek",
    api_key="your-key",
    middlewares=[CustomMiddleware()]
)
```

### 4. 中间件执行阶段

中间件在以下阶段执行：
- `preprocess` - 预处理用户输入
- `system_message` - 处理系统消息
- `user_message` - 处理用户消息
- `tools` - 处理工具列表
- `before_llm_call` - LLM 调用前
- `llm_response` - 处理 LLM 响应
- `assistant_message` - 处理助手消息
- `before_tool_call` - 工具调用前
- `tool_result` - 处理工具结果
- `tool_message` - 处理工具消息
- `final_response` - 处理最终响应
- `error` - 处理错误

---

## 人在环中

人在环中模式允许在自动化流程中引入人工决策。

### 1. 函数式人在环中

```python
def simple_approval(context):
    """简单的审批函数"""
    response = input("是否继续? (y/n): ").strip().lower()
    return response in ["y", "yes", "是"]

agent = create_my_agent(
    name="SafeAgent",
    model_provider="deepseek",
    api_key="your-key",
    human_in_the_loop=simple_approval
)
```

### 2. 异步审批

```python
async def async_approval(context):
    """异步审批函数"""
    print(f"当前操作: {context.data}")
    response = input("是否批准? (y/n): ").strip().lower()
    return response in ["y", "yes", "是"]

agent = create_my_agent(
    name="AsyncApprovalAgent",
    model_provider="deepseek",
    api_key="your-key",
    human_in_the_loop=async_approval
)
```

### 3. 控制台人在环中

```python
from src.my_agent import ConsoleHumanInTheLoop

agent = create_my_agent(
    name="ConsoleAgent",
    model_provider="deepseek",
    api_key="your-key",
    human_in_the_loop=ConsoleHumanInTheLoop(
        prompt="请确认是否继续? (y/n): "
    )
)
```

### 4. 高级人在环中

```python
from src.my_agent import HumanInTheLoop, MiddlewareContext

class ApprovalMiddleware(HumanInTheLoop):
    def __init__(self, approve_tools=None):
        self.approve_tools = approve_tools or []

    async def interrupt(self, context: MiddlewareContext, **kwargs):
        print("\n" + "=" * 60)
        print("人在环中中断")
        print("=" * 60)

        # 检查是否是需要审批的工具
        tool_name = context.get_metadata("tool_name")
        if tool_name in self.approve_tools:
            print(f"工具 '{tool_name}' 需要人工审批")
            return True
        return True

    async def approve(self, context: MiddlewareContext, **kwargs):
        # 复杂的审批逻辑
        tool_name = context.get_metadata("tool_name")
        arguments = context.get_metadata("arguments", {})

        print(f"工具: {tool_name}")
        print(f"参数: {arguments}")

        response = input("是否批准? (y/n): ").strip().lower()
        return response in ["y", "yes", "是"]

    def get_name(self):
        return "ApprovalMiddleware"

agent = create_my_agent(
    name="ApprovalAgent",
    model_provider="deepseek",
    api_key="your-key",
    human_in_the_loop=ApprovalMiddleware(
        approve_tools=["delete_file", "execute_command"]
    )
)
```

---

## 完整示例

### 示例 1: 带 MCP 和中间件的 Agent

```python
import asyncio
import logging
from src.my_agent import (
    create_my_agent,
    LoggingMiddleware,
    ConsoleHumanInTheLoop
)

async def main():
    # 创建中间件
    middlewares = [
        LoggingMiddleware(),
        lambda ctx: ctx  # 简单传递中间件
    ]

    # 创建人在环中
    human = ConsoleHumanInTheLoop()

    # 创建 Agent
    agent = create_my_agent(
        name="CompleteAgent",
        model_provider="deepseek",
        api_key="your-key",
        system_prompt="你是一个有用的助手，可以使用工具。",
        max_iterations=10,
        middlewares=middlewares,
        human_in_the_loop=human,
        mcp_servers=[
            {
                "id": "file-bash",
                "command": ["python", "src/mcp/file_bash_server.py"]
            }
        ]
    )

    # 注册本地工具
    @agent.tool(
        name="calculate",
        description="计算数学表达式",
        parameters={
            "type": "object",
            "properties": {
                "expression": {"type": "string"}
            },
            "required": ["expression"]
        }
    )
    def calculate(expression: str) -> str:
        return str(eval(expression))

    # 交互式聊天
    print("输入 'exit' 退出聊天\n")
    while True:
        user_input = input("> ").strip()
        if user_input.lower() == "exit":
            break

        response = await agent.run(user_input)
        print(f"\nAssistant: {response}\n")

    await agent.shutdown()

asyncio.run(main())
```

### 示例 2: 多功能 Agent

```python
import asyncio
from src.my_agent import create_my_agent

async def main():
    # 创建 Agent
    agent = create_my_agent(
        name="MultiFunctionAgent",
        model_provider="deepseek",
        api_key="your-key",
        system_prompt="你是一个多功能助手。",
        max_iterations=15,
        debug=True
    )

    # 添加 MCP 服务器
    await agent.add_mcp_server(
        "file-ops",
        ["python", "file_server.py"],
        "File Operations"
    )

    # 注册多个本地工具
    @agent.tool(
        name="weather",
        description="获取天气信息",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string"}
            },
            "required": ["city"]
        }
    )
    def get_weather(city: str) -> str:
        return f"{city} 的天气：晴朗，温度 25°C"

    @agent.tool(
        name="translate",
        description="翻译文本",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "target_lang": {"type": "string"}
            },
            "required": ["text", "target_lang"]
        }
    )
    def translate(text: str, target_lang: str) -> str:
        return f"[翻译到 {target_lang}] {text}"

    # 测试不同的功能
    test_queries = [
        "计算 100 * 5 + 20",
        "查询北京的天气",
        "将 'Hello World' 翻译成中文",
        "列出当前目录的文件"
    ]

    for query in test_queries:
        print(f"\n查询: {query}")
        response = await agent.run(query)
        print(f"回答: {response}")

    await agent.shutdown()

asyncio.run(main())
```

### 示例 3: 带审批的敏感操作 Agent

```python
import asyncio
from src.my_agent import create_my_agent

async def sensitive_operation_approval(context):
    """敏感操作审批"""
    tool_name = context.get_metadata("tool_name")
    arguments = context.get_metadata("arguments", {})

    print(f"\n⚠️  检测到敏感操作")
    print(f"工具: {tool_name}")
    print(f"参数: {arguments}")

    response = input("是否批准此操作? (yes/no): ").strip().lower()
    return response == "yes"

async def main():
    agent = create_my_agent(
        name="SecureAgent",
        model_provider="deepseek",
        api_key="your-key",
        human_in_the_loop=sensitive_operation_approval,
        mcp_servers=[
            {
                "id": "file-bash",
                "command": ["python", "src/mcp/file_bash_server.py"]
            }
        ]
    )

    # 测试敏感操作
    response = await agent.run(
        "请删除名为 'important.txt' 的文件"
    )
    print(f"结果: {response}")

    await agent.shutdown()

asyncio.run(main())
```

---

## 更多资源

- [README](README.md) - 快速开始
- [examples.py](examples.py) - 更多示例
- [API 文档](API_REFERENCE.md) - 完整 API 参考

---

**版本**: 1.0.0
**更新**: 2025-12-07
