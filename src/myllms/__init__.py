"""
myllms - 多模型提供商支持

支持多种 LLM 提供商：
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- DashScope (阿里云)

所有模型都实现了相同的接口，支持同步和异步调用。
"""

from .base import (
    BaseModel,
    ModelConfig,
    ChatResponse,
    convert_messages,
)

from .openai import (
    OpenAIModel,
    create_openai_model,
)

from .anthropic import (
    AnthropicModel,
    create_anthropic_model,
)

from .google import (
    GoogleModel,
    create_google_model,
)

from .dashscope import (
    DashScopeModel,
    create_dashscope_model,
)

from .factory import (
    create_model,
    get_llm_by_type,
    load_config_from_file,
    get_supported_providers,
    get_provider_info,
    _infer_provider_from_model,
)

# 包版本
__version__ = "2.0.0"
__author__ = "Claude Code"

# 公共 API
__all__ = [
    # 基础类
    "BaseModel",
    "ModelConfig",
    "ChatResponse",
    "convert_messages",

    # OpenAI
    "OpenAIModel",
    "create_openai_model",

    # Anthropic
    "AnthropicModel",
    "create_anthropic_model",

    # Google
    "GoogleModel",
    "create_google_model",

    # DashScope
    "DashScopeModel",
    "create_dashscope_model",

    # 工厂函数
    "create_model",
    "get_llm_by_type",
    "load_config_from_file",
    "get_supported_providers",
    "get_provider_info",
]

# 便捷别名
openai = create_openai_model
anthropic = create_anthropic_model
google = create_google_model
dashscope = create_dashscope_model

# 使用示例
"""
使用示例：

1. 直接创建模型（推荐）：
```python
from src.myllms import create_model

# OpenAI
model = create_model(
    url="https://api.openai.com/v1",
    api_key="your-key",
    model="gpt-4o-mini"
)

# Anthropic
model = create_model(
    url="https://api.anthropic.com/v1",
    api_key="your-key",
    model="claude-3-5-sonnet-20241022"
)

# Google
model = create_model(
    url="https://generativelanguage.googleapis.com/v1beta",
    api_key="your-key",
    model="gemini-pro"
)

# DashScope
model = create_model(
    url="https://dashscope.aliyuncs.com/api/v1",
    api_key="your-key",
    model="qwen-turbo"
)
```

2. 从配置文件自动加载：
```python
from src.myllms import get_llm_by_type

# conf.yaml 内容示例：
# BASIC_MODEL:
#   model: "gpt-4o-mini"
#   api_key: "YOUR_API_KEY_HERE"
#   base_url: "https://api.openai.com/v1"
#   max_tokens: 4096
#   temperature: 0.7

model = get_llm_by_type("basic")
```

3. 异步使用：
```python
import asyncio
from src.myllms import create_model

async def main():
    model = create_model(
        url="https://api.openai.com/v1",
        api_key="your-key",
        model="gpt-4o-mini"
    )

    messages = [
        {"role": "user", "content": "你好"}
    ]

    response = await model.chat(messages)
    print(response.content)

    async for chunk in model.stream_chat(messages):
        print(chunk, end="")

asyncio.run(main())
```

4. 同步使用：
```python
from src.myllms import create_model

model = create_model(
    url="https://api.openai.com/v1",
    api_key="your-key",
    model="gpt-4o-mini"
)

messages = [
    {"role": "user", "content": "你好"}
]

response = model.chat_sync(messages)
print(response.content)

result = model.stream_chat_sync(messages)
print(result)
```
"""
