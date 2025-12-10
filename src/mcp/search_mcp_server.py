#!/usr/bin/env python3
"""
MCP 搜索服务器 - 简化版

通过标准输入输出提供 MCP 协议服务
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List

from src.tools.search import (
    get_web_search_tool,
    TavilySearchTool,
    DuckDuckGoSearchTool,
    ArxivSearchTool,
    WikipediaSearchTool,
)

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class MCPSearchServer:
    def __init__(self):
        self.tools = self._register_tools()

    def _register_tools(self):
        """注册搜索工具"""
        return {
            "tavily_search": {
                "name": "tavily_search",
                "description": "使用 Tavily Search API 进行网络搜索",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索查询"},
                        "max_results": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            },
            "duckduckgo_search": {
                "name": "duckduckgo_search",
                "description": "使用 DuckDuckGo 进行免费搜索",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索查询"},
                        "max_results": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            },
            "arxiv_search": {
                "name": "arxiv_search",
                "description": "搜索 ArXiv 学术论文",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索查询"},
                        "max_results": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            },
            "wikipedia_search": {
                "name": "wikipedia_search",
                "description": "搜索 Wikipedia 百科全书",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索查询"},
                        "max_results": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            }
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理 MCP 请求"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "search-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                }

            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": list(self.tools.values())
                    }
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                if tool_name not in self.tools:
                    raise ValueError(f"Unknown tool: {tool_name}")

                result = await self._execute_tool(tool_name, arguments)

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result
                            }
                        ]
                    }
                }

            else:
                return self._error_response(request_id, -32601, "Method not found")

        except Exception as e:
            logger.error(f"Error: {e}")
            return self._error_response(request_id, -32603, str(e))

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """执行搜索工具"""
        query = arguments["query"]
        max_results = arguments.get("max_results", 5)

        if tool_name == "tavily_search":
            tool = TavilySearchTool(max_results=max_results)
        elif tool_name == "duckduckgo_search":
            tool = DuckDuckGoSearchTool(max_results=max_results)
        elif tool_name == "arxiv_search":
            tool = ArxivSearchTool(max_results=max_results)
        elif tool_name == "wikipedia_search":
            tool = WikipediaSearchTool(max_results=max_results)
        else:
            tool = get_web_search_tool(max_search_results=max_results)

        # 异步执行搜索
        result = await tool._arun(query)
        return result

    def _error_response(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        """返回错误响应"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

    async def run(self):
        """运行服务器"""
        logger.info("MCP Search Server started")

        # 读取初始化请求
        init_line = sys.stdin.readline()
        if init_line:
            try:
                init_request = json.loads(init_line.strip())
                init_response = await self.handle_request(init_request)
                print(json.dumps(init_response), flush=True)
            except Exception as e:
                logger.error(f"Initialization error: {e}")
                return

        # 主循环
        while True:
            line = sys.stdin.readline()
            if not line:
                break

            try:
                request = json.loads(line.strip())
                response = await self.handle_request(request)
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                logger.error("Invalid JSON")
            except Exception as e:
                logger.error(f"Error: {e}")


async def main():
    server = MCPSearchServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nServer stopped")
