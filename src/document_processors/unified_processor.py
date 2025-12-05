"""
统一文档处理器
提供统一的接口处理所有支持的文档类型
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional

from src.models.document import Document
from src.document_processors import (
    DocumentProcessorRegistry,
    chunk_document
)
from src.document_processors.pdf_processor import PDFProcessor
from src.document_processors.text_processor import TextProcessor
from src.document_processors.docx_processor import DocxProcessor
from src.document_processors.ppt_processor import PPTProcessor
from src.document_processors.image_processor import ImageProcessor

logger = logging.getLogger(__name__)


# 注册所有处理器
def register_processors():
    """注册所有文档处理器"""
    DocumentProcessorRegistry.register('.pdf', PDFProcessor)
    DocumentProcessorRegistry.register('.txt', TextProcessor)
    DocumentProcessorRegistry.register('.md', TextProcessor)
    DocumentProcessorRegistry.register('.markdown', TextProcessor)
    DocumentProcessorRegistry.register('.rst', TextProcessor)
    DocumentProcessorRegistry.register('.rtf', TextProcessor)
    DocumentProcessorRegistry.register('.doc', DocxProcessor)
    DocumentProcessorRegistry.register('.docx', DocxProcessor)
    DocumentProcessorRegistry.register('.ppt', PPTProcessor)
    DocumentProcessorRegistry.register('.pptx', PPTProcessor)
    DocumentProcessorRegistry.register('.png', ImageProcessor)
    DocumentProcessorRegistry.register('.jpg', ImageProcessor)
    DocumentProcessorRegistry.register('.jpeg', ImageProcessor)
    DocumentProcessorRegistry.register('.gif', ImageProcessor)
    DocumentProcessorRegistry.register('.bmp', ImageProcessor)
    DocumentProcessorRegistry.register('.tiff', ImageProcessor)

    logger.info(f"已注册支持的文档类型: {DocumentProcessorRegistry.get_supported_extensions()}")


# 初始化处理器
register_processors()


async def process(
    file_path: str,
    chunk: bool = True,
    chunk_strategy: str = 'auto',
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    extract_images: bool = False,
    use_vision: bool = False,
    **kwargs
) -> List[Document]:
    """
    统一文档处理接口

    Args:
        file_path: 文件路径
        chunk: 是否分块（默认True）
        chunk_strategy: 分块策略 ('auto', 'paragraph', 'title', 'page', 'semantic')
        chunk_size: 块大小
        chunk_overlap: 块间重叠
        extract_images: 是否提取PDF中的图片（仅对PDF有效）
        use_vision: 是否使用视觉模型（仅对PDF有效，启用v2内存buffer模式）
        **kwargs: 其他参数（如PDF的mode、dpi等）

    Returns:
        List[Document]: 处理后的文档或文档块列表
    """
    path_obj = Path(file_path)

    if not path_obj.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    file_ext = path_obj.suffix.lower()

    # 获取处理器
    # 对于PDF，如果use_vision=True，将通过mode参数传递给PDFProcessor
    processor_class = DocumentProcessorRegistry.get_processor(file_ext)

    # 如果是PDF且use_vision=True，添加到kwargs
    if use_vision and file_ext == '.pdf':
        kwargs['mode'] = 'v2_memory_buffer'

    if not processor_class:
        raise ValueError(f"不支持的文件类型: {file_ext}")

    logger.info(f"开始处理文档: {file_path} (使用{processor_class.__name__})")

    # 实例化处理器
    processor = processor_class()

    documents = await processor.process(file_path, **kwargs)

    logger.info(f"文档处理完成，共{len(documents)}个文档")

    # 分块处理
    if chunk and len(documents) > 0:
        logger.info(f"开始分块，策略: {chunk_strategy}")
        all_chunks = []

        for doc in documents:
            # 检查是否已经分页（如PPT每页一个文档）
            if doc.metadata.get('page_number') or doc.metadata.get('slide_number'):
                # 已经是分页的，不需要再分块
                all_chunks.append(doc)
            else:
                # 需要分块
                try:
                    chunks = chunk_document(
                        doc,
                        strategy=chunk_strategy,
                        chunk_size=chunk_size,
                        overlap=chunk_overlap
                    )
                    all_chunks.extend(chunks)
                except Exception as e:
                    logger.error(f"分块失败: {e}")
                    # 分块失败时使用原文档
                    all_chunks.append(doc)

        documents = all_chunks
        logger.info(f"分块完成，共{len(documents)}个块")

    # 计算总字数
    total_words = sum(len(doc.content) for doc in documents)
    logger.info(f"处理完成，总字符数: {total_words}")

    return documents


async def process_batch(
    file_paths: List[str],
    chunk: bool = True,
    chunk_strategy: str = 'auto',
    max_concurrent: int = 3,
    **kwargs
) -> List[List[Document]]:
    """
    批量处理文档

    Args:
        file_paths: 文件路径列表
        chunk: 是否分块
        chunk_strategy: 分块策略
        max_concurrent: 最大并发数
        **kwargs: 其他参数

    Returns:
        List[List[Document]]: 每个文件的文档列表
    """
    import asyncio

    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_single(file_path: str) -> List[Document]:
        async with semaphore:
            try:
                return await process(file_path, chunk=chunk, chunk_strategy=chunk_strategy, **kwargs)
            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")
                return []

    # 并发处理
    tasks = [process_single(fp) for fp in file_paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 过滤异常结果
    valid_results = []
    for result in results:
        if isinstance(result, list):
            valid_results.append(result)
        else:
            logger.error(f"处理异常: {result}")
            valid_results.append([])

    return valid_results


def get_supported_formats() -> Dict[str, str]:
    """
    获取支持的文档格式

    Returns:
        Dict[str, str]: 格式到描述的映射
    """
    return {
        '.pdf': 'PDF文档',
        '.txt': '纯文本文件',
        '.md': 'Markdown文档',
        '.rst': 'reStructuredText文档',
        '.rtf': '富文本格式',
        '.doc': 'Word文档 (旧版)',
        '.docx': 'Word文档',
        '.ppt': 'PowerPoint文档 (旧版)',
        '.pptx': 'PowerPoint文档',
        '.png': 'PNG图片',
        '.jpg': 'JPG图片',
        '.jpeg': 'JPEG图片',
        '.gif': 'GIF图片',
        '.bmp': 'BMP图片',
        '.tiff': 'TIFF图片',
    }


def detect_file_type(file_path: str) -> Optional[str]:
    """
    检测文件类型

    Args:
        file_path: 文件路径

    Returns:
        Optional[str]: 文件扩展名（带点），未知返回None
    """
    path_obj = Path(file_path)
    if path_obj.exists():
        return path_obj.suffix.lower()
    return None


# 示例用法
if __name__ == "__main__":
    import asyncio

    async def example():
        # 处理单个文档
        docs = await process("example.pdf")
        print(f"处理了{len(docs)}个文档块")

        # 批量处理
        docs_list = await process_batch([
            "doc1.pdf",
            "doc2.docx",
            "doc3.txt"
        ], max_concurrent=3)
        print(f"批量处理完成")

    asyncio.run(example())
