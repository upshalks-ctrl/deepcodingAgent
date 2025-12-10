# myllms - 多模型提供商支持

支持多种 LLM 提供商的统一接口，包括 OpenAI、Anthropic、Google 和 DashScope。

## 特性

- ✅ **统一接口** - 所有模型都实现相同的 BaseModel 接口
- ✅ **多提供商支持** - OpenAI, Anthropic, Google, DashScope
- ✅ **同步和异步** - 支持 async/await 和同步调用
- ✅ **流式输出** - 支持实时流式响应
- ✅ **工具调用** - 支持函数调用和工具调用
- ✅ **配置文件** - 支持从 YAML/JSON 配置文件加载
- ✅ **自动推断** - 优先根据 base_url 自动推断提供商，备选根据模型名称推断

## 安装

```bash
pip install httpx pyyaml
```

## 支持的提供商

| 提供商 | 模型示例 | 默认模型 | 环境变量 |
|--------|----------|----------|----------|
| **OpenAI** | GPT-4, GPT-3.5 | gpt-4o-mini | OPENAI_API_KEY |
| **Anthropic** | Claude-3.5, Claude-3 | claude-3-5-sonnet-20241022 | ANTHROPIC_API_KEY |
| **Google** | Gemini Pro, Gemini Ultra | gemini-pro | GOOGLE_API_KEY |
| **DashScope** | Qwen Turbo, Qwen Plus, Qwen Max | qwen-turbo | DASHSCOPE_API_KEY |

## 快速开始

### 1. 根据模型类型创建模型（推荐）

```python
from src.myllms import create_model

# 基础模型（对话、问答）
model = create_model(
    model_type="basic",
    config_path="conf.yaml"
)

# 代码模型（编程、代码生成）
model = create_model(
    model_type="coder",
    config_path="conf.yaml"
)

# 视觉模型（图像理解）
model = create_model(
    model_type="vision",
    config_path="conf.yaml"
)

# 推理模型（复杂逻辑、思考）
model = create_model(
    model_type="reasoning",
    config_path="conf.yaml"
)
```

### 2. 直接传递配置字典

```python
config_dict = {
    "BASIC_MODEL": {
        "model": "gpt-4o-mini",
        "api_key": "your-key",
        "base_url": "https://api.openai.com/v1",
        "max_tokens": 4096,
        "temperature": 0.7
    }
}

model = create_model("basic", config_dict=config_dict)
```

### 3. 从配置文件加载

创建 `conf.yaml` 文件：

```yaml
BASIC_MODEL:
  model: "gpt-4o-mini"
  api_key: "YOUR_API_KEY_HERE"
  base_url: "https://api.openai.com/v1"
  max_tokens: 4096
  temperature: 0.7

ADVANCED_MODEL:
  model: "claude-3-5-sonnet-20241022"
  api_key: "YOUR_ANTHROPIC_KEY"
  base_url: "https://api.anthropic.com/v1"
  max_tokens: 8192
  temperature: 0.5
```

加载模型：

```python
from src.myllms import get_llm_by_type

# 从配置文件加载
model = get_llm_by_type("BASIC_MODEL", "conf.yaml")
```

### 4. 异步使用

```python
import asyncio
from src.myllms import create_model

async def main():
    model = create_model(
        model_type="basic",
        config_path="conf.yaml"
    )

    messages = [
        {"role": "user", "content": "你好"}
    ]

    # 发送请求
    response = await model.chat(messages)
    print(response.content)

    # 流式响应
    async for chunk in model.stream_chat(messages):
        print(chunk, end="")

asyncio.run(main())
```

### 5. 同步使用

```python
from src.myllms import create_model

model = create_model(
    model_type="basic",
    config_path="conf.yaml"
)

messages = [
    {"role": "user", "content": "你好"}
]

# 同步请求
response = model.chat_sync(messages)
print(response.content)

# 同步流式响应
result = model.stream_chat_sync(messages)
print(result)
```

### 6. 使用环境变量

```bash
export BASIC_MODEL__api_key="your-key"
export CODE_MODEL__api_key="your-key"
export VISION_MODEL__api_key="your-key"
export REASONING_MODEL__api_key="your-key"
```

```python
from src.myllms import create_model

# 会自动从环境变量获取 API 密钥
model = create_model(
    model_type="basic",
    config_path="conf.yaml"
)
```

## API 参考

### create_model()

根据模型类型创建模型实例的工厂函数。

**参数:**
- `model_type`: 模型类型 ("basic", "coder", "vision", "reasoning")
- `config_path`: 配置文件路径（可选，默认使用 conf.yaml）
- `config_dict`: 配置字典（可选，如果提供，将忽略 config_path）
- `**kwargs`: 其他配置参数，会覆盖配置文件中的设置

**返回:** BaseModel 实例

**支持的模型类型:**
- `basic`: 基础模型（对话、问答）
- `coder`: 代码模型（编程、代码生成）
- `vision`: 视觉模型（图像理解）
- `reasoning`: 推理模型（复杂逻辑、思考）

### get_llm_by_type()

根据配置文件中的模型定义创建模型实例（主要用于向后兼容）。

**参数:**
- `model_type`: 配置键名（如 "BASIC_MODEL", "CODE_MODEL", "VISION_MODEL", "REASONING_MODEL"）
- `config_path`: 配置文件路径（可选）
- `config_dict`: 配置字典（可选）

**返回:** BaseModel 实例

**注意:** 推荐使用 `create_model()` 函数，根据模型类型（basic, coder, vision, reasoning）创建模型更简洁。

### BaseModel

所有模型的基类。

#### 异步方法

- `async def chat(messages, tools=None, **kwargs) -> ChatResponse`
- `async def stream_chat(messages, tools=None, **kwargs) -> AsyncIterator[str]`
- `async def close()`

#### 同步方法

- `def chat_sync(messages, tools=None, **kwargs) -> ChatResponse`
- `def stream_chat_sync(messages, tools=None, **kwargs) -> Union[str, List[str]]`
- `def close_sync()`

## 配置示例

查看 `conf.yaml.example` 文件获取完整的配置示例。

支持的配置字段：

- `model`: 模型名称（必需）
- `api_key`: API 密钥（必需）
- `base_url`: API 基础 URL（可选）
- `max_tokens`: 最大输出令牌数（可选，默认 4096）
- `temperature`: 温度参数（可选，默认 0.7）
- `timeout`: 超时时间（可选，默认 120）

## 示例

运行示例代码：

```bash
python src/myllms/examples.py
```

示例包括：
1. 直接创建模型
2. 从配置文件加载
3. 使用配置字典
4. 异步使用
5. 同步使用
6. 环境变量
7. 提供商信息
8. 工具调用
9. 上下文管理器

## 注意事项

1. **API 密钥安全** - 不要将 API 密钥硬编码在代码中，使用环境变量或配置文件
2. **配置文件权限** - 确保配置文件权限安全，避免泄露 API 密钥
3. **错误处理** - 建议在生产环境中添加适当的错误处理和重试逻辑
4. **速率限制** - 注意各提供商的 API 速率限制

## 许可证

MIT License

---

**版本:** 2.0.0
**更新:** 2025-12-07
