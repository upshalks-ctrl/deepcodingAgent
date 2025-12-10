#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索工具 Agent 示例

演示如何使用重构后的搜索工具与 Agent 集成
"""

import asyncio
import json
import os
import sys

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.myllms.factory import get_llm_by_type
from src.my_agent.agent import create_my_agent
from src.tools.search import (
    get_web_search_tool,
    TavilySearchTool,
    DuckDuckGoSearchTool,
    ArxivSearchTool,
    WikipediaSearchTool,
)


# ========== 搜索引擎依赖推荐 ==========

SEARCH_ENGINE_DEPENDENCIES = {
    "tavily": {
        "name": "Tavily Search",
        "description": "专业的搜索 API，提供高质量的搜索结果",
        "api_required": True,
        "pip_install": "# Tavily Search API\n# 1. 获取 API Key: https://tavily.com/\n# 2. 安装: pip install requests aiohttp\n# 3. 设置环境变量: export TAVILY_API_KEY=your_api_key\n",
        "features": ["网页搜索", "图片搜索", "答案生成", "高级过滤"],
        "recommended": True,
    },
    "duckduckgo": {
        "name": "DuckDuckGo Search",
        "description": "免费的搜索引擎，保护隐私",
        "api_required": False,
        "pip_install": "# DuckDuckGo Search\npip install duckduckgo-search requests aiohttp\n",
        "features": ["网页搜索", "图片搜索", "无 API 密钥"],
        "recommended": True,
    },
    "arxiv": {
        "name": "ArXiv Search",
        "description": "学术论文搜索",
        "api_required": False,
        "pip_install": "# ArXiv Search\npip install arxiv requests aiohttp\n",
        "features": ["学术论文", "预印本", "物理/数学/计算机科学"],
        "recommended": True,
    },
    "wikipedia": {
        "name": "Wikipedia Search",
        "description": "百科全书搜索",
        "api_required": False,
        "pip_install": "# Wikipedia Search\npip install wikipedia requests aiohttp\n",
        "features": ["百科全书", "多语言支持", "页面摘要"],
        "recommended": True,
    },
}


def print_dependency_guide():
    """打印搜索引擎依赖指南"""
    print("=" * 80)
    print("搜索引擎依赖指南")
    print("=" * 80)
    print("\n支持的搜索引擎及其依赖：\n")

    for engine, info in SEARCH_ENGINE_DEPENDENCIES.items():
        print(f"\n{'='*80}")
        print(f"搜索引擎: {info['name']}")
        print(f"描述: {info['description']}")
        print(f"API 密钥: {'需要' if info['api_required'] else '不需要'}")
        print(f"功能: {', '.join(info['features'])}")
        print(f"安装命令:")
        print(info['pip_install'])

    print("\n" + "=" * 80)
    print("推荐配置")
    print("=" * 80)
    print("""
推荐的搜索引擎组合：
1. Tavily Search（主要）+ DuckDuckGo（备用）
2. ArXiv（学术搜索）+ Wikipedia（百科全书）
3. DuckDuckGo（完全免费，无 API 密钥）

快速开始（无 API 密钥）：
  export SEARCH_API=duckduckgo
  pip install duckduckgo-search requests aiohttp
  python search_example.py
