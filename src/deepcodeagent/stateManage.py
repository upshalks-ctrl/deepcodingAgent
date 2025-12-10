"""
DeepCodeAgent特定状态定义

继承MessageState，定义DeepCodeAgent工作流需要的状态信息
"""

from typing import TypedDict, List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from src.my_agent.state import MessageState



class DeepCodeState(MessageState):
    """
    DeepCodeAgent工作流状态

    继承MessageState，添加DeepCodeAgent特定的状态信息
    """
    # 基础消息（来自MessageState）
    messages: List[Dict[str, Any]]

    # DeepCodeAgent特定数据
    requirement: str  # 初始需求
    clarified_requirement: Optional[str] 
    coordinator_action: Optional[str]
    task_type: Optional[str]
    assigned_team: Optional[str]
    assign_node: Optional[str]
    current_stage: Optional[str]
    complexity_score: Optional[float]
    estimated_effort: Optional[str]
    requires_clarification: bool
    clarification_questions: List[str]
    enable_clarify_requirement: bool  


# 团队注册系统
class TeamRegistry:
    """
    团队成员注册表

    用于注册和管理所有可用的团队处理器
    """

    def __init__(self):
        self.teams: Dict[str, Dict[str, Any]] = {}

    def register_team(
        self,
        name: str,
        processor_func: Callable,
        description: str = "",
        team_type: str = "processor"
    ):
        """
        注册团队成员

        Args:
            name: 团队名称
            processor_func: 处理器函数
            description: 团队描述
            team_type: 团队类型
        """
        self.teams[name] = {
            "name": name,
            "processor": processor_func,
            "description": description,
            "type": team_type,
            "registered_at": __import__("datetime").datetime.now().isoformat()
        }

    def get_team(self, name: str) -> Optional[Dict[str, Any]]:
        """
        根据名称获取团队信息

        Args:
            name: 团队名称

        Returns:
            团队信息字典或None
        """
        return self.teams.get(name)

    def get_all_teams(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有已注册的团队

        Returns:
            团队字典
        """
        return self.teams.copy()

    def list_team_names(self) -> List[str]:
        """
        获取所有团队名称列表

        Returns:
            团队名称列表
        """
        return list(self.teams.keys())

    def is_team_registered(self, name: str) -> bool:
        """
        检查团队是否已注册

        Args:
            name: 团队名称

        Returns:
            是否已注册
        """
        return name in self.teams


# 路由系统
def route_by_assign_node(state: DeepCodeState) -> str:
    """
    根据state中的assign_node或assigned_team决定下一个处理节点

    Args:
        state: 当前状态

    Returns:
        下一个节点的名称
    """
    # 优先使用assign_node，如果不存在则使用assigned_team
    next_node = state.get("assign_node") or state.get("assigned_team")

    # 如果都没有设置，使用默认节点
    if not next_node:
        return "basic_llm"

    return next_node


def route_to_processor(state: DeepCodeState) -> str:
    """
    路由到具体的处理器

    Args:
        state: 当前状态

    Returns:
        处理器名称
    """
    return route_by_assign_node(state)


def get_next_module_name(state: DeepCodeState) -> str:
    """
    获取下一个模块名称（兼容coordinator_simple.py的命名）

    Args:
        state: 当前状态

    Returns:
        模块名称
    """
    return route_by_assign_node(state)


# 团队处理器接口
async def process_with_team_routing(
    state: DeepCodeState,
    registry: TeamRegistry
) -> DeepCodeState:
    """
    使用团队路由处理状态

    Args:
        state: 当前状态
        registry: 团队注册表

    Returns:
        处理后的状态
    """
    # 确定下一个节点
    next_node = route_by_assign_node(state)

    # 获取团队信息
    team_info = registry.get_team(next_node)

    if not team_info:
        # 如果团队未注册，返回到默认处理器
        next_node = "basic_llm"
        team_info = registry.get_team(next_node)

        if not team_info:
            # 如果连默认处理器都没有，返回原状态
            return state

    # 调用团队处理器的run函数
    processor = team_info["processor"]

    try:
        # 获取run方法
        if hasattr(processor, 'run'):
            run_func = processor.run
        elif callable(processor):
            run_func = processor
        else:
            raise AttributeError(f"Team processor '{next_node}' has no run method or is not callable")

        # 调用run函数
        import asyncio
        if asyncio.iscoroutinefunction(run_func):
            # 异步run函数
            result = await run_func(state)
        else:
            # 同步run函数
            result = run_func(state)

        # 确保结果是DeepCodeState类型
        if isinstance(result, dict):
            result["assigned_team"] = next_node
            return DeepCodeState(**result)
        else:
            state["assigned_team"] = next_node
            return state

    except Exception as e:
        # 处理器调用失败，记录错误并返回
        print(f"Error calling team processor '{next_node}': {e}")
        state["assigned_team"] = "basic_llm"
        return state


# 便捷函数
def create_team_registry() -> TeamRegistry:
    """
    创建并配置团队注册表

    Returns:
        配置好的团队注册表
    """
    registry = TeamRegistry()

    # 注册所有核心团队
    registry.register_team(
        name="architecture_team",
        processor_func=lambda s: s,  # 占位符处理器
        description="架构设计团队 - 处理系统设计、架构规划、技术方案",
        team_type="design"
    )

    registry.register_team(
        name="coding_team",
        processor_func=lambda s: s,  # 占位符处理器
        description="编码团队 - 处理功能开发、代码实现、API编写",
        team_type="development"
    )

    registry.register_team(
        name="summary_llm",
        processor_func=lambda s: s,  # 占位符处理器
        description="总结分析团队 - 处理内容总结、数据分析、归纳整理",
        team_type="analysis"
    )

    registry.register_team(
        name="basic_llm",
        processor_func=lambda s: s,  # 占位符处理器
        description="基础对话团队 - 处理基础问答、知识介绍、简单对话",
        team_type="chat"
    )

    return registry


async def run_deepcodeagent_workflow(
    state: DeepCodeState,
    registry: Optional[TeamRegistry] = None
) -> DeepCodeState:
    """
    运行DeepCodeAgent工作流

    Args:
        state: 初始状态
        registry: 团队注册表（可选）

    Returns:
        处理后的状态
    """
    if registry is None:
        registry = create_team_registry()

    # 执行路由处理
    state = await process_with_team_routing(state, registry)

    return state


