import json
import logging
import os
import asyncio
from typing import Any, Dict, List, Optional

import aiohttp
import requests

from src.config import SearchEngine, load_yaml_config
from src.tools.decorators import BaseTool

logger = logging.getLogger(__name__)


def get_search_config() -> Dict[str, Any]:
    """获取搜索配置"""
    config = load_yaml_config("conf.yaml")
    search_config = config.get("SEARCH_ENGINE", {})
    return search_config


class BaseWebSearchTool(BaseTool):
    """搜索工具基类"""

    name: str = "web_search"
    description: str = "网络搜索工具"

    def __init__(self, max_results: int = 5):
        super().__init__()
        self.max_results = max_results


class TavilySearchTool(BaseWebSearchTool):
    """Tavily 搜索工具"""

    name: str = "tavily_search"
    description: str = "使用 Tavily Search API 进行网络搜索，支持图片搜索"

    def __init__(
        self,
        max_results: int = 5,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        include_answer: bool = False,
        search_depth: str = "advanced",
        include_raw_content: bool = True,
        include_images: bool = True,
        include_image_descriptions: bool = True,
    ):
        super().__init__(max_results)
        self.include_domains = include_domains or []
        self.exclude_domains = exclude_domains or []
        self.include_answer = include_answer
        self.search_depth = search_depth
        self.include_raw_content = include_raw_content
        self.include_images = include_images
        self.include_image_descriptions = include_image_descriptions
        self.api_key = os.getenv("TAVILY_API_KEY", "")

    async def execute(self, query: str) -> str:
        """异步执行搜索"""
        params = {
            "api_key": self.api_key,
            "query": query,
            "max_results": self.max_results,
            "search_depth": self.search_depth,
            "include_domains": self.include_domains,
            "exclude_domains": self.exclude_domains,
            "include_answer": self.include_answer,
            "include_raw_content": self.include_raw_content,
            "include_images": self.include_images,
            "include_image_descriptions": self.include_image_descriptions,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.tavily.com/search",
                    json=params
                ) as response:
                    response.raise_for_status()
                    raw_results = await response.json()

            # 处理结果
            results = raw_results.get("results", [])
            clean_results = []

            for result in results:
                clean_result = {
                    "type": "page",
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                }
                if result.get("raw_content"):
                    clean_result["raw_content"] = result["raw_content"]
                clean_results.append(clean_result)

            # 处理图片
            images = raw_results.get("images", [])
            for image in images:
                clean_result = {
                    "type": "image_url",
                    "image_url": {"url": image.get("url", "")},
                    "image_description": image.get("description", ""),
                }
                clean_results.append(clean_result)

            # 添加答案
            if raw_results.get("answer"):
                clean_results.insert(0, {
                    "type": "answer",
                    "content": raw_results["answer"]
                })

            return json.dumps(clean_results, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    

class DuckDuckGoSearchTool(BaseWebSearchTool):
    """DuckDuckGo 搜索工具"""

    name: str = "duckduckgo_search"
    description: str = "使用 DuckDuckGo 进行网络搜索"

    async def execute(self, query: str) -> str:
        """异步执行搜索"""
        def _search():
            try:
                from ddgs import DDGS

                results = []
                with DDGS() as ddgs:
                    search_results = ddgs.text(
                        query,
                        max_results=self.max_results,
                    )

                    for r in search_results:
                        results.append({
                            "type": "page",
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "content": r.get("body", ""),
                        })

                return json.dumps(results, ensure_ascii=False)

            except Exception as e:
                logger.error(f"DuckDuckGo search error: {e}")
                return json.dumps({"error": str(e)}, ensure_ascii=False)

        # 在单独的线程中运行同步搜索
        return await asyncio.to_thread(_search)




class ArxivSearchTool(BaseWebSearchTool):
    """ArXiv 搜索工具"""

    name: str = "arxiv_search"
    description: str = "搜索 ArXiv 学术论文"

    async def execute(self, query: str) -> str:
        """异步执行搜索"""
        def _search():
            try:
                import arxiv

                results = []
                search = arxiv.Search(
                    query=query,
                    max_results=self.max_results,
                    sort_by=arxiv.SortCriterion.Relevance,
                )

                for r in search.results():
                    results.append({
                        "type": "paper",
                        "title": r.title,
                        "url": r.entry_id,
                        "content": r.summary,
                        "authors": [str(a) for a in r.authors],
                        "published": str(r.published),
                        "categories": r.categories,
                    })

                return json.dumps(results, ensure_ascii=False)

            except Exception as e:
                logger.error(f"ArXiv search error: {e}")
                return json.dumps({"error": str(e)}, ensure_ascii=False)

        # 在单独的线程中运行同步搜索
        return await asyncio.to_thread(_search)



class WikipediaSearchTool(BaseWebSearchTool):
    """Wikipedia 搜索工具"""

    name: str = "wikipedia_search"
    description: str = "搜索 Wikipedia 百科全书"

    def __init__(self, max_results: int = 5, lang: str = "en"):
        super().__init__(max_results)
        self.lang = lang

    async def execute(self, query: str) -> str:
        """异步执行搜索"""
        def _search():
            try:
                import wikipedia

                wikipedia.set_lang(self.lang)
                results = []

                # 搜索页面
                search_results = wikipedia.search(query, results=self.max_results)

                for title in search_results:
                    try:
                        page = wikipedia.page(title)
                        results.append({
                            "type": "page",
                            "title": page.title,
                            "url": page.url,
                            "content": page.summary,
                            "categories": page.categories,
                        })
                    except wikipedia.exceptions.PageError:
                        continue
                    except wikipedia.exceptions.DisambiguationError as e:
                        # 处理消歧义页面
                        results.append({
                            "type": "disambiguation",
                            "title": title,
                            "content": str(e),
                        })

                return json.dumps(results, ensure_ascii=False)

            except Exception as e:
                logger.error(f"Wikipedia search error: {e}")
                return json.dumps({"error": str(e)}, ensure_ascii=False)

        # 在单独的线程中运行同步搜索
        return await asyncio.to_thread(_search)


def get_web_search_tool(max_search_results: int = 5):
    """
    获取配置的搜索工具

    Args:
        max_search_results: 最大搜索结果数

    Returns:
        搜索工具实例
    """
    from src.config import SELECTED_SEARCH_ENGINE

    search_config = get_search_config()

    if SELECTED_SEARCH_ENGINE == SearchEngine.TAVILY.value:
        include_domains = search_config.get("include_domains", [])
        exclude_domains = search_config.get("exclude_domains", [])
        include_answer = search_config.get("include_answer", False)
        search_depth = search_config.get("search_depth", "advanced")
        include_raw_content = search_config.get("include_raw_content", True)
        include_images = search_config.get("include_images", True)
        include_image_descriptions = include_images and search_config.get(
            "include_image_descriptions", True
        )

        logger.info(
            f"Tavily search configuration: include_domains={include_domains}, "
            f"exclude_domains={exclude_domains}, include_answer={include_answer}, "
            f"search_depth={search_depth}, include_raw_content={include_raw_content}, "
            f"include_images={include_images}, include_image_descriptions={include_image_descriptions}"
        )

        return TavilySearchTool(
            max_results=max_search_results,
            include_answer=include_answer,
            search_depth=search_depth,
            include_raw_content=include_raw_content,
            include_images=include_images,
            include_image_descriptions=include_image_descriptions,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
        )
    elif SELECTED_SEARCH_ENGINE == SearchEngine.DUCKDUCKGO.value:
        return DuckDuckGoSearchTool(max_results=max_search_results)
    elif SELECTED_SEARCH_ENGINE == SearchEngine.ARXIV.value:
        return ArxivSearchTool(max_results=max_search_results)
    elif SELECTED_SEARCH_ENGINE == SearchEngine.WIKIPEDIA.value:
        wiki_lang = search_config.get("wikipedia_lang", "en")
        return WikipediaSearchTool(max_results=max_search_results, lang=wiki_lang)
    else:
        raise ValueError(f"Unsupported search engine: {SELECTED_SEARCH_ENGINE}")


