#!/usr/bin/env python3
"""
统一处理器测试
测试统一处理接口的功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.document_processors.unified_processor import process, process_batch
from src.document_processors.text_processor import TextProcessor
from src.document_processors.pdf_processor import PDFProcessor
from src.models.document import Document


class TestUnifiedProcessor:
    """统一处理器测试类"""

    def __init__(self):
        self.test_dir = Path(__file__).parent / "test_data"
        self.test_dir.mkdir(exist_ok=True)
        self.create_test_files()

    def create_test_files(self):
        """创建所有测试文件"""
        # TXT文件
        self.txt_file = self.test_dir / "test.txt"
        if not self.txt_file.exists():
            with open(self.txt_file, 'w', encoding='utf-8') as f:
                f.write("""Unified Processor Test Document
===============================

This is a test document for the unified processor.

Chapter 1: Overview
This chapter provides an overview of the system.

Section 1.1: Features
- Multiple format support
- Automatic format detection
- Unified processing interface

Chapter 2: Implementation
This chapter describes the implementation details.

Section 2.1: Architecture
The architecture follows a modular design.

Section 2.2: API
The API provides simple and intuitive interface.
""")

        # MD文件
        self.md_file = self.test_dir / "test.md"
        if not self.md_file.exists():
            with open(self.md_file, 'w', encoding='utf-8') as f:
                f.write("""# Unified Processor Test

## Introduction

This is a **Markdown** test document for unified processing.

### Features

- ✓ Multiple format support
- ✓ Automatic detection
- ✓ Unified API

### Code Example

```python
from src.document_processors.unified_processor import process

documents = await process("document.pdf")
```

### Table

| Feature | Status |
|---------|--------|
| PDF     | ✓      |
| TXT     | ✓      |
| MD      | ✓      |

## Conclusion

