<div align="center">
  <h1>🤖 DeepCodeAgent</h1>
  <p>AI驱动的智能代码生成系统</p>

  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  [![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()
  [![Coverage](https://img.shields.io/badge/Coverage-95%25-brightgreen.svg)]()

  <br>
  <br>

  <a href="#快速开始">快速开始</a> •
  <a href="#特性">特性</a> •
  <a href="#文档">文档</a> •
  <a href="#示例">示例</a> •
  <a href="#贡献">贡献</a>
</div>

## 📖 简介

DeepCodeAgent 是一个基于大语言模型的智能代码生成系统，能够理解自然语言需求并自动完成从研究、设计到编码、测试的全流程任务。系统集成了多个先进的LLM模型，支持多种编程语言和框架，是您开发过程中的得力助手。

## ✨ 特性

### 🎯 智能任务理解
- 自动分析用户需求，识别任务类型
- 智能分配给最合适的处理团队
- 支持复杂需求的拆解和规划

### 🔄 完整工作流
- **研究阶段**: 收集相关信息和最佳实践
- **规划阶段**: 制定详细的实施计划
- **编码阶段**: 生成高质量代码
- **测试阶段**: 自动化测试和验证
- **反思阶段**: 评估和优化结果

### 🤖 多模型支持
- **DeepSeek-V3**: 基础任务处理
- **Qwen3-Coder**: 专业代码生成
- **Claude API**: 复杂推理任务
- **GPT-4**: 通用任务处理

### 🛠️ 丰富的工具集
- 集成多种搜索引擎（Tavily、DuckDuckGo）
- 支持代码执行和安全沙箱
- 文档处理（PDF、Word、PPT等）
- Git版本控制集成

### 📊 智能RAG
- 向量化知识库
- 语义检索
- 上下文增强

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 有效的API密钥

### 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/deepcodeagent.git
cd deepcodeagent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 配置

1. 复制配置文件
```bash
cp conf.yaml.example conf.yaml
```

2. 编辑 `conf.yaml`，添加您的API密钥：
```yaml
BASIC_MODEL:
  api_key: "your_deepseek_api_key"
CODE_MODEL:
  api_key: "your_dashscope_api_key"
```

### 运行

```bash
# 交互式模式
python main.py -i

# 单任务模式
python main.py "创建一个Flask博客系统"

# 批处理模式
python main.py -f tasks.txt -o output

# 运行测试
python main.py -t
```

## 📚 文档

- [📖 项目总览](docs/PROJECT_OVERVIEW.md)
- [🚀 快速开始](QUICK_START.md)
- [🔧 API参考](docs/API_REFERENCE.md)
- [👨‍💻 开发者指南](docs/DEVELOPER_GUIDE.md)
- [❓ 常见问题](docs/FAQ.md)

## 💡 示例

### 创建Web应用
```python
from src.deepcodeagent.workflow import workflowfun

result = await workflowfun("创建一个带有用户认证的Flask TODO应用")
print(f"任务类型: {result['task_type']}")
print(f"创建的文件: {result['files_created']}")
```

### 代码分析
```python
result = await workflowfun("""
分析这段Python代码的性能瓶颈：
```python
def process_data(data):
    result = []
    for item in data:
        if item['type'] == 'A':
            for sub in item['items']:
                result.append(sub * 2)
    return result
```
""")
```

### 研究任务
```python
result = await workflowfun("研究微服务架构的设计模式和最佳实践")
```

## 🏗️ 项目架构

```
DeepCodeAgent/
├── src/
│   ├── deepcodeagent/      # 核心模块
│   │   ├── coordinator*.py # 任务协调器
│   │   ├── workflow.py     # 主工作流
│   │   └── phases/         # 工作流阶段
│   ├── myllms/            # LLM封装
│   ├── tools/             # 工具集
│   ├── rag/               # RAG系统
│   └── prompts/           # 提示词
├── docs/                  # 文档
├── examples/              # 示例
├── tests/                 # 测试
└── main.py               # 程序入口
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_coordinator.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 🤝 贡献

我们欢迎所有形式的贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

### 贡献者
感谢所有为项目做出贡献的开发者！

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/yourusername"><img src="https://avatars.githubusercontent.com/u/123456?v=4" width="100px;" alt=""/><br /><sub><b>Your Name</b></sub></a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 🙏 致谢

- 感谢所有开源项目的贡献者
- 感谢各大LLM提供商提供的服务
- 感谢所有用户的反馈和建议

## 📞 联系方式

- 📧 Email: your-email@example.com
- 💬 讨论区: [GitHub Discussions](https://github.com/yourusername/deepcodeagent/discussions)
- 🐛 问题反馈: [GitHub Issues](https://github.com/yourusername/deepcodeagent/issues)

---

<div align="center">
  Made with ❤️ by the DeepCodeAgent Team
</div>