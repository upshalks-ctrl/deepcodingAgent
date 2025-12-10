# 贡献指南

感谢您对 DeepCodeAgent 项目的关注！我们欢迎并感谢所有形式的贡献。

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [测试指南](#测试指南)
- [文档贡献](#文档贡献)
- [问题反馈](#问题反馈)
- [社区](#社区)

## 🤝 行为准则

### 我们的承诺
为了营造一个开放和友好的环境，我们承诺：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

### 不可接受的行为
- 使用性别化语言或图像，以及不受欢迎的性关注或性骚扰
- 恶意评论、侮辱/贬损评论，以及人身或政治攻击
- 公开或私下骚扰
- 未经明确许可发布他人的私人信息
- 其他在专业环境中可能被认为不当的行为

## 🚀 如何贡献

### 报告Bug
如果您发现了bug，请：

1. 检查[已知问题](https://github.com/yourusername/deepcodeagent/issues)确认是否已被报告
2. 如果没有被报告，请[创建新issue](https://github.com/yourusername/deepcodeagent/issues/new)
3. 使用bug报告模板，提供尽可能详细的信息

### 提出新功能
我们欢迎功能建议！请：

1. 检查[现有功能请求](https://github.com/yourusername/deepcodeagent/labels/feature%20request)
2. 如果没有类似的请求，请[创建新issue](https://github.com/yourusername/deepcodeagent/issues/new)
3. 详细描述您希望添加的功能和使用场景

### 提交代码
这是最直接的贡献方式：

1. Fork项目仓库
2. 创建功能分支
3. 编写代码
4. 提交Pull Request

## 🔄 开发流程

### 1. 准备环境
```bash
# Fork并克隆您的仓库
git clone https://github.com/yourusername/deepcodeagent.git
cd deepcodeagent

# 添加上游仓库
git remote add upstream https://github.com/original/deepcodeagent.git

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 如果存在
```

### 2. 创建分支
```bash
# 同步上游主分支
git checkout main
git pull upstream main

# 创建新分支
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

### 3. 进行开发
- 遵循项目的代码规范
- 编写测试覆盖新功能
- 更新相关文档
- 确保所有测试通过

### 4. 提交更改
```bash
# 添加更改
git add .

# 提交（遵循提交信息规范）
git commit -m "feat: add new feature description"

# 推送到您的fork
git push origin feature/your-feature-name
```

### 5. 创建Pull Request
- 访问GitHub上的fork页面
- 点击"New Pull Request"
- 填写PR模板
- 等待代码审查

## 📝 代码规范

### Python代码风格
我们使用以下工具确保代码质量：

- **Black**: 代码格式化
- **isort**: 导入排序
- **flake8**: 代码检查
- **mypy**: 类型检查

### 格式化代码
```bash
# 格式化代码
black src/ tests/

# 排序导入
isort src/ tests/

# 检查代码风格
flake8 src/ tests/

# 类型检查
mypy src/
```

### 编码规范

#### 1. 命名规范
```python
# 类名：PascalCase
class TaskManager:
    pass

# 函数和变量：snake_case
def process_data():
    user_input = "value"
    return result

# 常量：UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
```

#### 2. 类型提示
```python
from typing import List, Dict, Optional, Union

def process_items(
    items: List[Dict[str, Any]],
    config: Optional[Dict] = None
) -> Dict[str, Union[int, str]]:
    """函数说明"""
    pass
```

#### 3. 文档字符串
```python
def complex_function(
    param1: str,
    param2: int,
    param3: Optional[float] = None
) -> bool:
    """函数简短描述

    详细描述可以跨越多行，解释函数的行为、
    算法细节或使用注意事项。

    Args:
        param1: 参数1的描述
        param2: 参数2的描述
        param3: 参数3的描述，可选

    Returns:
        返回值的描述

    Raises:
        ValueError: 当参数不符合要求时
        RuntimeError: 当运行时出错时

    Example:
        >>> result = complex_function("test", 10, 3.14)
        >>> print(result)
        True
    """
    pass
```

## 📋 提交规范

我们使用[约定式提交](https://www.conventionalcommits.org/zh-hans/v1.0.0/)规范。

### 提交格式
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### 类型说明
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式化（不影响功能）
- `refactor`: 重构代码
- `perf`: 性能优化
- `test`: 添加或修改测试
- `chore`: 构建过程或辅助工具的变动
- `ci`: CI配置文件和脚本的变动

### 示例
```bash
feat: add support for new LLM provider

Add integration with XYZ AI provider, enabling users to
use their models for code generation tasks.

Closes #123
```

```bash
fix: resolve memory leak in workflow execution

The workflow was not properly cleaning up resources after
completion, causing memory usage to increase over time.
```

## 🧪 测试指南

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_workflow.py

# 运行特定测试函数
pytest tests/unit/test_workflow.py::test_workflow_function

# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 运行性能测试
pytest tests/performance/
```

### 编写测试

#### 单元测试
```python
import pytest
from unittest.mock import AsyncMock, patch
from src.deepcodeagent.workflow import workflowfun

@pytest.mark.asyncio
async def test_workflow_with_mock():
    """测试工作流使用mock"""
    with patch('src.myllms.openai.OpenAI') as mock_openai:
        mock_openai.return_value = AsyncMock()
        result = await workflowfun("test requirement")
        assert result is not None
```

#### 集成测试
```python
import pytest
from src.deepcodeagent.coordinator import Coordinator

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow():
    """测试完整工作流"""
    coordinator = Coordinator()
    result = await coordinator.process("创建一个计算器")
    assert result["success"] is True
```

### 测试覆盖率
- 新功能必须有测试覆盖
- 目标覆盖率：90%以上
- 关键路径覆盖率：100%

## 📚 文档贡献

### 文档类型
1. **API文档**: 自动生成，代码中的docstring
2. **用户文档**: README、指南、教程
3. **开发者文档**: 架构说明、贡献指南

### 文档规范
- 使用清晰简洁的语言
- 提供实际示例
- 保持文档与代码同步
- 使用markdown格式

### 更新文档
```bash
# 本地预览文档（如果使用MkDocs等）
mkdocs serve

# 检查文档链接
markdownlint docs/**/*.md
```

## 🐛 问题反馈

### Bug报告
使用bug报告模板时，请提供：

1. **环境信息**
   - 操作系统
   - Python版本
   - 项目版本

2. **重现步骤**
   - 详细的重现步骤
   - 预期行为
   - 实际行为

3. **错误信息**
   - 完整的错误堆栈
   - 相关日志

4. **附加信息**
   - 配置文件
   - 最小可复现代码

### 功能请求
提供以下信息：

1. **问题背景**
   - 您想解决的问题
   - 当前的工作流程

2. **建议方案**
   - 详细的功能描述
   - 使用场景

3. **替代方案**
   - 考虑过的其他方案
   - 为什么建议的方案更好

## 👥 社区

### 沟通渠道
- **GitHub Discussions**: [讨论区](https://github.com/yourusername/deepcodeagent/discussions)
- **GitHub Issues**: [问题追踪](https://github.com/yourusername/deepcodeagent/issues)
- **Email**: [your-email@example.com](mailto:your-email@example.com)

### 获取帮助
- 查看[文档](docs/)
- 搜索[已知问题](https://github.com/yourusername/deepcodeagent/issues)
- 在讨论区提问

### 认可贡献者
我们使用[All Contributors](https://allcontributors.org/)规范来认可所有贡献者。

## 📜 许可证

通过贡献代码，您同意您的贡献将在[MIT许可证](LICENSE)下授权。

## 🙏 致谢

感谢所有为DeepCodeAgent做出贡献的开发者！

---

有任何问题吗？欢迎[联系我们](mailto:your-email@example.com)或在[讨论区](https://github.com/yourusername/deepcodeagent/discussions)提问。