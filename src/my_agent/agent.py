"""
Agent 核心实现
提供类似 create_agent 的功能，支持模型、MCP 工具、中间件和人在环中
"""

import asyncio
import json
import uuid
from typing import Any, Callable, Dict, List, Optional, AsyncIterator, Tuple
from dataclasses import dataclass, field
import logging

from src.mcp.mcp_client import MCPServerConfig
from src.mcp.mcp_manager import MCPManager
from .models import Message, ToolDefinition, ToolResult, AgentInfo
from src.myllms.base import BaseModel, ChatResponse
from src.hooks import HookEvent, HookContext, Hook, HookRegistry, hook

logger = logging.getLogger(__name__)


def limit_tool_result(data: Any, max_chars: int = 50000) -> Any:
    """
    限制工具返回结果的长度，避免token过多

    Args:
        data: 工具返回的数据
        max_chars: 最大字符数限制

    Returns:
        处理后的数据
    """
    if data is None:
        return None

    # 如果是错误信息，保留完整错误
    if isinstance(data, dict) and "error" in data:
        error_msg = str(data["error"])
        if len(error_msg) > max_chars:
            return {"error": error_msg[:max_chars] + "...[错误信息已截断]"}
        return data

    # 将数据转换为JSON字符串查看长度
    json_str = json.dumps(data, ensure_ascii=False, indent=2)

    # 如果不超过限制，直接返回
    if len(json_str) <= max_chars:
        return data

    # 超过限制时，根据数据类型进行不同处理
    if isinstance(data, list):
        # 列表类型：返回前几项和总数
        result = []
        current_chars = len('[\n')
        for i, item in enumerate(data):
            item_str = json.dumps(item, ensure_ascii=False)
            if current_chars + len(item_str) + 10 > max_chars:  # 10是缓冲
                break
            result.append(item)
            current_chars += len(item_str) + 1  # 1是逗号

        return {
            "_truncated": True,
            "_original_count": len(data),
            "_returned_count": len(result),
            "data": result,
            "_note": f"列表已截断，仅显示前{len(result)}项，共{len(data)}项"
        }

    elif isinstance(data, dict):
        # 字典类型：返回部分字段
        result = {}
        current_chars = len('{\n')
        for key, value in data.items():
            item_str = json.dumps({key: value}, ensure_ascii=False)[2:-2]  # 去掉外层的{}
            if current_chars + len(f'"{key}": {item_str},\n') + 10 > max_chars:
                break
            result[key] = value
            current_chars += len(f'"{key}": {item_str},\n')

        return {
            "_truncated": True,
            "_original_count": len(data),
            "_returned_keys": list(result.keys()),
            "data": result,
            "_note": f"字典已截断，仅显示{len(result)}个字段，共{len(data)}个字段"
        }

    else:
        # 其他类型：直接截断字符串
        if isinstance(data, str):
            return data[:max_chars] + "...[内容已截断]"
        else:
            json_str = json.dumps(data, ensure_ascii=False)
            return json_str[:max_chars] + "...[内容已截断]"


# ========== 事件系统 ==========

class AgentEventType:
    """事件类型常量"""
    ITERATION_START = "iteration_start"
    ITERATION_END = "iteration_end"
    LLM_CALL_START = "llm_call_start"
    LLM_CALL_END = "llm_call_end"
    LLM_TOKEN = "llm_token"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_END = "tool_call_end"
    TOOL_RESULT = "tool_result"
    MESSAGE_ADDED = "message_added"
    HUMAN_APPROVAL = "human_approval"
    ERROR = "error"
    FINISHED = "finished"


@dataclass
class AgentEvent:
    """Agent事件"""
    type: str
    data: Any = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentConfig:
    """Agent 配置"""
    name: str = "MyAgent"
    system_prompt: str = "You are a helpful assistant with access to tools."
    max_iterations: int = 10  # 最大工具调用轮次
    debug: bool = False

    def __post_init__(self):
        if self.max_iterations <= 0:
            raise ValueError("AgentConfig.max_iterations must be > 0")


@dataclass
class AgentState:
    """Agent 状态"""
    messages: List[Message] = field(default_factory=list)
    iteration: int = 0
    finished: bool = False
    error: Optional[str] = None

    def add_message(self, message: Message):
        """添加消息"""
        self.messages.append(message)

    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """获取最近的消息"""
        return self.messages[-limit:] if limit > 0 else self.messages


