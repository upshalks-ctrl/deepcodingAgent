"""
核心状态定义和Phase基类

定义5个核心工作流阶段和基础Phase接口
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

from src.myllms.base import BaseModel


class WorkflowPhase(Enum):
    """工作流阶段枚举"""
    PLANNING = "planning"           # 规划阶段：分析需求，制定计划
    SEARCHING = "searching"         # 搜索阶段：获取必要信息
    CODING = "coding"              # 编码阶段：生成代码
    EXECUTING = "executing"        # 执行阶段：运行代码
    REFLECTING = "reflecting"      # 反思阶段：分析结果，决定下一步
    FINISHED = "finished"          # 完成阶段：任务完成


@dataclass
class ExecutionResult:
    """代码执行结果"""
    stdout: str = ""
    stderr: str = ""
    return_code: int = -1
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SearchContext:
    """搜索上下文"""
    queries: List[str] = field(default_factory=list)
    results: List[str] = field(default_factory=list)
    summaries: List[str] = field(default_factory=list)
    last_query_time: Optional[datetime] = None


@dataclass
class WorkflowState:
    """工作流状态"""
    # 基本信息
    user_request: str = ""
    user_goal: str = ""
    current_phase: WorkflowPhase = WorkflowPhase.PLANNING

    # 计划信息
    plan: str = ""
    refined_plan: str = ""

    # 搜索信息
    search_context: SearchContext = field(default_factory=SearchContext)

    # 代码信息
    code_files: Dict[str, str] = field(default_factory=dict)
    current_file: str = ""

    # 执行信息
    execution_results: List[ExecutionResult] = field(default_factory=list)
    last_execution: Optional[ExecutionResult] = None

    # 反思信息
    reflection_notes: List[str] = field(default_factory=list)
    error_analysis: Optional[str] = None

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_phase(self, new_phase: WorkflowPhase) -> None:
        """更新当前阶段"""
        self.current_phase = new_phase
        self.updated_at = datetime.now()

    def add_execution_result(self, result: ExecutionResult) -> None:
        """添加执行结果"""
        self.execution_results.append(result)
        self.last_execution = result
        self.updated_at = datetime.now()

    def add_search_result(self, query: str, result: str, summary: str = "") -> None:
        """添加搜索结果"""
        self.search_context.queries.append(query)
        self.search_context.results.append(result)
        if summary:
            self.search_context.summaries.append(summary)
        self.search_context.last_query_time = datetime.now()
        self.updated_at = datetime.now()

    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        self.metadata[key] = value
        self.updated_at = datetime.now()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self.metadata.get(key, default)


class BasePhase(ABC):
    """Phase基类"""

    def __init__(self, model: BaseModel, hook_registry=None):
        self.model = model
        self.hook_registry = hook_registry
        self.phase_name = self.__class__.__name__

    @property
    @abstractmethod
    def phase_type(self) -> WorkflowPhase:
        """返回此Phase处理的阶段类型"""
        pass

    @abstractmethod
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """执行阶段逻辑"""
        pass

    @abstractmethod
    def can_enter(self, state: WorkflowState) -> bool:
        """检查是否可以进入此阶段"""
        pass

    async def before_execute(self, state: WorkflowState) -> WorkflowState:
        """执行前的钩子"""
        if self.hook_registry:
            from src.hooks.hooks import HookContext, HookEvent
            context = HookContext(
                data=state,
                metadata={"phase": self.phase_name},
                event_type=HookEvent.BEFORE_AGENT
            )
            result = await self.hook_registry.trigger(HookEvent.BEFORE_AGENT, context)
            return result.data
        return state

    async def after_execute(self, state: WorkflowState) -> WorkflowState:
        """执行后的钩子"""
        if self.hook_registry:
            from src.hooks.hooks import HookContext, HookEvent
            context = HookContext(
                data=state,
                metadata={"phase": self.phase_name},
                event_type=HookEvent.AFTER_AGENT
            )
            result = await self.hook_registry.trigger(HookEvent.AFTER_AGENT, context)
            return result.data
        return state

    async def run(self, state: WorkflowState) -> WorkflowState:
        """运行阶段（包含钩子）"""
        # 检查是否可以进入
        if not self.can_enter(state):
            raise ValueError(f"Cannot enter {self.phase_name} phase in current state")

        # 更新状态
        state.update_phase(self.phase_type)

        # 执行前置钩子
        state = await self.before_execute(state)

        # 执行阶段逻辑
        state = await self.execute(state)

        # 执行后置钩子
        state = await self.after_execute(state)

        return state