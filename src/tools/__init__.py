"""
DeepCodeAgent Tools Collection

Provides BaseTool abstract class and decorators for simplified tool definition.
"""

try:
    from src.rag.myrag_tool import MyRagSearchTool
except ImportError:
    MyRagSearchTool = None
from .decorators import (
    BaseTool,
    tool,
    log_io,
    LoggedToolMixin,
    create_logged_tool
)

# Import search functionality
from .search import get_web_search_tool
# Temporarily disable crawl due to missing dependency
# from .crawl import crawl
from .sandbox import PythonSandbox

# Import categorized tools
from .file import WriteFileTool, ReadFileTool, EditFileTool, ListFilesTool, AddImportsTool
from .search_tools_dir import WebSearchTool, CodeSearchTool, DocumentSearchTool
from .system.system_tools import BashTool, PythonExecuteTool, SystemInfoTool
from .approval import ApprovalTool, ConfigApprovalTool
from .todo import CreateTodoListTool, UpdateTodoTool, GetTodoListTool

# Import new tool modules
from .task_management import (
    CreateTaskTool, AssignTaskTool, UpdateTaskStatusTool,
    CreateCodingPlanTool, GenerateProgressReportTool, CreateTaskListTool
)
from .research_tools import (
    RequestResearchTool, AssignSearchTaskTool, AssignAnalysisTaskTool,
    AssignResearchTaskTool, SynthesizeFindingsTool, ReportCompletionTool,
    PlanNextRoundTool
)
from .architecture_tools import (
    CreateArchitectureDiagramTool, DocumentComponentTool, CreateImplementationRoadmapTool,
    AssessRisksTool, DecideArchitectureWritingTool, AnalyzeRequirementsTool
)
from .testing_tools import (
    CodeExecutorTool, TestRunnerTool, QualityCheckTool,
    TestSuiteTool, GenerateTestReportTool, CreateTestFileTool
)
from .reporting_tools import (
    ReportGeneratorTool, RetrospectiveTool, ReflectionTool,
    SuggestImprovementsTool, CompleteTaskTool, GenerateTodosTool
)
from .collaboration_tools import (
    TaskAssignmentTool, TeamCoordinationTool, ApprovalRequestTool,
    ReviewRequestTool, CoordinateTestingTool, MakeDecisionTool, SynthesizeResultsTool
)

# Optional tool for code execution
try:
    from .executor import CodeExecutor
except ImportError:
    CodeExecutor = None

# Tool registry
ALL_TOOLS = {
    # File tools
    "write_file": WriteFileTool,
    "read_file": ReadFileTool,
    "edit_file": EditFileTool,
    "list_files": ListFilesTool,
    "add_imports": AddImportsTool,

    # Search tools
    "web_search": WebSearchTool,
    "code_search": CodeSearchTool,
    "document_search": DocumentSearchTool,

    # System tools
    "bash": BashTool,
    "python_execute": PythonExecuteTool,
    "system_info": SystemInfoTool,

    # Approval tools
    "request_approval": ApprovalTool,
    "configure_approval": ConfigApprovalTool,

    # Todo tools
    "create_todo_list": CreateTodoListTool,
    "update_todo": UpdateTodoTool,
    "get_todo_list": GetTodoListTool,

    # Task management tools
    "create_task": CreateTaskTool,
    "assign_task": AssignTaskTool,
    "update_task_status": UpdateTaskStatusTool,
    "create_coding_plan": CreateCodingPlanTool,
    "generate_progress_report": GenerateProgressReportTool,
    "create_task_list": CreateTaskListTool,

    # Research tools
    "request_research": RequestResearchTool,
    "assign_search_task": AssignSearchTaskTool,
    "assign_analysis_task": AssignAnalysisTaskTool,
    "assign_research_task": AssignResearchTaskTool,
    "synthesize_findings": SynthesizeFindingsTool,
    "report_completion": ReportCompletionTool,
    "plan_next_round": PlanNextRoundTool,

    # Architecture tools
    "create_architecture_diagram": CreateArchitectureDiagramTool,
    "document_component": DocumentComponentTool,
    "create_implementation_roadmap": CreateImplementationRoadmapTool,
    "assess_risks": AssessRisksTool,
    "decide_architecture_writing": DecideArchitectureWritingTool,
    "analyze_requirements": AnalyzeRequirementsTool,

    # Testing tools
    "run_code": CodeExecutorTool,
    "execute_tests": TestRunnerTool,
    "check_quality": QualityCheckTool,
    "create_test_suite": TestSuiteTool,
    "generate_test_report": GenerateTestReportTool,
    "create_test_file": CreateTestFileTool,

    # Reporting tools
    "generate_report": ReportGeneratorTool,
    "create_retrospective": RetrospectiveTool,
    "record_reflection": ReflectionTool,
    "suggest_improvements": SuggestImprovementsTool,
    "complete_task": CompleteTaskTool,
    "generate_todos": GenerateTodosTool,

    # Collaboration tools
    "coordinate_task_assignment": TaskAssignmentTool,
    "coordinate_team_activities": TeamCoordinationTool,
    "request_approval": ApprovalRequestTool,
    "request_review": ReviewRequestTool,
    "coordinate_testing": CoordinateTestingTool,
    "make_decision": MakeDecisionTool,
    "synthesize_results": SynthesizeResultsTool,

    # Existing tools
    "get_web_search_tool": get_web_search_tool,
    # "crawl": crawl,  # Temporarily disabled
    "sandbox": PythonSandbox
}

