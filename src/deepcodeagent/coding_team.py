"""
代码工程团队 - 重构版本，使用tools包中的工具

包含：编码任务协调者、编码器、测试者、思考者
"""

import asyncio
import logging
import json
from typing import Optional, Dict, Any, List

from src.my_agent.agent import MyAgent, AgentConfig
from src.middleware import MiddlewareContext
from src.human_in_the_loop import HumanInTheLoop
from src.utils.prompt_loader import load_agent_prompt, format_prompt_for_agent
from src.tools import get_agent_tools, ALL_TOOLS
from src.myllms import get_llm_by_type

from .core import DeepCodeAgentState, WorkflowStage, TeamType, CodingTask, CodingPlan

logger = logging.getLogger(__name__)


class CodingTaskCoordinator:
    """编码任务协调者 - 负责整个编码流程的协调"""

    def __init__(self, model, middleware_chain=None, human_in_the_loop=None):
        self.model = model

        # Load prompt from markdown file with full formatting
        base_prompt = format_prompt_for_agent("code_coordinator", load_agent_prompt("code_coordinator"))
        system_prompt = base_prompt + "\n\n" + self._get_system_prompt()

        config = AgentConfig(
            name="CodingTaskCoordinator",
            system_prompt=system_prompt,
            max_iterations=10,
            debug=True,
        )

        self.agent = MyAgent(
            config=config,
            model=model,
        )

        # Register tools from tools package
        self._register_tools()

    def _get_system_prompt(self) -> str:
        return """
## Current Context
You are coordinating a coding team to implement an architecture document.

## Coordination Protocol
1. Analyze the architecture document thoroughly
2. Break down into concrete coding tasks
3. Assign tasks to appropriate team members
4. Track progress and quality
5. Ensure all coding standards are met

## Available Tools
- create_coding_plan: Create detailed coding plan with tasks
- assign_task: Assign tasks to team members
- update_task_status: Update task progress
- request_review: Request code reviews
- coordinate_testing: Coordinate testing activities
- generate_progress_report: Generate progress reports

## Team Members
- **Coder**: Writes and implements code
- **TestRunner**: Executes tests and validates quality
- **Reflector**: Reviews code and provides improvements
"""

    def _register_tools(self):
        # Get tools for code_coordinator from tools package
        tool_names = get_agent_tools("code_coordinator")

        for tool_name in tool_names:
            if tool_name in ALL_TOOLS:
                tool_class = ALL_TOOLS[tool_name]

                # Create a tool instance to get schema
                tool_instance = tool_class()
                if hasattr(tool_instance, 'get_schema'):
                    schema = tool_instance.get_schema()
                    func_def = schema.get('function', {})
                    description = func_def.get('description', '')
                    parameters = func_def.get('parameters', {})
                else:
                    description = ''
                    parameters = {}

                def make_tool_handler(t_instance, t_name):
                    async def tool_handler(**arguments):
                        try:
                            if hasattr(t_instance, 'execute'):
                                if asyncio.iscoroutinefunction(t_instance.execute):
                                    result = await t_instance.execute(**arguments)
                                else:
                                    result = t_instance.execute(**arguments)
                                return result
                            return {"success": True, "message": f"Tool {t_name} executed"}
                        except Exception as e:
                            return {"success": False, "error": str(e)}
                    return tool_handler

                self.agent.register_tool(
                    name=tool_name,
                    description=description,
                    parameters=parameters,
                    handler=make_tool_handler(tool_instance, tool_name)
                )

    async def process(self, state: DeepCodeAgentState) -> DeepCodeAgentState:
        """处理编码任务协调逻辑"""
        logger.info("[CODING_COORDINATOR] Starting coding task coordination")
        logger.debug(f"[CODING_COORDINATOR] Current stage: {state.current_stage.value}")

        # 如果没有编码计划，创建计划
        if not state.coding_plan and state.architecture_document:
            logger.info("[CODING_COORDINATOR] No coding plan found, creating new one")
            # 准备创建计划的消息
            messages = self._prepare_messages(state)
            logger.debug(f"[CODING_COORDINATOR] Prepared {len(messages)} messages for plan creation")

            # 准备工具
            tools = []
            tool_names = get_agent_tools("code_coordinator")
            logger.debug(f"[CODING_COORDINATOR] Available tools: {tool_names}")
            for tool_name in tool_names:
                if tool_name in ALL_TOOLS:
                    tool_class = ALL_TOOLS[tool_name]
                    tool_instance = tool_class()
                    if hasattr(tool_instance, 'get_schema'):
                        schema = tool_instance.get_schema()
                        tools.append(schema)
            logger.debug(f"[CODING_COORDINATOR] Prepared {len(tools)} tools")

            try:
                # 使用模型的 ainvoke 方法直接调用
                logger.info("[CODING_COORDINATOR] Invoking model to create coding plan")
                response = await self.model.ainvoke(messages, tools=tools)
                logger.debug("[CODING_COORDINATOR] Model response received")

                # 处理工具调用
                if response.tool_calls:
                    logger.info(f"[CODING_COORDINATOR] Found {len(response.tool_calls)} tool calls")
                    for tool_call in response.tool_calls:
                        tool_name = tool_call.get("name")
                        args = tool_call.get("arguments", {})
                        logger.debug(f"[CODING_COORDINATOR] Processing tool: {tool_name}")

                        if tool_name == "create_coding_plan":
                            logger.info("[CODING_COORDINATOR] Creating coding plan")
                            # 创建编码计划
                            tasks_data = args.get("tasks", [])
                            logger.debug(f"[CODING_COORDINATOR] Plan includes {len(tasks_data)} tasks")

                            state.coding_plan = CodingPlan(
                                id=f"coding_{state.task_id}",
                                title=args.get("plan_title", f"编码计划 - {state.task_id}"),
                                architecture=args.get("architecture_summary", state.architecture_document),
                            )

                            # 添加任务到计划
                            for task_data in tasks_data:
                                task = CodingTask(
                                    id=task_data.get("id", f"task_{len(state.coding_plan.tasks)}"),
                                    title=task_data.get("title", ""),
                                    description=task_data.get("description", ""),
                                    status="pending"
                                )
                                state.coding_plan.tasks.append(task)
                                logger.debug(f"[CODING_COORDINATOR] Added task: {task.title}")

                            logger.info(f"[CODING_COORDINATOR] Created coding plan with {len(state.coding_plan.tasks)} tasks")
                else:
                    logger.warning("[CODING_COORDINATOR] No tool calls in response")

            except Exception as e:
                logger.error(f"[CODING_COORDINATOR] Error creating coding plan: {e}", exc_info=True)
                state.error = f"Coding coordinator error: {str(e)}"
        else:
            if state.coding_plan:
                logger.info(f"[CODING_COORDINATOR] Existing coding plan found with {len(state.coding_plan.tasks)} tasks")
            else:
                logger.warning("[CODING_COORDINATOR] No architecture document available for planning")

        # 根据当前阶段决定行动
        if state.current_stage == WorkflowStage.CODING_COORDINATION:
            state.current_stage = WorkflowStage.TASK_BREAKDOWN
            logger.info("[CODING_COORDINATOR] Moved to task breakdown stage")
        elif state.current_stage == WorkflowStage.TASK_BREAKDOWN:
            # After task breakdown, move to code writing
            state.current_stage = WorkflowStage.CODE_WRITING
            logger.info("[CODING_COORDINATOR] Moved to code writing stage")

        return state

    def _prepare_messages(self, state: DeepCodeAgentState) -> list:
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": f"架构文档:\n{state.architecture_document}"},
        ]

        if state.coding_plan:
            messages.append({
                "role": "system",
                "content": f"当前编码计划状态: {state.coding_plan.status}\n"
                          f"任务数量: {len(state.coding_plan.tasks) if state.coding_plan.tasks else 0}"
            })

        return messages


