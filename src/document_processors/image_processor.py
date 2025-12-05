"""
图片处理器
支持PNG、JPG等图片格式
使用视觉模型理解图片内容
"""
import base64
import io
import logging
import os
from pathlib import Path
from typing import List, Optional

from PIL import Image

from src.models.document import Document
from src.document_processors import create_document_metadata

logger = logging.getLogger(__name__)
# This Default Prompt Using Chinese and could be changed to other languages.
DEFAULT_PROMPT = """使用markdown语法，将图片中识别到的内容转换为markdown格式输出。你必须做到：
1. 输出和用户提问相同的语言。
2. 不要解释和输出无关的文字，直接输出图片中的内容。例如，严禁输出 "以下是我根据图片内容生成的markdown文本："这样的例子，而是应该直接输出markdown。
3. 内容不要包含在```markdown ```中、段落公式使用 $$ $$ 的形式、行内公式使用 $ $ 的形式。
4. 对于图表、图表、表格等结构化内容，请使用适当的markdown语法进行表示。
5. 对于OCR文本，请准确提取并保持原始格式。
6. 对于纯图像内容，请提供详细的文字描述。
再次强调，不要解释和输出无关的文字，直接输出图片中的内容。
"""
DEFAULT_ROLE_PROMPT = """你是一个图像内容解析器，能够准确识别图像中的文本、图表、表格和其他视觉元素，并将其转换为结构化的markdown格式。
"""

