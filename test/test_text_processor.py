#!/usr/bin/env python3
"""
文本处理器测试
测试TextProcessor的功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.document_processors.text_processor import TextProcessor
from src.models.document import Document


class TestTextProcessor:
    """文本处理器测试类"""

    def __init__(self):
        self.test_dir = Path(__file__).parent / "test_data"
        self.test_dir.mkdir(exist_ok=True)

    async def create_test_files(self):
        """创建各种测试文本文件"""
        files = {}

        # 1. UTF-8 TXT文件
        txt_utf8 = self.test_dir / "test_utf8.txt"
        files['txt_utf8'] = txt_utf8
        if not txt_utf8.exists():
            with open(txt_utf8, 'w', encoding='utf-8') as f:
                f.write("""Text Processor Test Document
UTF-8 Encoding

This is a test document for text processing.

Chapter 1: Introduction
This chapter introduces the text processor and its capabilities.

Section 1.1: Features
- Automatic encoding detection
- Multiple format support
- Efficient text extraction

Section 1.2: Use Cases
- Log file processing
- Data file analysis
- Content extraction

Chapter 2: Technical Details
This chapter provides technical implementation details.

2.1: Encoding Detection
The processor automatically detects the file encoding.

2.2: Format Support
Supports TXT, MD, RST, and RTF formats.
""")

        # 2. Markdown文件
        md_file = self.test_dir / "test.md"
        files['md'] = md_file
        if not md_file.exists():
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write("""# Markdown Test Document

## Introduction

This is a **Markdown** test document with various formatting elements.

### Features

- **Bold text**
- *Italic text*
- `Code snippets`

### Code Example

```python
def hello():
    print("Hello, World!")
```

### Lists

1. First item
2. Second item
3. Third item

- Bullet point 1
- Bullet point 2

### Table

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
| Value 3  | Value 4  |

### Links

