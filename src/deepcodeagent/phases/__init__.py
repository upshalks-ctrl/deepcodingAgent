"""
工作流阶段模块
实现5个核心阶段：Planning, Searching, Coding, Executing, Reflection
"""

from .core import (
    WorkflowPhase,
    WorkflowState,
    BasePhase,
    ExecutionResult,
    SearchContext
)
from .planning_phase import PlanningPhase
from .search_phase import SearchingPhase
from .coding_phase import CodingPhase
from .executing_phase import ExecutingPhase
from .reflection_phase import ReflectionPhase

# Phase工厂
def create_phase(phase_type: WorkflowPhase, model, hook_registry=None, **kwargs):
    """创建Phase实例"""
    phases = {
        WorkflowPhase.PLANNING: PlanningPhase,
        WorkflowPhase.SEARCHING: SearchingPhase,
        WorkflowPhase.CODING: CodingPhase,
        WorkflowPhase.EXECUTING: ExecutingPhase,
        WorkflowPhase.REFLECTING: ReflectionPhase
    }

    phase_class = phases.get(phase_type)
    if not phase_class:
        raise ValueError(f"Unknown phase type: {phase_type}")

    return phase_class(model=model, hook_registry=hook_registry, **kwargs)

__all__ = [
    "WorkflowPhase",
    "WorkflowState",
    "BasePhase",
    "ExecutionResult",
    "SearchContext",
    "PlanningPhase",
    "SearchingPhase",
    "CodingPhase",
    "ExecutingPhase",
    "ReflectionPhase",
    "create_phase"
]