# Add MyRagSearchTool if available
if MyRagSearchTool:
    ALL_TOOLS["MyRagSearchTool"] = MyRagSearchTool

# Agent tool assignments
AGENT_TOOLS = {
    # Global coordinator
    "coordinator": ["make_decision"],

    # Architecture team
    "planner": ["request_research", "plan_next_round", "decide_architecture_writing"],
    "research_coordinator": ["assign_search_task", "synthesize_findings", "report_completion"],
    "searcher": ["web_search"],
    "architecture_writer": ["create_architecture_diagram", "document_component", "create_implementation_roadmap", "assess_risks", "decide_architecture_writing"],

    # Coding team
    "code_coordinator": ["create_coding_plan", "assign_task", "update_task_status", "request_review", "coordinate_testing", "generate_progress_report", "request_approval"],
    "coder": ["write_file", "read_file", "edit_file", "list_files", "code_search", "create_task", "add_imports", "create_test_file", "request_approval"],
    "executor": ["run_code", "execute_tests", "check_quality", "create_test_suite", "generate_test_report", "bash", "python_execute"],
    "reflector": ["generate_todos", "record_reflection", "suggest_improvements", "complete_task", "create_retrospective"],

    # Reporter
    "reporter": ["generate_report", "synthesize_results", "create_retrospective", "suggest_improvements"],

    # Legacy aliases
    "search": ["web_search", "code_search", "document_search"],
    "test_runner": ["run_code", "execute_tests", "check_quality", "generate_test_report"]
}

# Add MyRagSearchTool to searcher if available
if MyRagSearchTool:
    AGENT_TOOLS["searcher"].append("MyRagSearchTool")

def get_tool_schemas(tool_names: list) -> list:
    """Get tool schemas for specified tools"""
    schemas = []
    for name in tool_names:
        if name in ALL_TOOLS:
            tool_class = ALL_TOOLS[name]
            if hasattr(tool_class, 'get_schema'):
                schemas.append(tool_class.get_schema())
    return schemas

def get_agent_tools(agent_name: str) -> list:
    """Get tools for a specific agent"""
    return AGENT_TOOLS.get(agent_name, [])

__all__ = [
    "BaseTool",
    "tool",
    "log_io",
    "LoggedToolMixin",
    "create_logged_tool",
    # Search functionality
    "get_web_search_tool",
    # "crawl",  # Temporarily disabled
    "MyRagSearchTool",
    "PythonSandbox",
    "CodeExecutor",
    "WriteFileTool",
    "ReadFileTool",
    "EditFileTool",
    "ListFilesTool",
    "WebSearchTool",
    "CodeSearchTool",
    "DocumentSearchTool",
    "BashTool",
    "PythonExecuteTool",
    "SystemInfoTool",
    "ApprovalTool",
    "ConfigApprovalTool",
    # Utilities
    "ALL_TOOLS",
    "AGENT_TOOLS",
    "get_tool_schemas",
    "get_agent_tools"
]
