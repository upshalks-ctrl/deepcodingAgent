# DeepCodeAgent API 参考文档

## 目录

1. [核心模块 API](#核心模块-api)
2. [LLM 封装 API](#llm-封装-api)
3. [工具系统 API](#工具系统-api)
4. [工作流 API](#工作流-api)
5. [状态管理 API](#状态管理-api)
6. [RAG 系统 API](#rag-系统-api)

---

## 核心模块 API

### GlobalCoordinator 系列类

#### 1. SimpleCoordinator (简化版)
```python
from src.deepcodeagent.coordinator_simple import SimpleCoordinator

class SimpleCoordinator:
    """简化版任务协调器"""

    def __init__(self, model: Optional[Any] = None):
        """初始化协调器"""
        pass

    async def process(self, requirement: str, state: Any) -> Tuple[Any, str]:
        """
        处理需求并返回决策

        Args:
            requirement: 用户需求描述
            state: 任务状态对象

        Returns:
            Tuple[更新后的状态, 决策动作]
        """
        pass

# 使用示例
coordinator = SimpleCoordinator(model=None)
state, action = await coordinator.process("创建一个用户管理系统", state)
```

#### 2. StructuredGlobalCoordinator (结构化版)
```python
from src.deepcodeagent.coordinator_structured import StructuredGlobalCoordinator, TaskAnalysis

class StructuredGlobalCoordinator:
    """结构化任务协调器"""

    async def process(self, requirement: str) -> CoordinatorResponse:
        """
        分析任务并返回结构化结果

        Returns:
            CoordinatorResponse: 包含任务分析、复杂度评分等
        """
        pass

class TaskAnalysis(BaseModel):
    """任务分析结果"""
    task_type: TaskType
    team_assigned: str
    complexity_score: int  # 1-10
    estimated_hours: Optional[float]
    required_tools: List[str]
```

### Workflow 函数
```python
from src.deepcodeagent.workflow import workflowfun

async def workflowfun(
    requirement: str,
    output_dir: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    主工作流函数

    Args:
        requirement: 用户需求
        output_dir: 输出目录
        session_id: 会话ID

    Returns:
        Dict: 包含执行结果、文件列表、错误信息等
    """
    pass
```

---

## LLM 封装 API

### 基础 LLM 类
```python
from src.myllms.base import BaseLLM

class BaseLLM:
    """LLM 基类"""

    def __init__(self, config: Dict[str, Any]):
        pass

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """生成文本"""
        pass

    async def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> str:
        """基于对话历史生成"""
        pass
```

### LLM 工厂
```python
from src.myllms.factory import LLMFactory, ModelType

# 创建 LLM 实例
llm = LLMFactory.create_llm(
    model_type=ModelType.DEEPSEEK,
    config={
        "api_key": "your_api_key",
        "base_url": "https://api.deepseek.com"
    }
)

# 使用示例
response = await llm.generate("解释什么是微服务架构")
```

---

## 工具系统 API

### 工具装饰器
```python
from src.tools.decorators import tool

@tool
def calculate_sum(numbers: List[float]) -> float:
    """
    计算数字列表的和

    Args:
        numbers: 数字列表

    Returns:
        float: 计算结果
    """
    return sum(numbers)
```

### 核心工具类

#### 1. 搜索工具
```python
from src.tools.search import SearchTool

search_tool = SearchTool(config)

# 执行搜索
results = await search_tool.search(
    query="Python异步编程最佳实践",
    max_results=10,
    include_domains=["docs.python.org", "realpython.com"]
)
```

#### 2. 文件工具
```python
from src.tools.file.file_tools import FileTools

file_tools = FileTools()

# 创建文件
await file_tools.create_file("hello.py", "print('Hello, World!')")

# 读取文件
content = await file_tools.read_file("hello.py")

# 批量操作
files = await file_tools.create_batch({
    "main.py": "def main(): pass",
    "utils.py": "def helper(): pass"
})
```

#### 3. 代码执行工具
```python
from src.tools.sandbox import SandboxExecutor

executor = SandboxExecutor()

# 执行 Python 代码
result = await executor.execute_python("""
import math
def factorial(n):
    return math.factorial(n)
print(factorial(5))
""")

# 执行 Shell 命令
result = await executor.execute_command("ls -la")
```

---

## 工作流 API

### Phase 基类
```python
from src.deepcodeagent.phases.core import Phase, PhaseResult

class Phase:
    """工作流阶段基类"""

    async def execute(
        self,
        input_data: Any,
        context: Dict[str, Any]
    ) -> PhaseResult:
        """
        执行阶段任务

        Args:
            input_data: 阶段输入数据
            context: 执行上下文

        Returns:
            PhaseResult: 阶段执行结果
        """
        pass

class PhaseResult(BaseModel):
    """阶段执行结果"""
    success: bool
    data: Any
    artifacts: Dict[str, Any] = {}
    next_phase: Optional[str] = None
    error: Optional[str] = None
```

### 具体阶段实现

#### 1. 研究阶段
```python
from src.deepcodeagent.phases.search_phase import SearchPhase

phase = SearchPhase(config)
result = await phase.execute(
    input_data="研究微服务架构的设计模式",
    context={"user_id": "user123"}
)
```

#### 2. 编码阶段
```python
from src.deepcodeagent.phases.coding_phase import CodingPhase

phase = CodingPhase(config)
result = await phase.execute(
    input_data={
        "task": "实现一个 REST API",
        "spec": {"endpoints": ["/users", "/posts"]},
        "language": "Python"
    },
    context={"framework": "Flask"}
)
```

---

## 状态管理 API

### State 类
```python
from src.my_agent.state import State, TaskState, create_state

# 创建状态
state = create_state(
    task_id="task_001",
    requirement="创建一个TODO应用",
    user_id="user123"
)

# 更新状态
state.update_task_progress(50)
state.set_current_phase("coding")
state.add_artifact("main.py", "/path/to/main.py")

# 获取状态信息
print(state.task.status)
print(state.task.progress)
print(state.task.artifacts)
```

### 状态模型
```python
from src.my_agent.models import Task, TaskStatus, Phase

class Task(BaseModel):
    """任务模型"""
    id: str
    requirement: str
    status: TaskStatus
    progress: float
    current_phase: Optional[str]
    artifacts: Dict[str, str] = {}
    created_at: datetime
    updated_at: datetime
```

---

## RAG 系统 API

### RAG 构建器
```python
from src.rag.builder import RAGBuilder

# 构建 RAG 系统
builder = RAGBuilder()
rag = builder.with_qdrant("localhost", 6333)\
              .with_embeddings("text-embedding-ada-002")\
              .build()

# 添加文档
await rag.add_document("doc1", "微服务架构是一种...")
await rag.add_batch([
    ("doc2", "容器化技术..."),
    ("doc3", "API网关模式...")
])
```

### 检索器
```python
from src.rag.retriever import DocumentRetriever

retriever = DocumentRetriever(rag_system)

# 检索相关文档
results = await retriever.retrieve(
    query="如何设计可扩展的微服务架构",
    top_k=5,
    similarity_threshold=0.7
)

# 带重排序的检索
results = await retriever.retrieve_with_rerank(
    query="Python异步编程",
    top_k=10,
    rerank_model="cross-encoder/ms-marco-MiniLM-L-6-v2"
)
```

---

## 错误处理

### 异常类
```python
from src.deepcodeagent.core import DeepCodeAgentError

class CoordinatorError(DeepCodeAgentError):
    """协调器错误"""
    pass

class PhaseExecutionError(DeepCodeAgentError):
    """阶段执行错误"""
    pass

class ToolExecutionError(DeepCodeAgentError):
    """工具执行错误"""
    pass
```

### 错误处理示例
```python
try:
    result = await workflowfun("创建一个复杂的应用")
except CoordinatorError as e:
    logger.error(f"任务协调失败: {e}")
except PhaseExecutionError as e:
    logger.error(f"阶段执行失败: {e.phase} - {e}")
except Exception as e:
    logger.error(f"未知错误: {e}")
```

---

## 配置管理

### 配置类
```python
from src.config.loader import ConfigLoader

# 加载配置
config = ConfigLoader.load("conf.yaml")

# 访问配置
basic_model_config = config.get_model_config("BASIC_MODEL")
search_config = config.get_search_config()

# 运行时更新配置
config.update("CODE_MODEL.temperature", 0.5)
config.save("updated_conf.yaml")
```

---

## 事件系统

### 事件发布订阅
```python
from src.deepcodeagent.core import EventBus, Event, EventType

# 创建事件总线
event_bus = EventBus()

# 订阅事件
@event_bus.subscribe(EventType.TASK_CREATED)
async def on_task_created(event: Event):
    print(f"新任务创建: {event.data['task_id']}")

# 发布事件
await event_bus.publish(Event(
    type=EventType.TASK_CREATED,
    data={"task_id": "task_001", "requirement": "..."}
))
```

---

## 扩展指南

### 自定义工具
```python
from src.tools.decorators import tool

@tool
async def custom_api_call(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict] = None
) -> Dict:
    """自定义API调用工具"""
    async with aiohttp.ClientSession() as session:
        async with session.request(method, endpoint, json=data) as resp:
            return await resp.json()
```

### 自定义阶段
```python
from src.deepcodeagent.phases.core import Phase

class CustomPhase(Phase):
    """自定义工作流阶段"""

    async def execute(self, input_data, context):
        # 实现自定义逻辑
        result = self.process_data(input_data)

        return PhaseResult(
            success=True,
            data=result,
            artifacts={"output.json": result}
        )
```

---

## 更多信息

- [完整示例](../examples/)
- [最佳实践](../docs/BEST_PRACTICES.md)
- [故障排除](../docs/TROUBLESHOOTING.md)
- [更新日志](../CHANGELOG.md)