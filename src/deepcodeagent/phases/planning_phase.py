"""
规划阶段实现
Phase 1: Planning - 分析用户请求，制定计划
"""

import json
import logging
from typing import Optional

from .core import BasePhase, WorkflowPhase, WorkflowState
from ...prompts import PROMPTS
from ...tools.search import TavilySearchTool, DuckDuckGoSearchTool
from ...myllms.base import BaseModel

logger = logging.getLogger(__name__)


class PlanningPhase(BasePhase):
    """规划阶段"""

    def __init__(self, model: BaseModel, search_tool=None, hook_registry=None):
        super().__init__(model, hook_registry)
        self.search_tool = search_tool or TavilySearchTool()

    @property
    def phase_type(self) -> WorkflowPhase:
        return WorkflowPhase.PLANNING

    def can_enter(self, state: WorkflowState) -> bool:
        """检查是否可以进入规划阶段"""
        return state.current_phase in [WorkflowPhase.PLANNING, WorkflowPhase.REFLECTING]

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """执行规划逻辑"""
        logger.info("Entering Planning Phase")

        # 构建用户消息
        user_message = PROMPTS["planning"]["user"].format(
            user_request=state.user_request,
            context=self._get_context_summary(state),
            search_results=self._get_search_summary(state)
        )

        # 调用模型进行分析
        messages = [
            {"role": "system", "content": PROMPTS["planning"]["system"]},
            {"role": "user", "content": user_message}
        ]

        response = await self.model.ainvoke(messages)
        decision_data = self._parse_decision_response(response.content)

        # 根据决策执行相应操作
        if decision_data["decision"] == "SEARCHING":
            logger.info("Decision: Need to search for more information")
            state.plan = decision_data.get("plan", "")
            state.set_metadata("search_queries", decision_data.get("search_queries", []))
            state.set_metadata("missing_info", decision_data.get("missing_info", []))
            # 状态将在工作流协调器中更新
        else:  # CODING
            logger.info("Decision: Ready to start coding")
            state.plan = decision_data.get("plan", "")
            # 状态将在工作流协调器中更新

        state.set_metadata("planning_decision", decision_data)
        return state

    def _get_context_summary(self, state: WorkflowState) -> str:
        """获取上下文摘要"""
        context_parts = []

        if state.user_goal:
            context_parts.append(f"用户目标: {state.user_goal}")

        if state.plan:
            context_parts.append(f"当前计划: {state.plan}")

        if state.code_files:
            context_parts.append(f"已有文件: {', '.join(state.code_files.keys())}")

        if state.execution_results:
            last_result = state.execution_results[-1]
            context_parts.append(
                f"上次执行结果: 返回码={last_result.return_code}, "
                f"耗时={last_result.execution_time:.2f}秒"
            )

        return "\n".join(context_parts) if context_parts else "无上下文信息"

    def _get_search_summary(self, state: WorkflowState) -> str:
        """获取搜索结果摘要"""
        if not state.search_context.results:
            return "无搜索结果"

        summary_parts = []
        for i, (query, result, summary) in enumerate(
            zip(
                state.search_context.queries,
                state.search_context.results,
                state.search_context.summaries or [""] * len(state.search_context.queries)
            )
        ):
            summary_parts.append(f"搜索{i+1}: {query}")
            if summary:
                summary_parts.append(f"  总结: {summary[:200]}...")

        return "\n".join(summary_parts)

    def _parse_decision_response(self, response: str) -> dict:
        """解析模型决策响应"""
        try:
            # 尝试解析JSON
            if response.strip().startswith("{"):
                return json.loads(response)

            # 如果不是JSON，尝试提取关键信息
            decision = "CODING"  # 默认
            if any(word in response.lower() for word in ["search", "searching", "need more", "missing"]):
                decision = "SEARCHING"

            return {
                "decision": decision,
                "reason": response,
                "plan": "",
                "missing_info": [],
                "search_queries": []
            }

        except Exception as e:
            logger.error(f"Error parsing decision response: {e}")
            return {
                "decision": "CODING",
                "reason": f"解析错误，默认进入编码阶段: {str(e)}",
                "plan": "",
                "missing_info": [],
                "search_queries": []
            }

    async def refine_plan(self, state: WorkflowState) -> WorkflowState:
        """基于搜索结果完善计划"""
        if not state.search_context.results:
            return state

        logger.info("Refining plan based on search results")

        messages = [
            {"role": "system", "content": PROMPTS["planning"]["system"]},
            {"role": "user", "content": PROMPTS["planning"]["refinement"].format(
                original_plan=state.plan,
                search_results=self._get_search_summary(state)
            )}
        ]

        response = await self.model.ainvoke(messages)
        state.refined_plan = response.content

        # 更新计划
        state.plan = state.refined_plan

        return state