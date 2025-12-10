# V1 - 旧版本（保持向后兼容）
from src.rag.builder import build_retriever
from src.rag.rag import Resource, Retriever

# V2 - 新版本 (暂时注释掉，因为缺少依赖)
# from src.rag.models import (
#     ContentType,
#     DocumentSource,
#     DocumentMetadata,
#     ChunkMetadata,
#     ImageContent,
#     TableContent,
#     EquationContent,
#     CodeContent,
#     DocumentChunk,
#     Document,
#     QueryRequest,
#     QueryResult,
#     QueryResponse,
#     IndexStats,
#     BatchInsertRequest,
#     BatchInsertResponse,
# )

# from src.rag.base import (
#     BaseVectorStorage,
#     BaseMetadataStorage,
#     BaseDocumentParser,
#     BaseEmbeddingProvider,
#     BaseQuestionGenerator,
#     BaseReranker,
#     RAGEngine,
# )

# from src.rag.qdrant_v2 import QdrantVectorStorageV2
# from src.rag.engine_v2 import SimpleRAGEngine
# from src.rag.factory import RAGFactory, create_rag_engine
# from src.rag.rag_tool import (
#     RAGSearchTool,
#     RAGAddDocumentTool,
#     RAGAddFolderTool,
#     RAGDeleteDocumentTool,
#     RAGStatsTool,
#     RAGLoadParsedDocumentsTool,
#     RAGListParsedDocumentsTool,
#     RAGRemoveParsedDocumentTool,
# )

__all__ = [
    # V1 exports
    "Retriever",
    "Resource",
    "build_retriever",

    # V2 models
    "ContentType",
    "DocumentSource",
    "DocumentMetadata",
    "ChunkMetadata",
    "ImageContent",
    "TableContent",
    "EquationContent",
    "CodeContent",
    "DocumentChunk",
    "Document",
    "QueryRequest",
    "QueryResult",
    "QueryResponse",
    "IndexStats",
    "BatchInsertRequest",
    "BatchInsertResponse",

    # V2 base classes
    "BaseVectorStorage",
    "BaseMetadataStorage",
    "BaseDocumentParser",
    "BaseEmbeddingProvider",
    "BaseQuestionGenerator",
    "BaseReranker",
    "RAGEngine",

    # V2 implementations
    "QdrantVectorStorageV2",
    "SimpleRAGEngine",
    "RAGFactory",
    "create_rag_engine",

    # V2 tools
    "RAGSearchTool",
    "RAGAddDocumentTool",
    "RAGAddFolderTool",
    "RAGDeleteDocumentTool",
    "RAGStatsTool",
    "RAGLoadParsedDocumentsTool",
    "RAGListParsedDocumentsTool",
    "RAGRemoveParsedDocumentTool",
]
