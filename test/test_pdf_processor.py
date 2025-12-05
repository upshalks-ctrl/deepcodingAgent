#!/usr/bin/env python3
"""
PDF处理器测试
测试PDFProcessor和PDFProcessorV2的功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.document_processors.pdf_processor import PDFProcessor
from src.models.document import Document


class TestPDFProcessor:
    """PDF处理器测试类"""

    def __init__(self):
        self.test_dir = Path(__file__).parent / "test_data"
        self.test_dir.mkdir(exist_ok=True)
        self.test_pdf = self.test_dir / "test_document.pdf"

    async def create_test_pdf(self):
        """创建测试PDF文件"""
        if self.test_pdf.exists():
            return

        try:
            import fitz
            doc = fitz.open()

            # 第1页
            page = doc.new_page()
            page.insert_text((50, 50), "PDF Processor Test Document", fontsize=20)
            page.insert_text((50, 100), "Page 1: Introduction", fontsize=14)
            page.insert_text((50, 150), "This is a test document for PDF processing.", fontsize=12)
            page.insert_text((50, 200), "Chapter 1: Overview", fontsize=16)
            page.insert_text((50, 250), "This chapter provides an overview of the system.", fontsize=12)

            # 第2页
            page = doc.new_page()
            page.insert_text((50, 50), "Page 2: Technical Details", fontsize=14)
            page.insert_text((50, 100), "Chapter 2: Architecture", fontsize=16)
            page.insert_text((50, 150), "2.1 System Components", fontsize=14)
            page.insert_text((50, 180), "Component A, Component B, Component C", fontsize=12)
            page.insert_text((50, 230), "2.2 Data Flow", fontsize=14)
            page.insert_text((50, 260), "Data flows from input to output through various stages.", fontsize=12)

            # 第3页
            page = doc.new_page()
            page.insert_text((50, 50), "Page 3: Implementation", fontsize=14)
            page.insert_text((50, 100), "Chapter 3: Implementation Details", fontsize=16)
            page.insert_text((50, 150), "3.1 Core Algorithm", fontsize=14)
            page.insert_text((50, 180), "The algorithm processes data in multiple passes.", fontsize=12)
            page.insert_text((50, 230), "3.2 Performance Optimization", fontsize=14)
            page.insert_text((50, 260), "Various optimization techniques are employed.", fontsize=12)

            doc.save(str(self.test_pdf))
            doc.close()
            print(f"✓ Created test PDF: {self.test_pdf}")
        except Exception as e:
            print(f"✗ Failed to create test PDF: {e}")
            raise

    async def test_v1_processor_mineru(self):
        """测试PDFProcessor v1 - mineru方法"""
        print("\n" + "="*70)
        print("TEST 1: PDFProcessor v1 - mineru method")
        print("="*70)

        processor = PDFProcessor()

        try:
            # 尝试使用mineru方法
            documents = await processor.process(str(self.test_pdf), method='mineru')
            print(f"✓ mineru method processed {len(documents)} pages")

            for i, doc in enumerate(documents, 1):
                print(f"\n  Page {i}:")
                print(f"    Title: {doc.title}")
                print(f"    Content length: {len(doc.content)} chars")
                print(f"    Preview: {doc.content[:100]}...")

            return True
        except Exception as e:
            print(f"✗ mineru method failed: {e}")
            return False

    async def test_v1_processor_pymupdf(self):
        """测试PDFProcessor v1 - PyMuPDF方法"""
        print("\n" + "="*70)
        print("TEST 2: PDFProcessor v1 - PyMuPDF method")
        print("="*70)

        processor = PDFProcessor()

        try:
            documents = await processor.process(str(self.test_pdf), method='pymupdf')
            print(f"✓ PyMuPDF method processed {len(documents)} pages")

            for i, doc in enumerate(documents, 1):
                print(f"\n  Page {i}:")
                print(f"    Title: {doc.title}")
                print(f"    Content length: {len(doc.content)} chars")
                print(f"    Preview: {doc.content[:100]}...")

            return True
        except Exception as e:
            print(f"✗ PyMuPDF method failed: {e}")
            return False

    async def test_v1_extract_images(self):
        """测试PDFProcessor v1 - 图片提取"""
        print("\n" + "="*70)
        print("TEST 3: PDFProcessor v1 - Image Extraction")
        print("="*70)

        processor = PDFProcessor()

        try:
            images = await processor.extract_images_from_pdf(str(self.test_pdf))
            print(f"✓ Extracted {len(images)} images")

            if images:
                for i, img in enumerate(images[:3], 1):
                    print(f"\n  Image {i}:")
                    print(f"    Content length: {len(img.content)} chars")
                    print(f"    Preview: {img.content[:100]}...")

            return True
        except Exception as e:
            print(f"✗ Image extraction failed: {e}")
            return False

    async def test_v2_processor_basic(self):
        """测试PDFProcessor v2模式 - 基础功能"""
        print("\n" + "="*70)
        print("TEST 4: PDFProcessor v2 - Basic Processing")
        print("="*70)

        processor = PDFProcessor()

        try:
            # 使用v2内存buffer模式，不使用视觉模型
            documents = await processor.process(
                str(self.test_pdf),
                mode='v2_memory_buffer',
                chunk_after=False
            )
            print(f"✓ Processed {len(documents)} documents (no vision)")

            for i, doc in enumerate(documents, 1):
                print(f"\n  Document {i}:")
                print(f"    Title: {doc.title}")
                print(f"    Content length: {len(doc.content)} chars")
                print(f"    Processing method: {doc.metadata.get('processing_method', 'N/A')}")
                print(f"    Preview: {doc.content[:150]}...")

            return True
        except Exception as e:
            print(f"✗ Basic processing failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_v2_processor_with_vision(self):
        """测试PDFProcessor v2模式 - 视觉模型功能"""
        print("\n" + "="*70)
        print("TEST 5: PDFProcessor v2 - With Vision Model")
        print("="*70)

        processor = PDFProcessor()

        try:
            documents = await processor.process(
                str(self.test_pdf),
                mode='v2_memory_buffer',
                dpi=150,
                chunk_after=True,
                chunk_size=500,
                chunk_overlap=50
            )
            print(f"✓ Vision processing created {len(documents)} chunks")

            for i, doc in enumerate(documents, 1):
                print(f"\n  Chunk {i}:")
                print(f"    Title: {doc.title}")
                print(f"    Content length: {len(doc.content)} chars")
                print(f"    Chunk type: {doc.metadata.get('chunk_type', 'N/A')}")
                print(f"    Chunk title: {doc.metadata.get('chunk_title', 'N/A')}")
                print(f"    Processing method: {doc.metadata.get('processing_method', 'N/A')}")

            return True
        except Exception as e:
            print(f"✗ Vision processing failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_v2_memory_buffer(self):
        """测试PDFProcessor v2模式 - 内存buffer功能"""
        print("\n" + "="*70)
        print("TEST 6: PDFProcessor v2 - Memory Buffer & Base64")
        print("="*70)

        processor = PDFProcessor()

        try:
            # 测试内部方法
            documents = await processor._process_with_vision_combined_memory(
                str(self.test_pdf),
                dpi=150
            )
            print(f"✓ Memory buffer processing created {len(documents)} documents")

            doc = documents[0]
            print(f"\n  Complete Document:")
            print(f"    Title: {doc.title}")
            print(f"    Content length: {len(doc.content)} chars")
            print(f"    Total pages: {doc.metadata.get('total_pages', 'N/A')}")
            print(f"    Processing method: {doc.metadata.get('processing_method', 'N/A')}")
            print(f"    Format: {doc.metadata.get('format', 'N/A')}")
            print(f"    Preview: {doc.content[:200]}...")

            return True
        except Exception as e:
            print(f"✗ Memory buffer processing failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_metadata(self):
        """测试元数据完整性"""
        print("\n" + "="*70)
        print("TEST 7: Metadata Integrity")
        print("="*70)

        processor = PDFProcessor()

        try:
            documents = await processor.process(
                str(self.test_pdf),
                chunk_after=False
            )

            doc = documents[0]
            required_fields = ['source_path', 'title', 'url']

            print(f"✓ Document has {len(doc.metadata)} metadata fields")

            for field in required_fields:
                if field in doc.metadata:
                    print(f"  ✓ {field}: {doc.metadata[field]}")
                else:
                    print(f"  ✗ Missing {field}")

            # 检查其他有用字段
            useful_fields = ['total_pages', 'word_count', 'processing_method', 'format']
            for field in useful_fields:
                if field in doc.metadata:
                    print(f"  ✓ {field}: {doc.metadata[field]}")

            return True
        except Exception as e:
            print(f"✗ Metadata test failed: {e}")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*70)
        print("PDF PROCESSOR TEST SUITE")
        print("="*70)

        # 创建测试PDF
        await self.create_test_pdf()

        # 运行测试
        results = []
        results.append(("v1 mineru", await self.test_v1_processor_mineru()))
        results.append(("v1 PyMuPDF", await self.test_v1_processor_pymupdf()))
        results.append(("v1 Image Extraction", await self.test_v1_extract_images()))
        results.append(("v2 Basic", await self.test_v2_processor_basic()))
        results.append(("v2 Vision", await self.test_v2_processor_with_vision()))
        results.append(("v2 Memory Buffer", await self.test_v2_memory_buffer()))
        results.append(("Metadata", await self.test_metadata()))

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
    test_suite = TestPDFProcessor()
    success = await test_suite.run_all_tests()

    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")

    return success


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    result = asyncio.run(main())
    sys.exit(0 if result else 1)
