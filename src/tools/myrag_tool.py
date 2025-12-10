"""
基于 MyRag 的 RAG 工具
"""

import asyncio
import logging
from typing import Any, Dict



from src.rag.jsonkvDB import JsonKVStorage
from src.rag.modalprocessors import ContextExtractor
from src.rag.qdrant import QdrantRetriever
from src.tools.decorators import BaseTool, tool, log_io
from src.rag.myRag import MyRag

logger = logging.getLogger(__name__)


@tool()
class MyRagSearchTool(BaseTool):
    """
    MyRag 搜索工具
    """

    name = "myrag_search"
    description = "Search documents using MyRag system"
    schema = {
        "type": "function",
        "function": {
            "name": "myrag_search",
            "description": "Search for relevant documents using MyRag",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text"
                    },
                },
                "required": ["query"]
            }
        }
    }

    def __init__(self):
        self.rag = MyRag(ContextExtractor, QdrantRetriever(), JsonKVStorage())

    @log_io
    def execute(
        self,
        query: str,
        top_k: int = 5,
        output_dir: str = "output"
    ) -> Dict[str, Any]:
        """
        执行 MyRag 搜索

        Args:
            query: 搜索查询
            top_k: 返回结果数量
            output_dir: output 目录路径

        Returns:
            搜索结果
        """
        try:
            # 执行异步搜索
            loop = asyncio.new_event_loop()
            results = loop.run_until_complete(
                self.rag.aquery(query)
            )
            loop.close()

            # 格式化结果
            formatted_results = []
            for i, result in enumerate(results[:top_k]):
                formatted_results.append({
                    "index": i + 1,
                    "content": result[:500] + "..." if len(result) > 500 else result,
                    "length": len(result)
                })

            return {
                "success": True,
                "query": query,
                "results": formatted_results,
                "total_results": len(results),
                "top_k": top_k
            }
        except Exception as e:
            logger.error(f"MyRag search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "query": query
            }



# 导出所有工具
__all__ = [
    "MyRagSearchTool",

]