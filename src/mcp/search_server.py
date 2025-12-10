#!/usr/bin/env python3
"""
MCP 搜索服务器

通过 MCP (Model Context Protocol) 协议提供搜索工具
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from src.tools.search import (
    get_web_search_tool,
    TavilySearchTool,
    DuckDuckGoSearchTool,
    ArxivSearchTool,
    WikipediaSearchTool,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SearchMCPServer:
    """MCP 搜索服务器"""

    def __init__(self):
        self.tools = {}
        self._setup_tools()

    def _setup_tools(self):
        """设置可用的搜索工具"""
        # Tavily 搜索
        self.tools["tavily_search"] = {
            "name": "tavily_search",
            "description": "使用 Tavily Search API 进行网络搜索，支持图片搜索",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数",
                        "default": 5
                    },
                    "include_answer": {
                        "type": "boolean",
                        "description": "是否包含答案",
                        "default": False
                    },
                    "include_images": {
                        "type": "boolean",
                        "description": "是否包含图片",
                        "default": True
                    }
                },
                "required": ["query"]
            }
        }

        # DuckDuckGo 搜索
        self.tools["duckduckgo_search"] = {
            "name": "duckduckgo_search",
            "description": "使用 DuckDuckGo 进行免费搜索，保护隐私",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }

        # ArXiv 搜索
        self.tools["arxiv_search"] = {
            "name": "arxiv_search",
            "description": "搜索 ArXiv 学术论文",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }

        # Wikipedia 搜索
        self.tools["wikipedia_search"] = {
            "name": "wikipedia_search",
            "description": "搜索 Wikipedia 百科全书",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数",
                        "default": 5
                    },
                    "lang": {
                        "type": "string",
                        "description": "语言",
                        "default": "en"
                    }
                },
                "required": ["query"]
            }
        }

        # 通用搜索工具
        self.tools["web_search"] = {
            "name": "web_search",
            "description": "使用配置的搜索引擎进行网络搜索",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }

    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理 initialize 请求"""
        logger.info("Initializing MCP Search Server")
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "search-server",
                "version": "1.0.0",
                "description": "MCP 搜索服务器，提供多种搜索引擎访问"
            }
        }

    async def handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理 list_tools 请求"""
        logger.info("Listing available tools")
        return {
            "tools": list(self.tools.values())
        }

    async def handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理 call_tool 请求"""
        logger.info(f"Calling tool: {name} with args: {arguments}")

        try:
            if name == "tavily_search":
                return await self._call_tavily_search(arguments)
            elif name == "duckduckgo_search":
                return await self._call_duckduckgo_search(arguments)
            elif name == "arxiv_search":
                return await self._call_arxiv_search(arguments)
            elif name == "wikipedia_search":
                return await self._call_wikipedia_search(arguments)
            elif name == "web_search":
                return await self._call_web_search(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}"
                    }
                ],
                "isError": True
            }

    async def _call_tavily_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用 Tavily 搜索"""
        query = arguments["query"]
        max_results = arguments.get("max_results", 5)
        include_answer = arguments.get("include_answer", False)
        include_images = arguments.get("include_images", True)

        tool = TavilySearchTool(
            max_results=max_results,
            include_answer=include_answer,
            include_images=include_images
        )

        result = await tool._arun(query)
        return {
            "content": [
                {
                    "type": "text",
                    "text": result
                }
            ]
        }

    async def _call_duckduckgo_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用 DuckDuckGo 搜索"""
        query = arguments["query"]
        max_results = arguments.get("max_results", 5)

        tool = DuckDuckGoSearchTool(max_results=max_results)
        result = await tool._arun(query)
        return {
            "content": [
                {
                    "type": "text",
                    "text": result
                }
            ]
        }

    async def _call_arxiv_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用 ArXiv 搜索"""
        query = arguments["query"]
        max_results = arguments.get("max_results", 5)

        tool = ArxivSearchTool(max_results=max_results)
        result = await tool._arun(query)
        return {
            "content": [
                {
                    "type": "text",
                    "text": result
                }
            ]
        }

    async def _call_wikipedia_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用 Wikipedia 搜索"""
        query = arguments["query"]
        max_results = arguments.get("max_results", 5)
        lang = arguments.get("lang", "en")

        tool = WikipediaSearchTool(max_results=max_results, lang=lang)
        result = await tool._arun(query)
        return {
            "content": [
                {
                    "type": "text",
                    "text": result
                }
            ]
        }

    async def _call_web_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用通用网络搜索"""
        query = arguments["query"]
        max_results = arguments.get("max_results", 5)

        tool = get_web_search_tool(max_search_results=max_results)
        result = await tool._arun(query)
        return {
            "content": [
                {
                    "type": "text",
                    "text": result
                }
            ]
        }

    async def run(self):
        """运行 MCP 服务器"""
        logger.info("Starting MCP Search Server...")

        try:
            # 读取初始化请求
            init_request = await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )
            init_data = json.loads(init_request)

            # 处理 initialize
            init_response = await self.handle_initialize(init_data.get("params", {}))
            await self._send_response(init_response)

            # 主循环：处理请求
            while True:
                try:
                    line = await asyncio.get_event_loop().run_in_executor(
                        None, sys.stdin.readline
                    )

                    if not line:
                        break

                    request = json.loads(line)
                    method = request.get("method")
                    params = request.get("params", {})
                    request_id = request.get("id")

                    if method == "tools/list":
                        response = await self.handle_list_tools(params)
                    elif method == "tools/call":
                        tool_name = params.get("name")
                        arguments = params.get("arguments", {})
                        response = await self.handle_call_tool(tool_name, arguments)
                    else:
                        response = {
                            "error": {"code": -32601, "message": "Method not found"},
                            "id": request_id
                        }

                    if request_id:
                        response["id"] = request_id
                        await self._send_response(response)

                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                except Exception as e:
                    logger.error(f"Request handling error: {e}", exc_info=True)
                    if 'request_id' in locals():
                        await self._send_response({
                            "id": request_id,
                            "error": {"code": -32603, "message": str(e)}
                        })

        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
        finally:
            logger.info("MCP Search Server stopped")

    async def _send_response(self, response: Dict[str, Any]):
        """发送响应"""
        response_line = json.dumps(response, ensure_ascii=False)
        print(response_line, flush=True)


async def main():
    """主函数"""
    server = SearchMCPServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped")
        sys.exit(0)