[Example Link](https://example.com)

### Blockquote

> This is a blockquote.
> It can span multiple lines.

## Conclusion

This document demonstrates various Markdown features.
""")

        # 3. RST文件
        rst_file = self.test_dir / "test.rst"
        files['rst'] = rst_file
        if not rst_file.exists():
            with open(rst_file, 'w', encoding='utf-8') as f:
                f.write("""=================
RST Test Document
=================

Introduction
============

This is a reStructuredText test document.

Features
--------

- Automatic encoding detection
- Format parsing
- Content extraction

Technical Details
=================

Section 1: Implementation
-------------------------

The implementation follows standard practices.

Section 2: Performance
----------------------

Performance is optimized for large files.

Code Block
==========

.. code-block:: python

   def process_text():
       return "processed"

Table
=====

+----------+----------+
| Column 1 | Column 2 |
+==========+==========+
| Value 1  | Value 2  |
+----------+----------+
| Value 3  | Value 4  |
+----------+----------+
""")

        # 4. GBK编码文件
        txt_gbk = self.test_dir / "test_gbk.txt"
        files['txt_gbk'] = txt_gbk
        if not txt_gbk.exists():
            with open(txt_gbk, 'w', encoding='gbk') as f:
                f.write("""GBK编码测试文档
==================

这是使用GBK编码的文本文件测试。

第一章：概述
本章介绍GBK编码的特点。

第二章：应用
GBK编码常用于中文环境。

第三章：技术细节
GBK是双字节编码方案。
""")

        print(f"✓ Created {len(files)} test text files")
        return files

    async def test_utf8_txt(self):
        """测试UTF-8编码的TXT文件"""
        print("\n" + "="*70)
        print("TEST 1: UTF-8 TXT File")
        print("="*70)

        txt_file = self.test_dir / "test_utf8.txt"
        processor = TextProcessor()

        try:
            documents = await processor.process(str(txt_file))
            print(f"✓ Processed {len(documents)} documents")

            for i, doc in enumerate(documents, 1):
                print(f"\n  Document {i}:")
                print(f"    Title: {doc.title}")
                print(f"    Content length: {len(doc.content)} chars")
                print(f"    Preview: {doc.content[:150]}...")
                print(f"    Encoding: {doc.metadata.get('encoding', 'N/A')}")

            return True
        except Exception as e:
            print(f"✗ UTF-8 TXT test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_markdown(self):
        """测试Markdown文件"""
        print("\n" + "="*70)
        print("TEST 2: Markdown File")
        print("="*70)

        md_file = self.test_dir / "test.md"
        processor = TextProcessor()

        try:
            documents = await processor.process(str(md_file))
            print(f"✓ Processed {len(documents)} documents")

            for i, doc in enumerate(documents, 1):
                print(f"\n  Document {i}:")
                print(f"    Title: {doc.title}")
                print(f"    Content length: {len(doc.content)} chars")
                print(f"    Preview: {doc.content[:150]}...")

            return True
        except Exception as e:
            print(f"✗ Markdown test failed: {e}")
            return False

    async def test_rst(self):
        """测试RST文件"""
        print("\n" + "="*70)
        print("TEST 3: RST File")
        print("="*70)

        rst_file = self.test_dir / "test.rst"
        processor = TextProcessor()

        try:
            documents = await processor.process(str(rst_file))
            print(f"✓ Processed {len(documents)} documents")

            for i, doc in enumerate(documents, 1):
                print(f"\n  Document {i}:")
                print(f"    Title: {doc.title}")
                print(f"    Content length: {len(doc.content)} chars")
                print(f"    Preview: {doc.content[:150]}...")

            return True
        except Exception as e:
            print(f"✗ RST test failed: {e}")
            return False

    async def test_gbk_encoding(self):
        """测试GBK编码检测"""
        print("\n" + "="*70)
        print("TEST 4: GBK Encoding Detection")
        print("="*70)

        txt_file = self.test_dir / "test_gbk.txt"
        processor = TextProcessor()

        try:
            documents = await processor.process(str(txt_file))
            print(f"✓ Processed {len(documents)} documents")

            for i, doc in enumerate(documents, 1):
                print(f"\n  Document {i}:")
                print(f"    Title: {doc.title}")
                print(f"    Content length: {len(doc.content)} chars")
                print(f"    Encoding: {doc.metadata.get('encoding', 'N/A')}")
                print(f"    Preview: {doc.content[:100]}...")

            # 验证中文内容正确解码
            if documents:
                content = documents[0].content
                if "GBK编码测试文档" in content:
                    print("  ✓ Chinese content correctly decoded")
                else:
                    print("  ✗ Chinese content not correctly decoded")
                    return False

            return True
        except Exception as e:
            print(f"✗ GBK encoding test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_auto_encoding_detection(self):
        """测试自动编码检测"""
        print("\n" + "="*70)
        print("TEST 5: Automatic Encoding Detection")
        print("="*70)

        processor = TextProcessor()

        test_files = [
            (self.test_dir / "test_utf8.txt", "UTF-8"),
            (self.test_dir / "test_gbk.txt", "GBK"),
        ]

        results = []
        for file_path, expected_encoding in test_files:
            if file_path.exists():
                try:
                    documents = await processor.process(str(file_path))
                    detected = documents[0].metadata.get('encoding', 'Unknown')
                    match = detected.upper() == expected_encoding.upper()
                    results.append((file_path.name, expected_encoding, detected, match))

                    status = "✓" if match else "✗"
                    print(f"  {status} {file_path.name}: {detected} (expected {expected_encoding})")
                except Exception as e:
                    print(f"  ✗ {file_path.name}: Error - {e}")
                    results.append((file_path.name, expected_encoding, "Error", False))

        passed = sum(1 for _, _, _, match in results if match)
        total = len(results)
        print(f"\n  Accuracy: {passed}/{total} files correctly detected")

        return passed >= total * 0.75

    async def test_format_support(self):
        """测试格式支持"""
        print("\n" + "="*70)
        print("TEST 6: Format Support")
        print("="*70)

        processor = TextProcessor()

        formats = {
            '.txt': 'test_utf8.txt',
            '.md': 'test.md',
            '.rst': 'test.rst',
        }

        results = []
        for ext, filename in formats.items():
            file_path = self.test_dir / filename
            if file_path.exists():
                try:
                    documents = await processor.process(str(file_path))
                    success = len(documents) > 0 and documents[0].content
                    results.append((ext, success))

                    status = "✓" if success else "✗"
                    print(f"  {status} {ext} format: {len(documents)} documents")
                except Exception as e:
                    print(f"  ✗ {ext} format: Error - {e}")
                    results.append((ext, False))

        passed = sum(1 for _, success in results if success)
        total = len(results)
        print(f"\n  Success rate: {passed}/{total} formats supported")

        return passed == total

    async def test_metadata(self):
        """测试元数据完整性"""
        print("\n" + "="*70)
        print("TEST 7: Metadata Integrity")
        print("="*70)

        txt_file = self.test_dir / "test_utf8.txt"
        processor = TextProcessor()

        try:
            documents = await processor.process(str(txt_file))

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

            # 检查文本特定字段
            text_fields = ['encoding', 'word_count']
            for field in text_fields:
                if field in doc.metadata:
                    print(f"  ✓ {field}: {doc.metadata[field]}")

            return True
        except Exception as e:
            print(f"✗ Metadata test failed: {e}")
            return False

    async def test_content_preservation(self):
        """测试内容完整性"""
        print("\n" + "="*70)
        print("TEST 8: Content Preservation")
        print("="*70)

        md_file = self.test_dir / "test.md"
        processor = TextProcessor()

        try:
            documents = await processor.process(str(md_file))

            if not documents:
                print("✗ No documents returned")
                return False

            doc = documents[0]
            content = doc.content

            # 检查预期关键词
            expected_keywords = [
                "Markdown Test Document",
                "Introduction",
                "Features",
                "Code Example",
                "Table",
                "Conclusion"
            ]

            found_keywords = []
            for keyword in expected_keywords:
                if keyword in content:
                    found_keywords.append(keyword)
                    print(f"  ✓ Found: {keyword}")
                else:
                    print(f"  ✗ Missing: {keyword}")

            print(f"\n  Found {len(found_keywords)}/{len(expected_keywords)} keywords")

            # 检查Markdown格式标记
            if "```" in content:
                print("  ✓ Code blocks preserved")
            if "| Column" in content:
                print("  ✓ Tables preserved")
            if "> This is a blockquote" in content:
                print("  ✓ Blockquotes preserved")

            return len(found_keywords) >= len(expected_keywords) * 0.75
        except Exception as e:
            print(f"✗ Content preservation test failed: {e}")
            return False

    async def test_chunking(self):
        """测试分块功能"""
        print("\n" + "="*70)
        print("TEST 9: Chunking")
        print("="*70)

        txt_file = self.test_dir / "test_utf8.txt"
        processor = TextProcessor()

        try:
            # 测试自动分块
            documents = await processor.process(
                str(txt_file),
                chunk=True,
                chunk_size=500,
                chunk_overlap=50
            )

            print(f"✓ Created {len(documents)} chunks")

            if documents:
                for i, doc in enumerate(documents[:3], 1):
                    print(f"\n  Chunk {i}:")
                    print(f"    Title: {doc.title}")
                    print(f"    Content length: {len(doc.content)} chars")
                    print(f"    Preview: {doc.content[:100]}...")

            return len(documents) > 0
        except Exception as e:
            print(f"✗ Chunking test failed: {e}")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*70)
        print("TEXT PROCESSOR TEST SUITE")
        print("="*70)

        # 创建测试文件
        await self.create_test_files()

        # 运行测试
        results = []
        results.append(("UTF-8 TXT", await self.test_utf8_txt()))
        results.append(("Markdown", await self.test_markdown()))
        results.append(("RST", await self.test_rst()))
        results.append(("GBK Encoding", await self.test_gbk_encoding()))
        results.append(("Encoding Detection", await self.test_auto_encoding_detection()))
        results.append(("Format Support", await self.test_format_support()))
        results.append(("Metadata", await self.test_metadata()))
        results.append(("Content Preservation", await self.test_content_preservation()))
        results.append(("Chunking", await self.test_chunking()))

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
    test_suite = TestTextProcessor()
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
