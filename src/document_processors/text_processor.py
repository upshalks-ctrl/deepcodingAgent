"""
文本文档处理器
支持TXT、Markdown等纯文本格式
"""
import logging
from pathlib import Path
from typing import List

from src.models.document import Document
from src.document_processors import create_document_metadata

logger = logging.getLogger(__name__)


class TextProcessor:
    """文本文档处理器"""

    async def process(self, file_path: str, **kwargs) -> List[Document]:
        """
        处理文本文档

        Args:
            file_path: 文件路径
            **kwargs: 额外参数

        Returns:
            List[Document]: 文档列表
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        logger.info(f"处理文本文件: {file_path}")

        # 读取文件内容
        path_obj = Path(file_path)
        encoding = kwargs.get('encoding', 'utf-8')

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            for enc in ['gbk', 'gb2312', 'latin-1']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        content = f.read()
                    logger.info(f"使用{enc}编码读取")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise RuntimeError("无法识别文件编码")

        # 判断文档类型
        doc_type = 'text'
        if path_obj.suffix.lower() == '.md':
            doc_type = 'markdown'
        elif path_obj.suffix.lower() in ['.rst', '.rtf']:
            doc_type = path_obj.suffix.lower()[1:]

        # 创建元数据
        metadata = create_document_metadata(
            processor='TextProcessor',
            encoding=encoding,
            word_count=len(content),
            line_count=len(content.splitlines())
        )

        # 创建文档
        document = Document(
            content=content,
            metadata=metadata,
            document_type = doc_type,
            source_path = file_path,
            title = path_obj.name,
            url = f"text://{path_obj.name}"
        )

        logger.info(f"文本处理完成，共{len(content)}字符")
        return [document]

