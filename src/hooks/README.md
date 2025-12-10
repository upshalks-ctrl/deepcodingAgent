# 上下文管理器使用指南

本指南展示如何在项目中使用上下文管理器来控制对话历史和避免 token 超限。

## 快速开始

### 1. 基础使用 - 直接注册钩子

```python
from src.my_agent.agent import MyAgent, AgentConfig
from src.myllms import get_llm_by_type
from src.hooks.context_manager import create_context_compression_hook

# 创建 Agent
model = get_llm_by_type("basic")
config = AgentConfig(
    name="MyAgent",
    system_prompt="你是一个有用的助手",
    max_iterations=5
)

agent = MyAgent(config=config, model=model)

# 创建并注册上下文压缩钩子
compression_hook = create_context_compression_hook(
    max_tokens=50000,  # 最大允许的 tokens 数
    model="basic"      # 用于压缩的模型
)

# 注册钩子
agent.register_hook(agent.hooks.HookEvent.BEFORE_MODEL, compression_hook)

# 现在 Agent 会自动管理上下文
response = await agent.arun("你好")
```

### 2. 使用混入类（推荐）

```python
from src.my_agent.agent import MyAgent, AgentConfig
from src.myllms import get_llm_by_type
from src.hooks.integration_example import ContextManagerMixin

class ContextAwareAgent(ContextManagerMixin, MyAgent):
    """自动启用上下文管理的 Agent"""
    pass

# 创建 Agent（会自动根据环境配置启用上下文管理）
agent = ContextAwareAgent(
    config=AgentConfig(
        name="SmartAgent",
        system_prompt="你是一个有用的助手"
    ),
    model=get_llm_by_type("basic")
)

# 直接使用，无需额外配置
response = await agent.arun("处理长对话...")
```

### 3. 使用装饰器方式

```python
from src.hooks import hook, HookEvent
from src.my_agent.agent import MyAgent

@hook(HookEvent.BEFORE_MODEL, priority=10)
async def custom_compression(context):
    """自定义压缩逻辑"""
    if context.event_type != HookEvent.BEFORE_MODEL:
        return context

    messages = context.data.get("messages", [])
    # 自定义压缩逻辑
    if len(messages) > 10:
        # 压缩逻辑
        context.data["messages"] = messages[-10:]

    return context

# 全局注册后，所有 Agent 都会使用这个压缩逻辑
```

## 配置选项

### 环境变量配置

设置 `ENVIRONMENT` 环境变量来自动选择配置：

```bash
# 开发环境 - 不压缩或宽松限制
export ENVIRONMENT=development

# 测试环境 - 基础压缩
export ENVIRONMENT=testing

# 生产环境 - 标准压缩
export ENVIRONMENT=production
```

### 预定义配置

| 配置名称 | 最大 tokens | 适用场景 |
|---------|-----------|----------|
| `development` | 200000 | 开发调试，基本不压缩 |
| `basic` | 50000 | 测试环境，适度压缩 |
| `compact` | 30000 | 资源受限环境 |
| `high_capacity` | 100000 | 高容量场景 |
| `production` | 80000 | 生产环境 |

## 在 Architecture Team V2 中使用

### 方法一：修改 Search 类

```python
# 在 architecture_team_v2.py 中
from src.hooks.context_manager import create_context_compression_hook

class Search:
    def __init__(self, model, output_dir: Path = None):
        self.model = model
        self.output_dir = output_dir or Path("@testdir")

        # 创建 Agent
        self.agent = create_agent_with_tools(
            agent_name="searcher",
            model=model,
            system_prompt=load_agent_prompt("searcher")
        )

        # 添加上下文压缩
        compression_hook = create_context_compression_hook(
            max_tokens=30000,  # 搜索器使用较小限制
            model="basic"
        )
        self.agent.register_hook(HookEvent.BEFORE_MODEL, compression_hook)
```

### 方法二：使用混入类

