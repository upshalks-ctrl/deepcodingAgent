"""
RAG Tool - 为 DeepCodeAgent 提供的 RAG 工具
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from rag.rag import Rag
from src.tools.decorators import BaseTool, tool, log_io
from src.rag.models import QueryRequest, ContentType

logger = logging.getLogger(__name__)


@tool()
class RAGSearchTool(BaseTool):
    """
    RAG 搜索工具 - 用于搜索文档知识库
    """

    name = "rag_search"
    description = "Search documents in the RAG knowledge base"
    schema = {
        "type": "function",
        "function": {
            "name": "rag_search",
            "description": "Search for relevant documents in the knowledge base",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5
                    },
                    "filters": {
                        "type": "object",
                        "description": "Optional filters to apply to search"
                    },
                    "rerank": {
                        "type": "boolean",
                        "description": "Whether to rerank results for better relevance (default: false)",
                        "default": False
                    }
                },
                "required": ["query"]
            }
        }
    }

    def __init__(self, rag_engine: Rag):
        self.rag_engine = rag_engine

    @log_io
    def execute(self, query: str, top_k: int = 5, filters: Optional[Dict] = None, rerank: bool = False) -> Dict[str, Any]:
        """
        执行 RAG 搜索

        Args:
            query: 搜索查询
            top_k: 返回结果数量
            filters: 过滤条件
            rerank: 是否重排序

        Returns:
            搜索结果
        """
        try:
            # 创建查询请求


            # 执行搜索
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(self.rag_engine.query(query))
            loop.close()

            # 格式化结果
            results = []
            for result in response.results:
                chunk = result.chunk
                results.append({
                    "content": chunk.content,
                    "doc_id": chunk.doc_id,
                    "chunk_id": chunk.chunk_id,
                    "content_type": chunk.content_type.value,
                    "score": result.score,
                    "metadata": chunk.metadata.dict() if chunk.metadata else {}
                })

            return {
                "success": True,
                "query": query,
                "results": results,
                "total": len(results),
                "execution_time": response.execution_time
            }
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }









# 导出所有工具
__all__ = [
    "RAGSearchTool",
]