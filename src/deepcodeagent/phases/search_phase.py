"""
搜索阶段实现
Phase 2: Searching - 生成查询，搜索信息，总结结果
"""

import json
import logging
from typing import List, Dict, Any

from .core import BasePhase, WorkflowPhase, WorkflowState
from ...prompts import PROMPTS
from ...tools.search import TavilySearchTool, DuckDuckGoSearchTool
from ...myllms.base import BaseModel

logger = logging.getLogger(__name__)


class SearchingPhase(BasePhase):
    """搜索阶段"""

    def __init__(self, model: BaseModel, search_tool=None, hook_registry=None):
        super().__init__(model, hook_registry)
        self.search_tool = search_tool or TavilySearchTool()

    @property
    def phase_type(self) -> WorkflowPhase:
        return WorkflowPhase.SEARCHING

    def can_enter(self, state: WorkflowState) -> bool:
        """检查是否可以进入搜索阶段"""
        return state.current_phase == WorkflowPhase.SEARCHING

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """执行搜索逻辑"""
        logger.info("Entering Searching Phase")

        # 获取待搜索信息
        missing_info = state.get_metadata("missing_info", [])
        search_queries = state.get_metadata("search_queries", [])

        if not missing_info and not search_queries:
            # 生成搜索查询
            queries = await self._generate_search_queries(state)
        else:
            queries = search_queries

        # 执行搜索
        search_results = []
        for query in queries[:3]:  # 限制搜索次数
            logger.info(f"Searching for: {query}")
            result = await self._perform_search(query)
            search_results.append({
                "query": query,
                "result": result
            })

            # 添加到状态
            state.add_search_result(query, result)

        # 总结搜索结果
        summaries = await self._summarize_results(state, search_results)

        # 更新搜索上下文
        state.search_context.summaries.extend(summaries)

        return state

    async def _generate_search_queries(self, state: WorkflowState) -> List[str]:
        """生成搜索查询"""
        messages = [
            {"role": "system", "content": PROMPTS["search"]["system"]},
            {"role": "user", "content": PROMPTS["search"]["user"].format(
                missing_info=state.get_metadata("missing_info", ["需要更多信息"]),
                user_goal=state.user_goal,
                previous_queries=state.search_context.queries
            )}
        ]

        response = await self.model.ainvoke(messages)
        query_data = self._parse_search_response(response.content)

        return query_data.get("queries", [])

    async def _perform_search(self, query: str) -> str:
        """执行搜索"""
        try:
            # 触发搜索钩子
            if self.hook_registry:
                from ...hooks.hooks import HookContext, HookEvent
                context = HookContext(
                    data={"query": query},
                    metadata={"tool_name": "search_tool"},
                    event_type=HookEvent.BEFORE_TOOL_CALL
                )
                await self.hook_registry.trigger(HookEvent.BEFORE_TOOL_CALL, context)

            # 执行搜索
            if hasattr(self.search_tool, 'search'):
                results = await self.search_tool.search(query)
            else:
                # 回退到DuckDuckGo
                ddg = DuckDuckGoSearchTool()
                results = await ddg.search(query)

            # 格式化结果
            if isinstance(results, list):
                formatted_results = []
                for item in results[:5]:  # 限制结果数量
                    if isinstance(item, dict):
                        title = item.get("title", "")
                        snippet = item.get("snippet", "")
                        link = item.get("link", "")
                        formatted_results.append(f"- {title}\n  {snippet}\n  {link}")
                    else:
                        formatted_results.append(f"- {item}")
                result_text = "\n".join(formatted_results)
            else:
                result_text = str(results)

            # 触发搜索后钩子
            if self.hook_registry:
                context.data["result"] = result_text
                await self.hook_registry.trigger(HookEvent.AFTER_TOOL_CALL, context)

            return result_text

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return f"搜索失败: {str(e)}"

    async def _summarize_results(self, state: WorkflowState, search_results: List[Dict]) -> List[str]:
        """总结搜索结果"""
        summaries = []

        for item in search_results:
            query = item["query"]
            result = item["result"]

            messages = [
                {"role": "system", "content": PROMPTS["search"]["system"]},
                {"role": "user", "content": f"请总结以下搜索结果的关键信息：\n\n查询: {query}\n\n结果:\n{result}"}
            ]

            response = await self.model.ainvoke(messages)
            summaries.append(response.content)

        return summaries

    def _parse_search_response(self, response: str) -> Dict[str, Any]:
        """解析搜索响应"""
        try:
            # 尝试解析JSON
            if response.strip().startswith("{"):
                return json.loads(response)

            # 提取查询列表
            queries = []
            for line in response.split("\n"):
                if line.strip().startswith("-") or line.strip().startswith("*"):
                    query = line.strip().lstrip("-* ").strip()
                    if query:
                        queries.append(query)

            return {"queries": queries}

        except Exception as e:
            logger.error(f"Error parsing search response: {e}")
            return {"queries": []}

    async def check_sufficiency(self, state: WorkflowState) -> bool:
        """检查信息是否足够"""
        messages = [
            {"role": "system", "content": PROMPTS["search"]["system"]},
            {"role": "user", "content": PROMPTS["search"]["refinement"].format(
                search_results=self._get_search_summary(state),
                user_goal=state.user_goal
            )}
        ]

        response = await self.model.ainvoke(messages)

        # 简单判断：如果响应中包含"足够"、"complete"等词，则认为信息足够
        sufficient_keywords = ["足够", "sufficient", "complete", "已完成", "无需更多搜索"]
        return any(keyword in response.lower() for keyword in sufficient_keywords)

    def _get_search_summary(self, state: WorkflowState) -> str:
        """获取搜索摘要"""
        if not state.search_context.results:
            return "无搜索结果"

        summary_parts = []
        for i, (query, result) in enumerate(zip(state.search_context.queries, state.search_context.results)):
            summary_parts.append(f"搜索{i+1}: {query[:100]}...")
            summary_parts.append(f"  结果: {result[:300]}...")

        return "\n".join(summary_parts)