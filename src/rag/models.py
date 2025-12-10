"""
RAG Data Models - 定义清晰的数据结构
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """内容类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    EQUATION = "equation"
    CHART = "chart"
    CODE = "code"
    GENERIC = "generic"


class DocumentSource(BaseModel):
    """文档来源信息"""
    file_path: str = Field(..., description="文档文件路径")
    file_name: str = Field(..., description="文档文件名")
    file_extension: str = Field(..., description="文件扩展名")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    mime_type: Optional[str] = Field(None, description="MIME类型")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    modified_at: Optional[datetime] = Field(None, description="修改时间")


class DocumentMetadata(BaseModel):
    """文档元数据"""
    doc_id: str = Field(..., description="文档唯一标识符")
    source: DocumentSource = Field(..., description="文档来源信息")
    title: Optional[str] = Field(None, description="文档标题")
    author: Optional[str] = Field(None, description="作者")
    language: Optional[str] = Field("zh", description="语言")
    page_count: Optional[int] = Field(None, description="页数")
    word_count: Optional[int] = Field(None, description="字数")
    parse_method: Optional[str] = Field(None, description="解析方法")
    parse_version: Optional[str] = Field(None, description="解析器版本")
    tags: List[str] = Field(default_factory=list, description="标签")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="自定义字段")


class ChunkMetadata(BaseModel):
    """文档块元数据"""
    chunk_id: str = Field(..., description="块唯一标识符")
    doc_id: str = Field(..., description="所属文档ID")
    chunk_index: int = Field(..., description="块在文档中的索引")
    page_number: Optional[int] = Field(None, description="页码")
    section_title: Optional[str] = Field(None, description="章节标题")
    position: Optional[Dict[str, Any]] = Field(None, description="位置信息")
    tokens: Optional[int] = Field(None, description="token数量")
    content_type: ContentType = Field(ContentType.TEXT, description="内容类型")
    bbox: Optional[List[float]] = Field(None, description="边界框 [x1, y1, x2, y2]")
    confidence: Optional[float] = Field(None, description="置信度")
    context_before: Optional[str] = Field(None, description="前文上下文")
    context_after: Optional[str] = Field(None, description="后文上下文")
    custom_data: Dict[str, Any] = Field(default_factory=dict, description="自定义数据")


class ImageContent(BaseModel):
    """图像内容"""
    url: Optional[str] = Field(None, description="图像URL")
    path: Optional[str] = Field(None, description="图像路径")
    base64: Optional[str] = Field(None, description="Base64编码")
    width: Optional[int] = Field(None, description="宽度")
    height: Optional[int] = Field(None, description="高度")
    format: Optional[str] = Field(None, description="格式")
    caption: Optional[str] = Field(None, description="图注")
    ocr_text: Optional[str] = Field(None, description="OCR识别的文本")
    description: Optional[str] = Field(None, description="图像描述")


class TableContent(BaseModel):
    """表格内容"""
    headers: List[str] = Field(default_factory=list, description="表头")
    rows: List[List[str]] = Field(default_factory=list, description="表格行")
    markdown: Optional[str] = Field(None, description="Markdown格式")
    html: Optional[str] = Field(None, description="HTML格式")
    caption: Optional[str] = Field(None, description="表注")
    description: Optional[str] = Field(None, description="表格描述")


class EquationContent(BaseModel):
    """公式内容"""
    latex: Optional[str] = Field(None, description="LaTeX表达式")
    mathml: Optional[str] = Field(None, description="MathML格式")
    image_path: Optional[str] = Field(None, description="公式图片路径")
    alt_text: Optional[str] = Field(None, description="替代文本")
    description: Optional[str] = Field(None, description="公式描述")


class CodeContent(BaseModel):
    """代码内容"""
    language: Optional[str] = Field(None, description="编程语言")
    code: str = Field(..., description="代码内容")
    line_start: Optional[int] = Field(None, description="起始行号")
    line_end: Optional[int] = Field(None, description="结束行号")
    function_name: Optional[str] = Field(None, description="函数名")
    class_name: Optional[str] = Field(None, description="类名")
    description: Optional[str] = Field(None, description="代码描述")


