# 基于 RAG 的代码库问答系统架构设计

在构建针对私有代码库的 AI 助手时，检索增强生成（RAG）是解决上下文限制的关键技术。本文档探讨如何构建高效的代码 RAG 系统。

## 数据预处理策略

### 1. 代码分块 (Chunking)
代码与普通文本不同，不能简单地按字符长度切割。
* **基于 AST 的分割**：使用抽象语法树（AST）将代码按类（Class）或函数（Function）进行分割，保证语义完整性。
* **重叠窗口**：保留 10-20% 的重叠（Overlap），以维持上下文连贯性。

### 2. 向量化 (Embedding)
选择适合代码的 Embedding 模型至关重要。
- 推荐模型：`text-embedding-3-small` 或 `bge-m3`。
- 维度选择：通常 1536 维足以捕捉代码的语义特征。

## 代码示例：使用 Python 进行简单分块

以下是一个使用 LangChain 进行代码分割的示例：

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

def split_python_code(code_text):
    python_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON, 
        chunk_size=500, 
        chunk_overlap=50
    )
    docs = python_splitter.create_documents([code_text])
    return docs