class Coder:
    """编码器 - 负责编写代码"""

    def __init__(self, model, middleware_chain=None, human_in_the_loop=None):
        self.model = model

        # Load prompt from markdown file with full formatting
        base_prompt = format_prompt_for_agent("coder", load_agent_prompt("coder"))
        system_prompt = base_prompt + "\n\n" + self._get_system_prompt()

        config = AgentConfig(
            name="Coder",
            system_prompt=system_prompt,
            max_iterations=10,
            debug=True,
        )

        self.agent = MyAgent(
            config=config,
            model=model,
        )

        # Register tools from tools package
        self._register_tools()

    def _get_system_prompt(self) -> str:
        return """
## Coding Environment
You have access to file system tools to read, write, and edit code files.

## Available Tools
- read_file: Read existing files
- write_file: Create new files
- edit_file: Modify existing files
- list_files: List directory contents
- code_search: Search code patterns
- create_task: Create coding tasks
- create_test_file: Create test files

## Implementation Guidelines
1. Always read existing files before editing
2. Write clean, modular code with clear separation of concerns
3. Include proper error handling and logging
4. Add type annotations where applicable
5. Write meaningful comments for complex logic
"""

    def _register_tools(self):
        # Get tools for coder from tools package
        tool_names = get_agent_tools("coder")

        for tool_name in tool_names:
            if tool_name in ALL_TOOLS:
                tool_class = ALL_TOOLS[tool_name]

                # Create a tool instance to get schema
                tool_instance = tool_class()
                if hasattr(tool_instance, 'get_schema'):
                    schema = tool_instance.get_schema()
                    func_def = schema.get('function', {})
                    description = func_def.get('description', '')
                    parameters = func_def.get('parameters', {})
                else:
                    description = ''
                    parameters = {}

                def make_tool_handler(t_instance, t_name):
                    async def tool_handler(**arguments):
                        try:
                            if hasattr(t_instance, 'execute'):
                                if asyncio.iscoroutinefunction(t_instance.execute):
                                    result = await t_instance.execute(**arguments)
                                else:
                                    result = t_instance.execute(**arguments)
                                return result
                            return {"success": True, "message": f"Tool {t_name} executed"}
                        except Exception as e:
                            return {"success": False, "error": str(e)}
                    return tool_handler

                self.agent.register_tool(
                    name=tool_name,
                    description=description,
                    parameters=parameters,
                    handler=make_tool_handler(tool_instance, tool_name)
                )

    async def process(self, state: DeepCodeAgentState) -> DeepCodeAgentState:
        """处理编码逻辑"""
        logger.info("Coder processing")

        if not state.coding_plan or not state.coding_plan.tasks:
            return state

        current_task = state.get_current_task()
        if not current_task:
            return state

        # 准备编码消息
        messages = self._prepare_messages(state)

        try:
            # 执行代码生成
            response = await self.agent.ainvoke(messages)

            # 解析响应，提取生成的代码和文件信息
            generated_code = self._extract_code_from_response(response)

            # 保存生成的代码到任务中
            current_task.code = generated_code.get("code", "")
            current_task.files_generated = generated_code.get("files", [])

            # 记录生成的代码文件
            if hasattr(state, 'code_files'):
                if not state.code_files:
                    state.code_files = []
                state.code_files.extend(current_task.files_generated)

            # 更新任务状态
            current_task.status = "completed"
            state.current_stage = WorkflowStage.CODE_TESTING

            logger.info(f"Task {current_task.id} coding completed")
            logger.info(f"Generated {len(current_task.files_generated)} files")

        except Exception as e:
            logger.error(f"Coder error: {e}", exc_info=True)
            current_task.status = "failed"
            state.error = f"Coder error: {str(e)}"

        return state

    def _extract_code_from_response(self, response) -> Dict[str, Any]:
        """
        从响应中提取代码和文件信息

        Args:
            response: Agent响应对象

        Returns:
            包含代码和文件信息的字典
        """
        result = {
            "code": "",
            "files": [],
            "status": "unknown"
        }

        # 获取响应内容
        if hasattr(response, 'content'):
            content = str(response.content)
        elif isinstance(response, dict):
            content = response.get("content", "")
        else:
            content = str(response)

        result["code"] = content

        # 尝试解析标准化输出格式
        import re

        # 查找标准化摘要部分
        summary_pattern = r'### CODING_TASK_SUMMARY ###\n(.*?)\n### END_SUMMARY ###'
        summary_match = re.search(summary_pattern, content, re.DOTALL)

        if summary_match:
            summary_content = summary_match.group(1)

            # 解析任务状态
            status_match = re.search(r'TASK_STATUS:\s*(\w+)', summary_content)
            if status_match:
                result["status"] = status_match.group(1).lower()

            # 解析创建的文件
            files_section = re.search(r'FILES_CREATED:\n(.*?)(?=\n\n|\w+:)', summary_content, re.DOTALL)
            if files_section:
                files_text = files_section.group(1)
                file_lines = [line.strip() for line in files_text.split('\n') if line.strip().startswith('-')]
                for line in file_lines:
                    # 提取文件路径 (第一个冒号前的内容)
                    if ':' in line:
                        file_path = line.split(':', 1)[0].replace('-', '').strip()
                        if file_path:
                            result["files"].append(file_path)

            # 解析修改的文件
            modified_section = re.search(r'FILES_MODIFIED:\n(.*?)(?=\n\n|\w+:)', summary_content, re.DOTALL)
            if modified_section:
                files_text = modified_section.group(1)
                file_lines = [line.strip() for line in files_text.split('\n') if line.strip().startswith('-')]
                for line in file_lines:
                    if ':' in line:
                        file_path = line.split(':', 1)[0].replace('-', '').strip()
                        if file_path and file_path not in result["files"]:
                            result["files"].append(file_path)
        else:
            # 如果没有标准化格式，使用旧的解析方法
            file_pattern = r'文件路径[：:]\s*([^\n]+)'
            matches = re.findall(file_pattern, content)
            for match in matches:
                result["files"].append(match.strip())

            # 默认状态为已完成（如果有代码生成）
            if result["files"] or result["code"].strip():
                result["status"] = "completed"
            else:
                result["status"] = "failed"

        return result

    def _prepare_messages(self, state: DeepCodeAgentState) -> list:
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": f"架构文档:\n{state.coding_plan.architecture if state.coding_plan else ''}"},
        ]

        current_task = state.get_current_task()
        if current_task:
            messages.append({
                "role": "user",
                "content": f"当前任务: {current_task.title}\n描述: {current_task.description}\n\n请实现这个任务。"
            })

        return messages


