"""
文档处理器统一接口
支持多种文件类型的智能处理和分块
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.models.document import Document

logger = logging.getLogger(__name__)


class DocumentProcessorRegistry:
    """文档处理器注册表"""

    _processors = {}

    @classmethod
    def register(cls, file_ext: str, processor_class):
        """注册处理器"""
        cls._processors[file_ext.lower()] = processor_class

    @classmethod
    def get_processor(cls, file_ext: str):
        """获取处理器"""
        return cls._processors.get(file_ext.lower())

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """获取支持的文件扩展名"""
        return list(cls._processors.keys())


def create_document_metadata(
    **extra_metadata
) -> Dict[str, Any]:
    """
    创建文档元数据

    Args:
        file_path: 文件路径
        document_type: 文档类型
        **extra_metadata: 额外元数据

    Returns:
        Dict[str, Any]: 元数据字典
    """

    metadata = {
        'created_at': datetime.now().isoformat(),
        'language': 'zh-CN',  # 默认语言，可根据内容检测
        **extra_metadata
    }

    return metadata


def chunk_document(
    document: Document,
    strategy: str = 'auto',
    chunk_size: int = 1000,
    overlap: int = 100
) -> List[Document]:
    """
    将文档切分为多个块

    Args:
        document: 原始文档
        strategy: 分块策略 ('auto', 'paragraph', 'title', 'page', 'semantic')
        chunk_size: 块大小（字符数）
        overlap: 块间重叠字符数

    Returns:
        List[Document]: 切分后的文档块列表
    """
    content = document.content
    metadata = document.metadata.copy()

    chunks = []

    if not content.strip():
        return chunks

    # 根据文档类型选择默认策略
    if strategy == 'auto':
        doc_type = document.document_type.lower()
        if doc_type in ['txt', 'markdown', 'text']:
            strategy = 'paragraph'
        elif doc_type in ['pdf']:
            strategy = 'title'
        elif doc_type in ['ppt', 'powerpoint']:
            strategy = 'page'
        elif doc_type in ['docx', 'word']:
            strategy = 'paragraph'
        else:
            strategy = 'semantic'

    logger.debug(f"使用分块策略: {strategy}")

    # 执行分块
    if strategy == 'paragraph':
        chunks = _chunk_by_paragraph(document, chunk_size, overlap)
    elif strategy == 'title':
        chunks = _chunk_by_title(document, chunk_size, overlap)
    elif strategy == 'page':
        chunks = _chunk_by_page(document)
    elif strategy == 'semantic':
        chunks = _chunk_semantic(document, chunk_size, overlap)
    else:
        # 默认简单分块
        chunks = _chunk_simple(document, chunk_size, overlap)

    # 为每个块添加索引
    for i, chunk in enumerate(chunks):
        chunk.metadata['chunk_index'] = i
        chunk.metadata['chunk_total'] = len(chunks)

    logger.info(f"文档分为 {len(chunks)} 个块")
    return chunks


def _chunk_by_paragraph(
    document: Document,
    chunk_size: int,
    overlap: int
) -> List[Document]:
    """按段落分块"""
    import re
    content = document.content
    metadata = document.metadata.copy()
    # 按段落分割（双换行符或单换行符）
    paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n', content)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current_chunk = ""
    current_index = 0

    for paragraph in paragraphs:
        # 如果添加这个段落会超出大小限制，先保存当前块
        if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
            doc = Document(
                content=current_chunk.strip(),
                metadata=metadata.copy(),
                document_type=document.document_type,
                source_path=document.source_path,
                title=document.title,
                url=document.url
            )
            doc.metadata['chunk_type'] = 'paragraph'
            doc.metadata['start_index'] = current_index
            chunks.append(doc)

            # 计算重叠部分
            if overlap > 0 and len(current_chunk) > overlap:
                overlap_text = current_chunk[-overlap:]
                current_chunk = overlap_text + "\n\n" + paragraph
            else:
                current_chunk = paragraph
            current_index += len(current_chunk)
        else:
            # 添加段落到当前块
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph

    # 添加最后一个块
    if current_chunk:
        doc = Document(
            content=current_chunk.strip(),
            metadata=metadata.copy(),
            document_type=document.document_type,
            source_path=document.source_path,
            title=document.title,
            url=document.url
        )

        chunks.append(doc)

    return chunks


def _chunk_by_title(
    document: Document,
    chunk_size: int,
    overlap: int
) -> List[Document]:
    """按标题分块（适用于PDF等）"""
    import re

    # 匹配标题模式（# 标题，1. 标题，等）
    title_patterns = [
        r'^#{1,6}\s+(.+)$',  # Markdown标题
        r'^(\d+\.)\s+(.+)$',  # 数字标题
        r'^([IVX]+\.)\s+(.+)$',  # 罗马数字标题
        r'^([A-Z][A-Z\s]{2,})\s*$',  # 全大写标题
    ]
    content = document.content
    metadata = document.metadata.copy()
    lines = content.split('\n')
    chunks = []
    current_chunk = ""
    current_title = metadata.get('title', '文档')
    current_index = 0

    for line in lines:
        # 检查是否是标题
        is_title = False
        for pattern in title_patterns:
            match = re.match(pattern, line.strip())
            if match:
                is_title = True
                # 提取标题文本
                title_text = match.group(1) if match.groups() else line.strip()
                current_title = title_text
                break

        # 如果是标题且当前块不为空，先保存
        if is_title and current_chunk:
            doc = Document(
                content=current_chunk.strip(),
                metadata=metadata.copy(),
                document_type=document.document_type,
                source_path=document.source_path,
                title=document.title,
                url=document.url
            )
            doc.metadata['chunk_type'] = 'title'
            doc.metadata['chunk_title'] = current_title
            doc.metadata['start_index'] = current_index
            chunks.append(doc)

            # 处理重叠
            if overlap > 0 and len(current_chunk) > overlap:
                overlap_text = current_chunk[-overlap:]
                current_chunk = overlap_text + "\n" + line
            else:
                current_chunk = line
            current_index += len(current_chunk)
        else:
            # 添加行到当前块
            if current_chunk:
                current_chunk += "\n" + line
            else:
                current_chunk = line

        # 如果当前块超过大小限制，切分
        if len(current_chunk) > chunk_size:
            doc = Document(
                content=current_chunk.strip(),
                metadata=metadata.copy(),
                document_type=document.document_type,
                source_path=document.source_path,
                title=document.title,
                url=document.url
            )
            doc.metadata['chunk_type'] = 'title'
            doc.metadata['chunk_title'] = current_title
            doc.metadata['start_index'] = current_index
            chunks.append(doc)

            # 处理重叠
            if overlap > 0 and len(current_chunk) > overlap:
                overlap_text = current_chunk[-overlap:]
                current_chunk = overlap_text
            else:
                current_chunk = ""

    # 添加最后一个块
    if current_chunk:
        doc = Document(
            content=current_chunk.strip(),
            metadata=metadata.copy(),
            document_type=document.document_type,
            source_path=document.source_path,
            title=document.title,
            url=document.url
        )
        doc.metadata['chunk_type'] = 'title'
        doc.metadata['chunk_title'] = current_title
        doc.metadata['start_index'] = current_index
        chunks.append(doc)

    return chunks


def _chunk_by_page(
    document: Document,
) -> List[Document]:
    """按页面分块（适用于PPT等）"""
    # PPT通常按幻灯片分页
    import re
    content = document.content
    metadata = document.metadata.copy()
    # 尝试按分页符切分
    page_splits = re.split(r'\n\s*---\s*\n|\n\s*===+\s*\n', content)
    page_splits = [p.strip() for p in page_splits if p.strip()]

    chunks = []
    for i, page_content in enumerate(page_splits):
        doc = Document(
            content=page_content,
            metadata=metadata.copy(),
            document_type=document.document_type,
            source_path=document.source_path,
            title=document.title,
            url=document.url
        )
        doc.metadata['chunk_type'] = 'page'
        doc.metadata['page_number'] = i + 1
        doc.metadata['chunk_title'] = f"第{i+1}页"
        doc.metadata['start_index'] = i
        chunks.append(doc)

    return chunks


def _chunk_semantic(
    document: Document,
    chunk_size: int,
    overlap: int
) -> List[Document]:
    """语义分块（按句子和语义边界）"""
    import re
    content = document.content
    metadata = document.metadata.copy()
    # 按句子分割
    sentences = re.split(r'[。！？\n]', content)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current_chunk = ""
    current_index = 0

    for sentence in sentences:
        # 如果添加这个句子会超出大小限制
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            doc = Document(
                content=current_chunk.strip(),
                metadata=metadata.copy(),
                document_type=document.document_type,
                source_path=document.source_path,
                title=document.title,
                url=document.url
            )
            doc.metadata['chunk_type'] = 'semantic'
            doc.metadata['start_index'] = current_index
            chunks.append(doc)

            # 处理重叠
            if overlap > 0 and len(current_chunk) > overlap:
                overlap_text = current_chunk[-overlap:]
                current_chunk = overlap_text + "。" + sentence
            else:
                current_chunk = sentence
            current_index += len(current_chunk)
        else:
            # 添加句子
            if current_chunk:
                current_chunk += "。" + sentence
            else:
                current_chunk = sentence

    # 添加最后一个块
    if current_chunk:
        doc = Document(
            content=current_chunk.strip(),
            metadata=metadata.copy(),
            document_type=document.document_type,
            source_path=document.source_path,
            title=document.title,
            url=document.url
        )
        doc.metadata['chunk_type'] = 'semantic'
        doc.metadata['start_index'] = current_index
        chunks.append(doc)

    return chunks


def _chunk_simple(
    document: Document,
    chunk_size: int,
    overlap: int
) -> List[Document]:
    """简单固定大小分块"""
    chunks = []
    start = 0
    chunk_index = 0
    content = document.content
    metadata = document.metadata.copy()

    while start < len(content):
        end = start + chunk_size

        # 尝试在句子边界处截断
        if end < len(content):
            # 向前查找句号
            for i in range(end, max(start, end - 100), -1):
                if content[i] in '。！？\n':
                    end = i + 1
                    break

        chunk_content = content[start:end].strip()

        if chunk_content:
            doc = Document(
                content=chunk_content,
                metadata=metadata.copy(),
                document_type=document.document_type,
                source_path=document.source_path,
                title=document.title,
                url=document.url
            )
            doc.metadata['chunk_type'] = 'fixed'
            doc.metadata['start_index'] = start
            doc.metadata['chunk_index'] = chunk_index
            chunks.append(doc)
            chunk_index += 1

        # 移动起始位置（考虑重叠）
        start = end - overlap
        if start < 0:
            start = 0

    return chunks
