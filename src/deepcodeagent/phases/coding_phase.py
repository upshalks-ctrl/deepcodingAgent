"""
编码阶段实现
Phase 3: Coding - 基于计划和搜索结果生成代码
"""

import json
import logging
import os
from typing import Dict, Any, Optional

from .core import BasePhase, WorkflowPhase, WorkflowState
from ...prompts import PROMPTS
from ...myllms.base import BaseModel

logger = logging.getLogger(__name__)


class CodingPhase(BasePhase):
    """编码阶段"""

    def __init__(self, model: BaseModel, hook_registry=None):
        super().__init__(model, hook_registry)

    @property
    def phase_type(self) -> WorkflowPhase:
        return WorkflowPhase.CODING

    def can_enter(self, state: WorkflowState) -> bool:
        """检查是否可以进入编码阶段"""
        return state.current_phase == WorkflowPhase.CODING

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """执行编码逻辑"""
        logger.info("Entering Coding Phase")

        # 构建编码消息
        user_message = PROMPTS["coding"]["user"].format(
            plan=state.plan,
            search_summary=self._get_search_summary(state),
            api_details=self._extract_api_details(state),
            user_goal=state.user_goal
        )

        # 调用模型生成代码
        messages = [
            {"role": "system", "content": PROMPTS["coding"]["system"]},
            {"role": "user", "content": user_message}
        ]

        response = await self.model.ainvoke(messages)
        code_data = self._parse_code_response(response.content)

        # 保存代码文件
        if code_data.get("files"):
            for filename, content in code_data["files"].items():
                state.code_files[filename] = content
                logger.info(f"Generated file: {filename}")

            # 设置主入口
            if code_data.get("main_entry"):
                state.current_file = code_data["main_entry"]

            # 保存元数据
            state.set_metadata("dependencies", code_data.get("dependencies", []))
            state.set_metadata("execution_command", code_data.get("execution_command", ""))
            state.set_metadata("code_description", code_data.get("description", ""))

        return state

    def _get_search_summary(self, state: WorkflowState) -> str:
        """获取搜索结果摘要，特别是API信息"""
        if not state.search_context.results:
            return "无搜索结果"

        # 重点关注API相关的搜索结果
        api_info = []
        for i, summary in enumerate(state.search_context.summaries):
            if summary and any(keyword in summary.lower() for keyword in ["api", "method", "function", "class"]):
                api_info.append(f"API信息{i+1}: {summary[:500]}")

        return "\n\n".join(api_info) if api_info else "无特定API信息"

    def _extract_api_details(self, state: WorkflowState) -> str:
        """提取API详情"""
        api_details = []

        # 从搜索结果中提取API信息
        for result in state.search_context.results:
            if "api" in result.lower() or "method" in result.lower():
                # 简单提取，实际可以更复杂
                api_details.append(result[:1000])

        return "\n\n".join(api_details) if api_details else "无API详情"

    def _parse_code_response(self, response: str) -> Dict[str, Any]:
        """解析代码响应"""
        try:
            # 尝试解析JSON
            if response.strip().startswith("{"):
                return json.loads(response)

            # 如果不是JSON，尝试提取代码块
            files = {}
            current_file = "main.py"
            current_content = []

            lines = response.split("\n")
            for line in lines:
                if line.strip().startswith("```"):
                    continue
                elif line.strip().startswith("# 文件:") or line.strip().startswith("# File:"):
                    # 保存之前的文件
                    if current_content:
                        files[current_file] = "\n".join(current_content)
                    # 开始新文件
                    current_file = line.split(":", 1)[1].strip()
                    current_content = []
                else:
                    current_content.append(line)

            # 保存最后一个文件
            if current_content:
                files[current_file] = "\n".join(current_content)

            return {
                "files": files,
                "main_entry": current_file if files else "main.py",
                "dependencies": [],
                "execution_command": "python main.py",
                "description": "Generated code"
            }

        except Exception as e:
            logger.error(f"Error parsing code response: {e}")
            # 作为回退，将整个响应作为单个文件
            return {
                "files": {"main.py": response},
                "main_entry": "main.py",
                "dependencies": [],
                "execution_command": "python main.py",
                "description": "Generated code (fallback)"
            }

    async def refine_code(self, state: WorkflowState) -> WorkflowState:
        """基于执行结果修复代码"""
        if not state.last_execution:
            return state

        logger.info("Refining code based on execution results")

        # 获取最新的代码
        latest_code = ""
        if state.current_file and state.current_file in state.code_files:
            latest_code = state.code_files[state.current_file]

        messages = [
            {"role": "system", "content": PROMPTS["coding"]["system"]},
            {"role": "user", "content": PROMPTS["coding"]["refinement"].format(
                original_code=latest_code,
                execution_error=state.last_execution.stderr,
                error_analysis=state.error_analysis or ""
            )}
        ]

        response = await self.model.ainvoke(messages)
        code_data = self._parse_code_response(response.content)

        # 更新代码文件
        if code_data.get("files"):
            for filename, content in code_data["files"].items():
                state.code_files[filename] = content
                logger.info(f"Refined file: {filename}")

        return state

    def get_main_code(self, state: WorkflowState) -> str:
        """获取要执行的主代码"""
        if state.current_file and state.current_file in state.code_files:
            return state.code_files[state.current_file]

        # 如果没有指定主文件，返回第一个Python文件
        for filename, content in state.code_files.items():
            if filename.endswith(".py"):
                return content

        # 如果没有Python文件，返回第一个文件
        if state.code_files:
            return list(state.code_files.values())[0]

        return ""