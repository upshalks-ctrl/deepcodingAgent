#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
架构团队V2 - 整合Planner、Coordinator、Search和Writer的新架构
包含所有组件在一个文件中
"""

import json
import asyncio
import logging
from pydoc import text
import re
from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

from .tool_registry import register_tools_by_agent_name
from src.hooks.context_manager import create_context_compression_hook
from src.hooks.hooks import HookEvent
from src.my_agent.agent import MyAgent, AgentConfig, create_my_agent
from .core import DeepCodeAgentState, WorkflowStage, ResearchPlan
from src.utils.prompt_loader import load_agent_prompt

logger = logging.getLogger(__name__)


@dataclass
class ResearchTask:
    """研究任务数据结构"""
    id: str
    query: str
    title: str = None  # 任务标题
    focus_areas: List[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    result: str = None
    observations: List[str] = None

    def __post_init__(self):
        if self.observations is None:
            self.observations = []


class Planner:
    """规划器 - 不使用工具，生成结构化的研究计划（JSON格式）"""

    def __init__(self, model):
        self.model = model
        self.max_research_rounds = 3

        # 创建不使用工具的Planner agent
        config = AgentConfig(
            name="Planner",
            system_prompt=load_agent_prompt("planner"),
            max_iterations=3,
            debug=False
        )
        self.agent = MyAgent(config=config, model=model)

    async def process(self, state: DeepCodeAgentState) -> DeepCodeAgentState:
        """处理规划逻辑，生成搜索计划"""
        logger.info(f"[PLANNER] Starting to generate search plan (Round {state.research_plan.current_round if state.research_plan else 1})")

        # 准备提示
        user_requirement = state.clarified_requirement or state.user_requirement

        # 如果是后续轮次，包含之前的搜索结果
        previous_findings = ""
        if state.research_plan and state.research_plan.current_round > 1:
            previous_findings = f"\n\n之前的搜索结果（轮次 {state.research_plan.current_round - 1}）：\n"
            if hasattr(state, 'observations') and state.observations:
                previous_findings += "\n".join(state.observations[-3:])  # 最近3个观察
            elif state.research_findings:
                previous_findings += "\n".join(state.research_findings[-3:])  # 最近3个发现
            previous_findings += "\n\n请基于这些结果，生成新的搜索计划来填补信息空白。"

        messages = [
            {"role": "user", "content": f"""
            用户需求：{user_requirement}
            {previous_findings}

            请为这个需求生成一个详细的搜索计划，包含具体的搜索任务。
            """}
        ]

        try:
            # 获取计划内容
            response = await self.agent.arun(messages)
            plan_text = str(response) if response else ""

            # 提取JSON
            plan_json = self._extract_json_from_response(plan_text)

            if plan_json:
                # 创建或更新研究计划
                if not state.research_plan:
                    state.research_plan = ResearchPlan(
                        id=f"plan_{state.task_id}",
                        title=plan_json.get('title', f"研究计划 - {state.task_id}"),
                        thought=json.dumps(plan_json, ensure_ascii=False),  # 存储完整的JSON
                        max_rounds=self.max_research_rounds,
                        current_round=1,
                        status="planning"
                    )
                else:
                    # 更新现有计划
                    state.research_plan.thought = json.dumps(plan_json, ensure_ascii=False)
                    state.research_plan.status = "planning"

                logger.info(f"[PLANNER] Generated research plan: {state.research_plan.title}")
            else:
                # 如果无法提取JSON，创建默认计划
                default_title = f"默认研究计划 - {state.task_id}"
                if not state.research_plan:
                    state.research_plan = ResearchPlan(
                        id=f"plan_{state.task_id}",
                        title=default_title,
                        thought=json.dumps({
                            "title": default_title,
                            "objective": user_requirement,
                            "tasks": [{"query": user_requirement, "focus_areas": ["general"]}]
                        }, ensure_ascii=False),
                        max_rounds=self.max_research_rounds,
                        current_round=1,
                        status="planning"
                    )
                else:
                    state.research_plan.thought = json.dumps({
                        "title": default_title,
                        "objective": user_requirement,
                        "tasks": [{"query": user_requirement, "focus_areas": ["general"]}]
                    }, ensure_ascii=False)
                    state.research_plan.status = "planning"

                logger.warning("[PLANNER] Using default plan due to JSON extraction failure")

        except Exception as e:
            logger.error(f"[PLANNER] Error generating plan: {e}")
            # 创建错误处理计划
            error_title = f"错误处理计划 - {state.task_id}"
            if not state.research_plan:
                state.research_plan = ResearchPlan(
                    id=f"plan_{state.task_id}_error",
                    title=error_title,
                    thought=json.dumps({
                        "title": error_title,
                        "objective": user_requirement,
                        "tasks": [{"query": f"Error occurred: {str(e)}", "focus_areas": ["error"]}]
                    }, ensure_ascii=False),
                    max_rounds=1,
                    current_round=1,
                    status="planning"
                )
            else:
                state.research_plan.thought = json.dumps({
                    "title": error_title,
                    "objective": user_requirement,
                    "tasks": [{"query": f"Error occurred: {str(e)}", "focus_areas": ["error"]}]
                }, ensure_ascii=False)
                state.research_plan.status = "planning"

        return state

    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:

        """从响应文本中提取JSON"""
        try:
            if response_text.find("```json") != -1:
                # 提取代码块中的JSON
                match = re.search(r"```json(.*?)```", response_text, re.DOTALL)
                if match:
                    json_str = match.group(1).strip()
                    return json.loads(json_str)

            # 如果没有找到完整的JSON行，尝试查找多行JSON
            json_start = None
            json_end = None
            brace_count = 0

            for i, char in enumerate(response_text):
                if char == '{':
                    if brace_count == 0:
                        json_start = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and json_start is not None:
                        json_end = i + 1
                        break

            if json_start is not None and json_end is not None:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)

        except Exception as e:
            logger.error(f"[PLANNER] JSON extraction error: {e}")

        return None


class Search:
    """搜索类 - 使用MyAgent执行搜索任务"""

    def __init__(self, model, output_dir: Path = None):
        self.model = model
        self.output_dir = output_dir or Path("@testdir")
        self.agent = None
        self._context_hook = None

    async def _ensure_agent(self):
        """确保 agent 已初始化"""
        if not self.agent:
            self._context_hook = create_context_compression_hook(
                max_tokens=100000,  # Set to 100k tokens (below the 131072 limit)
                model="basic"
            )
            # 使用工具注册创建Search agent
            self.agent = await create_my_agent(
                name="searcher",
                model=self.model,
                system_prompt=load_agent_prompt("searcher"),
                hooks=[(HookEvent.BEFORE_MODEL, self._context_hook, 10)]
            )
            register_tools_by_agent_name(self.agent, "searcher")

    async def search(self, query: str, focus_areas: List[str] = None) -> str:
        """执行搜索任务"""
        # 确保 agent 已初始化
        await self._ensure_agent()

        user_message = f"请使用工具搜索以下内容并总结结果：{query}"

        if focus_areas:
            areas_text = "\n重点关注领域：\n" + "\n".join(f"- {area}" for area in focus_areas)
            user_message += areas_text

        user_message = [{"role": "user", "content": user_message}]
        logger.info(f"[SEARCH] Starting search for: {query}")

        try:
            response = await self.agent.arun(user_message)
            result = str(response) if response else "No results"
            logger.info(f"[SEARCH] Search completed for: {query}")
            return result
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            logger.error(f"[SEARCH] {error_msg}")
            return error_msg


class Coordinator:
    """协调器 - 负责协调Planner和Search之间的交互"""

    def __init__(self, model, output_dir: Path = None):
        self.model = model
        self.output_dir = output_dir or Path("@testdir")
        self.search = None  # Will be initialized when needed
        self.max_iterations = 5
        self.current_iteration = 0

    async def process(self, state: DeepCodeAgentState) -> DeepCodeAgentState:
        """处理协调逻辑"""
        logger.info("[COORDINATOR] Starting coordination process")

        # 确保有研究计划
        if not state.research_plan:
            logger.error("[COORDINATOR] No research plan found")
            return state

        # 解析研究计划中的任务
        research_tasks = self._parse_research_plan(state.research_plan)
        logger.info(f"[COORDINATOR] Parsed {len(research_tasks)} research tasks")



        # 并行执行研究任务
        logger.info(f"[COORDINATOR] Executing {len(research_tasks)} tasks in parallel")

        async def execute_task(task):
            logger.info(f"[COORDINATOR] Starting task: {task.title or task.id}")
            task.status = "in_progress"

            try:
                # 创建或获取Search agent
                if not self.search:
                    self.search = Search(self.model, self.output_dir)
                result = await self.search.search(task.query, task.focus_areas)
                task.result = result
                task.observations.append(f"Search result: {result[:200]}...")
                task.status = "completed"
                logger.info(f"[COORDINATOR] Task completed: {task.id}")
                return task
            except Exception as e:
                task.observations.append(f"Search error: {str(e)}")
                task.status = "failed"
                logger.error(f"[COORDINATOR] Task failed: {task.id}, error: {e}")
                return task

        # 并行执行所有任务
        executed_tasks = await asyncio.gather(*[execute_task(task) for task in research_tasks])

        # 更新原任务列表
        for i, task in enumerate(research_tasks):
            research_tasks[i] = executed_tasks[i]

        # 更新研究发现
        state.research_findings = [task.result for task in research_tasks if task.result]

        # 检查是否需要新的搜索计划
        logger.info("[COORDINATOR] Checking if need new search plan")
        need_more = await self.check_need_new_plan(state)

        if need_more and state.research_plan.current_round < 3:  # 最多3轮
            logger.info(f"[COORDINATOR] Need more search, current round: {state.research_plan.current_round}")
            state.research_plan.current_round += 1
            state.research_plan.status = "needs_more_search"
            # 添加到observations中
            if not hasattr(state, 'observations'):
                state.observations = []
            state.observations.append(f"Round {state.research_plan.current_round}: Need more search based on findings")
            # 返回到搜索规划阶段
            state.current_stage = WorkflowStage.RESEARCH_PLANNING
        else:
            logger.info("[COORDINATOR] Search completed, no more plans needed")
            state.research_plan.status = "completed"
            # 进入架构编写阶段
            state.current_stage = WorkflowStage.ARCHITECTURE_WRITING

        logger.info("[COORDINATOR] Coordination completed")
        return state

    def _parse_research_plan(self, research_plan: ResearchPlan) -> List[ResearchTask]:
        """解析搜索计划，提取搜索任务"""
        tasks = []

        try:
            # 尝试解析thought字段中的JSON
            if research_plan.thought:
                # 查找JSON部分
                thought_lines = research_plan.thought.split('\n')
                json_str = None

                for line in thought_lines:
                    if line.strip().startswith('{') and line.strip().endswith('}'):
                        json_str = line.strip()
                        break

                # 如果没有找到单行JSON，尝试提取多行JSON
                if not json_str:
                    json_str = self._extract_json_from_response(research_plan.thought)
                    if json_str:
                        json_str = json.dumps(json_str, ensure_ascii=False)

                if json_str:
                    plan_data = json.loads(json_str)

                    # 处理新的steps格式
                    if 'steps' in plan_data:
                        for i, step_data in enumerate(plan_data['steps']):
                            # 只处理需要搜索的步骤
                            if step_data.get('need_search', True) and step_data.get('step_type') == 'research':
                                task = ResearchTask(
                                    id=f"step_{i+1}",
                                    title=step_data.get('title', f'Step {i+1}'),
                                    query=step_data.get('description', ''),
                                    focus_areas=['research']
                                )
                                # 将步骤描述存入observations
                                task.observations = [f"Step goal: {step_data.get('description', '')}"]
                                tasks.append(task)

                    # 兼容旧的search_tasks格式
                    elif 'search_tasks' in plan_data:
                        for i, task_data in enumerate(plan_data['search_tasks']):
                            task = ResearchTask(
                                id=f"search_task_{i+1}",
                                query=task_data.get('query', ''),
                                focus_areas=task_data.get('focus_areas', [])
                            )
                            # 将期望结果存入observations
                            if 'expected_results' in task_data:
                                task.observations = [f"Expected: {task_data['expected_results']}"]
                            tasks.append(task)

                    # 兼容更旧的tasks格式
                    elif 'tasks' in plan_data:
                        for i, task_data in enumerate(plan_data['tasks']):
                            task = ResearchTask(
                                id=f"task_{i+1}",
                                query=task_data.get('query', ''),
                                focus_areas=task_data.get('focus_areas', [])
                            )
                            tasks.append(task)

            # 如果没有找到JSON任务，创建默认搜索任务
            if not tasks:
                # 从搜索计划标题创建任务
                task = ResearchTask(
                    id="default_search_task",
                    query=research_plan.title,
                    focus_areas=["general"]
                )
                tasks.append(task)

        except Exception as e:
            logger.error(f"[COORDINATOR] Failed to parse search plan: {e}")
            # 创建默认任务
            task = ResearchTask(
                id="fallback_search_task",
                query=research_plan.title or "Search task",
                focus_areas=["general"]
            )
            tasks.append(task)

        return tasks

    async def check_need_new_plan(self, state: DeepCodeAgentState) -> bool:
        """检查是否需要生成新的搜索计划"""
        if not state.research_findings:
            return True

        # 创建评估agent（使用coordinator自己的模型）
        config = AgentConfig(
            name="SearchEvaluator",
            system_prompt="""
            你是一个搜索评估专家。你的任务是评估当前的搜索结果是否足够完整以编写架构文档。

            评估标准：
            1. 搜索是否覆盖了技术栈选择
            2. 是否包含了实现方案
            3. 是否有足够的细节支持开发
            4. 搜索结果的质量和相关性

            请基于搜索结果给出客观评估。
            """,
            max_iterations=1,
            debug=False
        )
        evaluator = MyAgent(config=config, model=self.model)

        prompt = f"""
        评估当前的搜索结果是否足够完整以编写架构文档。

        需求：{state.user_requirement}

        当前搜索结果：
        {chr(10).join(state.research_findings[:3])}

        请回答：是否需要更多的搜索？

        回答格式：
        {{
            "need_more_search": true/false,
            "reason": "原因说明"
        }}
        """

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await evaluator.arun(messages)
            response_text = str(response) if response else ""

            # 提取JSON响应
            for line in response_text.split('\n'):
                if line.strip().startswith('{') and line.strip().endswith('}'):
                    result = json.loads(line.strip())
                    # 兼容新旧字段名
                    need_more = result.get('need_more_search', result.get('need_more_research', False))
                    logger.info(f"[COORDINATOR] Evaluation result: need_more_search={need_more}, reason={result.get('reason', 'N/A')}")
                    return need_more

        except Exception as e:
            logger.error(f"[COORDINATOR] Error checking need for new plan: {e}")

        return False


class Writer:
    """编写器 - 基于研究结果编写架构文档"""

    def __init__(self, model):
        self.model = model

        # 创建不使用工具的Writer agent
        config = AgentConfig(
            name="Writer",
            system_prompt=load_agent_prompt("reporter"),
            max_iterations=3,
            debug=False
        )
        self.agent = MyAgent(config=config, model=model)

    async def write_document(self, requirement: str, research_findings: List[str]) -> str:
        """编写架构文档"""
        findings_text = "\n\n".join([f"发现{i+1}: {finding}" for i, finding in enumerate(research_findings)])

        user_message = f"""
        需求：{requirement}

        研究发现：
        {findings_text}

        请基于以上信息编写详细的架构文档。
        """

        logger.info("[WRITER] Starting to write architecture document")

        try:
            # Convert user_message to proper message format
            messages = [{"role": "user", "content": user_message}]
            response = await self.agent.arun(messages)
            document = str(response) if response else "No document generated"
            logger.info("[WRITER] Architecture document completed")
            return document
        except Exception as e:
            error_msg = f"Document writing failed: {str(e)}"
            logger.error(f"[WRITER] {error_msg}")
            return error_msg


class ArchitectureTeam:
    """架构团队"""

    def __init__(
        self,
        planner_model,
        coordinator_model,  # 用于协调的模型
        researcher_model,    # 用于搜索的模型
        writer_model,        # 用于编写文档的模型
        output_dir: Path,
    ):
        self.planner = Planner(planner_model)
        self.coordinator = Coordinator(coordinator_model, output_dir)
        self.writer = Writer(writer_model)
        self.output_dir = output_dir
        self.max_planning_rounds = 3

    async def process(self, state: DeepCodeAgentState) -> DeepCodeAgentState:
        """处理整个架构研究流程"""
        logger.info(f"[ARCHITECTURE_TEAM_V2] Starting processing, stage: {state.current_stage.value}")

        # 需求分析阶段 - 直接跳到研究规划
        if state.current_stage == WorkflowStage.REQUIREMENT_ANALYSIS:
            state.current_stage = WorkflowStage.RESEARCH_PLANNING
            logger.info("[ARCHITECTURE_TEAM_V2] Skipping requirement analysis, moving to research planning")
            return state

        # 研究规划阶段
        elif state.current_stage == WorkflowStage.RESEARCH_PLANNING:
            logger.info("[ARCHITECTURE_TEAM_V2] Delegating to planner for research planning")
            state = await self.planner.process(state)
            if state.research_plan:
                state.research_plan.status = "planning_completed"
                state.current_stage = WorkflowStage.RESEARCH_EXECUTION
            logger.info(f"[ARCHITECTURE_TEAM_V2] Planner completed, new stage: {state.current_stage.value}")
            return state

        # 研究执行阶段
        elif state.current_stage == WorkflowStage.RESEARCH_EXECUTION:
            logger.info("[ARCHITECTURE_TEAM_V2] Executing research with coordinator")
            state = await self.coordinator.process(state)
            # Coordinator已经处理了阶段转换
            return state

        # 架构编写阶段
        elif state.current_stage == WorkflowStage.ARCHITECTURE_WRITING:
            logger.info("[ARCHITECTURE_TEAM_V2] Delegating to writer for architecture document")

            if state.research_findings:
                architecture_doc = await self.writer.write_document(
                    state.user_requirement,
                    state.research_findings
                )
                state.architecture_document = architecture_doc
                logger.info("[ARCHITECTURE_TEAM_V2] Architecture document generated")

            state.current_stage = WorkflowStage.COMPLETED
            return state

        else:
            logger.warning(f"[ARCHITECTURE_TEAM_V2] Unknown stage: {state.current_stage}")
            return state