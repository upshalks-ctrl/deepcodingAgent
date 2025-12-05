"""
文档数据模型
标准化文档内容格式
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Document:
    """
    标准文档格式

    Attributes:
        content: 文档内容（纯文本）
        metadata: 元数据字典，包含：
            - source_path: 源文件路径
            - title: 文档标题
            - url: 可选，文档的URL或标识符
            - document_type: 文档类型
            - word_count: 字数
            - language: 语言
            - created_at: 创建时间
            - chunk_index: 如果是块级文档，记录块索引
            - 其他自定义元数据
    """
    content: str
    document_type: str
    source_path: str
    title: str
    url: str
    metadata: Dict[str, Any] = field(default_factory=dict)



    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'content': self.content,
            'metadata': self.metadata,
            'document_type': self.document_type,
            'source_path': self.source_path,
            'title': self.title,
            'url': self.url
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """从字典创建实例"""
        return cls(
            content=data['content'],
            metadata=data.get('metadata', {}),
            document_type = data.get('document_type', 'unknown'),
            source_path = data.get('source_path', ''),
            title = data.get('title', ''),
            url = data.get('url', '')
        )
