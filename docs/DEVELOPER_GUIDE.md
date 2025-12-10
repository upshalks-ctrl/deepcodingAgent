# DeepCodeAgent 开发者指南

## 目录

1. [开发环境搭建](#开发环境搭建)
2. [项目结构详解](#项目结构详解)
3. [核心概念](#核心概念)
4. [开发工作流](#开发工作流)
5. [测试指南](#测试指南)
6. [调试技巧](#调试技巧)
7. [贡献指南](#贡献指南)
8. [常见问题](#常见问题)

---

## 开发环境搭建

### 1. 环境要求
- Python 3.8+ (推荐 3.10)
- Git
- IDE (推荐 VSCode 或 PyCharm)
- Docker (可选，用于容器化开发)

### 2. 克隆项目
```bash
git clone https://github.com/yourusername/deepcodeagent.git
cd deepcodeagent
```

### 3. 创建虚拟环境
```bash
# 使用 venv
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 4. 安装依赖
```bash
# 安装生产依赖
pip install -r requirements.txt

# 安装开发依赖（如果有）
pip install -r requirements-dev.txt
```

### 5. 配置环境变量
```bash
# 复制配置模板
cp conf.yaml.example conf.yaml

# 编辑配置文件，添加你的 API keys
```

### 6. 验证安装
```bash
python main.py -t  # 运行测试
```

---

## 项目结构详解

### 核心目录说明

```
deepcodeagent/
├── src/
│   ├── deepcodeagent/          # 核心业务逻辑
│   │   ├── coordinator*.py     # 任务协调器实现
│   │   ├── workflow.py         # 主工作流
│   │   ├── phases/            # 工作流各阶段实现
│   │   ├── core.py            # 核心类和接口
│   │   └── utils.py           # 工具函数
│   │
│   ├── myllms/                # LLM 接口封装
│   │   ├── base.py            # 基础接口
│   │   ├── openai.py          # OpenAI 实现
│   │   ├── anthropic.py       # Anthropic 实现
│   │   ├── dashscope.py       # 阿里云实现
│   │   └── factory.py         # 工厂模式
│   │
│   ├── tools/                 # 工具集合
│   │   ├── search.py          # 搜索工具
│   │   ├── file/              # 文件操作
│   │   ├── system/            # 系统工具
│   │   └── decorators.py      # 工具装饰器
│   │
│   ├── rag/                   # 检索增强生成
│   │   ├── builder.py         # RAG 构建器
│   │   ├── retriever.py       # 检索器
│   │   └── qdrant.py          # 向量数据库
│   │
│   ├── prompts/               # 提示词管理
│   │   ├── coder.md           # 编码提示
│   │   ├── researcher.md      # 研究提示
│   │   └── coordinator.md     # 协调提示
│   │
│   └── config/                # 配置管理
│       ├── loader.py          # 配置加载器
│       └── agents.py          # 代理配置
│
├── docs/                      # 文档
├── examples/                  # 示例代码
├── tests/                     # 测试代码
├── main.py                    # 程序入口
├── conf.yaml                  # 主配置文件
└── requirements.txt           # 依赖列表
```

---

## 核心概念

### 1. 任务协调器 (Coordinator)
负责分析和分配用户需求的核心组件。

**三种实现版本**：
- **简化版** (`coordinator_simple.py`): 快速决策，5个选项
- **结构化版** (`coordinator_structured.py`): 详细分析，结构化输出
- **工具调用版** (`coordinator_tool_based.py`): 基于工具的决策

### 2. 工作流阶段 (Phase)
工作流由多个阶段组成，每个阶段完成特定任务。

**阶段类型**：
- `SearchPhase`: 信息收集与研究
- `PlanningPhase`: 制定执行计划
- `CodingPhase`: 代码生成与实现
- `ExecutingPhase`: 代码执行与测试
- `ReflectionPhase`: 结果评估与优化

### 3. 工具系统 (Tools)
提供各种功能的工具集合，通过装饰器注册。

**工具分类**：
- 搜索工具
- 文件工具
- 系统工具
- 代码执行工具
- 研究工具

### 4. 状态管理 (State)
跟踪任务执行状态，包括进度、产物、错误等。

**状态组成**：
- 任务基本信息
- 执行进度
- 当前阶段
- 产物列表
- 错误信息

---

## 开发工作流

### 1. 功能开发流程

#### 步骤 1: 需求分析
```python
# 示例：添加一个新的 LLM 提供商
# 1. 分析现有接口
from src.myllms.base import BaseLLM

# 2. 明确需要实现的方法
# - generate()
# - generate_with_history()
# - embed() (可选)
```

#### 步骤 2: 设计实现
```python
# 设计新的 LLM 提供商类
class NewProviderLLM(BaseLLM):
    def __init__(self, config):
        # 初始化逻辑
        pass

    async def generate(self, prompt, **kwargs):
        # 实现生成逻辑
        pass
```

#### 步骤 3: 编码实现
```python
# 在 src/myllms/new_provider.py 中实现
# 遵循现有代码风格和模式
```

#### 步骤 4: 添加测试
```python
# 创建 tests/test_new_provider.py
import pytest
from src.myllms.new_provider import NewProviderLLM

@pytest.mark.asyncio
async def test_generate():
    llm = NewProviderLLM(test_config)
    result = await llm.generate("Test prompt")
    assert result is not None
```

#### 步骤 5: 更新工厂
```python
# 在 src/myllms/factory.py 中注册新提供商
class ModelType(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    NEW_PROVIDER = "new_provider"  # 添加这一行
```

### 2. 代码规范

#### Python 代码风格
- 使用 Black 进行格式化
- 使用 isort 进行导入排序
- 遵循 PEP 8 规范
- 使用 type hints

```python
# 好的示例
from typing import List, Dict, Optional, Any

async def process_data(
    data: List[Dict[str, Any]],
    config: Optional[Dict] = None
) -> Dict[str, Any]:
    """处理数据并返回结果

    Args:
        data: 输入数据列表
        config: 可选配置

    Returns:
        处理结果字典
    """
    if config is None:
        config = {}

    # 实现逻辑
    result = {}

    return result
```

#### 文档字符串
- 使用 Google 风格的 docstring
- 提供清晰的参数说明
- 包含示例代码

```python
def example_function(param1: str, param2: int) -> bool:
    """函数简短描述

    详细描述可以跨越多行，解释函数的行为、
    算法细节或使用注意事项。

    Args:
        param1: 参数1的描述
        param2: 参数2的描述

    Returns:
        返回值的描述

    Raises:
        ValueError: 当参数不符合要求时

    Example:
        >>> result = example_function("test", 10)
        >>> print(result)
        True
    """
    pass
```

### 3. 版本控制

#### Git 工作流
```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 提交更改
git add .
git commit -m "feat: add new feature"

# 3. 推送分支
git push origin feature/new-feature

# 4. 创建 Pull Request
```

#### 提交信息规范
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式化
- refactor: 重构代码
- test: 添加测试
- chore: 构建/工具相关

---

## 测试指南

### 1. 测试结构
```
tests/
├── unit/              # 单元测试
│   ├── test_coordinator.py
│   ├── test_workflow.py
│   └── test_tools.py
├── integration/       # 集成测试
│   ├── test_full_workflow.py
│   └── test_llm_integration.py
└── e2e/              # 端到端测试
    └── test_scenarios.py
```

### 2. 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_coordinator.py

# 运行特定测试函数
pytest tests/unit/test_coordinator.py::test_simple_coordinator

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 3. 编写测试

#### 单元测试示例
```python
import pytest
from unittest.mock import AsyncMock, patch
from src.deepcodeagent.coordinator_simple import SimpleCoordinator

@pytest.mark.asyncio
async def test_simple_coordinator_decision():
    """测试简化版协调器的决策逻辑"""
    # 准备
    mock_model = AsyncMock()
    mock_model.generate.return_value = "coding_team"

    coordinator = SimpleCoordinator(model=mock_model)
    state = create_state("task1", "创建一个网站")

    # 执行
    _, action = await coordinator.process("创建一个网站", state)

    # 断言
    assert action == "coding_team"
    mock_model.generate.assert_called_once()
```

#### 集成测试示例
```python
import pytest
from src.deepcodeagent.workflow import workflowfun

@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_coding_task():
    """测试工作流处理编码任务"""
    result = await workflowfun(
        requirement="创建一个简单的计算器函数",
        output_dir="test_output"
    )

    assert result["success"] is True
    assert result["task_type"] == "coding_only"
    assert len(result["files_created"]) > 0
```

### 4. Mock 使用
```python
from unittest.mock import patch, AsyncMock

# Mock 外部 API
@pytest.mark.asyncio
async def test_with_mock():
    with patch('src.myllms.openai.OpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = {
            "choices": [{"message": {"content": "Mocked response"}}]
        }

        # 测试代码
        result = await function_that_uses_openai()
        assert result == "Mocked response"
```

---

## 调试技巧

### 1. 日志配置
```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

# 在代码中使用
logger = logging.getLogger(__name__)
logger.info("Processing request")
logger.debug(f"Data: {data}")
```

### 2. 断点调试
```python
# 使用 pdb 进行调试
import pdb; pdb.set_trace()

# 或使用 ipdb（如果已安装）
import ipdb; ipdb.set_trace()
```

### 3. VSCode 调试配置
创建 `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Debug Main",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "args": ["-t"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "Python: Debug Test",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/unit/test_coordinator.py", "-v", "-s"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

### 4. 性能分析
```python
import cProfile
import pstats

# 性能分析
profiler = cProfile.Profile()
profiler.enable()

# 执行代码
result = await your_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # 显示前10个最耗时的函数
```

---

## 贡献指南

### 1. 代码贡献流程

1. Fork 项目
2. 创建功能分支
3. 编写代码
4. 添加测试
5. 确保所有测试通过
6. 更新文档（如需要）
7. 提交 Pull Request

### 2. PR 模板
```markdown
## 描述
简要描述这个 PR 的目的和改动

## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 代码重构
- [ ] 性能优化

## 测试
- [ ] 添加了新的测试
- [ ] 所有测试通过

## 检查清单
- [ ] 代码符合项目规范
- [ ] 已更新相关文档
- [ ] 无明显性能影响
```

### 3. 代码审查要点

1. **功能性**
   - 代码是否实现了预期功能
   - 是否处理了边界情况
   - 错误处理是否完善

2. **可读性**
   - 代码是否易于理解
   - 变量和函数命名是否清晰
   - 注释是否充分

3. **性能**
   - 是否有性能瓶颈
   - 资源使用是否合理
   - 是否有内存泄漏风险

4. **安全性**
   - 是否有安全漏洞
   - 敏感信息是否正确处理
   - 输入验证是否充分

---

## 常见问题

### Q1: 如何添加新的工具？
A: 使用 `@tool` 装饰器创建新工具：
```python
from src.tools.decorators import tool

@tool
def my_tool(param1: str) -> str:
    """工具描述"""
    # 实现逻辑
    return result
```

### Q2: 如何自定义工作流阶段？
A: 继承 `Phase` 基类：
```python
from src.deepcodeagent.phases.core import Phase

class MyCustomPhase(Phase):
    async def execute(self, input_data, context):
        # 实现阶段逻辑
        pass
```

### Q3: 如何处理异步操作？
A: 使用 `async/await`：
```python
async def my_async_function():
    result = await some_async_operation()
    return result
```

### Q4: 如何调试 LLM 调用？
A: 启用详细日志：
```python
import logging
logging.getLogger('src.myllms').setLevel(logging.DEBUG)
```

### Q5: 如何优化性能？
A: 考虑以下优化：
- 使用缓存
- 批量处理请求
- 并发执行独立任务
- 优化提示词长度

---

## 更多资源

- [API 参考](API_REFERENCE.md)
- [最佳实践](BEST_PRACTICES.md)
- [常见问题解答](FAQ.md)
- [项目 Wiki](https://github.com/yourusername/deepcodeagent/wiki)