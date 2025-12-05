import logging
import os
from typing import List, Optional

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ToolCallLimitMiddleware

from src.agents.tool_interceptor import wrap_tools_with_interceptor
from src.config.agents import AGENT_LLM_MAP
from src.graph.state import State
from src.llms.llm import get_llm_by_type
from src.prompts import apply_prompt_template
from src.prompts.template import get_prompt_template

logger = logging.getLogger(__name__)


# Create agents using configured LLM types
def create_react_agent(
        agent_name: str,
        agent_type: str,
        tools: list,
        prompt_template: str,
        state:State,
        middleware: list = None,
        interrupt_before_tools: Optional[List[str]] = None,
):
    """Factory function to create agents with consistent configuration.

    Args:
        agent_name: Name of the agent
        agent_type: Type of agent (researcher, coder, etc.)
        tools: List of tools available to the agent
        prompt_template: Name of the prompt template to use
        interrupt_before_tools: Optional list of tool names to interrupt before execution

    Returns:
        A configured agent graph
    """
    logger.debug(
        f"Creating agent '{agent_name}' of type '{agent_type}' "
        f"with {len(tools)} tools and template '{prompt_template}'"
    )

    # Wrap tools with interrupt logic if specified
    processed_tools = tools
    if interrupt_before_tools:
        logger.info(
            f"Creating agent '{agent_name}' with tool-specific interrupts: {interrupt_before_tools}"
        )
        logger.debug(f"Wrapping {len(tools)} tools for agent '{agent_name}'")
        processed_tools = wrap_tools_with_interceptor(tools, interrupt_before_tools)
        logger.debug(f"Agent '{agent_name}' tool wrapping completed")
    else:
        logger.debug(f"Agent '{agent_name}' has no interrupt-before-tools configured")

    if agent_type not in AGENT_LLM_MAP:
        logger.warning(
            f"Agent type '{agent_type}' not found in AGENT_LLM_MAP. "
            f"Falling back to default LLM type 'basic' for agent '{agent_name}'. "
            "This may indicate a configuration issue."
        )
    llm_type = AGENT_LLM_MAP.get(agent_type, "basic")
    logger.debug(f"Agent '{agent_name}' using LLM type: {llm_type}")

    logger.debug(f"Creating ReAct agent '{agent_name}'")
    prompt = get_prompt_template(prompt_template, state, "zh-CN")

    # Invoke the agent
    default_recursion_limit = 25
    try:
        env_value_str = os.getenv("AGENT_RECURSION_LIMIT", str(default_recursion_limit))
        parsed_limit = int(env_value_str)

        if parsed_limit > 0:
            recursion_limit = parsed_limit
            logger.info(f"Recursion limit set to: {recursion_limit}")
        else:
            logger.warning(
                f"AGENT_RECURSION_LIMIT value '{env_value_str}' (parsed as {parsed_limit}) is not positive. "
                f"Using default value {default_recursion_limit}."
            )
            recursion_limit = default_recursion_limit
    except ValueError:
        raw_env_value = os.getenv("AGENT_RECURSION_LIMIT")
        logger.warning(
            f"Invalid AGENT_RECURSION_LIMIT value: '{raw_env_value}'. "
            f"Using default value {default_recursion_limit}."
        )
        recursion_limit = default_recursion_limit
    # Global limit
    middleware.append(ToolCallLimitMiddleware(run_limit=recursion_limit))
    # Tool-specific limit
    agent = create_agent(
        name=agent_name,
        model=get_llm_by_type(llm_type),
        tools=processed_tools,
        system_prompt=prompt,
        middleware=middleware,
        interrupt_before = interrupt_before_tools,
    )
    logger.info(f"Agent '{agent_name}' created successfully")

    return agent