class TestRunner:
    """测试者 - 负责运行和测试代码"""

    def __init__(self, model, middleware_chain=None, human_in_the_loop=None):
        self.model = model

        # Load prompt from markdown file with full formatting
        base_prompt = format_prompt_for_agent("executor", load_agent_prompt("executor"))
        system_prompt = base_prompt + "\n\n" + self._get_system_prompt()

        config = AgentConfig(
            name="TestRunner",
            system_prompt=system_prompt,
            max_iterations=5,
            debug=True,
        )

        self.agent = MyAgent(
            config=config,
            model=model,
        )

        # Register tools from tools package
        self._register_tools()

    def _get_system_prompt(self) -> str:
        return """
## Testing Framework
You are responsible for ensuring code quality through comprehensive testing.

## Available Tools
- run_code: Execute code in sandbox
- execute_tests: Run various test types
- check_quality: Check code quality metrics
- create_test_suite: Create test suites
- generate_test_report: Generate test reports

## Test Types
1. Unit Tests - Test individual functions/methods
2. Integration Tests - Test component interactions
3. Quality Checks - Code style, security, performance
4. smoke Tests - Basic functionality validation

## Testing Process
1. Identify test requirements
2. Create test cases
3. Execute tests
4. Analyze results
5. Generate reports
"""

    def _register_tools(self):
        # Get tools for executor from tools package
        tool_names = get_agent_tools("executor")

        for tool_name in tool_names:
            if tool_name in ALL_TOOLS:
                tool_class = ALL_TOOLS[tool_name]

                # Create a tool instance to get schema
                tool_instance = tool_class()
                if hasattr(tool_instance, 'get_schema'):
                    schema = tool_instance.get_schema()
                    func_def = schema.get('function', {})
                    description = func_def.get('description', '')
                    parameters = func_def.get('parameters', {})
                else:
                    description = ''
                    parameters = {}

                def make_tool_handler(t_instance, t_name):
                    async def tool_handler(**arguments):
                        try:
                            if hasattr(t_instance, 'execute'):
                                if asyncio.iscoroutinefunction(t_instance.execute):
                                    result = await t_instance.execute(**arguments)
                                else:
                                    result = t_instance.execute(**arguments)
                                return result
                            return {"success": True, "message": f"Tool {t_name} executed"}
                        except Exception as e:
                            return {"success": False, "error": str(e)}
                    return tool_handler

                self.agent.register_tool(
                    name=tool_name,
                    description=description,
                    parameters=parameters,
                    handler=make_tool_handler(tool_instance, tool_name)
                )

    async def process(self, state: DeepCodeAgentState) -> DeepCodeAgentState:
        """处理测试逻辑"""
        logger.info("Test runner processing")

        current_task = state.get_current_task()
        if not current_task:
            return state

        # 准备测试消息
        messages = self._prepare_messages(state)

        try:
            # 执行测试
            response = await self.agent.ainvoke(messages)

            # 解析测试结果
            test_results = self._extract_test_results(response)

            # 更新任务的测试结果
            current_task.test_results = test_results
            current_task.test_passed = test_results.get("passed", False)

            # 如果有测试报告，保存到状态中
            if "report" in test_results:
                if not hasattr(state, 'test_reports'):
                    state.test_reports = []
                state.test_reports.append({
                    "task_id": current_task.id,
                    "task_title": current_task.title,
                    "report": test_results["report"]
                })

            # 根据测试结果决定下一步
            if current_task.test_passed:
                state.current_stage = WorkflowStage.REFLECTION
                logger.info(f"Task {current_task.id} testing PASSED")
            else:
                state.current_stage = WorkflowStage.CODE_WRITING
                logger.info(f"Task {current_task.id} testing FAILED, returning to coding")

        except Exception as e:
            logger.error(f"Test runner error: {e}", exc_info=True)
            current_task.status = "failed"
            state.error = f"Test runner error: {str(e)}"

        return state

    def _extract_test_results(self, response) -> Dict[str, Any]:
        """
        从响应中提取测试结果

        Args:
            response: Agent响应对象

        Returns:
            包含测试结果的字典
        """
        result = {
            "passed": False,
            "tests": [],
            "report": "",
            "errors": [],
            "total_tests": 0,
            "passed_count": 0,
            "failed_count": 0,
            "coverage": {}
        }

        # 获取响应内容
        if hasattr(response, 'content'):
            content = str(response.content)
        elif isinstance(response, dict):
            content = response.get("content", "")
        else:
            content = str(response)

        # 尝试解析标准化输出格式
        import re

        # 查找标准化摘要部分
        summary_pattern = r'### TESTING_TASK_SUMMARY ###\n(.*?)\n### END_SUMMARY ###'
        summary_match = re.search(summary_pattern, content, re.DOTALL)

        if summary_match:
            summary_content = summary_match.group(1)

            # 解析任务状态
            status_match = re.search(r'TASK_STATUS:\s*(\w+)', summary_content)
            if status_match:
                status = status_match.group(1).lower()
                result["passed"] = status == "completed"

            # 解析测试结果统计
            total_match = re.search(r'TOTAL_TESTS:\s*(\d+)', summary_content)
            if total_match:
                result["total_tests"] = int(total_match.group(1))

            passed_match = re.search(r'PASSED:\s*(\d+)', summary_content)
            if passed_match:
                result["passed_count"] = int(passed_match.group(1))

            failed_match = re.search(r'FAILED:\s*(\d+)', summary_content)
            if failed_match:
                result["failed_count"] = int(failed_match.group(1))

            # 解析覆盖率指标
            line_cov_match = re.search(r'LINE_COVERAGE:\s*([\d.]+%?)', summary_content)
            if line_cov_match:
                result["coverage"]["line"] = line_cov_match.group(1)

            branch_cov_match = re.search(r'BRANCH_COVERAGE:\s*([\d.]+%?)', summary_content)
            if branch_cov_match:
                result["coverage"]["branch"] = branch_cov_match.group(1)

            # 解析测试执行的列表
            tests_section = re.search(r'TESTS_EXECUTED:\n(.*?)(?=\n\n|\w+:)', summary_content, re.DOTALL)
            if tests_section:
                tests_text = tests_section.group(1)
                test_lines = [line.strip() for line in tests_text.split('\n') if line.strip().startswith('-')]
                for line in test_lines:
                    result["tests"].append(line)

            # 解析发现的问题
            issues_section = re.search(r'ISSUES_FOUND:\n(.*?)(?=\n\n|\w+:)', summary_content, re.DOTALL)
            if issues_section:
                issues_text = issues_section.group(1)
                issue_lines = [line.strip() for line in issues_text.split('\n') if line.strip().startswith('-')]
                result["errors"] = issue_lines

            # 组合测试报告
            if result["total_tests"] > 0:
                result["report"] = f"执行了 {result['total_tests']} 个测试，"
                if result["passed_count"] == result["total_tests"]:
                    result["report"] += "全部通过"
                else:
                    result["report"] += f"{result['passed_count']} 通过，{result['failed_count']} 失败"

                if result["coverage"]:
                    result["report"] += f"\n覆盖率: 行覆盖率 {result['coverage'].get('line', 'N/A')}"
        else:
            # 如果没有标准化格式，使用旧的解析方法
            if "测试通过" in content or "TEST PASSED" in content or "All tests passed" in content:
                result["passed"] = True

            # 查找测试报告
            report_pattern = r'测试报告[：:]\s*([\s\S]*?)(?=\n\n|\Z)'
            report_match = re.search(report_pattern, content)
            if report_match:
                result["report"] = report_match.group(1).strip()

            # 查找错误信息
            error_pattern = r'错误[：:]\s*([^\n]+)'
            errors = re.findall(error_pattern, content)
            result["errors"] = errors

        return result

    def _prepare_messages(self, state: DeepCodeAgentState) -> list:
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
        ]

        current_task = state.get_current_task()
        if current_task:
            messages.append({
                "role": "user",
                "content": f"待测试任务: {current_task.title}\n描述: {current_task.description}"
            })

            if current_task.code:
                messages.append({
                    "role": "user",
                    "content": f"\n代码内容:\n{current_task.code}"
                })

        return messages