```python
# 创建一个支持上下文管理的 Agent 基类
from src.hooks.integration_example import ContextManagerMixin
from src.my_agent.agent import MyAgent

class ContextAwareMyAgent(ContextManagerMixin, MyAgent):
    pass

# 在 tool_registry.py 中修改
def create_agent_with_tools(agent_name: str, model, system_prompt: str = None, output_dir: Path = None):
    # ...
    agent = ContextAwareMyAgent(config=config, model=model)
    # ...
```

## 高级用法

### 1. 自适应压缩

```python
from src.hooks.adaptive_context_manager import create_adaptive_context_compression_hook

# 使用自适应压缩，会智能选择压缩策略
adaptive_hook = create_adaptive_context_compression_hook(
    max_tokens=80000,
    model="reasoning"  # 使用更强的模型进行压缩
)

agent.register_hook(HookEvent.BEFORE_MODEL, adaptive_hook)
```

### 2. 自定义压缩钩子

```python
from src.hooks.hooks import Hook, HookEvent, HookContext

class MyCompressionHook(Hook):
    async def execute(self, context: HookContext) -> HookContext:
        if context.event_type == HookEvent.BEFORE_MODEL:
            messages = context.data.get("messages", [])

            # 自定义逻辑：保留用户问题，压缩助手回答
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]

            if len(assistant_messages) > 5:
                # 只保留最近的5个助手回答
                assistant_messages = assistant_messages[-5:]

                # 生成摘要
                summary = f"之前有{len(messages) - len(user_messages) - len(assistant_messages)}条助手回复已压缩"

                # 重新组合消息
                messages = user_messages + [
                    {"role": "system", "content": summary}
                ] + assistant_messages

                context.data["messages"] = messages

        return context
```

### 3. 监控压缩效果

```python
@hook(HookEvent.AFTER_MODEL)
async def monitor_compression(context):
    """监控压缩效果"""
    if "compressed" in context.metadata:
        original = context.metadata.get("original_tokens", 0)
        compressed = context.metadata.get("compressed_tokens", 0)

        if original > 0:
            reduction = (1 - compressed / original) * 100
            logger.info(f"压缩率: {reduction:.1f}% ({original} -> {compressed} tokens)")
```

## 最佳实践

### 1. 选择合适的 tokens 限制

- **简单任务**: 30,000 - 50,000 tokens
- **复杂任务**: 80,000 - 100,000 tokens
- **长对话**: 使用自适应压缩

### 2. 压缩策略选择

- 保留最近的消息（通常 5-10 条）
- 系统消息可以合并，但保留最新的指令
- 工具响应可以截断，只保留关键信息
- 使用更强的模型进行压缩效果更好

### 3. 性能优化

```python
# 对于高频调用，可以缓存压缩结果
from functools import lru_cache

class CachedCompressionHook(Hook):
    @lru_cache(maxsize=100)
    async def cached_summarize(self, content_hash: str, content: str):
        # 缓存压缩结果
        pass
```

### 4. 调试技巧

```python
# 启用详细日志
import logging
logging.getLogger("src.hooks").setLevel(logging.INFO)

# 添加钩子来观察处理过程
@hook(HookEvent.BEFORE_MODEL)
async def debug_messages(context):
    messages = context.data.get("messages", [])
    print(f"消息数量: {len(messages)}")
    print(f"估算 tokens: {sum(len(m.get('content', '')) for m in messages) // 2.5}")
    return context
```

## 故障排除

### 问题：压缩后上下文丢失

**解决方案**：检查压缩策略，确保关键信息被保留

```python
# 在压缩钩子中添加检查
if len(compressed_messages) < 3:
    logger.warning("压缩后消息太少，可能丢失重要上下文")
    # 保留更多消息
```

### 问题：压缩效果不佳

**解决方案**：使用更强的模型或调整压缩提示

```python
# 使用 reasoning 模型进行压缩
compression_hook = create_context_compression_hook(
    max_tokens=50000,
    model="reasoning"  # 更强的模型
)
```

### 问题：性能影响

**解决方案**：
- 使用缓存避免重复压缩
- 调整压缩频率
- 使用更简单的压缩策略

## 示例项目

查看 `integration_example.py` 获取完整的集成示例。