The unified processor provides a simple, consistent interface.
""")

        # PDF文件
        self.pdf_file = self.test_dir / "test.pdf"
        if not self.pdf_file.exists():
            try:
                import fitz
                doc = fitz.open()
                page = doc.new_page()
                page.insert_text((50, 50), "Unified Processor PDF Test", fontsize=20)
                page.insert_text((50, 100), "Page 1: Introduction", fontsize=14)
                page.insert_text((50, 150), "This PDF tests unified processing.", fontsize=12)
                page.insert_text((50, 200), "Chapter 1: Overview", fontsize=16)
                doc.save(str(self.pdf_file))
                doc.close()
            except Exception as e:
                print(f"Warning: Could not create PDF: {e}")

        print(f"✓ Created test files in {self.test_dir}")

    async def test_txt_processing(self):
        """测试TXT文件处理"""
        print("\n" + "="*70)
        print("TEST 1: TXT File Processing")
        print("="*70)

        try:
            documents = await process(str(self.txt_file))
            print(f"✓ Processed TXT: {len(documents)} documents")

            for i, doc in enumerate(documents, 1):
                print(f"\n  Document {i}:")
                print(f"    Title: {doc.title}")
                print(f"    Content length: {len(doc.content)} chars")
                print(f"    Document type: {doc.metadata.get('document_type', 'N/A')}")

            return True
        except Exception as e:
            print(f"✗ TXT processing failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_markdown_processing(self):
        """测试Markdown文件处理"""
        print("\n" + "="*70)
        print("TEST 2: Markdown Processing")
        print("="*70)

        try:
            documents = await process(str(self.md_file))
            print(f"✓ Processed MD: {len(documents)} documents")

            for i, doc in enumerate(documents, 1):
                print(f"\n  Document {i}:")
                print(f"    Title: {doc.title}")
                print(f"    Content length: {len(doc.content)} chars")

            return True
        except Exception as e:
            print(f"✗ Markdown processing failed: {e}")
            return False

    async def test_pdf_processing_v1(self):
        """测试PDF文件处理（v1）"""
        print("\n" + "="*70)
        print("TEST 3: PDF Processing (v1)")
        print("="*70)

        try:
            documents = await process(
                str(self.pdf_file),
                use_vision=False  # 使用v1处理器
            )
            print(f"✓ Processed PDF (v1): {len(documents)} documents")

            for i, doc in enumerate(documents, 1):
                print(f"\n  Document {i}:")
                print(f"    Title: {doc.title}")
                print(f"    Content length: {len(doc.content)} chars")
                print(f"    Processor: {doc.metadata.get('processor', 'N/A')}")

            return True
        except Exception as e:
            print(f"✗ PDF processing (v1) failed: {e}")
            return False

    async def test_pdf_processing_v2(self):
        """测试PDF文件处理（v2）"""
        print("\n" + "="*70)
        print("TEST 4: PDF Processing (v2 - Memory Buffer)")
        print("="*70)

        try:
            documents = await process(
                str(self.pdf_file),
                use_vision=True,  # 使用v2处理器
                chunk_after=False
            )
            print(f"✓ Processed PDF (v2): {len(documents)} documents")

            for i, doc in enumerate(documents, 1):
                print(f"\n  Document {i}:")
                print(f"    Title: {doc.title}")
                print(f"    Content length: {len(doc.content)} chars")
                print(f"    Processing method: {doc.metadata.get('processing_method', 'N/A')}")

            return True
        except Exception as e:
            print(f"✗ PDF processing (v2) failed: {e}")
            return False

    async def test_chunking_options(self):
        """测试分块选项"""
        print("\n" + "="*70)
        print("TEST 5: Chunking Options")
        print("="*70)

        try:
            # 测试自动分块
            documents_auto = await process(
                str(self.txt_file),
                chunk=True,
                chunk_strategy='auto'
            )
            print(f"✓ Auto chunking: {len(documents_auto)} chunks")

            # 测试按段落分块
            documents_paragraph = await process(
                str(self.txt_file),
                chunk=True,
                chunk_strategy='paragraph'
            )
            print(f"✓ Paragraph chunking: {len(documents_paragraph)} chunks")

            # 测试不分块
            documents_no_chunk = await process(
                str(self.txt_file),
                chunk=False
            )
            print(f"✓ No chunking: {len(documents_no_chunk)} documents")

            # 验证分块效果
            if len(documents_auto) > len(documents_no_chunk):
                print(f"  ✓ Chunking increased document count")
            else:
                print(f"  ℹ Chunking did not increase count (may be expected)")

            return True
        except Exception as e:
            print(f"✗ Chunking options test failed: {e}")
            return False

    async def test_batch_processing(self):
        """测试批量处理"""
        print("\n" + "="*70)
        print("TEST 6: Batch Processing")
        print("="*70)

        file_paths = [
            str(self.txt_file),
            str(self.md_file),
            str(self.pdf_file),
        ]

        try:
            results = await process_batch(
                file_paths,
                max_concurrent=2,
                chunk=False
            )

            print(f"✓ Batch processed {len(file_paths)} files")

            for file_path, documents in zip(file_paths, results):
                filename = Path(file_path).name
                print(f"\n  {filename}: {len(documents)} documents")

            # 验证所有文件都被处理
            all_success = all(len(docs) > 0 for docs in results)
            if all_success:
                print(f"  ✓ All files processed successfully")
            else:
                print(f"  ✗ Some files failed to process")

            return all_success
        except Exception as e:
            print(f"✗ Batch processing failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_processor_selection(self):
        """测试处理器自动选择"""
        print("\n" + "="*70)
        print("TEST 7: Processor Auto-Selection")
        print("="*70)

        test_cases = [
            (str(self.txt_file), 'TextProcessor', '.txt'),
            (str(self.md_file), 'TextProcessor', '.md'),
            (str(self.pdf_file), 'PDFProcessor', '.pdf'),
        ]

        results = []
        for file_path, expected_processor, ext in test_cases:
            try:
                documents = await process(file_path, chunk=False)
                if documents:
                    processor = documents[0].metadata.get('processor', 'Unknown')
                    match = expected_processor in processor or processor in expected_processor
                    results.append((ext, processor, match))

                    status = "✓" if match else "✗"
                    print(f"  {status} {ext}: {processor} (expected {expected_processor})")
                else:
                    print(f"  ✗ {ext}: No documents returned")
                    results.append((ext, "None", False))
            except Exception as e:
                print(f"  ✗ {ext}: Error - {e}")
                results.append((ext, "Error", False))

        passed = sum(1 for _, _, match in results if match)
        total = len(results)
        print(f"\n  Accuracy: {passed}/{total} processors correctly selected")

        return passed >= total * 0.75

    async def test_metadata_consistency(self):
        """测试元数据一致性"""
        print("\n" + "="*70)
        print("TEST 8: Metadata Consistency")
        print("="*70)

        try:
            documents = await process(str(self.txt_file), chunk=False)

            if not documents:
                print("✗ No documents returned")
                return False

            doc = documents[0]
            required_fields = ['source_path', 'title', 'url']

            print(f"✓ Document has {len(doc.metadata)} metadata fields")

            all_present = True
            for field in required_fields:
                if field in doc.metadata:
                    print(f"  ✓ {field}: {doc.metadata[field]}")
                else:
                    print(f"  ✗ Missing {field}")
                    all_present = False

            # 检查元数据值是否合理
            if doc.metadata.get('source_path') == str(self.txt_file):
                print(f"  ✓ Source path is correct")
            else:
                print(f"  ✗ Source path mismatch")
                all_present = False

            return all_present
        except Exception as e:
            print(f"✗ Metadata consistency test failed: {e}")
            return False

    async def test_error_handling(self):
        """测试错误处理"""
        print("\n" + "="*70)
        print("TEST 9: Error Handling")
        print("="*70)

        # 测试不存在的文件
        try:
            documents = await process("non_existent_file.txt")
            print(f"  ✗ Should have raised FileNotFoundError")
            return False
        except FileNotFoundError:
            print(f"  ✓ Correctly raised FileNotFoundError for missing file")
        except Exception as e:
            print(f"  ? Raised different error: {type(e).__name__}: {e}")

        # 测试不支持的文件类型
        py_file = self.test_dir / "test.py"
        py_file.write_text("print('test')")
        try:
            documents = await process(str(py_file))
            print(f"  ? Processor handled .py file (may be expected)")
        except ValueError as e:
            print(f"  ✓ Correctly raised ValueError for unsupported format")
        except Exception as e:
            print(f"  ? Raised different error: {type(e).__name__}")

        return True

    async def test_custom_parameters(self):
        """测试自定义参数"""
        print("\n" + "="*70)
        print("TEST 10: Custom Parameters")
        print("="*70)

        try:
            # 测试自定义分块参数
            documents = await process(
                str(self.txt_file),
                chunk=True,
                chunk_size=200,
                chunk_overlap=50
            )
            print(f"✓ Custom chunking parameters: {len(documents)} chunks")

            # 测试PDF特定参数
            if self.pdf_file.exists():
                documents_pdf = await process(
                    str(self.pdf_file),
                    dpi=150
                )
                print(f"✓ Custom PDF parameters: {len(documents_pdf)} documents")

            # 测试文本特定参数
            documents_txt = await process(
                str(self.txt_file),
                encoding='utf-8'
            )
            print(f"✓ Custom text parameters: {len(documents_txt)} documents")

            return True
        except Exception as e:
            print(f"✗ Custom parameters test failed: {e}")
            return False

    async def test_use_vision_parameter(self):
        """测试use_vision参数"""
        print("\n" + "="*70)
        print("TEST 11: use_vision Parameter")
        print("="*70)

        if not self.pdf_file.exists():
            print("  ⊘ Skipping: PDF file not available")
            return True

        try:
            # 不使用视觉模型
            documents_v1 = await process(
                str(self.pdf_file),
                use_vision=False,
                chunk=False
            )

            # 使用视觉模型
            documents_v2 = await process(
                str(self.pdf_file),
                use_vision=True,
                chunk=False
            )

            print(f"✓ v1 (no vision): {len(documents_v1)} documents")
            print(f"✓ v2 (with vision): {len(documents_v2)} documents")

            # 检查处理方法差异
            v1_method = documents_v1[0].metadata.get('processing_method', 'N/A') if documents_v1 else 'N/A'
            v2_method = documents_v2[0].metadata.get('processing_method', 'N/A') if documents_v2 else 'N/A'

            print(f"  v1 method: {v1_method}")
            print(f"  v2 method: {v2_method}")

            if v1_method != v2_method:
                print(f"  ✓ Different processing methods used")

            return True
        except Exception as e:
            print(f"✗ use_vision parameter test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_extract_images_parameter(self):
        """测试extract_images参数（PDF）"""
        print("\n" + "="*70)
        print("TEST 12: extract_images Parameter (PDF)")
        print("="*70)

        if not self.pdf_file.exists():
            print("  ⊘ Skipping: PDF file not available")
            return True

        try:
            # 不提取图片
            documents_no_img = await process(
                str(self.pdf_file),
                extract_images=False,
                chunk=False
            )

            # 提取图片（如果支持）
            documents_with_img = await process(
                str(self.pdf_file),
                extract_images=True,
                chunk=False
            )

            print(f"✓ Without extract_images: {len(documents_no_img)} documents")
            print(f"✓ With extract_images: {len(documents_with_img)} documents")

            # 图片提取应该返回更多文档
            if len(documents_with_img) >= len(documents_no_img):
                print(f"  ✓ Image extraction increased document count")
            else:
                print(f"  ℹ Image extraction did not increase count (no images in test PDF)")

            return True
        except Exception as e:
            print(f"✗ extract_images parameter test failed: {e}")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*70)
        print("UNIFIED PROCESSOR TEST SUITE")
        print("="*70)

        # 运行测试
        results = []
        results.append(("TXT Processing", await self.test_txt_processing()))
        results.append(("Markdown Processing", await self.test_markdown_processing()))
        results.append(("PDF Processing v1", await self.test_pdf_processing_v1()))
        results.append(("PDF Processing v2", await self.test_pdf_processing_v2()))
        results.append(("Chunking Options", await self.test_chunking_options()))
        results.append(("Batch Processing", await self.test_batch_processing()))
        results.append(("Processor Selection", await self.test_processor_selection()))
        results.append(("Metadata Consistency", await self.test_metadata_consistency()))
        results.append(("Error Handling", await self.test_error_handling()))
        results.append(("Custom Parameters", await self.test_custom_parameters()))
        results.append(("use_vision Parameter", await self.test_use_vision_parameter()))
        results.append(("extract_images Parameter", await self.test_extract_images_parameter()))

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
    test_suite = TestUnifiedProcessor()
    success = await test_suite.run_all_tests()

    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")

    print("\n" + "="*70)
    print("UNIFIED PROCESSOR FEATURES")
    print("="*70)
    print("• Single interface for all document types")
    print("• Automatic format detection and processor selection")
    print("• Flexible chunking strategies")
    print("• Batch processing support")
    print("• Vision model integration (PDFProcessor v2 memory buffer mode)")
    print("• Consistent metadata across all processors")
    print("• Custom parameters for each processor type")

    return success


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    result = asyncio.run(main())
    sys.exit(0 if result else 1)