class Reflector:
    """思考者 - 负责反思和改进"""

    def __init__(self, model, middleware_chain=None, human_in_the_loop=None):
        self.model = model

        # Load prompt from markdown file with full formatting
        base_prompt = format_prompt_for_agent("reflector", load_agent_prompt("reflector"))
        system_prompt = base_prompt + "\n\n" + self._get_system_prompt()

        config = AgentConfig(
            name="Reflector",
            system_prompt=system_prompt,
            max_iterations=5,
            debug=True,
        )

        self.agent = MyAgent(
            config=config,
            model=model,
        )

        # Register tools from tools package
        self._register_tools()

    def _get_system_prompt(self) -> str:
        return """
## Reflection Process
Review completed work and identify opportunities for improvement.

## Available Tools
- generate_todos: Create actionable todo items
- record_reflection: Record reflections
- suggest_improvements: Suggest improvements
- complete_task: Complete tasks with summary
- create_retrospective: Create team retrospectives

## Reflection Areas
1. Code Quality - Maintainability, readability, performance
2. Architecture - Design patterns, modularity, scalability
3. Best Practices - Security, testing, documentation
4. Process - Workflow efficiency, collaboration

## Output Format
Provide actionable insights and specific improvement recommendations.
"""

    def _register_tools(self):
        # Get tools for reflector from tools package
        tool_names = get_agent_tools("reflector")

        for tool_name in tool_names:
            if tool_name in ALL_TOOLS:
                tool_class = ALL_TOOLS[tool_name]

                # Create a tool instance to get schema
                tool_instance = tool_class()
                if hasattr(tool_instance, 'get_schema'):
                    schema = tool_instance.get_schema()
                    func_def = schema.get('function', {})
                    description = func_def.get('description', '')
                    parameters = func_def.get('parameters', {})
                else:
                    description = ''
                    parameters = {}

                def make_tool_handler(t_instance, t_name):
                    async def tool_handler(**arguments):
                        try:
                            if hasattr(t_instance, 'execute'):
                                if asyncio.iscoroutinefunction(t_instance.execute):
                                    result = await t_instance.execute(**arguments)
                                else:
                                    result = t_instance.execute(**arguments)
                                return result
                            return {"success": True, "message": f"Tool {t_name} executed"}
                        except Exception as e:
                            return {"success": False, "error": str(e)}
                    return tool_handler

                self.agent.register_tool(
                    name=tool_name,
                    description=description,
                    parameters=parameters,
                    handler=make_tool_handler(tool_instance, tool_name)
                )

    async def process(self, state: DeepCodeAgentState) -> DeepCodeAgentState:
        """处理反思逻辑"""
        logger.info("Reflector processing")

        current_task = state.get_current_task()
        if not current_task:
            return state

        # 准备反思消息
        messages = self._prepare_messages(state)

        try:
            response = await self.agent.ainvoke(messages)

            # 记录反思结果
            reflection = f"反思任务 {current_task.id}: 实现质量良好，已完成测试"
            state.reflection_notes.append(reflection)

            # 推进到下一任务或完成
            state.advance_to_next_task()

            # 如果所有任务完成，进入编码完成阶段
            if state.current_stage == WorkflowStage.CODING_COMPLETED:
                logger.info("All coding tasks completed")

        except Exception as e:
            logger.error(f"Reflector error: {e}", exc_info=True)
            state.error = f"Reflector error: {str(e)}"

        return state

    def _prepare_messages(self, state: DeepCodeAgentState) -> list:
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": f"架构文档:\n{state.coding_plan.architecture if state.coding_plan else ''}"},
        ]

        current_task = state.get_current_task()
        if current_task:
            task_info = f"已完成任务: {current_task.title}\n"
            if current_task.code:
                task_info += f"\n代码实现:\n{current_task.code}"
            if current_task.test_results:
                task_info += f"\n测试结果:\n" + "\n".join(current_task.test_results)

            messages.append({
                "role": "user",
                "content": task_info
            })

        return messages


