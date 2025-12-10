# Tools Module - 工具系统

提供工具抽象基类和装饰器，简化工具定义和调用过程。

## 功能特性

- **BaseTool 抽象基类**: 继承后实现 `_run` 方法即可创建工具
- **@tool 装饰器**: 直接装饰函数，自动生成工具定义
- **自动 JSON Schema 生成**: 从类型注解自动生成参数定义
- **异步执行支持**: `_arun` 方法自动使用 `run_in_executor`
- **无缝集成 Agent**: 与 `create_my_agent` 直接集成

## 快速开始

### 方法一：使用 BaseTool 抽象类

```python
from src.tools.decorators import BaseTool
from src.my_agent import create_my_agent
from src.myllms.factory import get_llm_by_type

# 1. 定义工具类
class WeatherTool(BaseTool):
    name = "get_weather"
    description = "获取指定城市的天气信息"

    def _run(self, city: str) -> str:
        """同步执行方法"""
        # 实现你的逻辑
        return f"{city}的天气：晴朗，22°C"

# 2. 创建模型和 Agent
model = get_llm_by_type("basic")
agent = create_my_agent(
    name="MyAgent",
    model=model,
    base_tools=[WeatherTool()]  # 传入工具实例
)

# 3. 使用 Agent
response = await agent.ainvoke("北京天气怎么样？")
```

### 方法二：使用 @tool 装饰器

```python
from src.tools.decorators import tool
from src.my_agent import create_my_agent
from src.myllms.factory import get_llm_by_type

# 1. 装饰函数
@tool()
def get_weather(city: str) -> str:
    """获取指定城市的天气信息"""
    return f"{city}的天气：晴朗，22°C"

@tool(name="calculator", description="执行计算")
def calculate(operation: str, a: float, b: float) -> float:
    """计算器"""
    operations = {
        "add": lambda x, y: x + y,
        "multiply": lambda x, y: x * y
    }
    return operations[operation](a, b)

# 2. 创建模型和 Agent
model = get_llm_by_type("basic")
agent = create_my_agent(
    name="MyAgent",
    model=model,
    decorated_tools=[get_weather, calculate]  # 传入装饰的函数
)

# 3. 使用 Agent
response = await agent.ainvoke("计算 10 + 5")
```

## 详细说明

### BaseTool 抽象基类

#### 特性

- **自动 Schema 生成**: 从 `_run` 方法签名自动生成 JSON Schema
- **异步执行**: 自动实现 `_arun` 方法，使用 `run_in_executor`
- **类型推断**: 支持 `str`、`int`、`float`、`bool`、`list`、`dict` 等类型

#### 示例

```python
class CalculatorTool(BaseTool):
    name = "calculator"
    description = "执行数学计算"

    def _run(self, operation: str, a: float, b: float) -> float:
        """计算器实现"""
        if operation == "add":
            return a + b
        elif operation == "multiply":
            return a * b
        else:
            raise ValueError(f"不支持的操作: {operation}")

# 使用
tool = CalculatorTool()
result = tool._run("add", 10, 5)  # 同步执行
result = await tool._arun("multiply", 3, 4)  # 异步执行

# 获取工具定义
definition = tool.get_tool_definition()
print(definition)
# 输出:
# {
#     "name": "calculator",
#     "description": "执行数学计算",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "operation": {"type": "string"},
#             "a": {"type": "number"},
#             "b": {"type": "number"}
#         },
#         "required": ["operation", "a", "b"]
#     }
# }
```

### @tool 装饰器

#### 特性

- **自动 Schema 生成**: 从函数签名自动生成
- **自定义参数**: 可以覆盖自动生成的 Schema
- **函数原意保持**: 装饰后仍可正常调用函数

#### 示例

```python
# 简单用法（自动生成 Schema）
@tool()
def get_weather(city: str) -> str:
    """获取天气"""
    return f"{city}的天气"

# 自定义名称和描述
@tool(name="weather", description="获取天气信息")
def get_weather_custom(city: str) -> str:
    """自定义描述"""
    return f"{city}的天气"

# 完全自定义参数
custom_params = {
    "type": "object",
    "properties": {
        "city": {
            "type": "string",
            "description": "城市名称",
            "enum": ["北京", "上海", "广州"]
        }
    },
    "required": ["city"]
}

@tool(parameters=custom_params)
def get_weather_with_enum(city: str) -> str:
    """使用枚举参数"""
    return f"{city}的天气"
```

### Agent 集成

#### 混合使用多种工具

```python
from src.my_agent import create_my_agent
from src.tools.decorators import BaseTool, tool
from src.myllms.factory import get_llm_by_type

# BaseTool
class WeatherTool(BaseTool):
    name = "get_weather"
    def _run(self, city: str) -> str:
        return f"{city}的天气"

# 装饰器工具
@tool()
def calculate(a: float, b: float) -> float:
    """计算"""
    return a + b

# 传统方式
def get_time() -> str:
    """获取时间"""
    import datetime
    return datetime.datetime.now().isoformat()

# 创建 Agent
agent = create_my_agent(
    name="MyAgent",
    model=get_llm_by_type("basic"),
    base_tools=[WeatherTool()],
    decorated_tools=[calculate],
    local_tools=[
        {
            "name": "get_time",
            "description": "获取当前时间",
            "parameters": {"type": "object", "properties": {}},
            "handler": get_time
        }
    ]
)
```

