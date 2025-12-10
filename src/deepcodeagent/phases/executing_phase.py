"""
执行阶段实现
Phase 4: Executing - 运行代码，捕获结果
"""

import logging
from typing import Dict, Any

from .core import BasePhase, WorkflowPhase, WorkflowState, ExecutionResult
from ...tools.sandbox import get_sandbox, SandboxConfig
from ...myllms.base import BaseModel

logger = logging.getLogger(__name__)


class ExecutingPhase(BasePhase):
    """执行阶段"""

    def __init__(self, model: BaseModel, hook_registry=None, sandbox_config=None):
        super().__init__(model, hook_registry)
        self.sandbox_config = sandbox_config or SandboxConfig()

    @property
    def phase_type(self) -> WorkflowPhase:
        return WorkflowPhase.EXECUTING

    def can_enter(self, state: WorkflowState) -> bool:
        """检查是否可以进入执行阶段"""
        return state.current_phase == WorkflowPhase.EXECUTING and bool(state.code_files)

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """执行代码逻辑"""
        logger.info("Entering Executing Phase")

        # 获取要执行的代码
        code = self._prepare_execution_code(state)

        if not code:
            logger.error("No code to execute")
            state.error_analysis = "没有可执行的代码"
            return state

        # 获取沙箱
        sandbox = get_sandbox(self.sandbox_config)

        # 触发执行前钩子
        if self.hook_registry:
            from ...hooks.hooks import HookContext, HookEvent
            context = HookContext(
                data={"code": code[:500] + "..." if len(code) > 500 else code},
                metadata={
                    "tool_name": "execute_python_code",
                    "phase": self.phase_name,
                    "files": list(state.code_files.keys())
                },
                event_type=HookEvent.BEFORE_TOOL_CALL
            )
            context = await self.hook_registry.trigger(HookEvent.BEFORE_TOOL_CALL, context)

            # 检查是否被批准执行
            if not context.get_metadata("execution_approved", True):
                state.error_analysis = context.get_metadata("rejection_reason", "执行未获批准")
                return state

        # 执行代码
        logger.info(f"Executing code with {len(state.code_files)} files")
        result = await sandbox.execute_code(
            code=code,
            files=state.code_files,
            command=state.get_metadata("execution_command")
        )

        # 添加执行结果
        state.add_execution_result(result)

        # 记录执行信息
        logger.info(f"Execution completed: return_code={result.return_code}, "
                   f"duration={result.execution_time:.2f}s")

        # 触发执行后钩子
        if self.hook_registry:
            context.data.update({
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.return_code
            })
            await self.hook_registry.trigger(HookEvent.AFTER_TOOL_CALL, context)

        return state

    def _prepare_execution_code(self, state: WorkflowState) -> str:
        """准备要执行的代码"""
        # 如果有主文件，使用主文件
        if state.current_file and state.current_file in state.code_files:
            return state.code_files[state.current_file]

        # 查找main.py或__main__.py
        for filename in ["main.py", "__main__.py", "app.py"]:
            if filename in state.code_files:
                state.current_file = filename
                return state.code_files[filename]

        # 使用第一个Python文件
        for filename, content in state.code_files.items():
            if filename.endswith(".py"):
                state.current_file = filename
                return content

        return ""

    async def execute_with_tests(self, state: WorkflowState, test_code: str) -> WorkflowState:
        """带测试的执行"""
        logger.info("Executing code with tests")

        # 获取主代码
        main_code = self._prepare_execution_code(state)

        if not main_code:
            logger.error("No code to test")
            state.error_analysis = "没有可测试的代码"
            return state

        # 获取沙箱
        sandbox = get_sandbox(self.sandbox_config)

        # 执行测试
        result = await sandbox.execute_test(main_code, test_code)

        # 添加执行结果
        state.add_execution_result(result)

        logger.info(f"Test execution completed: return_code={result.return_code}")

        return state

    def analyze_execution_result(self, state: WorkflowState) -> Dict[str, Any]:
        """分析执行结果"""
        if not state.last_execution:
            return {"success": False, "reason": "无执行结果"}

        result = state.last_execution

        analysis = {
            "success": result.return_code == 0,
            "return_code": result.return_code,
            "has_output": bool(result.stdout.strip()),
            "has_errors": bool(result.stderr.strip()),
            "execution_time": result.execution_time
        }

        # 错误分类
        if result.return_code != 0:
            error_output = result.stderr.lower()
            if any(keyword in error_output for keyword in [
                "syntaxerror", "indentationerror", "syntax error"
            ]):
                analysis["error_type"] = "syntax"
            elif any(keyword in error_output for keyword in [
                "importerror", "modulenotfounderror", "no module named"
            ]):
                analysis["error_type"] = "import"
            elif any(keyword in error_output for keyword in [
                "attributeerror", "method not found", "object has no attribute"
            ]):
                analysis["error_type"] = "api_misuse"
            elif any(keyword in error_output for keyword in [
                "nameerror", "not defined", "undefined"
            ]):
                analysis["error_type"] = "name"
            else:
                analysis["error_type"] = "runtime"

        # 输出分析
        if result.stdout.strip():
            # 简单的输出分析
            output_length = len(result.stdout)
            analysis["output_length"] = output_length
            analysis["output_preview"] = result.stdout[:200] + "..." if output_length > 200 else result.stdout

        return analysis