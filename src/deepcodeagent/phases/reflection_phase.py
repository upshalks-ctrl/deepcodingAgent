"""
反思阶段实现
Phase 5: Reflection - 分析执行结果，决定下一步
"""

import json
import logging
from typing import Dict, Any

from .core import BasePhase, WorkflowPhase, WorkflowState
from ...prompts import PROMPTS
from ...myllms.base import BaseModel

logger = logging.getLogger(__name__)


class ReflectionPhase(BasePhase):
    """反思阶段"""

    def __init__(self, model: BaseModel, hook_registry=None):
        super().__init__(model, hook_registry)

    @property
    def phase_type(self) -> WorkflowPhase:
        return WorkflowPhase.REFLECTING

    def can_enter(self, state: WorkflowState) -> bool:
        """检查是否可以进入反思阶段"""
        return state.current_phase == WorkflowPhase.REFLECTING

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """执行反思逻辑"""
        logger.info("Entering Reflection Phase")

        if not state.last_execution:
            logger.error("No execution result to reflect on")
            state.update_phase(WorkflowPhase.CODING)  # 返回编码阶段
            return state

        # 获取执行的代码
        executed_code = self._get_executed_code(state)

        # 构建反思消息
        user_message = PROMPTS["reflection"]["user"].format(
            user_goal=state.user_goal,
            return_code=state.last_execution.return_code,
            stdout=state.last_execution.stdout,
            stderr=state.last_execution.stderr,
            execution_time=state.last_execution.execution_time,
            code_content=executed_code[:1000] + "..." if len(executed_code) > 1000 else executed_code,
            expected_output=state.get_metadata("expected_output", "未指定")
        )

        # 调用模型进行反思
        messages = [
            {"role": "system", "content": PROMPTS["reflection"]["system"]},
            {"role": "user", "content": user_message}
        ]

        response = await self.model.ainvoke(messages)
        reflection_data = self._parse_reflection_response(response.content)

        # 保存反思结果
        state.reflection_notes.append(response.content)
        state.error_analysis = reflection_data.get("error_details", "")

        # 根据反思结果决定下一步
        next_phase = self._determine_next_phase(reflection_data, state)
        state.update_phase(next_phase)

        # 如果需要改进计划，保存改进建议
        if reflection_data.get("improvements"):
            state.set_metadata("improvements", reflection_data["improvements"])

        logger.info(f"Reflection complete, next phase: {next_phase.value}")

        return state

    def _get_executed_code(self, state: WorkflowState) -> str:
        """获取被执行的代码"""
        if state.current_file and state.current_file in state.code_files:
            return state.code_files[state.current_file]

        # 返回第一个Python文件
        for filename, content in state.code_files.items():
            if filename.endswith(".py"):
                return content

        return ""

    def _parse_reflection_response(self, response: str) -> Dict[str, Any]:
        """解析反思响应"""
        try:
            # 尝试解析JSON
            if response.strip().startswith("{"):
                return json.loads(response)

            # 如果不是JSON，分析文本内容
            response_lower = response.lower()

            # 判断场景
            scenario = "D"  # 默认逻辑错误
            success = False

            if any(keyword in response_lower for keyword in [
                "success", "成功", "completed", "完成", "scenario a"
            ]):
                scenario = "A"
                success = True
            elif any(keyword in response_lower for keyword in [
                "syntax error", "import error", "typo", "scenario b"
            ]):
                scenario = "B"
            elif any(keyword in response_lower for keyword in [
                "api misuse", "method not found", "knowledge gap", "scenario c"
            ]):
                scenario = "C"

            # 提取建议
            improvements = []
            lines = response.split("\n")
            for line in lines:
                if line.strip().startswith("-") or line.strip().startswith("*"):
                    improvements.append(line.strip().lstrip("-* "))

            return {
                "scenario": scenario,
                "success": success,
                "analysis": response,
                "error_type": "unknown" if not success else None,
                "error_details": "",
                "next_action": self._map_scenario_to_action(scenario),
                "improvements": improvements
            }

        except Exception as e:
            logger.error(f"Error parsing reflection response: {e}")
            return {
                "scenario": "D",
                "success": False,
                "analysis": f"解析错误: {str(e)}",
                "next_action": "CODING",
                "improvements": []
            }

    def _map_scenario_to_action(self, scenario: str) -> str:
        """将场景映射到下一个动作"""
        mapping = {
            "A": "FINISHED",
            "B": "CODING",
            "C": "SEARCHING",
            "D": "CODING"
        }
        return mapping.get(scenario, "CODING")

    def _determine_next_phase(self, reflection_data: Dict[str, Any], state: WorkflowState) -> WorkflowPhase:
        """确定下一个阶段"""
        next_action = reflection_data.get("next_action", "CODING")

        if next_action == "FINISHED":
            return WorkflowPhase.FINISHED
        elif next_action == "CODING":
            # 更新计划
            if reflection_data.get("improvements"):
                # 可以在这里更新计划
                pass
            return WorkflowPhase.CODING
        elif next_action == "SEARCHING":
            return WorkflowPhase.SEARCHING
        else:
            return WorkflowPhase.CODING

    def generate_summary(self, state: WorkflowState) -> str:
        """生成执行摘要"""
        summary_parts = []

        # 基本信息
        summary_parts.append(f"用户目标: {state.user_goal}")

        # 执行结果
        if state.last_execution:
            result = state.last_execution
            summary_parts.append(
                f"最终执行结果: 返回码={result.return_code}, "
                f"耗时={result.execution_time:.2f}秒"
            )
            if result.stdout.strip():
                summary_parts.append(f"输出: {result.stdout[:200]}...")
            if result.stderr.strip():
                summary_parts.append(f"错误: {result.stderr[:200]}...")

        # 反思结论
        if state.reflection_notes:
            summary_parts.append(f"反思结论: {state.reflection_notes[-1][:300]}...")

        # 生成的文件
        if state.code_files:
            summary_parts.append(f"生成文件: {', '.join(state.code_files.keys())}")

        return "\n\n".join(summary_parts)