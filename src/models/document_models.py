"""
数据模型定义 - 文档处理相关
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
import datetime


class DocumentType(str, Enum):
    """文档类型枚举"""
    PDF = "pdf"
    PPT = "ppt"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "markdown"
    IMAGE = "image"
    FLOWCHART = "flowchart"
    ARCHITECTURE_DIAGRAM = "architecture_diagram"
    CODE = "code"


class InsightType(str, Enum):
    """洞察类型枚举"""
    TECHNICAL_REQUIREMENT = "technical_requirement"
    ARCHITECTURE_PATTERN = "architecture_pattern"
    DESIGN_DECISION = "design_decision"
    CONSTRAINT = "constraint"
    DEPENDENCY = "dependency"
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    BEST_PRACTICE = "best_practice"


class CodeLanguage(str, Enum):
    """编程语言枚举"""
    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    C = "c"
    CPP = "cpp"
    CSHARP = "csharp"
    PHP = "php"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"


class DocumentMetadata(BaseModel):
    """文档元数据"""
    title: str
    author: Optional[str] = None
    document_type: DocumentType
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    creation_date: Optional[datetime.datetime] = None
    last_modified: Optional[datetime.datetime] = None
    source_path: str
    language: str = "zh-CN"


class TechnicalRequirement(BaseModel):
    """技术需求"""
    id: str
    category: str  # 功能性需求、性能需求、安全性需求等
    description: str
    priority: str  # High, Medium, Low
    acceptance_criteria: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    estimated_complexity: str  # Simple, Medium, Complex, Very Complex


class ArchitecturePattern(BaseModel):
    """架构模式"""
    name: str
    pattern_type: str  # MVC, Microservices, Event-Driven, etc.
    description: str
    components: List[str] = Field(default_factory=list)
    interactions: List[str] = Field(default_factory=list)
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)


class DesignDecision(BaseModel):
    """设计决策"""
    decision_id: str
    title: str
    context: str
    decision: str
    rationale: str
    implications: List[str] = Field(default_factory=list)
    status: str  # Proposed, Accepted, Deprecated
    date: datetime.datetime


class Dependency(BaseModel):
    """依赖项"""
    name: str
    version: Optional[str] = None
    type: str  # library, service, database, external_api
    description: Optional[str] = None
    license: Optional[str] = None
    criticality: str  # Critical, High, Medium, Low


class Risk(BaseModel):
    """风险项"""
    risk_id: str
    description: str
    impact: str  # High, Medium, Low
    probability: str  # High, Medium, Low
    mitigation_strategy: Optional[str] = None
    owner: Optional[str] = None


class Insight(BaseModel):
    """洞察点"""
    insight_id: str
    type: InsightType
    title: str
    content: str
    confidence: float  # 0.0 - 1.0
    source_locations: List[str] = Field(default_factory=list)
    related_insights: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class DocumentInsights(BaseModel):
    """文档洞察集合"""
    document_id: str
    metadata: DocumentMetadata
    summary: str
    key_findings: List[str] = Field(default_factory=list)
    insights: List[Insight] = Field(default_factory=list)
    technical_requirements: List[TechnicalRequirement] = Field(default_factory=list)
    architecture_patterns: List[ArchitecturePattern] = Field(default_factory=list)
    design_decisions: List[DesignDecision] = Field(default_factory=list)
    dependencies: List[Dependency] = Field(default_factory=list)
    risks: List[Risk] = Field(default_factory=list)
    overall_confidence: float = 0.0
    analysis_timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)


class ComponentSpecification(BaseModel):
    """组件规范"""
    name: str
    type: str  # service, module, library, etc.
    description: str
    responsibilities: List[str] = Field(default_factory=list)
    interfaces: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    technology_stack: List[str] = Field(default_factory=list)
    estimated_effort: str  # story points or person-days


class DataModel(BaseModel):
    """数据模型"""
    name: str
    description: str
    attributes: List[Dict[str, Any]] = Field(default_factory=list)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)


class APIEndpoint(BaseModel):
    """API端点"""
    path: str
    method: str  # GET, POST, PUT, DELETE
    description: str
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    authentication_required: bool = False


class TechnicalRequirements(BaseModel):
    """技术需求集合"""
    requirements_id: str
    functional_requirements: List[TechnicalRequirement] = Field(default_factory=list)
    non_functional_requirements: List[TechnicalRequirement] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)


class SystemArchitecture(BaseModel):
    """系统架构"""
    architecture_type: str  # Monolithic, Microservices, Serverless, etc.
    description: str
    components: List[ComponentSpecification] = Field(default_factory=list)
    data_models: List[DataModel] = Field(default_factory=list)
    api_endpoints: List[APIEndpoint] = Field(default_factory=list)
    deployment_topology: Optional[str] = None
    scalability_considerations: List[str] = Field(default_factory=list)
    security_considerations: List[str] = Field(default_factory=list)


class DesignBlueprint(BaseModel):
    """设计蓝图"""
    blueprint_id: str
    project_name: str
    project_description: str
    technical_requirements: TechnicalRequirements
    system_architecture: SystemArchitecture
    technology_stack: List[str] = Field(default_factory=list)
    implementation_phases: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_timeline: Optional[str] = None
    risk_assessment: List[Risk] = Field(default_factory=list)
    created_timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    created_by: str = "DeepCodeAgent"


class CodeFile(BaseModel):
    """代码文件模型"""
    file_path: str
    language: CodeLanguage
    content: str
    docstring: Optional[str] = None
    functions: List[Dict[str, Any]] = Field(default_factory=list)
    classes: List[Dict[str, Any]] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    complexity_score: Optional[float] = None


class TestSpec(BaseModel):
    """测试规范"""
    test_id: str
    test_type: str  # unit, integration, e2e, performance
    description: str
    test_cases: List[Dict[str, Any]] = Field(default_factory=list)
    coverage_targets: List[str] = Field(default_factory=list)
    mock_dependencies: List[str] = Field(default_factory=list)


class RepositoryStructure(BaseModel):
    """代码仓库结构"""
    root_path: str
    project_name: str
    description: str
    files: List[CodeFile] = Field(default_factory=list)
    test_specs: List[TestSpec] = Field(default_factory=list)
    documentation: List[Dict[str, Any]] = Field(default_factory=list)
    configuration_files: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies: List[Dependency] = Field(default_factory=list)
    build_system: Optional[str] = None  # maven, gradle, npm, etc.
