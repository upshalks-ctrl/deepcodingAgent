# my_agent - 独立 Agent 框架

一个**完全独立**的 Agent 框架，提供类似 `langchain create_agent` 的功能，同时额外支持 MCP (Model Context Protocol) 工具访问能力。

## ✨ 核心特性

- ✅ **零依赖框架** - 仅使用 Python 标准库 + asyncio
- ✅ **MCP 原生支持** - 支持多服务器 MCP 工具动态加载
- ✅ **简洁架构** - 仅 6 个核心文件，~2355 行代码
- ✅ **易于理解** - 不依赖复杂框架，完全可控
- ✅ **完整功能** - 支持工具调用、异步消息处理、LLM 集成

## 📁 文件结构

```
src/my_agent/
├── __init__.py           # 包导出，公共 API
├── models.py             # 数据模型 (Message, ToolCall, ToolDefinition, ToolResult)
├── mcp_client.py         # 单 MCP 服务器客户端
├── mcp_manager.py        # 多 MCP 服务器管理
├── llm_provider.py       # LLM 抽象层
├── agent.py              # 主 Agent 类和工厂函数
├── examples.py           # 使用示例
└── README.md             # 文档说明
```

## 🚀 快速开始

### 基础使用

```python
import asyncio
from src.my_agent import create_my_agent

async def main():
    # 创建 Agent
    agent = create_my_agent(
        name="MyAgent",
        api_key="your-api-key",
        model="deepseek-chat"
    )

    # 简单对话
    response = await agent.chat("你好，请介绍一下你自己")
    print(response)

    await agent.shutdown()

asyncio.run(main())
```

### 添加 MCP 服务器

```python
async def main():
    agent = create_my_agent(api_key="your-api-key")

    # 添加 MCP 服务器
    await agent.add_mcp_server(
        server_id="file-bash",
        command=["python", "src/mcp/file_bash_server.py"],
        name="File System Server"
    )

    # 使用工具
    response = await agent.run("请帮我读取 README.md 文件")
    print(response)

    await agent.shutdown()

asyncio.run(main())
```

### 注册本地工具

```python
agent = create_my_agent(api_key="your-api-key")

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

# 使用工具
response = await agent.run("请计算 15 * 23 + 7")
```

## 📚 API 参考

### 核心函数

#### `create_my_agent(**kwargs) -> MyAgent`
创建 Agent 实例的工厂函数

**参数:**
- `name`: Agent 名称 (默认: "MyAgent")
- `system_prompt`: 系统提示词
- `api_key`: LLM API 密钥
- `base_url`: LLM API 基础 URL (默认: "https://api.deepseek.com/v1")
- `model`: 模型名称 (默认: "deepseek-chat")
- `max_iterations`: 最大工具调用轮次 (默认: 10)
- `llm_provider`: 自定义 LLM 提供者
- `debug`: 是否启用调试日志 (默认: False)

### MyAgent 类

#### 主要方法

##### `async def add_mcp_server(server_id, command, name=None, env=None) -> bool`
添加 MCP 服务器

##### `async def run(user_input: str) -> str`
运行 Agent 处理用户输入（完整的消息循环）

##### `async def chat(user_input: str) -> str`
简单的聊天接口（无状态）

##### `async def stream_chat(user_input: str) -> AsyncIterator[str]`
流式聊天

##### `def register_tool(name, description, parameters, handler)`
注册本地工具

##### `async def shutdown()`
关闭 Agent

#### 属性

- `tools_count`: 工具数量
- `mcp_servers`: MCP 服务器列表
- `config`: Agent 配置

### 装饰器

#### `@agent.tool(name, description, parameters)`
工具装饰器，用于注册本地工具

```python
@agent.tool(
    name="my_tool",
    description="我的工具",
    parameters={...}
)
def my_tool_handler(arg1: str, arg2: int) -> str:
    return "处理结果"
```

## 🔧 支持的 LLM 提供商

框架支持任何兼容 OpenAI API 格式的 LLM 提供商：

- **DeepSeek** (默认) - `https://api.deepseek.com/v1`
- **OpenAI** - `https://api.openai.com/v1`
- **Anyscale** - `https://api.endpoints.anyscale.com/v1`
- **自定义** - 通过 `base_url` 参数

## 🔌 MCP 集成

框架原生支持 MCP (Model Context Protocol)，可以：

1. **动态加载工具** - 自动发现和加载 MCP 服务器提供的工具
2. **多服务器管理** - 同时连接多个 MCP 服务器
3. **自动路由** - 根据工具名称自动路由到正确的服务器
4. **简单配置** - 只需提供服务器 ID 和启动命令

### 示例 MCP 服务器

框架可以连接任何标准 MCP 服务器，例如：
- 文件系统操作服务器
- Web 搜索服务器
- 数据库操作服务器
- API 调用服务器

## 📝 使用示例

运行示例代码：

```bash
cd D:\code\PythonWorkPath\deepcodeagent1
python src/my_agent/examples.py
```

示例包括：
1. 基础 Agent 创建
2. 带 MCP 服务器的 Agent
3. 注册本地工具
4. 多 MCP 服务器
5. 交互式聊天
6. 流式输出
7. 高级配置

## 🔍 消息处理流程

```
用户输入
    |
    v
[1. 添加消息] -> [2. 调用 LLM] -> [3. 检查工具调用]
                                                  |
                                                  v
                                           [4. 执行工具调用]
                                                  |
                                                  v
                                           [5. 添加工具结果]
                                                  |
                                                  v
                                           [6. 检查迭代次数]
                                                  |
                                           否 -> 回到 [2]
                                           是 -> 返回结果
```

## 🎯 与 langchain 对比

| 特性 | langchain | my_agent |
|------|-----------|----------|
| 依赖 | 10+ 包 | 仅标准库 |
| 代码量 | ~500+ 行 | ~2355 行 |
| 复杂度 | 高 | 中等 |
| MCP 支持 | 有限 | 原生多服务器 |
| 可控性 | 受框架限制 | 完全可控 |
| 学习曲线 | 陡峭 | 平缓 |

## 🛡️ 安全注意事项

1. **工具执行** - 本地工具执行可能存在安全风险，请谨慎使用
2. **API 密钥** - 不要将 API 密钥硬编码在代码中，使用环境变量
3. **文件操作** - MCP 服务器的文件操作可能访问敏感文件，请注意权限控制
4. **命令执行** - 避免执行未知命令，使用白名单机制

## 🐛 调试

启用调试模式：

```python
agent = create_my_agent(
    name="DebugAgent",
    api_key="your-api-key",
    debug=True
)
```

调试模式会输出详细的日志信息，包括：
- 消息处理流程
- 工具调用详情
- LLM API 请求/响应
- MCP 服务器通信

## 📦 依赖

**必需的依赖:**
- Python 3.8+
- asyncio (内置)
- dataclasses (内置)

**可选的依赖:**
- `httpx` - 用于 HTTP 请求（LLM API 调用）

安装可选依赖：
```bash
pip install httpx
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

感谢所有为独立 AI 工具开发做出贡献的开发者！

---

**版本:** 1.0.0
**作者:** Claude Code
**更新:** 2025-12-07
