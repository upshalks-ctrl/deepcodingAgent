# 常见问题解答 (FAQ)

本文档收集了 DeepCodeAgent 的常见问题和解决方案。

## 目录

- [安装和配置](#安装和配置)
- [使用问题](#使用问题)
- [API和集成](#api和集成)
- [性能和优化](#性能和优化)
- [错误排查](#错误排查)
- [高级功能](#高级功能)

---

## 安装和配置

### Q: 安装时出现依赖冲突怎么办？
A: 建议使用虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

如果仍有冲突，可以尝试：
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --force-reinstall
```

### Q: 如何配置多个LLM提供商？
A: 编辑 `conf.yaml` 文件：
```yaml
BASIC_MODEL:
  base_url: https://api.openai.com
  model: "gpt-4"
  api_key: "your_openai_key"

CODE_MODEL:
  base_url: https://api.anthropic.com
  model: "claude-3-opus"
  api_key: "your_claude_key"
```

### Q: API密钥如何安全存储？
A: 推荐使用环境变量：
```bash
export OPENAI_API_KEY="your_key"
export DASHSCOPE_API_KEY="your_key"
```

然后在 `conf.yaml` 中引用：
```yaml
BASIC_MODEL:
  api_key: ${OPENAI_API_KEY}
```

---

## 使用问题

### Q: 如何选择合适的模型？
A: 根据任务类型选择：
- **基础任务**: 使用 BASIC_MODEL (DeepSeek-V3)
- **代码生成**: 使用 CODE_MODEL (Qwen3-Coder)
- **复杂推理**: 使用 REASONING_MODEL (Qwen3-235B)
- **图像理解**: 使用 VISION_MODEL (Qwen3-VL)

### Q: 任务执行时间过长怎么办？
A: 可以尝试以下优化：
1. 使用更快的模型（如 DeepSeek-V3）
2. 限制搜索深度
3. 调整 `max_tokens` 参数
4. 使用缓存功能

### Q: 如何中断正在运行的任务？
A: 在命令行中按 `Ctrl+C` 可以中断任务。状态会被保存，可以稍后恢复。

### Q: 批处理任务失败了怎么办？
A: 检查 `batch_summary_*.json` 文件查看失败原因。常见原因：
- API限制
- 网络问题
- 无效的任务描述

---

## API和集成

### Q: 如何在自己的代码中使用 DeepCodeAgent？
A: 参考以下示例：
```python
from src.deepcodeagent.workflow import workflowfun

async def generate_code():
    result = await workflowfun(
        requirement="创建一个REST API",
        output_dir="./output"
    )
    return result

# 运行
result = await generate_code()
```

### Q: 如何扩展工具系统？
A: 使用 `@tool` 装饰器：
```python
from src.tools.decorators import tool

@tool
def custom_tool(param: str) -> str:
    """自定义工具描述"""
    # 实现逻辑
    return result
```

### Q: 如何自定义工作流阶段？
A: 继承 `Phase` 基类：
```python
from src.deepcodeagent.phases.core import Phase

class CustomPhase(Phase):
    async def execute(self, input_data, context):
        # 实现自定义逻辑
        return PhaseResult(success=True, data=result)
```

---

## 性能和优化

### Q: 如何提高响应速度？
A: 优化建议：
1. 使用缓存
2. 并行处理独立任务
3. 选择更快的模型
4. 减少不必要的搜索

### Q: 内存占用过高怎么办？
A: 可以：
1. 清理缓存：`rm -rf .cache/`
2. 减少批处理大小
3. 使用流式处理（如果支持）

### Q: 如何监控性能？
A: 启用性能日志：
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('src.deepcodeagent')
```

---

## 错误排查

### Q: "API key invalid" 错误
A: 检查：
1. API密钥是否正确
2. 是否有足够的额度
3. 网络是否正常

### Q: "Connection timeout" 错误
A: 解决方案：
1. 检查网络连接
2. 增加超时时间
3. 使用代理（如需要）

### Q: "Model not found" 错误
A: 确认：
1. 模型名称是否正确
2. 是否有权限访问该模型
3. API版本是否兼容

### Q: 生成结果不理想怎么办？
A: 改进方法：
1. 提供更详细的需求描述
2. 使用示例或模板
3. 分步骤执行复杂任务
4. 调整模型参数（temperature等）

---

## 高级功能

### Q: 如何使用RAG系统？
A: 示例：
```python
from src.rag.builder import RAGBuilder

# 构建 RAG
rag = RAGBuilder().with_qdrant().build()

# 添加文档
await rag.add_document("doc1", "content")

# 检索
results = await rag.retrieve("query")
```

### Q: 如何实现状态持久化？
A: 使用状态管理：
```python
from src.my_agent.state import create_state, save_state, load_state

# 创建状态
state = create_state("task1", "requirement")

# 保存状态
save_state(state, "state.json")

# 加载状态
state = load_state("state.json")
```

### Q: 如何自定义提示词？
A: 编辑 `src/prompts/` 目录下的 `.md` 文件，或使用：
```python
from src.prompts import load_prompt

prompt = load_prompt("custom_prompt.md")
```

---

## 其他问题

### Q: 项目支持哪些编程语言？
A: 目前主要支持：
- Python
- JavaScript/TypeScript
- Java
- Go
- Rust
- C++

### Q: 如何贡献代码？
A: 请查看 [贡献指南](../CONTRIBUTING.md)

### Q: 如何报告bug？
A: 请在 [GitHub Issues](https://github.com/yourusername/deepcodeagent/issues) 创建新问题

### Q: 是否有社区支持？
A: 可以通过以下方式获取帮助：
- [GitHub Discussions](https://github.com/yourusername/deepcodeagent/discussions)
- 邮件：your-email@example.com

---

## 有用的提示

1. **需求描述越具体，结果越好**
   - ❌ "创建一个网站"
   - ✅ "创建一个使用Flask的博客系统，支持用户注册、文章发布和评论功能"

2. **合理使用批处理**
   - 对于大量简单任务，使用批处理模式
   - 设置适当的并发数，避免触发API限制

3. **定期清理**
   - 定期清理 `testdir/` 和缓存目录
   - 监控API使用量

4. **备份重要配置**
   - 备份 `conf.yaml` 文件
   - 使用版本控制管理自定义代码

---

## 仍有问题？

如果您的问题没有在本文档中找到答案，请：

1. 查看[完整文档](../)
2. 搜索[已知问题](https://github.com/yourusername/deepcodeagent/issues)
3. 在[讨论区](https://github.com/yourusername/deepcodeagent/discussions)提问
4. 发送邮件至：your-email@example.com

我们会尽快回复您！