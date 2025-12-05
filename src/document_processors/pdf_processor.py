"""
PDF处理器
整合v1和v2版本，支持多种处理方式：
- v1: 临时文件模式，视觉模型逐页处理
- v2: 内存buffer模式，Base64编码，批量处理
"""

import logging
from pathlib import Path
from typing import List, Optional

from src.models.document import Document
from src.document_processors import create_document_metadata

logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF文档处理器 - 整合v1和v2版本"""

    async def process(self, file_path: str, **kwargs) -> List[Document]:
        """
        处理PDF文档

        Args:
            file_path: PDF文件路径
            **kwargs: 额外参数
                - mode: 处理模式 ('v1_temp_file', 'v2_memory_buffer', 默认'v2_memory_buffer')
                - dpi: 图片DPI（默认200）
                - languages: 识别语言（默认['zh', 'en']）
                - combine_pages: 是否合并所有页面为一个Markdown文档（默认True）
                - chunk_after: 是否在处理后自动按标题切分（默认True）

        Returns:
            List[Document]: 文档列表
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"PDF文件不存在: {file_path}")

        logger.info(f"开始处理PDF: {file_path}")

        # 获取处理模式
        mode = kwargs.get('mode', 'v2_memory_buffer')

        # v2模式（推荐）：内存buffer + base64编码
        if mode == 'v2_memory_buffer':
            try:
                return await self._process_with_vision_combined_memory(file_path, **kwargs)
            except ImportError as e:
                logger.warning(f"视觉模型方法依赖缺失: {e}")

            # 方法3: 使用pdfplumber
            try:
                return await self._process_with_pdfplumber(file_path, **kwargs)
            except ImportError:
                logger.warning("pdfplumber未安装")
            except Exception as e:
                logger.error(f"pdfplumber处理失败: {e}")

            raise RuntimeError("所有PDF处理方法都失败了")

        else:
            raise ValueError(f"不支持的处理模式: {mode}")

    def _create_fallback_document(self, file_path: str, error_msg: str) -> List[Document]:
        """创建错误回退文档"""
        metadata = create_document_metadata(
            file_path=file_path,
            document_type='pdf',
            url=f"pdf://{Path(file_path).name}",
            processor='ErrorHandler'
        )

        document = Document(
            content=f"[PDF处理失败: {error_msg}]",
            metadata=metadata
        )
        document.metadata['error'] = error_msg
        return [document]

    async def _process_with_vision_combined_memory(self, file_path: str, **kwargs) -> List[Document]:
        """
        使用视觉模型处理PDF v2（内存buffer + base64编码）
        将所有页面合并为一个Markdown文档

        Args:
            file_path: PDF文件路径
            **kwargs: 额外参数
                - dpi: 图片DPI（默认200）
                - languages: 识别语言（默认['zh', 'en']）
                - combine_pages: 是否合并所有页面（默认True）
                - chunk_after: 是否在处理后自动按标题切分（默认True）

        Returns:
            List[Document]: 返回1个完整的Markdown文档
        """
        try:
            import fitz  # PyMuPDF
            import base64
        except ImportError:
            raise ImportError("请安装PyMuPDF: pip install PyMuPDF")

        logger.info("使用视觉模型处理PDF（v2内存优化模式）")

        # 初始化视觉模型
        llm_vision = None
        try:
            from src.llms.llm import get_llm_by_type
            llm_vision = get_llm_by_type("vision")
            logger.info("已初始化视觉模型")
        except Exception as e:
            logger.warning(f"无法初始化视觉模型: {e}")

        # 获取参数
        dpi = kwargs.get('dpi', 200)
        languages = kwargs.get('languages', ['zh', 'en'])
        language_str = '+'.join(languages)

        # 打开PDF
        doc = fitz.open(file_path)

        # 创建元数据
        metadata = create_document_metadata(
            processor='VisionModel',
            total_pages=len(doc),
            dpi=dpi,
        )

        # 合并所有页面为一个Markdown文档
        logger.info(f"开始合并 {len(doc)} 个页面为Markdown文档（使用内存buffer）...")

        # 收集所有页面的图片（内存中）
        all_images_base64 = []

        for page_num in range(len(doc)):
            logger.info(f"正在转换第 {page_num + 1}/{len(doc)} 页为图片...")

            page = doc[page_num]

            # 将页面转换为图片（保存在内存中）
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            # 转换为PNG字节
            img_bytes = pix.tobytes("png")

            # Base64编码
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            all_images_base64.append(img_base64)

        doc.close()

        # 如果有视觉模型，一次性处理所有页面
        full_markdown = ""
        if llm_vision:
            try:
                logger.info(f"开始使用视觉模型分析 {len(all_images_base64)} 页...")

                # 构建多图片消息
                content = [
                    {
                        "type": "text",
                        "text": f"""请仔细分析这个PDF的所有页面（共{len(all_images_base64)}页），提取其中的所有文本内容。

要求：
1. 识别所有文字内容，包括中文和英文
2. 保持原有的段落结构和格式
3. 如果是表格，请用Markdown表格格式表示
4. 如果有标题、段落、列表等，请保持层次结构，使用Markdown标记
5. 不要遗漏任何文字信息
6. 如果内容较少，可以适当补充说明
7. 确保输出是纯Markdown格式，不要包含任何解释或前缀
8. 按页面顺序组织内容，并在每页内容前添加页码标记

请直接返回Markdown格式的文本内容。"""
                    }
                ]

                # 添加所有页面的图片（使用data URL格式）
                for img_base64 in all_images_base64:
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_base64}"
                        }
                    })  # type: ignore[arg-type]

                messages = [
                    {
                        "role": "user",
                        "content": content
                    }
                ]

                response = await llm_vision.ainvoke(messages)

                # 处理响应
                if hasattr(response, 'content'):
                    content_text = response.content
                else:
                    content_text = str(response)

                if isinstance(content_text, list):
                    if content_text and isinstance(content_text[0], dict) and 'content' in content_text[0]:
                        full_markdown = content_text[0]['content']
                    else:
                        full_markdown = str(content_text[0]) if content_text else ""
                else:
                    full_markdown = content_text or ""

                # 如果内容为空，添加占位符
                if not full_markdown.strip():
                    full_markdown = "[PDF内容为空或无法识别]"

                logger.info("视觉模型分析完成")

            except Exception as e:
                logger.error(f"视觉模型分析失败: {e}")
                full_markdown = f"[PDF分析失败: {e}]\n\n共{len(all_images_base64)}页"
        else:
            logger.warning("未配置视觉模型，使用默认标记")
            full_markdown = f"[请安装并配置视觉模型]\n\n共{len(all_images_base64)}页"

        # 如果需要自动切分
        if kwargs.get('chunk_after', True):
            logger.info("开始按标题切分Markdown文档...")
            from src.document_processors import chunk_document

            document = Document(
                content=full_markdown,
                metadata=metadata.copy(),
                document_type='pdf',
                source_path=file_path,
                title=Path(file_path).name,
                url=f"pdf://{Path(file_path).name}"
            )
            document.metadata['total_pages'] = len(all_images_base64)
            document.metadata['word_count'] = len(full_markdown)
            document.metadata['processing_method'] = 'vision_model_combined_memory'
            document.metadata['format'] = 'markdown'
            document.metadata['chunk_strategy'] = 'title'

            # 切分文档
            chunks = chunk_document(
                document,
                strategy='title',
                chunk_size=kwargs.get('chunk_size', 2000),
                overlap=kwargs.get('chunk_overlap', 200)
            )

            logger.info(f"文档切分为 {len(chunks)} 个块")
            return chunks

        # 创建完整的Markdown文档
        document = Document(
            content=full_markdown,
            metadata=metadata.copy(),
            document_type = 'pdf',
            source_path = file_path,
            title = Path(file_path).name,
            url = f"pdf://{Path(file_path).name}"
        )
        document.metadata['total_pages'] = len(all_images_base64)
        document.metadata['word_count'] = len(full_markdown)
        document.metadata['processing_method'] = 'vision_model_combined_memory'
        document.metadata['format'] = 'markdown'
        document.metadata['chunk_strategy'] = 'title'

        logger.info(f"视觉模型处理完成，生成完整Markdown文档，共 {len(full_markdown)} 字符")
        return [document]



    async def _process_with_fitz(self, file_path: str, **kwargs) -> List[Document]:
        """使用PyMuPDF处理PDF"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("请安装PyMuPDF: pip install PyMuPDF")

        logger.info("使用PyMuPDF处理PDF")

        documents = []
        metadata = create_document_metadata(
            file_path=file_path,
            document_type='pdf',
            url=f"pdf://{Path(file_path).name}",
            processor='PyMuPDF'
        )

        # 打开PDF
        doc = fitz.open(file_path)

        for page_num in range(len(doc)):
            page = doc[page_num]

            # 提取文本
            text = page.get_text()

            # 如果文本为空，尝试OCR
            if not text.strip():
                try:
                    import ocrmypdf
                    # 这里需要额外的OCR处理逻辑
                    logger.warning(f"第{page_num+1}页需要OCR，但未实现")
                except ImportError:
                    logger.warning("OCR未安装，跳过空白页")
                    continue

            doc_obj = Document(
                content=text,
                metadata=metadata.copy()
            )
            doc_obj.metadata['page_number'] = page_num + 1
            doc_obj.metadata['word_count'] = len(text)
            documents.append(doc_obj)

        doc.close()

        logger.info(f"PyMuPDF处理完成，共{len(documents)}页")
        return documents

    async def _process_with_pdfplumber(self, file_path: str, **kwargs) -> List[Document]:
        """使用pdfplumber处理PDF"""
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("请安装pdfplumber: pip install pdfplumber")

        logger.info("使用pdfplumber处理PDF")

        documents = []
        metadata = create_document_metadata(
            file_path=file_path,
            document_type='pdf',
            url=f"pdf://{Path(file_path).name}",
            processor='pdfplumber'
        )

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # 提取文本
                text = page.extract_text() or ""

                doc = Document(
                    content=text,
                    metadata=metadata.copy(),
                    document_type = 'pdf',
                    source_path = file_path,
                    title = Path(file_path).name,
                    url = f"pdf://{Path(file_path).name}"
                )
                doc.metadata['page_number'] = page_num + 1
                doc.metadata['word_count'] = len(text)
                documents.append(doc)

        logger.info(f"pdfplumber处理完成，共{len(documents)}页")
        return documents