class MyAgent:
    """独立的 Agent 实现

    支持：
    - 多种模型提供商
    - MCP 工具动态加载
    - 基于事件的钩子系统
    """

    def __init__(
        self,
        config: AgentConfig,
        model:BaseModel,
        hook_registry: Optional[HookRegistry] = None,
    ):
        self.config = config
        self.mcp_manager = MCPManager()
        self._local_tools: Dict[str, Callable] = {}
        self._local_tool_defs: List[ToolDefinition] = []

        # 模型
        self.model = model

        # 钩子注册表（所有扩展都通过钩子实现）
        self.hook_registry = hook_registry or HookRegistry()

        # 初始化日志
        if config.debug:
            logging.basicConfig(level=logging.DEBUG)
            logger.setLevel(logging.DEBUG)

        logger.info(f"Initialized agent: {self.config.name}")

    # ========== MCP 服务器管理 ==========

    async def add_mcp_server(
        self,
        server_id: str,
        command: List[str],
        name: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> bool:
        """添加 MCP 服务器"""
        config = MCPServerConfig(
            id=server_id,
            command=command,
            name=name,
            env=env
        )
        success = await self.mcp_manager.add_server(config)
        if success:
            logger.info(f"Added MCP server: {server_id}")
        return success

    async def remove_mcp_server(self, server_id: str) -> bool:
        """移除 MCP 服务器"""
        success = await self.mcp_manager.remove_server(server_id)
        if success:
            logger.info(f"Removed MCP server: {server_id}")
        return success

    # ========== 本地工具注册 ==========

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable
    ):
        """注册本地工具"""
        self._local_tools[name] = handler
        self._local_tool_defs.append(ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            server_id=None  # 本地工具
        ))
        logger.info(f"Registered local tool: {name}")

    def register_tool_from_base_tool(self, base_tool: Any):
        """
        从 BaseTool 实例注册工具

        Args:
            base_tool: BaseTool 子类实例
        """
        tool_def = base_tool.get_tool_definition()
        self.register_tool(
            name=tool_def["name"],
            description=tool_def["description"],
            parameters=tool_def["parameters"],
            handler=base_tool._run
        )
        logger.info(f"Registered BaseTool: {tool_def['name']}")

    def register_tool_from_decorator(self, decorated_func: Callable):
        """
        从 @tool 装饰的函数注册工具

        Args:
            decorated_func: 被 @tool 装饰的函数
        """
        if not hasattr(decorated_func, '_tool_config'):
            raise ValueError("Function must be decorated with @tool")

        config = decorated_func._tool_config
        self.register_tool(
            name=config["name"],
            description=config["description"],
            parameters=config["parameters"],
            handler=config["handler"]
        )
        logger.info(f"Registered decorated tool: {config['name']}")

    def tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any]
    ):
        """工具装饰器"""
        def decorator(func: Callable):
            self.register_tool(name, description, parameters, func)
            return func
        return decorator

    # ========== 工具调用 ==========

    def get_all_tools(self) -> List[ToolDefinition]:
        """获取所有可用工具"""
        mcp_tools = self.mcp_manager.get_all_tools()
        return mcp_tools + self._local_tool_defs

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """调用工具"""
        logger.debug(f"Calling tool '{tool_name}' with arguments: {arguments}")
        logger.debug(f"Arguments type: {type(arguments)}")

        # 先检查本地工具
        if tool_name in self._local_tools:
            try:
                handler = self._local_tools[tool_name]
                logger.debug(f"Handler: {handler}")
                logger.debug(f"Handler type: {type(handler)}")

                if asyncio.iscoroutinefunction(handler):
                    result = await handler(**arguments)
                else:
                    result = handler(**arguments)
                return ToolResult(success=True, data=result)
            except Exception as e:
                logger.error(f"Local tool '{tool_name}' failed: {e}", exc_info=True)
                return ToolResult(success=False, error=str(e))

        # 调用 MCP 工具
        return await self.mcp_manager.call_tool(tool_name, arguments)

    # ========== 钩子处理 ==========

    def add_hook(
        self,
        event_type: HookEvent,
        hook_func: Callable,
        priority: int = 0
    ):
        """添加钩子

        Args:
            event_type: 钩子事件类型
            hook_func: 钩子函数（可以是同步或异步函数）
            priority: 钩子优先级，值越高执行顺序越靠前
        """
        self.hook_registry.register(event_type, hook_func, priority)
        logger.info(f"Added hook for {event_type.value} with priority {priority}")

    def add_hooks(
        self,
        hooks: List[Tuple[HookEvent, Callable, int]]
    ):
        """批量添加钩子

        Args:
            hooks: 钩子列表，每个元素为 (event_type, hook_func, priority)
        """
        for event_type, hook_func, priority in hooks:
            self.add_hook(event_type, hook_func, priority)

    async def process_hooks(
        self,
        context_data: Any,
        event_type: HookEvent,
        **kwargs
    ) -> HookContext:
        """处理钩子"""
        context = HookContext(context_data)
        context.set_metadata("agent_name", self.config.name)

        return await self.hook_registry.trigger(event_type, context, **kwargs)

    async def check_human_approval(
        self,
        context: HookContext,
        **kwargs
    ) -> bool:
        """检查人工审批

        """
        # 检查钩子设置的审批结果
        if "human_approval" in context.metadata:
            approved = context.metadata["human_approval"]
            if approved:
                logger.info("Human approved via hook")
            else:
                logger.warning("Human rejected via hook")
            return approved

        # 如果没有设置审批结果，默认批准
        logger.warning("No human approval found in context, defaulting to approve")
        return True

    # ========== 单步执行逻辑（异步生成器） ==========

    async def _step(
        self,
        state: AgentState,
        all_tools: List[ToolDefinition]
    ) -> AsyncIterator[AgentEvent]:
        """
        执行 Agent 的单次迭代（异步生成器）

        Args:
            state: 当前状态
            all_tools: 可用工具列表

        Yields:
            AgentEvent: 执行过程中的各种事件
        """
        state.iteration += 1
        iteration_start_event = AgentEvent(
            type=AgentEventType.ITERATION_START,
            data={"iteration": state.iteration, "max_iterations": self.config.max_iterations},
            metadata={"messages_count": len(state.messages)}
        )
        yield iteration_start_event

        logger.debug(
            f"Iteration {state.iteration}/{self.config.max_iterations} "
            f"(messages: {len(state.messages)})"
        )

        try:
            # ===== 阶段1: BEFORE_AGENT =====
            # 在整个Agent执行前调用，可以访问整个状态
            before_agent_context_data = {
                "iteration": state.iteration,
                "messages": state.messages,
                "tools": all_tools
            }

            # 执行 BEFORE_AGENT 阶段钩子
            processed_context = await self.process_hooks(
                before_agent_context_data,
                event_type=HookEvent.BEFORE_AGENT
            )

            # 应用钩子返回的修改
            result_data = processed_context.data
            if isinstance(result_data, dict):
                if "messages" in result_data:
                    state.messages = result_data["messages"]
                if "tools" in result_data:
                    all_tools = result_data["tools"]

            # ===== 阶段2: BEFORE_MODEL =====
            before_model_context_data = {
                "iteration": state.iteration,
                "messages": state.messages,
                "tools": all_tools
            }

            # 执行 BEFORE_MODEL 阶段钩子
            processed_context = await self.process_hooks(
                before_model_context_data,
                event_type=HookEvent.BEFORE_MODEL
            )

            # 应用钩子返回的修改
            if processed_context.data:
                if "messages" in processed_context.data:
                    state.messages = processed_context.data["messages"]
                    logger.info(f"[AGENT] Messages updated by hooks. Current count: {len(state.messages)}")
                if "tools" in processed_context.data:
                    all_tools = processed_context.data["tools"]

            # ===== 阶段3: WRAP_MODEL_CALL =====
            # 调用模型
            if not self.model:
                yield AgentEvent(
                    type=AgentEventType.ERROR,
                    data="No model configured"
                )
                return

            yield AgentEvent(
                type=AgentEventType.LLM_CALL_START,
                data={"model": str(self.model)}
            )

            # 准备模型调用数据
            model_call_data = {
                "iteration": state.iteration,
                "messages": state.messages,
                "tools": all_tools
            }

            # 执行模型调用（可在钩子中包装）
            if BaseModel and isinstance(self.model, BaseModel):
                # 转换消息格式为字典列表
                messages_dict = [msg.to_dict() for msg in state.messages]

                # 转换工具格式
                tools_list = None
                if all_tools:
                    tools_list = [
                        {
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.parameters
                            }
                        }
                        for tool in all_tools
                    ]

                # 在钩子中处理模型调用
                await self.process_hooks(
                    model_call_data,
                    event_type=HookEvent.WRAP_MODEL_CALL
                )

                # 调用模型，传入工具（避免传递 None）
                if tools_list:
                    response = await self.model.ainvoke(
                        messages_dict,
                        tools=tools_list
                    )
                else:
                    response = await self.model.ainvoke(
                        messages_dict
                    )
                llm_response = response
            else:
                messages_dict = [
                    {"role": msg.role, "content": msg.content}
                    for msg in state.messages
                ]
                if state.iteration >1:
                    messages_dict.append({"role": "user", 
                                          "content": """1. 核验本次行动结果（工具返回/Agent协作/执行输出等）的完整性、准确性；
                                                        2. 判定结果是否匹配当前任务核心需求；
                                                        3. 如不匹配请继续调用工具或协作，直至满足需求为止。若满足需求，则回答用户问题。"""})

                # 转换工具格式（与 BaseModel 分支保持一致）
                tools_list = None
                if all_tools:
                    tools_list = [
                        {
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.parameters
                            }
                        }
                        for tool in all_tools
                    ]

                # 在钩子中处理模型调用
                await self.process_hooks(
                    model_call_data,
                    event_type=HookEvent.WRAP_MODEL_CALL
                )

                # 调用模型，传入工具（避免传递 None）
                if tools_list:
                    llm_response = await self.model.ainvoke(
                        messages_dict,
                        tools=tools_list
                    )
                else:
                    llm_response = await self.model.ainvoke(
                        messages_dict
                    )

            # ===== 阶段4: AFTER_MODEL =====
            after_model_data = llm_response

            # 执行 AFTER_MODEL 阶段钩子
            llm_response = await self.process_hooks(
                after_model_data,
                event_type=HookEvent.AFTER_MODEL
            )
            llm_response = llm_response.data

            # 检查是否有工具调用
            if llm_response.tool_calls:
                # 添加助手消息（包含工具调用）
                assistant_msg = Message(
                    role="assistant",
                    content=llm_response.content or "",
                    tool_calls=llm_response.tool_calls
                )

                # 助手消息处理（AFTER_AGENT阶段的一部分）
                state.add_message(assistant_msg)

                yield AgentEvent(
                    type=AgentEventType.MESSAGE_ADDED,
                    data=assistant_msg.to_dict(),
                    metadata={"role": assistant_msg.role}
                )

                logger.info(f"Model requested {len(llm_response.tool_calls)} tool calls")

                # ===== 阶段5: WRAP_TOOL_CALL =====
                # 并行执行工具调用
                async def execute_single_tool(
                    tool_name: str,
                    arguments: Dict[str, Any],
                    tool_call_id: str,
                    state: AgentState
                ) -> AsyncIterator[AgentEvent]:
                    """执行单个工具调用（异步生成器）"""
                    yield AgentEvent(
                        type=AgentEventType.TOOL_CALL_START,
                        data={"tool_name": tool_name, "tool_call_id": tool_call_id}
                    )

                    # 工具调用包装钩子（可以进行审批等操作）
                    tool_call_data = {
                        "tool_name": tool_name,
                        "arguments": arguments
                    }

                    # 在钩子中处理工具调用审批
                    tool_call_context = await self.process_hooks(
                        tool_call_data,
                        event_type=HookEvent.WRAP_TOOL_CALL
                    )

                    # 检查钩子是否设置了拒绝标记
                    rejected = tool_call_context.get_metadata("rejected", False)
                    human_approval = tool_call_context.get_metadata("human_approval", True)

                    if rejected or not human_approval:
                        logger.warning(f"Tool call '{tool_name}' rejected by hook (rejected={rejected}, human_approval={human_approval})")
                        yield AgentEvent(
                            type=AgentEventType.TOOL_CALL_END,
                            data={"tool_name": tool_name, "rejected": True}
                        )
                        return

                    result = await self.call_tool(tool_name, arguments)


                    # 添加工具结果消息
                    tool_msg = Message(
                        role="tool",
                        content=json.dumps(
                            result.data,
                            ensure_ascii=False,
                            indent=2
                        ),
                        tool_call_id=tool_call_id
                    )

                    # 调试输出工具消息
                    if self.config.debug:
                        logger.debug(f"Created tool message: {tool_msg}")
                        logger.debug(f"Tool message dict: {tool_msg.to_dict()}")

                    # 添加到状态
                    state.add_message(tool_msg)

                    yield AgentEvent(
                        type=AgentEventType.TOOL_RESULT,
                        data={
                            "tool_name": tool_name,
                            "success": result.success,
                            "tool_call_id": tool_call_id
                        },
                        metadata={"has_data": result.success}
                    )

                    yield AgentEvent(
                        type=AgentEventType.MESSAGE_ADDED,
                        data=tool_msg.to_dict(),
                        metadata={"role": tool_msg.role}
                    )

                    if result.success:
                        logger.debug(f"Tool '{tool_name}' succeeded")
                    else:
                        logger.warning(f"Tool '{tool_name}' failed: {result.error}")

                    yield AgentEvent(
                        type=AgentEventType.TOOL_CALL_END,
                        data={"tool_name": tool_name, "success": result.success}
                    )

                # 准备所有工具调用并并行执行
                tool_gens = []

                for tool_call in llm_response.tool_calls:
                    # 调试输出原始工具调用
                    logger.debug(f"Raw tool call: {tool_call}")
                    logger.debug(f"Tool call type: {type(tool_call)}")

                    # tool_call 可以是字典或对象，统一处理
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get('name')
                        arguments = tool_call.get('arguments', {})
                        tool_call_id = tool_call.get('id')
                    else:
                        tool_name = tool_call.name
                        arguments = tool_call.arguments
                        tool_call_id = tool_call.id

                    # 调试输出解析后的值
                    logger.debug(f"Parsed - tool_name: {tool_name}, tool_call_id: {tool_call_id}")
                    logger.debug(f"Arguments: {arguments}")
                    logger.debug(f"Arguments type: {type(arguments)}")

                    # 如果 arguments 是字符串，尝试解析为 JSON
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                            logger.debug(f"Parsed arguments from JSON: {arguments}")
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse arguments as JSON: {e}")
                            continue

                    # 确保 tool_name 不为 None
                    if not tool_name:
                        logger.error(f"Tool call missing name: {tool_call}")
                        continue

                    # 如果没有 tool_call_id，生成一个
                    if not tool_call_id:
                        tool_call_id = f"call_{uuid.uuid4().hex[:8]}"
                        logger.warning(f"Tool call missing ID, generated: {tool_call_id}")
                    else:
                        logger.debug(f"Using existing tool_call_id: {tool_call_id}")

                    logger.info(f"Preparing parallel tool call: {tool_name}")

                    # 创建异步生成器
                    tool_gen = execute_single_tool(tool_name, arguments, tool_call_id, state)
                    tool_gens.append(tool_gen)

                # 并行执行所有工具调用
                if tool_gens:
                    # 为每个生成器创建一个任务来收集其所有事件
                    async def collect_all_events(tool_gen: AsyncIterator[AgentEvent]) -> List[AgentEvent]:
                        """收集单个工具调用的所有事件"""
                        events = []
                        async for event in tool_gen:
                            events.append(event)
                        return events

                    # 创建收集任务
                    collect_tasks = [
                        collect_all_events(tool_gen)
                        for tool_gen in tool_gens
                    ]

                    # 并行收集所有事件
                    results = await asyncio.gather(*collect_tasks, return_exceptions=True)

                    # 处理所有收集到的事件
                    for events in results:
                        if isinstance(events, Exception):
                            logger.error(f"Tool execution failed: {events}")
                            continue

                        if isinstance(events, list):
                            for event in events:
                                yield event

                # 继续下一次迭代
                yield AgentEvent(
                    type=AgentEventType.ITERATION_END,
                    data={"should_continue": True, "reason": "has_tool_calls"}
                )
                return
            else:
                # 没有工具调用，添加助手消息并结束
                assistant_msg = Message(
                    role="assistant",
                    content=llm_response.content or ""
                )

                state.add_message(assistant_msg)

                yield AgentEvent(
                    type=AgentEventType.MESSAGE_ADDED,
                    data=assistant_msg.to_dict(),
                    metadata={"role": assistant_msg.role}
                )

            # ===== 阶段6: AFTER_AGENT =====
            after_agent_data = {
                "iteration": state.iteration,
                "messages": state.messages,
                "llm_response": llm_response
            }

            # 执行 AFTER_AGENT 阶段钩子
            await self.process_hooks(
                after_agent_data,
                event_type=HookEvent.AFTER_AGENT
            )

            # 检查是否应该结束
            should_continue = True
            reason = "has_response"
            if state.iteration >= self.config.max_iterations:
                logger.warning("Reached maximum iterations")
                state.finished = True
                should_continue = False
                reason = "max_iterations"
            elif llm_response.finish_reason == "stop":
                logger.info("Model indicated completion")
                state.finished = True
                should_continue = False
                reason = "finish_reason_stop"

            yield AgentEvent(
                type=AgentEventType.ITERATION_END,
                data={"should_continue": should_continue, "reason": reason}
            )
            return

        except Exception as e:
            logger.error(f"Iteration {state.iteration} failed: {e}", exc_info=True)
            state.error = str(e)
            state.finished = True

            yield AgentEvent(
                type=AgentEventType.ERROR,
                data=str(e),
                metadata={"iteration": state.iteration}
            )
            return

    async def arun(
        self,
        messages: List[Dict[str, Any]]
    ) -> str:
        """
        异步运行 Agent，支持消息列表输入（纯异步实现）

        Args:
            messages: 消息列表，格式为 List[Dict[str, Any]]，包含role和content等字段
                     例如：[{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

        Returns:
            str: Agent响应结果
        """
        try:
            # 创建状态
            state = AgentState()

            # 添加系统消息
            system_msg = Message(
                role="system",
                content=self.config.system_prompt
            )
            state.add_message(system_msg)

            # 处理消息列表
            for msg_dict in messages:
                # 验证消息格式
                if not isinstance(msg_dict, dict):
                    raise ValueError(f"消息必须是字典格式: {msg_dict}")

                if "role" not in msg_dict:
                    raise ValueError(f"消息必须包含'role'字段: {msg_dict}")

                if "content" not in msg_dict:
                    raise ValueError(f"消息必须包含'content'字段: {msg_dict}")


                # 创建Message对象
                content = msg_dict.get("content", "")
                if content is None:
                    content = ""

                msg = Message(
                    role=msg_dict["role"],
                    content=str(content),
                    tool_calls=msg_dict.get("tool_calls"),
                    tool_call_id=msg_dict.get("tool_call_id")
                )

                state.add_message(msg)

            logger.info(f"Agent '{self.config.name}' processing request with messages")

            # 获取可用工具
            all_tools = self.get_all_tools()

            logger.debug(f"Available tools: {len(all_tools)}")

            # 消息处理循环 - 使用_step异步生成器
            while not state.finished and state.iteration < self.config.max_iterations:
                async for event in self._step(state, all_tools):
                    # 处理各种事件
                    if event.type == AgentEventType.ERROR:
                        return f"Error: {event.data}"

                # 检查最新消息是否包含工具调用
                has_tool_calls = state.messages[-1].role == "tool"

                if not has_tool_calls:
                    break

            # 生成最终响应
            try:
                final_response = state.messages[-1].content
                return final_response
            except Exception as e:
                logger.error(f"Failed to generate final response: {e}")
                return f"Error: {str(e)}"

        finally:
            if state.error:
                logger.error(f"Agent failed: {state.error}")



    async def ainvoke(
        self,
        messages: List[Dict[str, Any]]
    ) -> str:
        """
        异步调用接口（无状态）

        Args:
            messages: 消息列表，格式为 List[Dict[str, Any]]，包含role和content等字段
                     例如：[{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

        Returns:
            str: Agent响应结果
        """
        return await self.arun(messages)

    async def astream(
        self,
        messages: List[Dict[str, Any]]
    ) -> AsyncIterator[str]:
        """
        异步流式调用接口（生成器）

        Args:
            messages: 消息列表，格式为 List[Dict[str, Any]]

        Yields:
            str: 流式响应内容
        """
        try:
            # 获取可用工具
            all_tools = self.get_all_tools()

            # 工具列表钩子处理（如果需要的话）
            # 注意：TOOLS 不是标准的 HookEvent，这里可能需要特殊处理或移除
            # tools_context = await self.process_hooks(
            #     all_tools,
            #     event_type=HookEvent.TOOLS  # 如果需要这个阶段
            # )
            # all_tools = tools_context.data

            # 创建状态
            state = AgentState()

            # 添加系统消息
            system_msg = Message(
                role="system",
                content=self.config.system_prompt
            )
            state.add_message(system_msg)

            # 处理消息列表
            for msg_dict in messages:
                # 验证消息格式
                if not isinstance(msg_dict, dict):
                    raise ValueError(f"消息必须是字典格式: {msg_dict}")

                if "role" not in msg_dict:
                    raise ValueError(f"消息必须包含'role'字段: {msg_dict}")

                if "content" not in msg_dict:
                    raise ValueError(f"消息必须包含'content'字段: {msg_dict}")


                # 创建Message对象
                content = msg_dict.get("content", "")
                if content is None:
                    content = ""

                msg = Message(
                    role=msg_dict["role"],
                    content=str(content),
                    tool_calls=msg_dict.get("tool_calls"),
                    tool_call_id=msg_dict.get("tool_call_id")
                )

                state.add_message(msg)

            # 消息处理循环 - 使用_step异步生成器
            while not state.finished and state.iteration < self.config.max_iterations:
                async for event in self._step(state, all_tools):
                    # 处理不同类型的事件
                    if event.type == AgentEventType.ERROR:
                        yield f"Error: {event.data}"
                        return
                    elif event.type == AgentEventType.LLM_TOKEN:
                        # 如果有token事件，yield token
                        if event.data:
                            yield str(event.data)
                    elif event.type == AgentEventType.MESSAGE_ADDED:
                        # 如果是助手消息，yield内容
                        msg_data = event.data
                        if msg_data and msg_data.get('role') == 'assistant':
                            content = msg_data.get('content', '')
                            if content:
                                yield content

                # 检查是否应该继续下一次迭代
                has_tool_calls = any(
                    msg.tool_calls
                    for msg in state.get_recent_messages(limit=1)
                    if msg.role == "tool"
                )

                if not has_tool_calls:
                    break
                else:
                    # 模型认为应该继续，但需要检查最大迭代次数
                    if state.iteration >= self.config.max_iterations:
                        logger.warning(f"Reached max iterations ({self.config.max_iterations}), stopping")
                        state.finished = True
                        break

            # 添加完成事件
            yield f"[COMPLETED] 迭代次数: {state.iteration}"

        except Exception as e:
            logger.error(f"Agent stream failed: {e}", exc_info=True)
            yield f"Error: {e}"

    # ========== 信息查询 ==========

    def get_info(self) -> AgentInfo:
        """获取 Agent 信息"""
        return AgentInfo(
            name=self.config.name,
            tools_count=self.tools_count,
            mcp_servers=self.mcp_manager.all_servers
        )

    @property
    def tools_count(self) -> int:
        """获取工具数量"""
        return len(self.get_all_tools())

    @property
    def mcp_servers(self) -> List[str]:
        """获取 MCP 服务器列表"""
        return self.mcp_manager.all_servers

    @property
    def hooks_count(self) -> int:
        """获取钩子数量"""
        return len(self.hook_registry)

    # ========== 生命周期管理 ==========

    async def shutdown(self):
        """关闭 Agent"""
        logger.info(f"Shutting down agent: {self.config.name}")
        await self.mcp_manager.shutdown()

        # 关闭模型
        if self.model and hasattr(self.model, 'close'):
            await self.model.close()

        logger.info(f"Agent '{self.config.name}' shut down")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.shutdown()

    def __repr__(self) -> str:
        return (
            f"MyAgent("
            f"name={self.config.name}, "
            f"tools={self.tools_count}, "
            f"servers={len(self.mcp_servers)}, "
            f"hooks={self.hooks_count}"
            f")"
        )


