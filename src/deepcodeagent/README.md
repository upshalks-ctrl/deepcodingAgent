# DeepCodeAgent - 完整的软件开发流程系统

## 概述

DeepCodeAgent 是一个完整的多智能体软件开发系统，它能够分析用户需求、制定架构、实现代码、测试和反思。该系统采用模块化设计，包含架构研究团队和代码工程团队，协同完成从需求分析到生产级代码的完整流程。

## 核心特性

- **智能任务分类**: 自动分析用户需求，判断任务复杂度
- **团队协作**: 架构团队和代码团队协同工作
- **完整工作流**: 从需求分析到代码实现的端到端流程
- **状态管理**: 完整的状态跟踪和序列化支持
- **可扩展性**: 支持自定义中间件和人在环中机制

## 系统架构

```
DeepCodeAgent
├── GlobalCoordinator          # 全局协调者
│   └── 任务类型分析
│   └── 团队分配决策
│
├── ArchitectureTeam           # 架构研究团队
│   ├── Planner               # 规划者 - 需求分析和研究计划
│   ├── TaskCoordinator       # 任务协调者 - 协调研究流程
│   ├── ResearchTeam          # 研究团队 - 执行具体研究
│   └── ArchitectureWriter    # 架构编写者 - 生成架构文档
│
└── CodingTeam                # 代码工程团队
    ├── CodingTaskCoordinator # 编码任务协调者 - 制定编码计划
    ├── Coder                 # 编码器 - 编写代码
    ├── TestRunner           # 测试者 - 运行和测试代码
    └── Reflector            # 思考者 - 反思和改进
```

## 工作流程

### 1. 全局协调阶段
```python
用户需求 -> 全局协调者分析 -> 任务类型判断 -> 团队分配
```

### 2. 架构研究流程
```
需求分析 -> 研究规划 -> 研究执行 -> 架构编写 -> 用户确认
```

### 3. 代码工程流程
```
编码协调 -> 任务分解 -> 代码编写 -> 代码测试 -> 反思总结
```

## 快速开始

### 基本使用

```python
import asyncio
from src.deepcodeagent import (
    DeepCodeAgentState,
    GlobalCoordinator,
    ArchitectureTeam,
    CodingTeam,
)

# 1. 创建状态
state = DeepCodeAgentState(
    task_id="task_001",
    user_requirement="设计并实现一个微服务架构的电商系统",
)

# 2. 全局协调
coordinator = GlobalCoordinator(model=your_model)
state, needs_clarification = await coordinator.process(state)

# 3. 根据分配的团队执行工作流
if state.assigned_team == TeamType.ARCHITECTURE:
    arch_team = ArchitectureTeam(
        planner_model=your_model,
        coordinator_model=your_model,
        researcher_model=your_model,
        writer_model=your_model,
    )
    state = await arch_team.process(state)
elif state.assigned_team == TeamType.CODING:
    code_team = CodingTeam(
        coordinator_model=your_model,
        coder_model=your_model,
        test_model=your_model,
        reflector_model=your_model,
    )
    state = await code_team.process(state)
```

## 核心组件详解

### 1. 状态管理 (DeepCodeAgentState)

状态是系统的核心，包含了整个工作流程的所有信息：

```python
from src.deepcodeagent import DeepCodeAgentState

state = DeepCodeAgentState(
    task_id="唯一任务ID",
    user_requirement="用户原始需求",
    # ... 其他参数
)

# 状态序列化
state_dict = state.to_dict()
restored_state = DeepCodeAgentState.from_dict(state_dict)
```

### 2. 工作流阶段 (WorkflowStage)

定义了完整的软件开发流程阶段：

- **GLOBAL_COORDINATION**: 全局协调
- **ARCHITECTURE_***: 架构研究阶段
  - ARCHITECTURE_COORDINATION
  - REQUIREMENT_ANALYSIS
  - RESEARCH_PLANNING
  - RESEARCH_EXECUTION
  - ARCHITECTURE_WRITING
  - ARCHITECTURE_COMPLETED
- **CODING_***: 代码工程阶段
  - CODING_COORDINATION
  - TASK_BREAKDOWN
  - CODE_WRITING
  - CODE_TESTING
  - REFLECTION
  - CODING_COMPLETED
- **COMPLETED/ERROR**: 结束状态

### 3. 任务类型 (TaskType)

- **SIMPLE_CODING**: 简单编码任务
- **COMPLEX_DEVELOPMENT**: 复杂开发任务（需要架构）
- **ARCHITECTURE_ONLY**: 仅架构设计
- **BUG_FIX**: Bug修复
- **FEATURE_ADDITION**: 功能添加
- **REFACTORING**: 重构

### 4. 团队类型 (TeamType)

- **ARCHITECTURE**: 架构研究团队
- **CODING**: 代码工程团队

## API 参考

### GlobalCoordinator

全局协调者，负责分析需求并分配团队。

