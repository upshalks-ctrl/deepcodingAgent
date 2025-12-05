# DeepCodeAgent - 文档处理器

## 项目简介

DeepCodeAgent是一个强大的端到端自动化编程系统，支持多种文档格式的智能处理。

## 主要功能

### 1. 统一文档处理
- 支持15种文件格式
- 智能分块策略
- 自动元数据提取

### 2. 支持的文件格式

| 格式 | 扩展名 | 特性 |
|------|--------|------|
| PDF | .pdf | 文本提取 + 图片提取 |
| Word | .docx | 段落和表格 |
| PowerPoint | .pptx | 按页分割 |
| 文本 | .txt | 自动编码检测 |
| Markdown | .md | 保持格式 |
| 图片 | .png/.jpg | 视觉理解 |

### 3. 问题导向索引

文档处理器不仅索引文档内容，还为每个文档块生成3-5个问题，实现更精准的搜索。

示例：
- 文档内容：系统支持用户注册、登录、权限管理
- 生成的问题：
  - "这个系统有哪些用户管理功能？"
  - "如何进行用户身份认证？"
  - "权限控制是如何实现的？"

## 安装依赖

```bash
pip install mineru python-pptx python-docx
```

## 使用方法

### 基本使用

```python
import asyncio
from src.document_processors.unified_processor import process

async def example():
    # 处理文档
    documents = await process(
        "document.pdf",
        chunk=True,
        extract_images=True
    )

    print(f"处理了 {len(documents)} 个文档块")
    for doc in documents:
        print(f"标题: {doc.title}")
        print(f"内容: {doc.content[:100]}...")

asyncio.run(example())
```

### 批量处理

```python
from src.document_processors.unified_processor import process_batch

results = await process_batch(
    ["doc1.pdf", "doc2.docx", "doc3.txt"],
    max_concurrent=3
)
```

## 智能分块

### 分块策略

1. **段落分块** - 适用于TXT/MD等文本文件
2. **标题分块** - 适用于PDF等结构化文档
3. **页面分块** - 适用于PPT等演示文稿
4. **语义分块** - 基于句子边界的智能分块

### 参数说明

- `chunk_size`: 块大小（默认1000字符）
- `chunk_overlap`: 块间重叠（默认100字符）
- `chunk_strategy`: 分块策略（默认'auto'）

## 问题导向索引

### 工作流程

1. 文档分块
2. LLM生成问题
3. 向量化问题
4. 索引到数据库
5. 支持问题搜索

### 搜索示例

```python
from src.rag.instant_vector_indexer_v2 import InstantVectorIndexer

indexer = InstantVectorIndexer()
await indexer.index_file_instantly("document.pdf")

results = await indexer.search_with_question_orientation(
    question="系统的技术架构是什么？"
)
```

## 贡献指南

欢迎贡献代码和建议！

## 许可证

MIT License