class CodingTeam:
    """代码工程团队"""

    def __init__(
        self,
        coordinator_model,
        coder_model,
        test_model,
        reflector_model,
        middleware_chain=None,
        human_in_the_loop=None,
    ):
        self.coordinator = CodingTaskCoordinator(coordinator_model, middleware_chain, human_in_the_loop)
        self.coder = Coder(coder_model, middleware_chain, human_in_the_loop)
        self.test_runner = TestRunner(test_model, middleware_chain, human_in_the_loop)
        self.reflector = Reflector(reflector_model, middleware_chain, human_in_the_loop)

    async def process(self, state: DeepCodeAgentState) -> DeepCodeAgentState:
        """处理整个编码流程，持续执行直到所有任务完成"""
        logger.info(f"[CODING_TEAM] Starting processing, stage: {state.current_stage.value}")

        try:
            # 持续处理循环，直到所有任务完成或出错
            max_iterations = 100  # 防止无限循环
            iteration = 0

            while iteration < max_iterations and state.current_stage != WorkflowStage.CODING_COMPLETED:
                iteration += 1
                logger.info(f"[CODING_TEAM] Iteration {iteration}, current stage: {state.current_stage.value}")

                # 根据当前阶段调用相应的组件
                if state.current_stage == WorkflowStage.CODING_COORDINATION:
                    logger.info("[CODING_TEAM] Delegating to coordinator")
                    state = await self.coordinator.process(state)
                    logger.debug(f"[CODING_TEAM] Coordinator completed, new stage: {state.current_stage.value}")

                elif state.current_stage == WorkflowStage.TASK_BREAKDOWN:
                    logger.info("[CODING_TEAM] Delegating to coordinator for task breakdown")
                    state = await self.coordinator.process(state)
                    logger.debug(f"[CODING_TEAM] Coordinator completed, new stage: {state.current_stage.value}")

                elif state.current_stage == WorkflowStage.CODE_WRITING:
                    logger.info("[CODING_TEAM] Delegating to coder")
                    state = await self.coder.process(state)
                    logger.debug(f"[CODING_TEAM] Coder completed, new stage: {state.current_stage.value}")

                elif state.current_stage == WorkflowStage.CODE_TESTING:
                    logger.info("[CODING_TEAM] Delegating to test runner")
                    state = await self.test_runner.process(state)
                    logger.debug(f"[CODING_TEAM] Test runner completed, new stage: {state.current_stage.value}")

                elif state.current_stage == WorkflowStage.REFLECTION:
                    logger.info("[CODING_TEAM] Delegating to reflector")
                    state = await self.reflector.process(state)
                    logger.debug(f"[CODING_TEAM] Reflector completed, new stage: {state.current_stage.value}")

                    # 反思后检查是否还有任务需要处理
                    if state.coding_plan and state.coding_plan.tasks:
                        # 查找下一个待处理的任务
                        next_task = None
                        for task in state.coding_plan.tasks:
                            if task.status != "completed":
                                next_task = task
                                break

                        if next_task:
                            logger.info(f"[CODING_TEAM] Found next task: {next_task.title}")
                            state.current_task_index = state.coding_plan.tasks.index(next_task)
                            state.current_stage = WorkflowStage.CODE_WRITING
                        else:
                            # 所有任务都完成了
                            logger.info("[CODING_TEAM] All tasks completed")
                            state.current_stage = WorkflowStage.CODING_COMPLETED
                            state.coding_plan.status = "completed"

                else:
                    logger.warning(f"[CODING_TEAM] Unknown stage: {state.current_stage.value}")
                    break

                # 短暂休息，避免过于频繁的处理
                await asyncio.sleep(0.1)

            logger.info(f"[CODING_TEAM] Processing completed after {iteration} iterations, final stage: {state.current_stage.value}")

        except Exception as e:
            logger.error(f"[CODING_TEAM] Error in process: {e}", exc_info=True)
            state.error = f"Coding team error: {str(e)}"

        return state