```python
coordinator = GlobalCoordinator(
    model=your_model,
    middleware_chain=None,  # 可选
    human_in_the_loop=None,  # 可选
)

state, needs_clarification = await coordinator.process(state)
```

### ArchitectureTeam

架构研究团队，负责需求分析和架构设计。

```python
arch_team = ArchitectureTeam(
    planner_model=your_model,
    coordinator_model=your_model,
    researcher_model=your_model,
    writer_model=your_model,
    middleware_chain=None,  # 可选
    human_in_the_loop=None,  # 可选
)

state = await arch_team.process(state)
```

#### 组件类

- **Planner**: 规划者
  - 分析用户需求
  - 制定研究计划
  - 决定研究重点

- **TaskCoordinator**: 任务协调者
  - 协调研究流程
  - 管理研究进度

- **ResearchTeam**: 研究团队
  - 执行具体研究
  - 收集相关信息
  - 整理研究结果

- **ArchitectureWriter**: 架构编写者
  - 整合研究结果
  - 编写架构文档
  - 提供实施指导

### CodingTeam

代码工程团队，负责代码实现和测试。

```python
code_team = CodingTeam(
    coordinator_model=your_model,
    coder_model=your_model,
    test_model=your_model,
    reflector_model=your_model,
    middleware_chain=None,  # 可选
    human_in_the_loop=None,  # 可选
)

state = await code_team.process(state)
```

#### 组件类

- **CodingTaskCoordinator**: 编码任务协调者
  - 制定编码计划
  - 分解编码任务
  - 协调整个编码流程

- **Coder**: 编码器
  - 编写高质量代码
  - 遵循最佳实践
  - 添加注释和文档

- **TestRunner**: 测试者
  - 运行代码测试
  - 检查代码质量
  - 生成测试报告

- **Reflector**: 思考者
  - 反思编码过程
  - 生成改进建议
  - 总结经验教训

## 数据模型

### Requirement

需求模型：

```python
from src.deepcodeagent import Requirement

req = Requirement(
    id="req_001",
    title="需求标题",
    description="需求描述",
    priority="high",  # high, medium, low
    status="pending",  # pending, in_progress, completed
    dependencies=[],  # 依赖的需求ID列表
)
```

### ResearchPlan

研究计划模型：

```python
from src.deepcodeagent import ResearchPlan

plan = ResearchPlan(
    id="plan_001",
    title="计划标题",
    thought="规划思路",
    max_rounds=3,
    requirements=[],  # Requirement 列表
    status="planning",  # planning, researching, writing_architecture, completed
)
```

### CodingTask

编码任务模型：

```python
from src.deepcodeagent import CodingTask

task = CodingTask(
    id="task_001",
    title="任务标题",
    description="任务描述",
    code="",  # 生成的代码
    test_results=[],  # 测试结果列表
    status="pending",  # pending, coding, testing, completed, failed
    dependencies=[],  # 依赖的任务ID列表
)
```

### CodingPlan

编码计划模型：

```python
from src.deepcodeagent import CodingPlan

plan = CodingPlan(
    id="coding_001",
    title="编码计划标题",
    architecture="架构方案",
    tasks=[],  # CodingTask 列表
    current_task_index=0,
    status="planning",  # planning, executing, completed
)
```

## 完整示例

查看 `example_deepcodeagent_simple.py` 获取完整的使用示例：

```bash
python example_deepcodeagent_simple.py
```

示例包括：
1. 创建 DeepCodeAgent 状态
2. 需求分析和团队分配
3. 架构研究工作流
4. 代码工程工作流
5. 状态序列化和反序列化

## 测试

运行完整性验证测试：

```bash
python test_deepcodeagent.py
```

## 文件结构

```
src/deepcodeagent/
├── __init__.py              # 包初始化，导出所有公共API
├── core.py                  # 核心状态管理、枚举和数据类
├── coordinator.py           # 全局协调者
├── architecture_team.py     # 架构研究团队
├── coding_team.py          # 代码工程团队
└── README.md               # 本文档
```

## 设计原则

1. **模块化设计**: 每个组件都是独立的，可以单独使用
2. **状态驱动**: 通过状态管理控制整个工作流程
3. **团队协作**: 多个智能体协同工作，各司其职
4. **可扩展性**: 支持自定义模型、中间件和人在环中机制
5. **可序列化**: 状态可以持久化和恢复

## 注意事项

1. **模型配置**: 需要配置真实的 LLM 模型以获得最佳效果
2. **人在环中**: 可以通过 `human_in_the_loop` 参数添加审批机制
3. **中间件**: 可以通过 `middleware_chain` 添加自定义处理逻辑
4. **错误处理**: 系统包含完整的错误处理和日志记录
5. **性能优化**: 实际使用时需要根据场景调整参数

## 版本信息

- 当前版本: 2.0.0
- 支持 Python: 3.8+

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 联系方式

如有问题，请通过 GitHub Issues 联系我们。
