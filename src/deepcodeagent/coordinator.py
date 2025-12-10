"""
Global Coordinator - 全局工作流协调者
负责分析用户需求并决定执行路径
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field

from src.my_agent.agent import MyAgent, AgentConfig
from src.myllms import get_llm_by_type
from src.tools import get_agent_tools, ALL_TOOLS
from src.utils.prompt_loader import load_agent_prompt, format_prompt_for_agent
from src.deepcodeagent.core import DeepCodeAgentState, WorkflowStage, ResearchPlan

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Task types"""
    DIRECT_ANSWER = "direct_answer"
    RESEARCH = "research"
    CODING = "coding"


class GlobalDecision(BaseModel):
    """Global coordinator's decision"""
    task_type: TaskType = Field(description="Task type")
    reasoning: str = Field(description="Reasoning for decision")
    next_phase_input: Dict[str, Any] = Field(default_factory=dict, description="Input for next phase")
    complexity: str = Field(description="Task complexity: simple/medium/complex")


class GlobalCoordinator:
    """Global coordinator"""

    def __init__(self):
        self.agent = self._create_agent("coordinator", "reasoning")

    def _create_agent(self, agent_name: str, model_type: str) -> MyAgent:
        """Create agent"""
        model = get_llm_by_type(model_type)

        # Load prompt from markdown file with full formatting
        system_prompt = format_prompt_for_agent(agent_name, load_agent_prompt(agent_name))

        # Add coordinator-specific instructions
        if agent_name == "coordinator":
            system_prompt += """

## Current Context
You are operating in a multi-agent workflow system and must route tasks appropriately.

## Available Tools
- make_decision: Make task routing decisions
- request_approval: Request approvals when needed
- synthesize_results: Synthesize information from multiple sources
- web_search: Search for additional information if needed

## Decision Process
1. Analyze requirement complexity and scope
2. Determine appropriate task type:
   - direct_answer: Simple queries that can be answered immediately
   - research: Requires investigation, analysis, and architecture design
   - coding: Direct implementation tasks with clear requirements

## Output Format
Must return structured JSON decision using the make_decision tool.
"""

        config = AgentConfig(
            name="global_coordinator",
            system_prompt=system_prompt,
            max_iterations=3,
            debug=False
        )

        agent = MyAgent(config=config, model=model)

        # Register tools from tools package
        tool_names = get_agent_tools(agent_name)
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
                                if asyncio.iscoroutinefunction(tool_instance.execute):
                                    result = await tool_instance.execute(**arguments)
                                else:
                                    result = tool_instance.execute(**arguments)
                                return result
                            return {"success": True, "message": f"Tool {t_name} executed"}
                        except Exception as e:
                            logger.error(f"Error executing tool {t_name}: {e}")
                            return {"success": False, "error": str(e)}
                    return tool_handler

                agent.register_tool(
                    name=tool_name,
                    description=description,
                    parameters=parameters,
                    handler=make_tool_handler(tool_instance, tool_name)
                )

        return agent

    async def analyze(self, requirement: str) -> GlobalDecision:
        """Analyze requirements and decide execution path"""
        logger.info(f"Analyzing requirement: {requirement}")

        # Get the model directly
        model = get_llm_by_type("reasoning")

        # Prepare messages
        messages = [
            {"role": "system", "content": self.agent.config.system_prompt},
            {"role": "user", "content": f"""
Please analyze the following requirement and decide execution path:

Requirement: {requirement}

Analysis dimensions:
1. Task type determination:
   - direct_answer: Simple questions that can be answered directly
   - research: Technical questions that require research and analysis
   - coding: Projects that need code implementation

2. Complexity assessment:
   - Simple: Single answer or small task
   - Medium: Requires some research but not a full project
   - Complex: Requires complete research and implementation

Please use the make_decision tool to provide your analysis.
"""}
        ]

        # Prepare tools
        tools = []
        for tool_name in get_agent_tools("coordinator"):
            if tool_name in ALL_TOOLS:
                tool_class = ALL_TOOLS[tool_name]
                tool_instance = tool_class()
                if hasattr(tool_instance, 'get_schema'):
                    schema = tool_instance.get_schema()
                    tools.append(schema)

        try:
            logger.debug(f"Sending request to model with {len(tools)} tools")
            response = await model.ainvoke(messages, tools=tools)

            logger.debug(f"Received response from model")
            if hasattr(response, 'usage') and response.usage:
                logger.debug(f"Token usage: {response.usage}")

            # Parse tool calls from response
            if response.tool_calls:
                logger.info(f"Found {len(response.tool_calls)} tool calls in response")
                for tool_call in response.tool_calls:
                    tool_name = tool_call.get("name")
                    logger.debug(f"Processing tool call: {tool_name}")

                    if tool_name == "make_decision":
                        args = tool_call.get("arguments", {})
                        logger.info(f"Got decision from make_decision: {args}")
                        return GlobalDecision(**args)
                    else:
                        logger.debug(f"Ignoring tool call: {tool_name}")

            # If no tool calls, check content
            if response.content:
                logger.debug(f"No tool calls, checking response content (length: {len(response.content)})")
                import re
                json_match = re.search(r'\{[\s\S]*\}', response.content)
                if json_match:
                    try:
                        decision_data = json.loads(json_match.group())
                        logger.info(f"Parsed JSON from content: {decision_data}")
                        return GlobalDecision(**decision_data)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON from content: {e}")

                logger.warning(f"No valid decision found in response")
            else:
                logger.warning("No content in response")

        except Exception as e:
            logger.error(f"Error parsing decision: {e}")

        # Default decision
        logger.warning("Using default decision (CODING)")
        return GlobalDecision(
            task_type=TaskType.CODING,
            reasoning="Default to coding due to parsing error or no valid decision found",
            next_phase_input={"requirement": requirement},
            complexity="Medium"
        )

    async def direct_answer(self, requirement: str) -> str:
        """Directly answer simple questions"""
        messages = [
            {"role": "user", "content": f"Please answer: {requirement}"}
        ]

        result = await self.agent.arun(messages)
        return result

    async def process(self, state: DeepCodeAgentState) -> DeepCodeAgentState:
        """Process state and update with decision"""
        requirement = state.user_requirement

        # Analyze requirement
        decision = await self.analyze(requirement)

        # Store decision in state
        state.task_type = decision.task_type.value
        state.assigned_team = decision.task_type.value

        # Set next stage based on decision
        if decision.task_type == TaskType.DIRECT_ANSWER:
            state.current_stage = WorkflowStage.COMPLETED
        elif decision.task_type == TaskType.RESEARCH:
            state.current_stage = WorkflowStage.REQUIREMENT_ANALYSIS
        else:  # CODING
            state.current_stage = WorkflowStage.CODING_COORDINATION

        logger.info(f"Decision: {decision.task_type.value}, Next stage: {state.current_stage.value}")

        return state