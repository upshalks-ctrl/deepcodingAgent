"""
MCP 管理器

管理 MCP 服务器的连接、工具发现和工具调用
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from .mcp_client import MCPServerConfig
from .models import ToolDefinition, ToolResult

logger = logging.getLogger(__name__)

# 导入真实搜索工具
try:
    from src.tools.search import TavilySearchTool, DuckDuckGoSearchTool
except ImportError:
    logger.warning("Failed to import search tools")
    TavilySearchTool = None
    DuckDuckGoSearchTool = None


class MCPManager:
    """MCP 服务器管理器"""

    def __init__(self):
        self.servers: Dict[str, MCPServerConfig] = {}
        self.tools: Dict[str, ToolDefinition] = {}
        self._running = False

    async def add_server(self, config: MCPServerConfig) -> bool:
        """添加 MCP 服务器并加载工具"""
        try:
            self.servers[config.id] = config
            logger.info(f"Added MCP server: {config.id}")

            # 尝试加载 MCP 工具（模拟实现）
            await self._load_mcp_tools(config.id)

            return True
        except Exception as e:
            logger.error(f"Failed to add MCP server: {e}")
            return False

    async def _load_mcp_tools(self, server_id: str):
        """加载 MCP 工具（模拟实现）"""
        try:
            # 模拟加载 MCP 工具
            # 在实际实现中，这里应该与 MCP 服务器通信，获取工具列表
            logger.info(f"Loading MCP tools from server: {server_id}")

            # 模拟搜索工具
            mock_tools = [
                {
                    "name": "tavily_search",
                    "description": "使用 Tavily Search API 进行网络搜索",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "搜索查询"},
                            "max_results": {"type": "integer", "default": 5}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "duckduckgo_search",
                    "description": "使用 DuckDuckGo 进行免费搜索",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "搜索查询"},
                            "max_results": {"type": "integer", "default": 5}
                        },
                        "required": ["query"]
                    }
                }
            ]

            # 注册模拟工具
            for tool_config in mock_tools:
                tool_def = ToolDefinition(
                    name=tool_config["name"],
                    description=tool_config["description"],
                    parameters=tool_config["parameters"],
                    server_id=server_id
                )
                self.tools[tool_config["name"]] = tool_def
                logger.info(f"Loaded MCP tool: {tool_config['name']} from {server_id}")

        except Exception as e:
            logger.error(f"Failed to load MCP tools from {server_id}: {e}")

    async def remove_server(self, server_id: str) -> bool:
        """移除 MCP 服务器"""
        if server_id in self.servers:
            del self.servers[server_id]
            # 移除相关工具
            self.tools = {
                k: v for k, v in self.tools.items() 
                if v.server_id != server_id
            }
            logger.info(f"Removed MCP server: {server_id}")
            return True
        return False

    def get_all_tools(self) -> List[ToolDefinition]:
        """获取所有可用工具"""
        return list(self.tools.values())

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """调用工具"""
        try:
            logger.info(f"Calling tool: {tool_name} with args: {arguments}")

            # 检查工具是否存在
            if tool_name not in self.tools:
                return ToolResult(
                    success=False,
                    error=f"Tool '{tool_name}' not found"
                )

            # 获取工具定义
            tool_def = self.tools[tool_name]
            server_id = tool_def.server_id

            # 根据工具名称执行实际逻辑
            if tool_name == "tavily_search":
                result = await self._call_tavily_search(arguments)
            elif tool_name == "duckduckgo_search":
                result = await self._call_duckduckgo_search(arguments)
            else:
                # 通用工具调用逻辑
                result = await self._call_generic_tool(tool_name, arguments, server_id)

            return ToolResult(success=True, data=result)

        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            return ToolResult(success=False, error=str(e))

    async def _call_tavily_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用 Tavily 搜索 API"""
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 5)

        logger.info(f"Tavily search: query='{query}', max_results={max_results}")

        # 使用真实的 Tavily 搜索工具
        if TavilySearchTool:
            try:
                tool = TavilySearchTool(max_results=max_results)
                result_str = await tool._arun(query)

                # 解析 JSON 结果
                try:
                    result_data = json.loads(result_str)
                    return {
                        "query": query,
                        "results": result_data,
                        "total_results": len(result_data) if isinstance(result_data, list) else 0
                    }
                except json.JSONDecodeError:
                    # 如果解析失败，返回原始字符串
                    return {
                        "query": query,
                        "results": [{"content": result_str}],
                        "total_results": 1
                    }

            except Exception as e:
                logger.error(f"Tavily search error: {e}")
                return {
                    "query": query,
                    "error": str(e),
                    "results": []
                }
        else:
            # 降级到模拟结果
            logger.warning("TavilySearchTool not available, using mock result")
            return {
                "query": query,
                "results": [
                    {
                        "title": f"Search result {i+1} for '{query}'",
                        "url": f"https://example.com/result{i+1}",
                        "snippet": f"This is a mock search result for the query '{query}'"
                    }
                    for i in range(min(max_results, 5))
                ],
                "total_results": max_results * 10,
                "note": "Mock result - TavilySearchTool not available"
            }

    async def _call_duckduckgo_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用 DuckDuckGo 搜索"""
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 5)

        logger.info(f"DuckDuckGo search: query='{query}', max_results={max_results}")

        # 使用真实的 DuckDuckGo 搜索工具
        if DuckDuckGoSearchTool:
            try:
                tool = DuckDuckGoSearchTool(max_results=max_results)
                result_str = await tool._arun(query)

                # 解析 JSON 结果
                try:
                    result_data = json.loads(result_str)
                    return {
                        "query": query,
                        "results": result_data,
                        "total_results": len(result_data) if isinstance(result_data, list) else 0
                    }
                except json.JSONDecodeError:
                    # 如果解析失败，返回原始字符串
                    return {
                        "query": query,
                        "results": [{"content": result_str}],
                        "total_results": 1
                    }

            except Exception as e:
                logger.error(f"DuckDuckGo search error: {e}")
                return {
                    "query": query,
                    "error": str(e),
                    "results": []
                }
        else:
            # 降级到模拟结果
            logger.warning("DuckDuckGoSearchTool not available, using mock result")
            return {
                "query": query,
                "results": [
                    {
                        "title": f"DDG Result {i+1}: {query}",
                        "url": f"https://duckduckgo.com/?q={query}&result={i+1}",
                        "snippet": f"DuckDuckGo search result {i+1} for the query '{query}'"
                    }
                    for i in range(min(max_results, 5))
                ],
                "total_results": max_results * 8,
                "note": "Mock result - DuckDuckGoSearchTool not available"
            }

    async def _call_generic_tool(self, tool_name: str, arguments: Dict[str, Any], server_id: str) -> Dict[str, Any]:
        """调用通用 MCP 工具"""
        logger.info(f"Calling generic tool: {tool_name} on server: {server_id}")

        # 这里可以实现通用的 MCP 工具调用逻辑
        # 例如：通过 JSON-RPC 与 MCP 服务器通信

        # 示例：返回工具执行成功的模拟结果
        return {
            "tool": tool_name,
            "server": server_id,
            "arguments": arguments,
            "result": f"Tool '{tool_name}' executed successfully",
            "timestamp": asyncio.get_event_loop().time()
        }

    @property
    def all_servers(self) -> List[str]:
        """获取所有服务器 ID"""
        return list(self.servers.keys())

    async def shutdown(self):
        """关闭所有 MCP 服务器"""
        logger.info("Shutting down MCP manager")
        self.servers.clear()
        self.tools.clear()
        self._running = False