class ImageProcessor:
    """图片文档处理器"""

    def __init__(self):
        """初始化图片处理器"""
        self.llm_vision = None
        try:
            from src.llms.llm import get_llm_by_type
            self.llm_vision = get_llm_by_type("vision")
            logger.info("成功初始化视觉模型")
        except Exception as e:
            logger.warning(f"无法初始化视觉模型: {e}")

    async def process(self, file_path: str, **kwargs) -> List[Document]:
        """
        处理图片文档

        Args:
            file_path: 图片路径
            **kwargs: 额外参数
                - describe: 是否使用视觉模型描述图片（默认True）

        Returns:
            List[Document]: 文档列表（每个图片一个）
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"图片文件不存在: {file_path}")

        logger.info(f"处理图片文件: {file_path}")

        path_obj = Path(file_path)

        # 创建元数据
        metadata = create_document_metadata(
            processor='ImageProcessor',
            image_format=path_obj.suffix.lower()[1:],
            file_size=path_obj.stat().st_size
        )

        document = Document(
            content="",  # 稍后填入图片描述
            metadata=metadata,
            document_type = 'image',
            source_path = file_path,
            title = path_obj.name,
            url = f"image://{path_obj.name}"
        )

        # 使用视觉模型描述图片
        describe = kwargs.get('describe', True)
        if describe:
            try:
                description = await self._describe_image(file_path)
                document.content = description
                metadata['has_description'] = True
                logger.info(f"图片描述完成: {len(description)}字符")
            except Exception as e:
                logger.error(f"图片描述失败: {e}")
                document.content = f"[图片文件: {path_obj.name}]"
                metadata['has_description'] = False
        else:
            document.content = f"[图片文件: {path_obj.name}]"
            metadata['has_description'] = False

        metadata['word_count'] = len(document.content)

        logger.info(f"图片处理完成: {path_obj.name}")
        return [document]

    async def _describe_image(self, file_path: str) -> str:
        """
        使用视觉模型描述图片

        Args:
            file_path: 图片路径

        Returns:
            str: 图片描述文本
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")

        if not self.llm_vision:
            logger.error("视觉模型未初始化，无法描述图片")
            return f"[图片文件: {Path(file_path).name}]"
        try:
            # 获取图像MIME类型
            mime_type = self._get_image_mime_type(file_path)

            # 读取并编码图像
            base64_encoded = self._compress_image_to_base64(file_path)
            # 调用LLM API处理图像
            response = self.llm_vision.invoke(
                [
                    {"role": "system", "content": DEFAULT_ROLE_PROMPT},
                    {"role": "user", "content": [
                        {"type": "text", "text": "详细描述图片中的内容"},
                        {"type": "image_url",
                         "image_url": {
                            "url": f"data:{mime_type};base64,{base64_encoded}"
                            }
                         }
                    ]}
                ]
            )
            description = response.content

            logger.debug(f"图片描述生成成功: {description[:100]}...")
            return description

        except Exception as e:
            logger.error(f"视觉模型描述图片失败: {e}")
            return f"[图片文件: {Path(file_path).name}]"

    async def extract_images_from_pdf(self, pdf_path: str) -> List[Document]:
        """
        从PDF中提取图片

        Args:
            pdf_path: PDF路径

        Returns:
            List[Document]: 提取的图片文档列表
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("请安装PyMuPDF: pip install PyMuPDF")

        logger.info(f"从PDF提取图片: {pdf_path}")

        doc = fitz.open(pdf_path)
        images = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # 获取页面中的图片
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                try:
                    # 获取图片数据
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)

                    # 如果是CMYK格式，转换为RGB
                    if pix.n - pix.alpha < 4:
                        img_data = pix.tobytes("png")
                    else:
                        pix1 = fitz.Pixmap(fitz.csRGB, pix)
                        img_data = pix1.tobytes("png")
                        pix1 = None

                    # 保存临时图片文件
                    temp_dir = Path("temp_images")
                    temp_dir.mkdir(exist_ok=True)
                    temp_img_path = temp_dir / f"page{page_num+1}_img{img_index+1}.png"

                    with open(temp_img_path, "wb") as f:
                        f.write(img_data)

                    # 处理图片
                    img_doc = await self.process(str(temp_img_path))
                    if img_doc:
                        img_doc[0].metadata['source_pdf'] = pdf_path
                        img_doc[0].metadata['page_number'] = page_num + 1
                        img_doc[0].metadata['image_index'] = img_index + 1
                        images.append(img_doc[0])

                    # 清理临时文件
                    temp_img_path.unlink(missing_ok=True)

                except Exception as e:
                    logger.error(f"提取第{page_num+1}页第{img_index+1}张图片失败: {e}")

        doc.close()

        logger.info(f"从PDF提取了{len(images)}张图片")
        return images

    def _compress_image_to_base64(self, image_path, max_size=1536, jpeg_quality=80, target_format='JPEG'):
        """
        读取图片，调整大小，压缩为指定格式，并转换为Base64编码。

        Args:
            image_path (str): 图片文件路径。
            max_size (int): 图片长边的最大像素值。如果图片本身小于此值则不调整。
                            建议设置为 1024, 1536 或 2048。
            jpeg_quality (int): JPEG 压缩质量 (1-100, 越高越好)。建议 75-85。
            target_format (str): 目标格式，通常为 'JPEG'。如果是透明图且必须保留透明度，可用 'PNG'。

        Returns:
            str: 压缩后的图片 Base64 字符串。
        """
        try:
            # 1. 打开图片
            with Image.open(image_path) as img:
                # 获取原始尺寸和大小用于对比
                original_size_bytes = os.path.getsize(image_path)
                print(f"原始图片: {img.format}, 尺寸: {img.size}, 大小: {original_size_bytes / 1024:.2f} KB")

                # 2. 智能调整尺寸 (Resizing)
                # 使用 thumbnail 方法，它会保持纵横比进行缩放，且只有当原图大于 max_size 时才缩小。
                # Image.Resampling.LANCZOS 是高质量的重采样滤波器。
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

                # 3. 格式处理 (处理透明度问题)
                # 如果目标是 JPEG，但源图像有透明通道 (RGBA, P)，需要转换为 RGB，背景填充白色
                if target_format.upper() == 'JPEG' and img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                    # 如果需要填充特定背景色，可以使用下面的方法替代上一行：
                    # background = Image.new("RGB", img.size, (255, 255, 255))
                    # background.paste(img, mask=img.split()[3]) # 使用 alpha 通道作为掩码
                    # img = background

                # 4. 剥离元数据 (如EXIF)
                # 通过重新创建一个 Image 对象来清除多余信息
                data = list(img.getdata())
                image_without_exif = Image.new(img.mode, img.size)
                image_without_exif.putdata(data)
                img = image_without_exif

                # 5. 压缩并保存到内存缓冲区 (BytesIO)
                # 我们不需要保存到硬盘，直接保存到内存中
                buffer = io.BytesIO()

                save_args = {'format': target_format}
                if target_format.upper() == 'JPEG':
                    save_args['quality'] = jpeg_quality
                    # optimize=True 可以进一步进行无损压缩优化
                    save_args['optimize'] = True

                img.save(buffer, **save_args)

                # 获取压缩后的二进制数据
                compressed_image_bytes = buffer.getvalue()
                compressed_size_bytes = len(compressed_image_bytes)
                print(f"压缩后 (中间态): 尺寸: {img.size}, 大小: {compressed_size_bytes / 1024:.2f} KB")
                print(f"压缩率: {(1 - compressed_size_bytes / original_size_bytes) * 100:.2f}%")

                # 6. 转换为 Base64 编码
                base64_encoded_str = base64.b64encode(compressed_image_bytes).decode('utf-8')
                print(f"Base64 编码后大小估算: {len(base64_encoded_str) / 1024:.2f} KB")

                return base64_encoded_str

        except FileNotFoundError:
            print(f"错误: 找不到文件 {image_path}")
            return None
        except Exception as e:
            print(f"处理图片时出错: {e}")
            return None

    def _get_image_mime_type(self,image_path: str) -> str:
        """
        根据文件扩展名确定图像的MIME类型
        @param image_path: 图像文件路径
        @return: MIME类型
        """
        ext = os.path.splitext(image_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.svg': 'image/svg+xml',
            '.tiff': 'image/tiff',
            '.webp': 'image/webp'
        }
        return mime_types.get(ext, 'image/jpeg')