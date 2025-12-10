"""
DeepCodeAgent 核心状态管理

完整的软件开发流程状态
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
import json
import uuid


class WorkflowStage(str, Enum):
    """工作流阶段"""
    # 全局阶段
    GLOBAL_COORDINATION = "global_coordination"

    # 架构研究团队阶段
    ARCHITECTURE_COORDINATION = "architecture_coordination"
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    RESEARCH_PLANNING = "research_planning"
    RESEARCH_EXECUTION = "research_execution"
    ARCHITECTURE_WRITING = "architecture_writing"
    ARCHITECTURE_COMPLETED = "architecture_completed"

    # 代码工程团队阶段
    CODING_COORDINATION = "coding_coordination"
    TASK_BREAKDOWN = "task_breakdown"
    CODE_WRITING = "code_writing"
    CODE_TESTING = "code_testing"
    REFLECTION = "reflection"
    CODING_COMPLETED = "coding_completed"

    # 结束阶段
    COMPLETED = "completed"
    ERROR = "error"


class TaskType(str, Enum):
    """任务类型"""
    ARCHITECTURE_ONLY = "architecture_only"  # 仅架构设计
    SIMPLE_CODING = "simple_coding"  # 简单编码（无需架构）
    COMPLEX_DEVELOPMENT = "complex_development"  # 复杂开发（需架构+编码）
    BUG_FIX = "bug_fix"  # Bug修复
    FEATURE_ADDITION = "feature_addition"  # 功能添加
    REFACTORING = "refactoring"  # 重构


class TeamType(str, Enum):
    """团队类型"""
    ARCHITECTURE = "architecture"
    CODING = "coding"


class ResearchRound(str, Enum):
    """研究轮次状态"""
    PLANNING = "planning"  # 规划中
    EXECUTING = "executing"  # 执行中
    COMPLETED = "已完成"  # 已完成


class CodingPhase(str, Enum):
    """编码阶段"""
    TASK_PLANNING = "task_planning"  # 任务规划
    CODING = "coding"  # 编码中
    TESTING = "testing"  # 测试中
    REFLECTING = "reflecting"  # 反思中
    COMPLETED = "已完成"  # 已完成


@dataclass
class Requirement:
    """需求"""
    id: str
    title: str
    description: str
    priority: Literal["high", "medium", "low"] = "medium"
    status: Literal["pending", "in_progress", "completed"] = "pending"
    dependencies: List[str] = field(default_factory=list)  # 依赖的需求ID

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "dependencies": self.dependencies,
        }


@dataclass
class ResearchPlan:
    """研究计划"""
    id: str
    title: str
    thought: str
    rounds: int = 0
    max_rounds: int = 3
    current_round: int = 0
    requirements: List[Requirement] = field(default_factory=list)
    architecture: Optional[str] = None  # 架构方案
    status: Literal["planning", "researching", "writing_architecture", "completed"] = "planning"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "thought": self.thought,
            "rounds": self.rounds,
            "max_rounds": self.max_rounds,
            "current_round": self.current_round,
            "requirements": [req.to_dict() for req in self.requirements],
            "architecture": self.architecture,
            "status": self.status,
        }


@dataclass
class CodingTask:
    """编码任务"""
    id: str
    title: str
    description: str
    code: str = ""
    test_results: List[str] = field(default_factory=list)
    status: Literal["pending", "coding", "testing", "completed", "failed"] = "pending"
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "code": self.code,
            "test_results": self.test_results,
            "status": self.status,
            "dependencies": self.dependencies,
        }


@dataclass
class CodingPlan:
    """编码计划"""
    id: str
    title: str
    architecture: str
    tasks: List[CodingTask] = field(default_factory=list)
    current_task_index: int = 0
    status: Literal["planning", "executing", "completed"] = "planning"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "architecture": self.architecture,
            "tasks": [task.to_dict() for task in self.tasks],
            "current_task_index": self.current_task_index,
            "status": self.status,
        }


@dataclass
class DeepCodeAgentState:
    """
    DeepCodeAgent 状态

    管理整个软件开发流程的状态
    """

    # 基础信息
    task_id: str
    user_requirement: str
    locale: str = "zh-CN"
    created_at: str = field(default_factory=lambda: str(uuid.uuid4()))

    # 全局控制
    current_stage: WorkflowStage = WorkflowStage.GLOBAL_COORDINATION
    task_type: TaskType = TaskType.COMPLEX_DEVELOPMENT
    assigned_team: Optional[TeamType] = None
    iteration: int = 0
    max_iterations: int = 20

    # 需求分析
    requirements: List[Requirement] = field(default_factory=list)
    clarified_requirement: str = ""

    # 架构研究团队状态
    research_plan: Optional[ResearchPlan] = None
    research_findings: List[str] = field(default_factory=list)
    architecture_document: str = ""

    # 代码工程团队状态
    coding_plan: Optional[CodingPlan] = None
    reflection_notes: List[str] = field(default_factory=list)
    final_summary: str = ""

    # 消息历史
    messages: List[Dict[str, Any]] = field(default_factory=list)

    # 错误信息
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "user_requirement": self.user_requirement,
            "locale": self.locale,
            "created_at": self.created_at,
            "current_stage": self.current_stage.value,
            "task_type": self.task_type.value,
            "assigned_team": self.assigned_team.value if self.assigned_team else None,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "requirements": [req.to_dict() for req in self.requirements],
            "clarified_requirement": self.clarified_requirement,
            "research_plan": self.research_plan.to_dict() if self.research_plan else None,
            "research_findings": self.research_findings,
            "architecture_document": self.architecture_document,
            "coding_plan": self.coding_plan.to_dict() if self.coding_plan else None,
            "reflection_notes": self.reflection_notes,
            "final_summary": self.final_summary,
            "messages": self.messages,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DeepCodeAgentState':
        """从字典创建状态"""
        state = cls(
            task_id=data.get("task_id", ""),
            user_requirement=data.get("user_requirement", ""),
            locale=data.get("locale", "zh-CN"),
            created_at=data.get("created_at", str(uuid.uuid4())),
            current_stage=WorkflowStage(data.get("current_stage", "global_coordination")),
            task_type=TaskType(data.get("task_type", "complex_development")),
            iteration=data.get("iteration", 0),
            max_iterations=data.get("max_iterations", 20),
            clarified_requirement=data.get("clarified_requirement", ""),
            research_findings=data.get("research_findings", []),
            architecture_document=data.get("architecture_document", ""),
            reflection_notes=data.get("reflection_notes", []),
            final_summary=data.get("final_summary", ""),
            messages=data.get("messages", []),
            error=data.get("error"),
        )

        # 解析需求
        if data.get("requirements"):
            state.requirements = [Requirement(**req) for req in data["requirements"]]

        # 解析研究计划
        if data.get("research_plan"):
            research_data = data["research_plan"]
            state.research_plan = ResearchPlan(
                id=research_data.get("id", ""),
                title=research_data.get("title", ""),
                thought=research_data.get("thought", ""),
                rounds=research_data.get("rounds", 0),
                max_rounds=research_data.get("max_rounds", 3),
                current_round=research_data.get("current_round", 0),
                requirements=[Requirement(**req) for req in research_data.get("requirements", [])],
                architecture=research_data.get("architecture"),
                status=research_data.get("status", "planning"),
            )

        # 解析编码计划
        if data.get("coding_plan"):
            coding_data = data["coding_plan"]
            state.coding_plan = CodingPlan(
                id=coding_data.get("id", ""),
                title=coding_data.get("title", ""),
                architecture=coding_data.get("architecture", ""),
                tasks=[CodingTask(**task) for task in coding_data.get("tasks", [])],
                current_task_index=coding_data.get("current_task_index", 0),
                status=coding_data.get("status", "planning"),
            )

        return state

    def add_message(self, role: str, content: str, name: Optional[str] = None):
        """添加消息"""
        message = {
            "role": role,
            "content": content,
        }
        if name:
            message["name"] = name
        self.messages.append(message)

    def is_architecture_research_complete(self) -> bool:
        """检查架构研究是否完成"""
        if not self.research_plan:
            return False
        return self.research_plan.status == "completed" or self.current_stage == WorkflowStage.ARCHITECTURE_COMPLETED

    def is_coding_complete(self) -> bool:
        """检查编码是否完成"""
        if not self.coding_plan:
            return False
        return self.coding_plan.status == "completed" or self.current_stage == WorkflowStage.CODING_COMPLETED

    def get_current_task(self) -> Optional[CodingTask]:
        """获取当前任务"""
        if not self.coding_plan or not self.coding_plan.tasks:
            return None
        if self.coding_plan.current_task_index >= len(self.coding_plan.tasks):
            return None
        return self.coding_plan.tasks[self.coding_plan.current_task_index]

    def advance_to_next_task(self):
        """推进到下一个任务"""
        if self.coding_plan:
            self.coding_plan.current_task_index += 1
            if self.coding_plan.current_task_index >= len(self.coding_plan.tasks):
                self.coding_plan.status = "completed"
                self.current_stage = WorkflowStage.CODING_COMPLETED

    def needs_clarification(self) -> bool:
        """检查是否需要澄清"""
        return (
            self.current_stage == WorkflowStage.GLOBAL_COORDINATION
            and not self.clarified_requirement
            and len(self.requirements) == 0
        )

    def should_continue(self) -> bool:
        """检查是否应该继续"""
        if self.current_stage in [WorkflowStage.COMPLETED, WorkflowStage.ERROR]:
            return False
        if self.iteration >= self.max_iterations:
            return False
        return True

    def __str__(self) -> str:
        """字符串表示"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
