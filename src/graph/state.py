from dataclasses import field, dataclass
from typing import Optional, Dict, List, Union, Any

from langgraph.graph import MessagesState
from pydantic import BaseModel

from src.rag import Resource
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field



@dataclass
class TestResult:
    test_name: str
    status: str  # passed, failed, skipped
    output: str
    duration: float

class StepType(str, Enum):
    RESEARCH = "research"
    PROCESSING = "processing"


class Step(BaseModel):
    description: str = Field(..., description="Specify exactly what data to collect")
    step_type: StepType = Field(..., description="Indicates the nature of the step")
    execution_res: Optional[str] = Field(
        default=None, description="The Step execution result"
    )
class Plan(BaseModel):
    locale: str = Field(
        ..., description="e.g. 'en-US' or 'zh-CN', based on the user's language"
    )
    thought: str = Field(default="", description="Thinking process for the plan")
    title: str
    steps: List[Step] = Field(
        default_factory=list,
        description="代码执行过程",
    )


# 2. 核心 State 模型
class State(MessagesState):
    """CodeAgent 的核心 State 模型"""

    current_plan: Plan|str
    observations: list[str]
    research_topic: str
    clarified_research_topic: str
    plan_iterations: int
    enable_background_investigation: bool

    enable_clarification: bool
    clarification_rounds: int
    clarification_history: list[str]
    is_clarification_complete: bool
    max_clarification_rounds: int


    # Workflow control
    goto: str = "planner"  # Default next node


    # 1. 基础元数据（标识任务与上下文）
    task_id: str
    user_requirement: str
    file_path:str
    locale:str
    resources: list[Resource]

    # 2. 任务规划相关（控制中枢输出）
    background_investigation_results: str



    # 代码相关
    code_file_path: Optional[str]
    source_code: Optional[str]
    test_code: Optional[str]
    filename: Optional[str]
    code_language: Optional[str]

    # 测试相关
    test_results: List[TestResult]
    tests_passed: bool


    # 测试相关
    test_results: List[TestResult]
    tests_passed: bool

    # 令牌相关
    total_tokens: int
    max_tokens: int

    # 待办事项
    todo_list: List[Step]

    # 总结
    summary: Optional[str]

