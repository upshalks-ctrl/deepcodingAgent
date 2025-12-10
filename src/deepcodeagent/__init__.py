"""
DeepCodeAgent - 完整的软件开发流程系统

包含架构研究团队和代码工程团队
"""

from .core import (
    DeepCodeAgentState,
    WorkflowStage,
    TaskType,
    TeamType,
    Requirement,
    ResearchPlan,
    CodingTask,
    CodingPlan,
)
from .coordinator import GlobalCoordinator
from .architecture_team import ArchitectureTeam
from .coding_team import CodingTeam

__all__ = [
    "DeepCodeAgentState",
    "WorkflowStage",
    "TaskType",
    "TeamType",
    "Requirement",
    "ResearchPlan",
    "CodingTask",
    "CodingPlan",
    "GlobalCoordinator",
    "ArchitectureTeam",
    "CodingTeam",
]

__version__ = "2.0.0"