""")


# ========== 示例 1: 使用配置好的搜索工具 ==========

async def example1_with_configured_search():
    """示例 1: 使用配置好的搜索工具"""
    print("\n" + "=" * 80)
    print("示例 1: 使用配置好的搜索工具")
    print("=" * 80)

    try:
        # 获取配置好的搜索工具
        search_tool = get_web_search_tool(max_search_results=3)
        print(f"\n✓ 获取搜索工具: {search_tool.name}")
        print(f"  工具类型: {type(search_tool).__name__}")

        # 创建 Agent 并注册搜索工具
        agent = await create_my_agent(
            model=get_llm_by_type("basic"),
            name="SearchAgent",
            system_prompt=(
                "你是一个智能搜索助手。用户提出问题后，你需要使用搜索工具"
                "查找相关信息，然后总结并回答用户的问题。"
            ),
            base_tools=[search_tool],
            debug=True,
        )

        print(f"\n✓ Agent 创建成功: {agent.config.name}")
        print(f"  注册工具数: {agent.tools_count}")

        # 测试搜索
        query = "Python 机器学习教程"
        print(f"\n📝 用户查询: {query}")
        print("\n🤖 Agent 响应中...")

        response = await agent.ainvoke(query)
        print(f"\n✅ 响应完成:\n{response}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


# ========== 示例 2: 使用特定搜索工具 ==========

async def example2_with_specific_tool():
    """示例 2: 使用特定搜索工具"""
    print("\n" + "=" * 80)
    print("示例 2: 使用特定搜索工具")
    print("=" * 80)

    try:
        # 创建特定的搜索工具
        # Tavily 搜索（需要 API 密钥）
        tavily_tool = TavilySearchTool(
            max_results=3,
            include_answer=True,
            include_images=True,
        )

        # DuckDuckGo 搜索（无需 API 密钥）
        ddg_tool = DuckDuckGoSearchTool(max_results=5)

        # ArXiv 搜索（学术）
        arxiv_tool = ArxivSearchTool(max_results=3)

        # Wikipedia 搜索
        wiki_tool = WikipediaSearchTool(max_results=3, lang="zh")

        # 创建 Agent，注册多个搜索工具
        agent = await create_my_agent(
            model=get_llm_by_type("basic"),
            name="MultiSearchAgent",
            system_prompt=(
                "你是一个多搜索引擎助手。根据用户的问题，"
                "选择合适的搜索引擎进行搜索。"
            ),
            base_tools=[tavily_tool, ddg_tool, arxiv_tool, wiki_tool],
            debug=True,
        )

        print(f"\n✓ Agent 创建成功: {agent.config.name}")
        print(f"  注册工具数: {agent.tools_count}")
        print(f"  工具列表: {[tool.name for tool in agent.get_all_tools()]}")

        # 测试学术搜索
        query = "transformer architecture neural networks"
        print(f"\n📝 学术查询: {query}")
        print("\n🤖 Agent 响应中...")

        response = await agent.ainvoke(query)
        print(f"\n✅ 响应完成:\n{response}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


# ========== 示例 3: 装饰器方式注册搜索 ==========

async def example3_with_decorator():
    """示例 3: 使用装饰器方式注册搜索工具"""
    print("\n" + "=" * 80)
    print("示例 3: 使用装饰器方式")
    print("=" * 80)

    try:
        from src.tools.decorators import tool

        @tool()
        def custom_search(query: str) -> str:
            """自定义搜索工具"""
            # 获取配置好的搜索工具
            search_tool = get_web_search_tool(max_search_results=3)
            # 执行搜索
            result = search_tool._run(query)
            return result

        # 创建 Agent 并注册装饰器工具
        agent = await create_my_agent(
            model=get_llm_by_type("basic"),
            name="CustomSearchAgent",
            system_prompt=(
                "你是一个自定义搜索助手。使用提供的搜索工具"
                "查找信息并回答用户问题。"
            ),
            decorated_tools=[custom_search],
            debug=True,
        )

        print(f"\n✓ Agent 创建成功: {agent.config.name}")
        print(f"  注册工具数: {agent.tools_count}")

        # 测试异步调用
        query = "人工智能最新发展"
        print(f"\n📝 查询: {query}")
        print("\n🤖 Agent 响应中...")

        response = await agent.ainvoke(query)
        print(f"\n✅ 响应完成:\n{response}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


# ========== 示例 4: 手动工具注册 ==========

async def example4_manual_registration():
    """示例 4: 手动注册搜索工具"""
    print("\n" + "=" * 80)
    print("示例 4: 手动注册搜索工具")
    print("=" * 80)

    try:
        # 创建 Agent
        agent = await create_my_agent(
            model=get_llm_by_type("basic"),
            name="ManualAgent",
            system_prompt=(
                "你是一个助手。可以使用搜索工具查找信息。"
            ),
            debug=True,
        )

        # 手动注册搜索工具
        search_tool = get_web_search_tool(max_search_results=3)

        agent.register_tool_from_base_tool(search_tool)

        print(f"\n✓ Agent 创建成功: {agent.config.name}")
        print(f"  注册工具数: {agent.tools_count}")

        # 测试工具调用
        query = "最新科技新闻"
        print(f"\n📝 查询: {query}")
        print("\n🤖 Agent 响应中...")

        response = await agent.ainvoke(query)
        print(f"\n✅ 响应完成:\n{response}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


# ========== 主函数 ==========

async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("搜索工具 Agent 示例")
    print("=" * 80)

    # 打印依赖指南
    print_dependency_guide()

    # 检查环境变量
    print("\n" + "=" * 80)
    print("环境检查")
    print("=" * 80)
    search_api = os.getenv("SEARCH_API", "未设置")
    tavily_key = os.getenv("TAVILY_API_KEY", "未设置")
    print(f"SEARCH_API: {search_api}")
    print(f"TAVILY_API_KEY: {'已设置' if tavily_key != '未设置' else '未设置'}")

    # 运行示例
    print("\n" + "=" * 80)
    print("运行示例")
    print("=" * 80)

    # 示例 1: 配置好的搜索工具
    await example1_with_configured_search()

    # 示例 2: 特定搜索工具
    await example2_with_specific_tool()

    # 示例 3: 装饰器方式
    await example3_with_decorator()

    # 示例 4: 手动注册
    await example4_manual_registration()

    print("\n" + "=" * 80)
    print("所有示例运行完成")
    print("=" * 80)


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
