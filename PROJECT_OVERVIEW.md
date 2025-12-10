# DeepCodeAgent - AI驱动的智能代码生成系统

## 项目简介

DeepCodeAgent是一个基于大语言模型的智能代码生成系统，能够理解用户需求并自动完成研究、设计、编码、测试等全流程任务。系统集成了多个先进的LLM模型，支持多种任务类型，并提供了灵活的工作流程管理。

## 核心特性

### 🤖 多模型支持
- **基础模型**: DeepSeek-V3 (处理基础任务)
- **推理模型**: Qwen3-235B (处理复杂推理)
- **代码模型**: Qwen3-Coder-480B (专业代码生成)
- **视觉模型**: Qwen3-VL-Plus (图像理解)

### 🔄 智能工作流
- **需求分析**: 自动理解并分析用户需求
- **任务分配**: 智能分配给合适的处理团队
- **多阶段执行**: 研究→规划→编码→测试→反思
- **状态管理**: 完整的任务状态跟踪

### 🛠️ 丰富的工具集
- **搜索引擎**: 集成Tavily、DuckDuckGo等
- **代码执行**: 安全沙箱环境
- **文档处理**: 支持PDF、Word、PPT等
- **版本控制**: Git集成
- **测试工具**: 自动化测试生成

## 快速开始

### 环境要求
- Python 3.8+
- 有效的API密钥（配置在conf.yaml中）

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置API密钥
编辑 `conf.yaml` 文件，填入您的API密钥：
```yaml
BASIC_MODEL:
  api_key: your_deepseek_api_key
CODE_MODEL:
  api_key: your_dashscope_api_key
```

### 运行方式

#### 1. 单任务模式
```bash
python main.py "创建一个Flask todo应用"
```

#### 2. 交互式模式
```bash
python main.py -i
```

#### 3. 批处理模式
```bash
python main.py -f tasks.txt -o output
```

#### 4. 测试模式
```bash
python main.py -t
```

## 项目架构

```
DeepCodeAgent/
├── src/
│   ├── deepcodeagent/          # 核心模块
│   │   ├── coordinator*.py     # 任务协调器（多版本实现）
│   │   ├── workflow.py         # 主工作流
│   │   ├── phases/            # 工作流阶段
│   │   └── stateManage.py     # 状态管理
│   ├── myllms/                # LLM封装
│   ├── tools/                 # 工具集
│   ├── rag/                   # 检索增强生成
│   ├── mcp/                   # MCP服务器
│   └── prompts/               # 提示词模板
├── main.py                    # 程序入口
├── conf.yaml                  # 配置文件
└── requirements.txt           # 依赖列表
```

## 主要功能模块

### 1. GlobalCoordinator (任务协调器)
提供三种实现方式：

- **简化版** (`coordinator_simple.py`): 5个核心选项，适合简单场景
- **结构化版** (`coordinator_structured.py`): 详细任务分析，适合复杂需求
- **工具调用版** (`coordinator_tool_based.py`): 基于工具的阶段流转

### 2. 工作流阶段 (Phases)
- **研究阶段** (`search_phase.py`): 信息收集与分析
- **规划阶段** (`planning_phase.py`): 制定执行计划
- **编码阶段** (`coding_phase.py`): 代码生成与实现
- **执行阶段** (`executing_phase.py`): 运行与测试
- **反思阶段** (`reflection_phase.py`): 评估与优化

### 3. 工具系统 (Tools)
- **搜索工具**: 多引擎支持，智能结果过滤
- **文件工具**: 文件读写、目录管理
- **代码工具**: 代码生成、执行、测试
- **研究工具**: 学术论文、技术文档检索
- **协作工具**: 团队协作、任务分配

### 4. RAG系统 (检索增强生成)
- **向量存储**: Qdrant数据库
- **文档处理**: 多格式文档解析
- **智能检索**: 语义搜索与相关性排序

## 配置说明

### 模型配置
```yaml
BASIC_MODEL:          # 基础任务模型
  base_url: https://api.deepseek.com
  model: "deepseek-chat"

CODE_MODEL:           # 代码生成模型
  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
  model: "qwen3-coder-480b-a35b-instruct"
```

### 搜索引擎配置
```yaml
SEARCH_ENGINE:
  engine: tavily
  search_depth: "advanced"
  include_raw_content: true
  include_images: true
```

## 使用示例

### 示例1：创建Web应用
```python
from src.deepcodeagent.workflow import workflowfun

result = await workflowfun("创建一个带有用户认证的Flask博客系统")
print(f"任务类型: {result['task_type']}")
print(f"创建的文件: {result['files_created']}")
```

### 示例2：代码分析与优化
```python
result = await workflowfun("分析这段Python代码的性能瓶颈并提供优化方案")
```

### 示例3：研究任务
```python
result = await workflowfun("研究微服务架构的最佳实践和设计模式")
```

## 测试覆盖

项目包含全面的测试套件：
- GlobalCoordinator测试: 26个测试用例，100%通过
- 工作流集成测试
- 各模块单元测试
- 端到端测试

运行测试：
```bash
# 测试协调器
python test_simple_coordinator.py
python test_structured_coordinator.py
python test_tool_based_coordinator.py

# 测试编码团队
python test_coding_team.py
python test_coding_team_quick.py

# 完整工作流测试
python main.py -t
```

## 扩展开发

### 添加新的LLM提供商
1. 在 `src/myllms/` 目录创建新的提供商文件
2. 继承 `BaseLLM` 类
3. 实现必要的方法
4. 更新 `factory.py` 添加新提供商

### 添加新工具
1. 在 `src/tools/` 目录创建工具文件
2. 使用 `@tool` 装饰器注册工具
3. 更新 `__init__.py` 导出新工具
4. 在相关提示词中添加工具使用说明

### 自定义工作流
1. 在 `src/deepcodeagent/phases/` 创建新阶段
2. 实现 `Phase` 基类的 `execute` 方法
3. 更新 `workflow.py` 集成新阶段

## 最佳实践

1. **明确需求**: 提供清晰、具体的任务描述
2. **合理配置**: 根据任务类型选择合适的模型
3. **状态管理**: 利用状态系统跟踪任务进度
4. **错误处理**: 检查返回结果并处理异常
5. **资源管理**: 及时清理临时文件和资源

## 常见问题

### Q: 如何切换到本地模型？
A: 修改 `conf.yaml` 中的 `base_url` 为本地模型服务地址。

### Q: 如何自定义输出目录？
A: 使用 `-o` 参数指定输出目录，或修改 `workflow.py` 中的默认路径。

### Q: 任务执行失败怎么办？
A: 检查API密钥配置、网络连接，查看错误日志进行调试。

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [Issues]
- 邮箱: [your-email@example.com]

---

**最后更新**: 2025-12-10
**版本**: 1.0.0