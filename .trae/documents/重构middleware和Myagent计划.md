# 重构计划

## 1. 项目结构设计

创建以下目录结构：

```
testagent/
├── __init__.py
├── hooks/              # 钩子系统
│   ├── __init__.py
│   ├── hooks.py        # 钩子核心实现
│   └── registry.py     # 钩子注册表
├── agent/              # 重构后的Agent
│   ├── __init__.py
│   ├── agent.py        # 基于Graph的Agent实现
│   ├── config.py       # Agent配置
│   └── state.py        # Agent状态管理
├── graph/              # 导入用户提供的Graph
│   ├── __init__.py
│   └── core.py         # 修改用户的graph代码
└── examples/           # 使用示例
    ├── __init__.py
    └── basic_agent.py  # 基本Agent示例
```

## 2. 钩子系统实现

### 2.1 核心组件

* `HookEvent`: 钩子事件枚举，对应原AgentStage

* `HookContext`: 钩子上下文，传递数据和元数据

* `HookRegistry`: 钩子注册表，管理钩子函数

* `Hook`: 钩子装饰器，用于注册钩子函数

### 2.2 实现要点

* 支持同步/异步钩子

* 支持优先级排序

* 支持动态注册/注销

* 支持批量注册

* 支持不同事件类型

## 3. 基于Graph的Agent实现

### 3.1 核心组件

* `GraphAgent`: 基于Graph的Agent实现

* `llmNode`: 图节点实现，对应原llm的不同执行阶段

* `llmEdge`: 图边实现，处理节点间的路由

* `AgentState`: Agent状态管理，与GraphState集成

### 3.2 实现要点

* 将原Agent的执行逻辑拆分为多个图节点

* 使用条件路由处理不同执行路径

* 集成钩子系统到图节点中

* 支持工具调用和LLM调用

* 支持状态持久化

* 支持mcp调用

## 4. 集成实现

### 4.1 钩子与Graph集成

* 在图节点执行前后触发相应钩子

* 支持通过钩子修改节点输入输出

* 支持通过钩子中断执行

### 4.2 Agent与Graph集成

* 使用Graph定义Agent的执行流程

* 每个图节点对应Agent的一个执行阶段

* 支持条件分支和循环执行

* 支持并行执行

## 5. 示例实现

创建一个基本的Agent示例，演示：

* 如何创建和配置Agent

* 如何注册钩子

* 如何使用Agent处理请求

* 如何扩展Agent功能

## 6. 测试与验证

* 测试钩子系统的基本功能

* 测试Agent的执行流程

* 测试钩子与Agent的集成

* 测试不同事件类型的钩子触发

## 7. 文档与说明

* 提供详细的API文档

* 提供使用示例

* 提供迁移指南

* 提供扩展指南

# 实现步骤

1. 创建项目结构和基础文件
2. 实现钩子系统核心组件
3. 实现基于Graph的Agent
4. 集成钩子系统到Agent中
5. 创建使用示例
6. 测试和验证
7. 完善文档

# 技术栈

* Python 3.12

* asyncio

* 基于用户提供的Graph实现

* 无外部依赖（除Python标准库）

