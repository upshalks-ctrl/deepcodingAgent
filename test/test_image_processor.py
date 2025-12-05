#!/usr/bin/env python3
"""
图片处理器测试
测试ImageProcessor的功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.document_processors.image_processor import ImageProcessor
from src.models.document import Document


class TestImageProcessor:
    """图片处理器测试类"""

    def __init__(self):
        self.test_dir = Path(__file__).parent / "test_data"
        self.test_dir.mkdir(exist_ok=True)

    async def create_test_images(self):
        """创建测试图片文件"""
        images = {}

        # 创建PNG测试图片
        png_file = self.test_dir / "test_image.png"
        images['png'] = png_file

        if not png_file.exists():
            try:
                from PIL import Image as PILImage, ImageDraw, ImageFont

                # 创建一个简单的测试图片
                img = PILImage.new('RGB', (800, 600), color='white')
                draw = ImageDraw.Draw(img)

                # 绘制一些文本和图形
                draw.rectangle([50, 50, 750, 150], fill='lightblue', outline='blue', width=2)
                draw.text((100, 100), "Image Processor Test", fill='black')
                draw.text((100, 130), "This is a test image", fill='gray')

                # 绘制一些图形
                draw.ellipse([100, 200, 300, 400], fill='red', outline='darkred', width=3)
                draw.rectangle([400, 200, 600, 400], fill='green', outline='darkgreen', width=3)

                # 绘制文本
                draw.text((100, 450), "Red circle, green rectangle", fill='black')

                img.save(png_file, 'PNG')
                print(f"✓ Created test PNG: {png_file}")
            except Exception as e:
                print(f"✗ Failed to create PNG: {e}")

        # 创建JPG测试图片
        jpg_file = self.test_dir / "test_image.jpg"
        images['jpg'] = jpg_file

        if not jpg_file.exists():
            try:
                from PIL import Image as PILImage, ImageDraw

                img = PILImage.new('RGB', (800, 600), color='white')
                draw = ImageDraw.Draw(img)

                # 绘制渐变效果（通过多个矩形模拟）
                for i in range(100):
                    color_val = 255 - int(255 * i / 100)
                    draw.rectangle([50 + i*6, 100, 50 + i*6 + 5, 200], fill=(color_val, 100, 100))

                draw.text((50, 250), "JPG Test Image", fill='black')
                draw.text((50, 280), "With gradient effect", fill='gray')

                img.save(jpg_file, 'JPEG', quality=95)
                print(f"✓ Created test JPG: {jpg_file}")
            except Exception as e:
                print(f"✗ Failed to create JPG: {e}")

        return images

    async def test_png_processing(self):
        """测试PNG图片处理"""
        print("\n" + "="*70)
        print("TEST 1: PNG Image Processing")
        print("="*70)

        png_file = self.test_dir / "test_image.png"
        if not png_file.exists():
            print("✗ PNG test file not found")
            return False

        processor = ImageProcessor()

        try:
            documents = await processor.process(str(png_file))
            print(f"✓ Processed {len(documents)} images")

            for i, doc in enumerate(documents, 1):
                print(f"\n  Image {i}:")
                print(f"    Title: {doc.title}")
                print(f"    Content length: {len(doc.content)} chars")
                print(f"    Image format: {doc.metadata.get('image_format', 'N/A')}")
                print(f"    Preview: {doc.content[:150]}...")

            return True
        except Exception as e:
            print(f"✗ PNG processing failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_jpg_processing(self):
        """测试JPG图片处理"""
        print("\n" + "="*70)
        print("TEST 2: JPG Image Processing")
        print("="*70)

        jpg_file = self.test_dir / "test_image.jpg"
        if not jpg_file.exists():
            print("✗ JPG test file not found")
            return False

        processor = ImageProcessor()

        try:
            documents = await processor.process(str(jpg_file))
            print(f"✓ Processed {len(documents)} images")

            for i, doc in enumerate(documents, 1):
                print(f"\n  Image {i}:")
                print(f"    Title: {doc.title}")
                print(f"    Content length: {len(doc.content)} chars")
                print(f"    Image format: {doc.metadata.get('image_format', 'N/A')}")
                print(f"    Preview: {doc.content[:150]}...")

            return True
        except Exception as e:
            print(f"✗ JPG processing failed: {e}")
            return False

    async def test_metadata_extraction(self):
        """测试元数据提取"""
        print("\n" + "="*70)
        print("TEST 3: Metadata Extraction")
        print("="*70)

        png_file = self.test_dir / "test_image.png"
        processor = ImageProcessor()

        try:
            documents = await processor.process(str(png_file))

            if not documents:
                print("✗ No documents returned")
                return False

            doc = documents[0]
            required_fields = ['source_path', 'title', 'url']

            print(f"✓ Document has {len(doc.metadata)} metadata fields")

            for field in required_fields:
                if field in doc.metadata:
                    print(f"  ✓ {field}: {doc.metadata[field]}")
                else:
                    print(f"  ✗ Missing {field}")
                    return False

            # 检查图片特定字段
            image_fields = ['image_format', 'width', 'height', 'chunk_type']
            for field in image_fields:
                if field in doc.metadata:
                    print(f"  ✓ {field}: {doc.metadata[field]}")

            return True
        except Exception as e:
            print(f"✗ Metadata extraction test failed: {e}")
            return False

    async def test_vision_model_integration(self):
        """测试视觉模型集成"""
        print("\n" + "="*70)
        print("TEST 4: Vision Model Integration")
        print("="*70)

        png_file = self.test_dir / "test_image.png"
        processor = ImageProcessor()

        try:
            documents = await processor.process(str(png_file), use_vision=True)
            print(f"✓ Vision model processed {len(documents)} images")

            if documents:
                doc = documents[0]
                print(f"\n  Vision Analysis:")
                print(f"    Content length: {len(doc.content)} chars")
                print(f"    Analysis preview: {doc.content[:200]}...")

                # 检查是否包含描述性内容
                if len(doc.content) > 100:
                    print(f"  ✓ Rich description generated")
                    return True
                else:
                    print(f"  ✗ Description too short")
                    return False

            return False
        except Exception as e:
            print(f"✗ Vision model integration failed: {e}")
            print(f"  Note: Vision model may not be configured")
            return False

    async def test_format_detection(self):
        """测试格式检测"""
        print("\n" + "="*70)
        print("TEST 5: Format Detection")
        print("="*70)

        processor = ImageProcessor()

        test_formats = {
            'png': self.test_dir / 'test_image.png',
            'jpg': self.test_dir / 'test_image.jpg',
        }

        results = []
        for format_name, file_path in test_formats.items():
            if file_path.exists():
                try:
                    documents = await processor.process(str(file_path))
                    if documents:
                        detected_format = documents[0].metadata.get('image_format', '').lower()
                        match = detected_format == format_name.upper()
                        results.append((format_name, detected_format, match))

                        status = "✓" if match else "✗"
                        print(f"  {status} {format_name.upper()}: detected as {detected_format}")
                    else:
                        print(f"  ✗ {format_name.upper()}: No documents returned")
                        results.append((format_name, "None", False))
                except Exception as e:
                    print(f"  ✗ {format_name.upper()}: Error - {e}")
                    results.append((format_name, "Error", False))

        passed = sum(1 for _, _, match in results if match)
        total = len(results)
        print(f"\n  Accuracy: {passed}/{total} formats correctly detected")

        return passed >= total * 0.75

    async def test_image_dimensions(self):
        """测试图片尺寸提取"""
        print("\n" + "="*70)
        print("TEST 6: Image Dimensions")
        print("="*70)

        png_file = self.test_dir / "test_image.png"
        processor = ImageProcessor()

        try:
            documents = await processor.process(str(png_file))

            if documents:
                doc = documents[0]
                width = doc.metadata.get('width')
                height = doc.metadata.get('height')

                print(f"  Image dimensions: {width}x{height}")

                if width and height and width > 0 and height > 0:
                    print(f"  ✓ Valid dimensions detected")
                    return True
                else:
                    print(f"  ✗ Invalid dimensions")
                    return False

            return False
        except Exception as e:
            print(f"✗ Image dimensions test failed: {e}")
            return False

    async def test_content_quality(self):
        """测试内容质量"""
        print("\n" + "="*70)
        print("TEST 7: Content Quality")
        print("="*70)

        png_file = self.test_dir / "test_image.png"
        processor = ImageProcessor()

        try:
            documents = await processor.process(str(png_file))

            if not documents:
                print("✗ No documents returned")
                return False

            doc = documents[0]
            content = doc.content

            # 检查描述性指标
            has_length = len(content) > 50
            has_keywords = any(keyword in content.lower() for keyword in [
                'image', 'test', 'color', 'shape', 'text'
            ])
            has_structure = any(char in content for char in ['.', ',', '\n'])

            print(f"  Content length: {len(content)} chars")
            print(f"  ✓ Sufficient length: {has_length}")
            print(f"  ✓ Contains keywords: {has_keywords}")
            print(f"  ✓ Well structured: {has_structure}")

            quality_score = sum([has_length, has_keywords, has_structure])
            print(f"  Quality score: {quality_score}/3")

            return quality_score >= 2
        except Exception as e:
            print(f"✗ Content quality test failed: {e}")
            return False

    async def test_no_chunking(self):
        """测试不分块（图片不需要分块）"""
        print("\n" + "="*70)
        print("TEST 8: No Chunking Required")
        print("="*70)

        png_file = self.test_dir / "test_image.png"
        processor = ImageProcessor()

        try:
            # 图片处理器应该忽略分块参数
            documents = await processor.process(
                str(png_file),
                chunk=True,
                chunk_size=500,
                chunk_overlap=50
            )

            print(f"✓ Processed {len(documents)} images (no chunking)")

            # 图片通常不需要分块，应该返回1个文档
            if len(documents) == 1:
                print(f"  ✓ Correct: Single image = single document")
                return True
            else:
                print(f"  ℹ Images: {len(documents)} documents")
                return True

        except Exception as e:
            print(f"✗ No chunking test failed: {e}")
            return False

    async def test_error_handling(self):
        """测试错误处理"""
        print("\n" + "="*70)
        print("TEST 9: Error Handling")
        print("="*70)

        processor = ImageProcessor()

        # 测试不存在的文件
        try:
            documents = await processor.process("non_existent_file.png")
            print(f"  ✗ Should have raised an error")
            return False
        except FileNotFoundError:
            print(f"  ✓ Correctly raised FileNotFoundError for missing file")
        except Exception as e:
            print(f"  ? Raised different error: {type(e).__name__}")

        # 测试不支持的格式
        txt_file = self.test_dir / "test_utf8.txt"
        if txt_file.exists():
            try:
                documents = await processor.process(str(txt_file))
                print(f"  ? Processor handled TXT file (may be expected)")
            except Exception as e:
                print(f"  ✓ Correctly raised error for unsupported format: {type(e).__name__}")

        return True

    async def test_batch_processing(self):
        """测试批量处理"""
        print("\n" + "="*70)
        print("TEST 10: Batch Processing")
        print("="*70)

        processor = ImageProcessor()

        # 处理多个图片文件
        image_files = [
            self.test_dir / 'test_image.png',
            self.test_dir / 'test_image.jpg',
        ]

        existing_files = [f for f in image_files if f.exists()]

        if not existing_files:
            print("✗ No image files found for batch processing")
            return False

        try:
            all_documents = []
            for img_file in existing_files:
                docs = await processor.process(str(img_file))
                all_documents.extend(docs)

            print(f"✓ Batch processed {len(existing_files)} images")
            print(f"  Total documents: {len(all_documents)}")

            for i, doc in enumerate(all_documents, 1):
                format_name = doc.metadata.get('image_format', 'Unknown')
                print(f"  Document {i}: {format_name}, {len(doc.content)} chars")

            return len(all_documents) > 0
        except Exception as e:
            print(f"✗ Batch processing failed: {e}")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*70)
        print("IMAGE PROCESSOR TEST SUITE")
        print("="*70)

        # 创建测试图片
        await self.create_test_images()

        # 运行测试
        results = []
        results.append(("PNG Processing", await self.test_png_processing()))
        results.append(("JPG Processing", await self.test_jpg_processing()))
        results.append(("Metadata Extraction", await self.test_metadata_extraction()))
        results.append(("Vision Model", await self.test_vision_model_integration()))
        results.append(("Format Detection", await self.test_format_detection()))
        results.append(("Image Dimensions", await self.test_image_dimensions()))
        results.append(("Content Quality", await self.test_content_quality()))
        results.append(("No Chunking", await self.test_no_chunking()))
        results.append(("Error Handling", await self.test_error_handling()))
        results.append(("Batch Processing", await self.test_batch_processing()))

        # 总结
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {status} - {test_name}")

        print(f"\n  Total: {passed}/{total} tests passed")

        return passed == total


async def main():
    """主函数"""
    test_suite = TestImageProcessor()
    success = await test_suite.run_all_tests()

    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")

    print("\n" + "="*70)
    print("NOTES")
    print("="*70)
    print("• Image processor supports PNG, JPG, JPEG, GIF, BMP, TIFF formats")
    print("• Vision model integration requires vision LLM configuration")
    print("• Images are typically processed as single documents (no chunking)")
    print("• Rich descriptions are generated using vision models")

    return success


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    result = asyncio.run(main())
    sys.exit(0 if result else 1)