#### 动态注册工具

```python
agent = create_my_agent(name="MyAgent", model=model)

# 注册 BaseTool 实例
weather_tool = WeatherTool()
agent.register_tool_from_base_tool(weather_tool)

# 注册装饰器函数
@tool()
def my_tool(param: str) -> str:
    return param

agent.register_tool_from_decorator(my_tool)
```

## 高级用法

### 带默认值的参数

```python
class DatabaseTool(BaseTool):
    name = "query_database"

    def _run(self, table: str, limit: int = 10) -> dict:
        """查询数据库，limit 默认为 10"""
        # 实现查询逻辑
        return {"table": table, "limit": limit}
```

### 复杂类型支持

```python
@tool()
def process_data(data: list, options: dict) -> dict:
    """处理数据和选项"""
    return {
        "processed": len(data),
        "options": options
    }
```

### 异步函数支持

```python
import asyncio

@tool()
async def async_fetch(url: str) -> str:
    """异步获取网页"""
    await asyncio.sleep(1)  # 模拟异步操作
    return f"获取了: {url}"
```

## 最佳实践

### 1. 选择合适的方式

- **BaseTool**: 适合复杂工具，需要状态管理或多个方法
- **@tool 装饰器**: 适合简单工具，快速定义
- **传统方式**: 适合已有函数或特殊需求

### 2. 命名规范

- 使用清晰的工具名称
- 描述要详细说明工具用途
- 参数名称要有意义

```python
# 好的命名
@tool()
def get_weather_forecast(city: str, date: str) -> str:
    """获取指定城市和日期的天气预报"""
    pass

# 避免
@tool()
def tool1(param: str) -> str:
    """工具"""
    pass
```

### 3. 类型注解

始终为参数和返回值添加类型注解，这样能自动生成正确的 Schema。

```python
# 推荐
@tool()
def calculate(a: int, b: int) -> int:
    return a + b

# 不推荐
@tool()
def calculate(a, b):
    return a + b
```

### 4. 错误处理

在工具中处理可能的错误情况。

```python
class SafeCalculator(BaseTool):
    name = "safe_calculator"

    def _run(self, operation: str, a: float, b: float) -> float:
        """安全计算"""
        if operation == "divide" and b == 0:
            raise ValueError("除数不能为零")

        operations = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "multiply": lambda x, y: x * y,
            "divide": lambda x, y: x / y
        }

        if operation not in operations:
            raise ValueError(f"不支持的操作: {operation}")

        return operations[operation](a, b)
```

## API 参考

### BaseTool

#### 属性

- `name: str` - 工具名称（默认使用类名）
- `description: str` - 工具描述（默认使用文档字符串）

#### 方法

- `__init__()` - 初始化工具
- `_run(*args, **kwargs)` - **必须实现**的同步执行方法
- `_arun(*args, **kwargs)` - 异步执行方法（自动实现）
- `get_tool_definition()` - 获取工具定义字典

### @tool 装饰器

#### 参数

- `name: Optional[str]` - 工具名称（默认使用函数名）
- `description: Optional[str]` - 工具描述（默认使用函数文档）
- `parameters: Optional[Dict]` - 自定义参数字典

#### 属性

装饰后的函数会有 `_tool_config` 属性，包含工具配置信息。

### Agent 方法

- `register_tool_from_base_tool(base_tool)` - 从 BaseTool 实例注册
- `register_tool_from_decorator(decorated_func)` - 从装饰函数注册

## 常见问题

### Q: 如何处理复杂参数类型？

A: 目前支持基础类型（str、int、float、bool、list、dict）。复杂类型会被推断为 "string"，可以在工具内部解析。

```python
@tool()
def process_json(json_str: str) -> dict:
    """处理 JSON 字符串"""
    import json
    return json.loads(json_str)
```

### Q: 如何让工具支持异步执行？

A: BaseTool 自动实现 `_arun` 方法。对于装饰器工具，如果函数是异步的，会自动检测。

```python
@tool()
async def async_tool(param: str) -> str:
    """异步工具"""
    await asyncio.sleep(1)
    return param
```

### Q: 如何调试工具？

A: 使用 `log_io` 装饰器或 `LoggedToolMixin`。

```python
from src.tools.decorators import log_io

@log_io
@tool()
def debug_tool(param: str) -> str:
    """带日志的工具"""
    return param

# 或

from src.tools.decorators import create_logged_tool

LoggedWeatherTool = create_logged_tool(WeatherTool)
```

## 示例代码

完整示例请参考：
- `src/tools/examples.py` - 详细使用示例
- `test_tool_system.py` - 测试用例
