"""
Content List Processor - 处理 output 文件夹下的 content_list.json 文件
"""

import json
import logging
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.rag.models import (
    Document,
    DocumentChunk,
    DocumentMetadata,
    DocumentSource,
    ChunkMetadata,
    ContentType,
    ImageContent,
    TableContent,
    EquationContent,
)

logger = logging.getLogger(__name__)


class ContentListProcessor:
    """处理 content_list.json 文件的处理器"""

    def __init__(self, output_dir: str = "output"):
        """
        初始化处理器

        Args:
            output_dir: output 目录路径
        """
        self.output_dir = Path(output_dir)

    def find_content_list_files(self) -> List[Path]:
        """
        查找所有的 content_list.json 文件

        Returns:
            content_list.json 文件路径列表
        """
        files = []
        for root, dirs, filenames in os.walk(self.output_dir):
            for filename in filenames:
                if filename.endswith("_content_list.json"):
                    files.append(Path(root) / filename)
        return files

    def parse_content_list_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        解析 content_list.json 文件

        Args:
            file_path: 文件路径

        Returns:
            内容列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content_list = json.load(f)
            return content_list
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return []

    def extract_document_name(self, file_path: Path) -> str:
        """
        从文件路径提取文档名称

        Args:
            file_path: content_list.json 文件路径

        Returns:
            文档名称
        """
        # 例如: output/test_document/auto/test_document_content_list.json
        # 提取 test_document
        parts = file_path.parts
        for part in parts:
            if part != "output" and part != "auto" and not part.endswith("_content_list.json"):
                return part
        return file_path.stem.replace("_content_list", "")

    def find_source_file(self, doc_name: str) -> Optional[Path]:
        """
        查找原始文档文件

        Args:
            doc_name: 文档名称

        Returns:
            原始文件路径或None
        """
        # 在 output 目录下查找
        for ext in ['.pdf', '.docx', '.doc', '.txt', '.md']:
            file_path = self.output_dir / f"{doc_name}{ext}"
            if file_path.exists():
                return file_path
        return None

    def convert_content_to_document(self, content_list: List[Dict[str, Any]], doc_name: str) -> Document:
        """
        将 content_list 转换为 Document 对象

        Args:
            content_list: 内容列表
            doc_name: 文档名称

        Returns:
            Document 对象
        """
        # 查找原始文件
        source_file = self.find_source_file(doc_name)
        if source_file:
            file_stat = source_file.stat()
        else:
            file_stat = None

        # 创建文档源信息
        source = DocumentSource(
            file_path=str(source_file) if source_file else f"unknown/{doc_name}",
            file_name=source_file.name if source_file else f"{doc_name}.unknown",
            file_extension=source_file.suffix if source_file else "",
            file_size=file_stat.st_size if file_stat else 0,
            mime_type=self._get_mime_type(source_file) if source_file else None,
            created_at=datetime.fromtimestamp(file_stat.st_ctime) if file_stat else None,
            modified_at=datetime.fromtimestamp(file_stat.st_mtime) if file_stat else None
        )

        # 生成文档ID
        doc_id = self._generate_doc_id(content_list, doc_name)

        # 创建文档元数据
        metadata = DocumentMetadata(
            doc_id=doc_id,
            source=source,
            title=doc_name.replace('_', ' ').title(),
            language="zh",  # 默认中文
            parse_method="mineru",
            tags=[],
            custom_fields={
                "original_file": str(source_file) if source_file else None,
                "content_list_path": str(self.output_dir / doc_name / "auto" / f"{doc_name}_content_list.json")
            }
        )

        # 创建文档块
        chunks = []
        chunk_index = 0

        # 合并连续的文本块
        text_buffer = []
        text_metadata = []

        for item in content_list:
            content_type = item.get("type", "text")

            # 跳过丢弃的内容
            if content_type == "discarded":
                continue

            if content_type == "text":
                # 收集文本
                text_content = item.get("text", "").strip()
                if text_content:
                    text_buffer.append(text_content)
                    text_metadata.append(item)

            else:
                # 如果有文本缓冲，先创建文本块
                if text_buffer:
                    chunk = self._create_text_chunk(
                        doc_id,
                        chunk_index,
                        text_buffer,
                        text_metadata
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    text_buffer = []
                    text_metadata = []

                # 处理其他类型的内容
                chunk = self._create_multimodal_chunk(
                    doc_id,
                    chunk_index,
                    item,
                    content_type
                )
                if chunk:
                    chunks.append(chunk)
                    chunk_index += 1

        # 处理剩余的文本缓冲
        if text_buffer:
            chunk = self._create_text_chunk(
                doc_id,
                chunk_index,
                text_buffer,
                text_metadata
            )
            chunks.append(chunk)

        return Document(metadata=metadata, chunks=chunks)

    def _create_text_chunk(
        self,
        doc_id: str,
        chunk_index: int,
        text_buffer: List[str],
        metadata_list: List[Dict[str, Any]]
    ) -> DocumentChunk:
        """创建文本块"""
        content = "\n".join(text_buffer)

        # 使用第一个文本项的元数据作为代表
        first_meta = metadata_list[0] if metadata_list else {}
        last_meta = metadata_list[-1] if metadata_list else {}

        # 生成块ID
        chunk_id = f"{doc_id}_text_{chunk_index}"

        # 创建块元数据
        chunk_metadata = ChunkMetadata(
            chunk_id=chunk_id,
            doc_id=doc_id,
            chunk_index=chunk_index,
            page_number=first_meta.get("page_idx", 0),
            section_title=first_meta.get("text_level", ""),
            position={
                "first_bbox": first_meta.get("bbox", []),
                "last_bbox": last_meta.get("bbox", [])
            },
            tokens=len(content.split()),
            content_type=ContentType.TEXT
        )

        return DocumentChunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            content=content,
            content_type=ContentType.TEXT,
            metadata=chunk_metadata
        )

    def _create_multimodal_chunk(
        self,
        doc_id: str,
        chunk_index: int,
        item: Dict[str, Any],
        content_type: str
    ) -> Optional[DocumentChunk]:
        """创建多模态块"""
        # 生成块ID
        chunk_id = f"{doc_id}_{content_type}_{chunk_index}"

        # 创建块元数据
        chunk_metadata = ChunkMetadata(
            chunk_id=chunk_id,
            doc_id=doc_id,
            chunk_index=chunk_index,
            page_number=item.get("page_idx", 0),
            bbox=item.get("bbox", []),
            content_type=ContentType(content_type)
        )

        # 处理不同类型的内容
        chunk = None
        if content_type == "image":
            image_path = item.get("img_path")
            if image_path:
                image_content = ImageContent(
                    path=image_path,
                    caption=item.get("caption", ""),
                    description=item.get("text", ""),
                    ocr_text=item.get("text", "")
                )
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    content=item.get("text", f"Image: {image_path}"),
                    content_type=ContentType.IMAGE,
                    metadata=chunk_metadata,
                    image=image_content
                )

        elif content_type == "table":
            table_body = item.get("table_body", "")
            if table_body:
                table_content = TableContent(
                    markdown=table_body,
                    caption=item.get("caption", ""),
                    description=item.get("text", "")
                )
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    content=table_body,
                    content_type=ContentType.TABLE,
                    metadata=chunk_metadata,
                    table=table_content
                )

        elif content_type == "equation":
            equation_text = item.get("text", "")
            if equation_text:
                equation_content = EquationContent(
                    latex=equation_text,
                    alt_text=item.get("text", ""),
                    description=item.get("caption", "")
                )
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    content=equation_text,
                    content_type=ContentType.EQUATION,
                    metadata=chunk_metadata,
                    equation=equation_content
                )

        return chunk

    def _generate_doc_id(self, content_list: List[Dict[str, Any]], doc_name: str) -> str:
        """生成文档ID"""
        # 使用内容生成hash
        content_str = json.dumps(content_list, sort_keys=True)
        hash_obj = hashlib.md5(content_str.encode())
        return f"doc_{hash_obj.hexdigest()}"

    def _get_mime_type(self, file_path: Path) -> str:
        """获取MIME类型"""
        ext = file_path.suffix.lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.html': 'text/html',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif'
        }
        return mime_types.get(ext, 'application/octet-stream')

    def process_all_documents(self) -> List[Document]:
        """
        处理所有的 content_list.json 文件

        Returns:
            文档列表
        """
        documents = []
        content_files = self.find_content_list_files()

        logger.info(f"Found {len(content_files)} content_list.json files")

        for file_path in content_files:
            doc_name = self.extract_document_name(file_path)
            logger.info(f"Processing document: {doc_name}")

            # 解析内容列表
            content_list = self.parse_content_list_file(file_path)
            if not content_list:
                logger.warning(f"No content found in {file_path}")
                continue

            # 转换为文档对象
            document = self.convert_content_to_document(content_list, doc_name)
            documents.append(document)

            logger.info(f"  - Document ID: {document.metadata.doc_id}")
            logger.info(f"  - Chunks: {len(document.chunks)}")

        return documents

    def process_document(self, doc_name: str) -> Optional[Document]:
        """
        处理指定的文档

        Args:
            doc_name: 文档名称

        Returns:
            文档对象或None
        """
        # 构建content_list文件路径
        content_list_path = self.output_dir / doc_name / "auto" / f"{doc_name}_content_list.json"

        if not content_list_path.exists():
            logger.error(f"Content list file not found: {content_list_path}")
            return None

        # 解析内容列表
        content_list = self.parse_content_list_file(content_list_path)
        if not content_list:
            logger.error(f"No content found in {content_list_path}")
            return None

        # 转换为文档对象
        document = self.convert_content_to_document(content_list, doc_name)

        logger.info(f"Processed document: {doc_name}")
        logger.info(f"  - Document ID: {document.metadata.doc_id}")
        logger.info(f"  - Chunks: {len(document.chunks)}")

        return document