# ========== 工厂函数 ==========

async def create_my_agent(
    # 模型配置
    model:BaseModel,
    # 基本配置
    name: str,
    system_prompt: str = "You are a helpful assistant with access to tools.",
    max_iterations: int = 10,
    debug: bool = False,

    # MCP 配置（可选）
    mcp_servers: Optional[List[Dict[str, Any]]] = None,

    # 本地工具（可选）
    local_tools: Optional[List[Dict[str, Any]]] = None,

    # BaseTool 工具（可选）
    base_tools: Optional[List[Any]] = None,

    # 装饰器工具（可选）
    decorated_tools: Optional[List[Callable]] = None,

    # 钩子（可选）
    hooks: Optional[List[Tuple[HookEvent, Callable, int]]] = None,
) -> MyAgent:
    """
    创建 Agent 实例的工厂函数

    所有参数都是可选的，可以根据需要配置。

    Args:
        # 基本配置
        name: Agent 名称
        system_prompt: 系统提示词
        max_iterations: 最大工具调用轮次
        debug: 是否启用调试日志

        # 模型配置（可选）
        model: 模型实例（使用 get_llm_by_type 或其他方式创建）

        # MCP 配置（可选）
        mcp_servers: MCP 服务器配置列表

        # 本地工具（可选）
        local_tools: 本地工具定义列表

        # BaseTool 工具（可选）
        base_tools: BaseTool 子类实例列表

        # 装饰器工具（可选）
        decorated_tools: 使用 @tool 装饰的函数列表

        # 钩子（可选）
        hooks: 钩子列表，每个元素为 (event_type, hook_func, priority)

    Returns:
        MyAgent: 配置好的 Agent 实例

    Examples:
        ```python
        # 使用 get_llm_by_type 创建模型后传入
        from src.myllms.factory import get_llm_by_type

        model = get_llm_by_type("basic")
        agent = create_my_agent(name="MyAgent", model=model)

        # 带 BaseTool 工具
        from src.tools.decorators import BaseTool

        class WeatherTool(BaseTool):
            name = "get_weather"
            description = "获取指定城市的天气信息"

            def _run(self, city: str) -> str:
                return f"{city}的天气：晴朗，22°C"

        agent = create_my_agent(
            name="ToolAgent",
            model=model,
            base_tools=[WeatherTool()]
        )

        # 带装饰器工具
        from src.tools.decorators import tool

        @tool()
        def get_weather(city: str) -> str:
            '''获取指定城市的天气信息'''
            return f"{city}的天气：晴朗，22°C"

        agent = create_my_agent(
            name="ToolAgent",
            model=model,
            decorated_tools=[get_weather]
        )

        # 带 MCP 服务器
        agent = create_my_agent(
            name="MCPAgent",
            model=model,
            mcp_servers=[
                {
                    "id": "file-bash",
                    "command": ["python", "file_bash_server.py"]
                }
            ]
        )

        # 带本地工具
        def get_weather(city: str) -> dict:
            return {"city": city, "temperature": "22°C"}

        agent = create_my_agent(
            name="ToolAgent",
            model=model,
            local_tools=[
                {
                    "name": "get_weather",
                    "description": "获取天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"}
                        }
                    },
                    "handler": get_weather
                }
            ]
        )

        # 带钩子
        from src.hooks import HookEvent, hook

        @hook(HookEvent.BEFORE_AGENT, priority=10)
        async def logging_hook(context):
            print(f"Processing before agent: {context.data}")
            return context

        @hook(HookEvent.AFTER_MODEL, priority=5)
        async def validation_hook(context):
            print(f"Validating model response: {context.data}")
            return context

        agent = create_my_agent(
            name="LoggingAgent",
            model=model,
            hooks=[
                (HookEvent.BEFORE_AGENT, logging_hook, 10),
                (HookEvent.AFTER_MODEL, validation_hook, 5)
            ]
        )

        # 带人在环中
        agent = create_my_agent(
            name="SafeAgent",
            model=model,
            human_in_the_loop=lambda ctx: input("Approve? (y/n): ").lower() == 'y'
        )
        ```
    """

    # 创建 Agent 配置
    config = AgentConfig(
        name=name,
        system_prompt=system_prompt,
        max_iterations=max_iterations,
        debug=debug
    )



    # 创建钩子注册表
    hook_registry = None
    if hooks:
        hook_registry = HookRegistry()
        for event_type, hook_func, priority in hooks:
            hook_registry.register(event_type, hook_func, priority)
            logger.debug(f"Added hook for {event_type.value} with priority {priority}")

        logger.info(f"Added {len(hooks)} hooks")

    # 创建 Agent
    agent = MyAgent(
        config=config,
        model=model,
        hook_registry=hook_registry,
    )

    # 添加 MCP 服务器
    if mcp_servers:
        logger.info(f"Adding {len(mcp_servers)} MCP servers")
        for server_config in mcp_servers:
            # 异步添加并等待完成
            await agent.add_mcp_server(
                server_config["id"],
                server_config["command"],
                name=server_config.get("name"),
                env=server_config.get("env")
            )

    # 注册本地工具
    if local_tools:
        logger.info(f"Registering {len(local_tools)} local tools")
        for tool_config in local_tools:
            agent.register_tool(
                tool_config["name"],
                tool_config["description"],
                tool_config["parameters"],
                tool_config["handler"]
            )

    # 注册 BaseTool 工具
    if base_tools:
        logger.info(f"Registering {len(base_tools)} BaseTool tools")
        for base_tool in base_tools:
            agent.register_tool_from_base_tool(base_tool)

    # 注册装饰器工具
    if decorated_tools:
        logger.info(f"Registering {len(decorated_tools)} decorated tools")
        for decorated_tool in decorated_tools:
            agent.register_tool_from_decorator(decorated_tool)

    return agent
