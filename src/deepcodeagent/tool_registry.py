#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工具注册函数 - 根据agent名称自动注册相应工具
"""

import asyncio
from typing import Dict, Any, List, Union
from pathlib import Path
import importlib
import inspect

from src.my_agent.agent import MyAgent
from src.tools import ALL_TOOLS, get_agent_tools


def register_tools_by_agent_name(agent: MyAgent, agent_name: str) -> None:
    """
    根据agent名称自动注册相应工具

    Args:
        agent: Agent实例
        agent_name: agent名称 (如 "planner", "searcher", "coder", "architecture_writer"等)
    """
    # 获取该agent应该拥有的工具列表
    tool_names = get_agent_tools(agent_name)

    if not tool_names:
        # 如果没有配置工具，使用默认空列表
        print(f"[WARNING] No tools configured for agent: {agent_name}")
        return

    # 注册每个工具
    for tool_name in tool_names:
        if tool_name in ALL_TOOLS:
            tool_class = ALL_TOOLS[tool_name]

            try:
                # 创建工具实例
                tool_instance = tool_class()

                # 获取工具的schema
                if hasattr(tool_instance, 'get_schema'):
                    schema = tool_instance.get_schema()
                    func_def = schema.get('function', {})
                    description = func_def.get('description', '')
                    parameters = func_def.get('parameters', {})
                else:
                    description = f'Tool {tool_name}'
                    parameters = {}

                # 创建异步处理器
                def make_tool_handler(t_instance, t_name):
                    async def tool_handler(**arguments):
                        try:
                            if hasattr(t_instance, 'execute'):
                                if asyncio.iscoroutinefunction(t_instance.execute):
                                    result = await t_instance.execute(**arguments)
                                else:
                                    result = t_instance.execute(**arguments)

                                # 确保返回字典格式
                                if not isinstance(result, dict):
                                    result = {"success": True, "result": result}

                                return result
                            return {"success": True, "message": f"Tool {t_name} executed"}
                        except Exception as e:
                            return {"success": False, "error": str(e)}
                    return tool_handler

                # 注册工具到agent
                agent.register_tool(
                    name=tool_name,
                    description=description,
                    parameters=parameters,
                    handler=make_tool_handler(tool_instance, tool_name)
                )

                print(f"[INFO] Registered tool '{tool_name}' for agent '{agent_name}'")

            except Exception as e:
                print(f"[ERROR] Failed to register tool '{tool_name}' for agent '{agent_name}': {e}")
        else:
            print(f"[WARNING] Tool '{tool_name}' not found in AVAILABLE_TOOLS")


def create_agent_with_tools(agent_name: str, model, system_prompt: str = None, output_dir: Path = None) -> MyAgent:
    """
    创建agent并自动注册相应工具

    Args:
        agent_name: agent名称
        model: 使用的模型
        system_prompt: 系统提示词 (可选)
        output_dir: 输出目录 (可选)

    Returns:
        配置好工具的MyAgent实例
    """
    # 需要导入AgentConfig
    from src.my_agent.agent import AgentConfig
    config = AgentConfig(
        name=agent_name,
        system_prompt=system_prompt or f"You are {agent_name} agent",
        max_iterations=5,
        debug=False
    )
    agent = MyAgent(config=config, model=model)

    # 自动注册工具
    register_tools_by_agent_name(agent, agent_name)

    return agent


# 预定义的agent工具配置映射
AGENT_TOOL_MAPPING = {
    "planner": ["request_research", "plan_next_round", "decide_architecture_writing"],
    "searcher": ["web_search"],
    "analyzer": ["code_search", "document_search", "analyze_solutions"],
    "researcher": ["deep_research", "synthesize_findings"],
    "architecture_writer": [
        "create_architecture_diagram",
        "document_component",
        "create_implementation_roadmap",
        "assess_risks",
        "decide_architecture_writing"
    ],
    "coder": [
        "write_file",
        "read_file",
        "edit_file",
        "list_files",
        "code_search",
        "create_task",
        "add_imports",
        "create_test_file",
        "request_approval"
    ],
    "test_runner": [
        "run_code",
        "execute_tests",
        "check_quality",
        "create_test_suite",
        "generate_test_report",
        "bash",
        "python_execute"
    ],
    "reflector": [
        "generate_todos",
        "record_reflection",
        "suggest_improvements",
        "complete_task",
        "create_retrospective"
    ]
}


def get_tools_for_agent(agent_name: str) -> List[str]:
    """
    获取指定agent的工具列表

    Args:
        agent_name: agent名称

    Returns:
        工具名称列表
    """
    return AGENT_TOOL_MAPPING.get(agent_name, [])