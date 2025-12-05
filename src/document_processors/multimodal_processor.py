"""
多模态文档处理系统

支持多种文档格式及对应的处理器：
- PDF文件 (.pdf) -> PDFProcessor
- PPT文件 (.ppt, .pptx) -> PPTProcessor
- DOCX文件 (.doc, .docx) -> DocxProcessor
- 图片文件 (.jpg, .jpeg, .png, .tiff, .tif, .bmp) -> ImageProcessor
- 其他文件 (.txt, .md, .rst, .rtf, .csv, .xlsx, .xls) -> TextProcessor (默认)

特性：
1. 支持单个文件或整个文件夹的批量解析
2. 智能合并小文档块
3. 统一接口处理所有文档类型
4. 自动文件类型检测和处理器选择
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set
from dataclasses import dataclass
import asyncio
import inspect

from src.models.document import Document as DocModel
from src.rag import Resource
from src.rag.enhanced_qdrant import EnhancedQdrantRetriever


@dataclass
class ProcessingOptions:
    """处理选项"""
    chunk_size: int = 800  # 合并的chunk大小阈值
    merge_threshold: float = 1.2  # 合并阈值：content < chunk_size * merge_threshold
    supported_extensions: Set[str] = None  # 支持的文件扩展名

    def __post_init__(self):
        if self.supported_extensions is None:
            self.supported_extensions = {
                '.pdf', '.ppt', '.pptx', '.doc', '.docx',
                '.txt', '.md', '.rst', '.rtf',
                '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp',
                '.csv', '.xlsx', '.xls'
            }


class MultimodalProcessor:
    """多模态文档处理器"""

    def __init__(self, options: Optional[ProcessingOptions] = None):
        self.options = options or ProcessingOptions()
        self.logger = logging.getLogger("multimodal_processor")

    def _detect_document_type(self, file_path: Path) -> Optional[str]:
        """
        检测文档类型并返回对应的处理器类

        处理器映射规则：
        - PDF文件 -> PDF处理器
        - PPT文件 -> PPT处理器
        - 图片文件 -> Image处理器
        - DOCX文件 -> Docx处理器
        - 其他所有文件 -> Text处理器（默认）

        Args:
            file_path: 文件路径

        Returns:
            处理器类型字符串
        """
        extension = file_path.suffix.lower()

        # 明确指定类型的映射
        specialized_types = {
            '.pdf': 'pdf',
            '.ppt': 'ppt',
            '.pptx': 'ppt',
            '.doc': 'docx',
            '.docx': 'docx',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.tiff': 'image',
            '.tif': 'image',
            '.bmp': 'image',
        }

        # 如果是明确指定的类型，直接返回
        if extension in specialized_types:
            return specialized_types[extension]

        # 对于其他文件（如txt, md, rst, rtf, csv, xlsx, xls等）
        # 统一使用Text处理器
        if extension in self.options.supported_extensions:
            self.logger.debug(f"文件 {file_path.name} 使用默认Text处理器")
            return 'text'

        # 不支持的文件类型
        self.logger.warning(f"不支持的文件类型: {extension}")
        return None

    def _scan_directory(self, path: Union[str, Path]) -> List[Path]:
        """
        扫描目录下的所有支持的文件

        Args:
            path: 目录路径

        Returns:
            文件路径列表
        """
        path = Path(path)

        if path.is_file():
            # 如果是单个文件，直接返回
            if path.suffix.lower() in self.options.supported_extensions:
                return [path]
            else:
                self.logger.warning(f"不支持的文件类型: {path}")
                return []

        if not path.is_dir():
            self.logger.error(f"路径不存在: {path}")
            return []

        files = []
        for ext in self.options.supported_extensions:
            files.extend(path.rglob(f"*{ext}"))

        # 过滤隐藏文件和临时文件
        files = [
            f for f in files
            if not f.name.startswith('.') and not f.name.startswith('~')
        ]

        self.logger.info(f"在 {path} 中发现 {len(files)} 个支持的文件")
        return files

    def _get_processor(self, doc_type: str):
        """
        获取对应的处理器

        Args:
            doc_type: 文档类型

        Returns:
            处理器实例
        """
        # 注意：这里需要根据实际的处理器类来导入
        # 这里使用字符串到类的映射
        processors_map = {
            'pdf': 'PDFProcessor',
            'ppt': 'PPTProcessor',
            'docx': 'DocxProcessor',
            'text': 'TextProcessor',
            'image': 'ImageProcessor',
        }

        processor_class_name = processors_map.get(doc_type)
        if not processor_class_name:
            raise ValueError(f"不支持的文档类型: {doc_type}")

        # 动态导入处理器类
        try:
            if doc_type == 'pdf':
                from src.document_processors.pdf_processor import PDFProcessor
                return PDFProcessor()
            elif doc_type == 'ppt':
                from src.document_processors.ppt_processor import PPTProcessor
                return PPTProcessor()
            elif doc_type == 'docx':
                from src.document_processors.docx_processor import DocxProcessor
                return DocxProcessor()
            elif doc_type == 'text':
                from src.document_processors.text_processor import TextProcessor
                return TextProcessor()
            elif doc_type == 'image':
                from src.document_processors.image_processor import ImageProcessor
                return ImageProcessor()
        except ImportError as e:
            self.logger.error(f"无法导入处理器 {processor_class_name}: {e}")
            raise

        raise ValueError(f"无法创建处理器: {doc_type}")

    def _merge_documents(self, documents: List[DocModel]) -> List[DocModel]:
        """
        合并小文档块

        合并规则：
        1. 只有 source_path, title, url 相同的 document 才会被合并
        2. 只有 content < chunk_size * merge_threshold 的 document 才会被合并
        3. 只合并不同 document 的 content，保持原有 metadata

        Args:
            documents: 原始文档列表

        Returns:
            合并后的文档列表
        """
        if not documents:
            return []

        self.logger.info(f"开始合并 {len(documents)} 个文档块")

        # 按 (source_path, title, url) 分组
        grouped: Dict[str, List[DocModel]] = {}
        for doc in documents:
            source_path = doc.metadata.get('source_path', '')
            title = doc.metadata.get('title', '')
            url = doc.metadata.get('url', source_path)
            group_key = f"{source_path}:{title}:{url}"

            if group_key not in grouped:
                grouped[group_key] = []
            grouped[group_key].append(doc)

        merged_documents = []
        merge_count = 0
        total_original = len(documents)

        for group_key, group_docs in grouped.items():
            if len(group_docs) == 1:
                # 单个文档直接添加
                merged_documents.append(group_docs[0])
                continue

            # 按 chunk_index 排序
            group_docs.sort(key=lambda x: x.metadata.get('chunk_index', 0))

            current_doc = None
            current_content_parts = []

            for doc in group_docs:
                if current_doc is None:
                    # 第一个文档
                    current_doc = doc
                    current_content_parts.append(doc.content)
                else:
                    # 检查是否可以合并
                    potential_size = sum(len(part) for part in current_content_parts) + len(doc.content)

                    if potential_size <= self.options.chunk_size * self.options.merge_threshold:
                        # 可以合并 - 只合并 content，不合并 metadata
                        current_content_parts.append(doc.content)
                    else:
                        # 不能合并，保存当前合并的文档
                        merged_content = '\n\n'.join(current_content_parts)

                        # 使用第一个文档的 metadata
                        merged_metadata = current_doc.metadata.copy()
                        merged_metadata['is_merged'] = True
                        merged_metadata['merged_from_chunks'] = [
                            d.metadata.get('chunk_index', 0) for d in group_docs[:group_docs.index(current_doc) + 1]
                        ]
                        merged_metadata['chunk_size'] = len(merged_content)

                        merged_doc = DocModel(
                            content=merged_content,
                            metadata=merged_metadata,
                            document_type=current_doc.document_type,
                            source_path=current_doc.source_path,
                            title=current_doc.title,
                            url=current_doc.url

                        )
                        merged_documents.append(merged_doc)
                        merge_count += 1

                        # 开始新的合并
                        current_doc = doc
                        current_content_parts = [doc.content]

            # 处理最后一组合并
            if current_doc is not None and current_content_parts:
                merged_content = '\n\n'.join(current_content_parts)

                merged_metadata = current_doc.metadata.copy()
                merged_metadata['is_merged'] = True
                merged_metadata['merged_from_chunks'] = [
                    d.metadata.get('chunk_index', 0) for d in group_docs[group_docs.index(current_doc):]
                ]
                merged_metadata['chunk_size'] = len(merged_content)

                merged_doc = DocModel(
                    content=merged_content,
                    metadata=merged_metadata,
                    document_type=current_doc.document_type,
                    source_path=current_doc.source_path,
                    title=current_doc.title,
                    url=current_doc.url
                )
                merged_documents.append(merged_doc)
                merge_count += 1

        self.logger.info(
            f"合并完成: {total_original} -> {len(merged_documents)} "
            f"(合并了 {merge_count} 次)"
        )

        return merged_documents

    async def process(
        self,
        path: Union[str, Path],
        **kwargs
    ) -> List[DocModel] | None:
        """
        处理单个文件或整个文件夹

        Args:
            path: 文件路径或文件夹路径
            **kwargs: 传递给处理器的参数

        Returns:
            合并后的文档列表
        """
        path = Path(path)
        all_documents = []

        # 1. 扫描文件
        files = self._scan_directory(path)

        if not files:
            self.logger.warning(f"没有找到可处理的文件: {path}")
            return None

        self.logger.info(f"开始处理 {len(files)} 个文件")

        # 2. 逐个处理文件
        for file_path in files:
            try:
                # 检测文档类型
                doc_type = self._detect_document_type(file_path)

                if not doc_type:
                    self.logger.warning(f"不支持的文件类型: {file_path}")
                    continue

                # 获取处理器
                processor = self._get_processor(doc_type)

                # 调用处理器的 process 方法
                # 注意：这里假设返回的是已经切割好的 [DocModel] 列表
                if hasattr(processor, 'process'):
                    result = processor.process(str(file_path), **kwargs)

                    # 如果是协程对象，需要 await
                    if inspect.iscoroutine(result):
                        result = await result

                    # result 应该是 List[DocModel]
                    if isinstance(result, list):
                        all_documents.extend(result)
                        self.logger.debug(f"处理文件 {file_path.name}: {len(result)} 个块")
                    else:
                        self.logger.error(f"处理器返回类型错误: {type(result)}")

            except Exception as e:
                self.logger.error(f"处理文件失败 {file_path}: {e}", exc_info=True)
                continue

        # 3. 合并小文档块
        if all_documents:
            merged_documents = self._merge_documents(all_documents)
            self.logger.info(f"处理完成: {len(files)} 个文件 -> {len(merged_documents)} 个合并文档")
            return merged_documents
        else:
            self.logger.warning("没有成功处理任何文件")
            return []


# 便捷函数
async def process_documents(
    path: Union[str, Path],
    chunk_size: int = 800,
    merge_threshold: float = 1.2,
    **kwargs
) -> List[DocModel]|None:
    """
    处理单个文件或整个文件夹

    Args:
        path: 文件路径或文件夹路径
        chunk_size: 合并的chunk大小阈值
        merge_threshold: 合并阈值
        **kwargs: 传递给处理器的参数

    Returns:
        合并后的文档列表
    """
    options = ProcessingOptions(
        chunk_size=chunk_size,
        merge_threshold=merge_threshold
    )

    processor = MultimodalProcessor(options=options)
    return await processor.process(path, **kwargs)


# 示例用法
if __name__ == "__main__":
    import asyncio

    async def example():
        result = await process_documents("D:\\code\\PythonWorkPath\\deepcodeagent1\\test\\test_data\\test.txt")
        vector_store = EnhancedQdrantRetriever()
        vector_store.create_index()
        vector_store.embed_documents(result, "user123","123")
        query_content = vector_store.query_relevant_documents("你好",[Resource(doc_id="D:\\code\\PythonWorkPath\\deepcodeagent1\\test\\test_data\\test.txt_user123_123")])
        for content in query_content:
            print(content)
        print(f"处理完成: {len(result)} 个文档")
        for doc in result:
            print(f"  - {doc.title}: {len(doc.content)} 字符")
    asyncio.run(example())
