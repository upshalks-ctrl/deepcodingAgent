"""
增强的 State 模型 - 支持复杂代码生成任务

主要增强功能：
1. 增强的 Agent 架构（Planner、Executor、Memory）
2. 多模态文档支持（PDF、PPT、DOCX、图片、文本）
3. 代码生成和自我调试支持
4. Human-in-the-loop 交互
5. 长短期记忆管理
"""

from dataclasses import field, dataclass
from typing import Optional, Dict, List, Union, Any, Callable
from enum import Enum
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState

from src.graph.state import Plan, Step


class TaskType(str, Enum):
    """任务类型枚举"""
    RESEARCH = "research"  # 研究型任务
    CODE_GENERATION = "code_generation"  # 代码生成任务
    COMPLEX_PROJECT = "complex_project"  # 复杂项目任务
    DEBUG_FIX = "debug_fix"  # 调试修复任务


class AgentRole(str, Enum):
    """Agent 角色枚举"""
    PLANNER = "planner"  # 规划器 - 负责任务规划和分解
    EXECUTOR = "executor"  # 执行器 - 负责任务执行
    MEMORY = "memory"  # 记忆 - 负责任务上下文和历史
    COORDINATOR = "coordinator"  # 协调器 - 负责任务分配和流程控制
    REPORTER = "reporter"  # 报告器 - 负责任务总结和输出


class HookEvent(str, Enum):
    """Hook 事件类型"""
    PRE_EXECUTION = "pre_execution"
    POST_EXECUTION = "post_execution"
    TOOL_INVOCATION = "tool_invocation"
    ERROR_OCCURRED = "error_occurred"
    HUMAN_FEEDBACK = "human_feedback"
    PLAN_CREATED = "plan_created"
    RESEARCH_STARTED = "research_started"
    RESEARCH_COMPLETED = "research_completed"
    CODE_GENERATED = "code_generated"
    TEST_PASSED = "test_passed"
    TEST_FAILED = "test_failed"


class CodeFile(BaseModel):
    """代码文件模型"""
    file_path: str
    content: str
    language: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TestResult(BaseModel):
    """测试结果模型"""
    test_name: str
    status: str  # passed, failed, skipped
    output: str
    duration: float
    error_message: Optional[str] = None
    coverage: Optional[float] = None


class ResearchFinding(BaseModel):
    """研究发现模型"""
    topic: str
    content: str
    sources: List[str]
    confidence: float
    timestamp: str


class MemoryEntry(BaseModel):
    """记忆条目模型"""
    key: str
    value: Any
    type: str  # short_term, long_term, episodic
    importance: float
    created_at: str
    last_accessed: str
    access_count: int = 1


class HookCallback(BaseModel):
    """Hook 回调函数模型"""
    event: HookEvent
    callback: Callable
    priority: int = 0  # 优先级，数字越大优先级越高


class PluginInfo(BaseModel):
    """插件信息模型"""
    name: str
    version: str
    description: str
    hooks: List[HookEvent]
    tools: List[str]
    dependencies: List[str]


class DocumentResource(BaseModel):
    """文档资源模型（增强版）"""
    resource_id: str
    title: str
    content: str
    doc_type: str  # pdf, ppt, docx, image, text
    file_path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedded: bool = False
    embedding_id: Optional[str] = None


# 增强的 State 模型
class EnhancedState(MessagesState):
    """增强的 CodeAgent State 模型，支持复杂代码生成任务"""

    # ============ 基础元数据 ============
    task_id: str
    task_type: TaskType
    user_requirement: str
    locale: str
    resources: List[DocumentResource]
    project_root: Optional[str] = None

    # ============ Agent 架构 ============
    current_agent_role: AgentRole
    agent_responses: Dict[AgentRole, str] = Field(default_factory=dict)

    # ============ 规划器（Planner）相关 ============
    current_plan: Optional[Plan] = None
    plan_iterations: int = 0
    max_plan_iterations: int = 3
    enable_clarification: bool = False
    clarification_rounds: int = 0
    clarification_history: List[str] = Field(default_factory=list)
    is_clarification_complete: bool = False
    max_clarification_rounds: int = 3

    # ============ 执行器（Executor）相关 ============
    current_step: Optional[Step] = None
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)
    active_agent: Optional[str] = None
    tool_invocations: List[Dict[str, Any]] = Field(default_factory=list)
    error_logs: List[Dict[str, Any]] = Field(default_factory=list)

    # ============ 记忆（Memory）相关 ============
    memory_store: Dict[str, MemoryEntry] = Field(default_factory=dict)
    short_term_memory: List[Dict[str, Any]] = Field(default_factory=list)
    long_term_memory: List[MemoryEntry] = Field(default_factory=list)
    episodic_memory: List[Dict[str, Any]] = Field(default_factory=list)
    context_window_size: int = 128000
    total_tokens: int = 0
    max_tokens: int = 128000

    # ============ 研究相关 ============
    research_topic: str
    clarified_research_topic: str
    background_investigation_results: str
    research_findings: List[ResearchFinding] = Field(default_factory=list)
    observations: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)

    # ============ 代码生成相关 ============
    code_files: Dict[str, CodeFile] = Field(default_factory=dict)
    source_code: Optional[str] = None
    test_code: Optional[str] = None
    filename: Optional[str] = None
    code_language: Optional[str] = None
    generated_files: List[str] = Field(default_factory=list)
    repo_structure: Dict[str, Any] = Field(default_factory=dict)

    # ============ 测试相关 ============
    test_results: List[TestResult] = Field(default_factory=list)
    tests_passed: bool = False
    test_coverage: Optional[float] = None
    self_reflection_results: List[str] = Field(default_factory=list)

    # ============ 工作流控制 ============
    goto: str = "coordinator"  # 默认下一个节点
    current_workflow_state: str = "initializing"
    workflow_history: List[Dict[str, Any]] = Field(default_factory=list)

    # ============ Hooks 和插件系统 ============
    hooks: Dict[HookEvent, List[HookCallback]] = Field(default_factory=dict)
    enabled_plugins: List[PluginInfo] = Field(default_factory=dict)
    custom_hooks_enabled: bool = True

    # ============ Human-in-the-loop ============
    human_feedback_enabled: bool = False
    human_feedback_pending: bool = False
    human_feedback_requests: List[Dict[str, Any]] = Field(default_factory=list)
    human_approvals: Dict[str, bool] = Field(default_factory=dict)

    # ============ 多模态支持 ============
    multimodal_inputs: Dict[str, Any] = Field(default_factory=dict)
    embedded_documents: List[str] = Field(default_factory=list)

    # ============ 自我反思和调试 ============
    enable_self_reflection: bool = True
    reflection_depth: int = 3
    debugging_enabled: bool = True
    auto_fix_enabled: bool = True

    # ============ MCP 支持 ============
    mcp_servers: Dict[str, Any] = Field(default_factory=dict)
    mcp_enabled_tools: List[str] = Field(default_factory=list)

    # ============ 输出和总结 ============
    summary: Optional[str] = None
    final_report: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)


# 为了向后兼容，保留原来的 State 模型
State = EnhancedState