class DocumentChunk(BaseModel):
    """文档块 - RAG系统的核心数据结构"""
    chunk_id: str = Field(..., description="块唯一标识符")
    doc_id: str = Field(..., description="所属文档ID")
    content: str = Field(..., description="文本内容")
    content_type: ContentType = Field(ContentType.TEXT, description="内容类型")
    metadata: ChunkMetadata = Field(..., description="块元数据")

    # 多模态内容
    image: Optional[ImageContent] = Field(None, description="图像内容")
    table: Optional[TableContent] = Field(None, description="表格内容")
    equation: Optional[EquationContent] = Field(None, description="公式内容")
    code: Optional[CodeContent] = Field(None, description="代码内容")

    # 向量相关
    embedding: Optional[List[float]] = Field(None, description="内容向量")
    question_embedding: Optional[List[float]] = Field(None, description="问题向量")

    # 检索相关
    score: Optional[float] = Field(None, description="相关性分数")
    highlights: Optional[List[str]] = Field(None, description="高亮片段")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class Document(BaseModel):
    """完整文档"""
    metadata: DocumentMetadata = Field(..., description="文档元数据")
    chunks: List[DocumentChunk] = Field(default_factory=list, description="文档块列表")

    def add_chunk(self, chunk: DocumentChunk) -> None:
        """添加文档块"""
        chunk.doc_id = self.metadata.doc_id
        self.chunks.append(chunk)

    def get_chunk_by_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        """根据ID获取文档块"""
        for chunk in self.chunks:
            if chunk.chunk_id == chunk_id:
                return chunk
        return None

    def get_chunks_by_type(self, content_type: ContentType) -> List[DocumentChunk]:
        """根据类型获取文档块"""
        return [chunk for chunk in self.chunks if chunk.content_type == content_type]


class QueryRequest(BaseModel):
    """查询请求"""
    query: str = Field(..., description="查询文本")
    top_k: int = Field(10, description="返回结果数量")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    include_metadata: bool = Field(True, description="是否包含元数据")
    include_content: bool = Field(True, description="是否包含内容")
    min_score: Optional[float] = Field(None, description="最低相关性分数")
    rerank: bool = Field(False, description="是否重排序")


class QueryResult(BaseModel):
    """查询结果"""
    chunk: DocumentChunk = Field(..., description="文档块")
    score: float = Field(..., description="相关性分数")
    explanation: Optional[str] = Field(None, description="解释")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class QueryResponse(BaseModel):
    """查询响应"""
    results: List[QueryResult] = Field(..., description="查询结果列表")
    total: int = Field(..., description="总结果数")
    query: str = Field(..., description="原始查询")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    has_more: bool = Field(False, description="是否还有更多结果")


class IndexStats(BaseModel):
    """索引统计信息"""
    total_documents: int = Field(..., description="总文档数")
    total_chunks: int = Field(..., description="总块数")
    indexed_at: Optional[datetime] = Field(None, description="索引时间")
    size_bytes: Optional[int] = Field(None, description="索引大小（字节）")
    dimension: Optional[int] = Field(None, description="向量维度")
    content_types: Dict[ContentType, int] = Field(default_factory=dict, description="内容类型分布")


class BatchInsertRequest(BaseModel):
    """批量插入请求"""
    documents: List[Document] = Field(..., description="文档列表")
    update_mode: str = Field("upsert", description="更新模式: insert/upsert/update")
    batch_size: int = Field(100, description="批处理大小")
    generate_questions: bool = Field(False, description="是否生成问题")


class BatchInsertResponse(BaseModel):
    """批量插入响应"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    failed_ids: List[str] = Field(default_factory=list, description="失败的文档ID")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    processing_time: float = Field(..., description="处理时间（秒）")


# 导出所有模型
__all__ = [
    "ContentType",
    "DocumentSource",
    "DocumentMetadata",
    "ChunkMetadata",
    "ImageContent",
    "TableContent",
    "EquationContent",
    "CodeContent",
    "DocumentChunk",
    "Document",
    "QueryRequest",
    "QueryResult",
    "QueryResponse",
    "IndexStats",
    "BatchInsertRequest",
    "BatchInsertResponse",
]