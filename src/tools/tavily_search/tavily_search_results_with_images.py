# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import json
import logging
from typing import List, Optional

from src.tools.decorators import BaseTool
from src.tools.tavily_search.tavily_search_api_wrapper import (
    EnhancedTavilySearchAPIWrapper,
)

logger = logging.getLogger(__name__)


class TavilySearchWithImages(BaseTool):
    """Tavily 搜索工具，支持图片搜索

    Setup:
        设置环境变量 TAVILY_API_KEY

        .. code-block:: bash

            export TAVILY_API_KEY="your-api-key"

    Instantiate:

        .. code-block:: python

            from src.tools.tavily_search import TavilySearchWithImages

            tool = TavilySearchWithImages(
                max_results=5,
                include_answer=True,
                include_raw_content=True,
                include_images=True,
                include_image_descriptions=True,
            )

    Invoke:

        .. code-block:: python

            result = tool._run('who won the last french open')

        .. code-block:: json

            {
                "results": [
                    {
                        "title": "...",
                        "url": "https://...",
                        "content": "Novak Djokovic won...",
                        "score": 0.995,
                        "raw_content": "Tennis\nNovak ..."
                    }
                ],
                "images": [
                    {
                        "image_url": "https://...",
                        "image_description": "Tennis match"
                    }
                ]
            }

    """

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
        api_key: Optional[str] = None,
    ):
        """初始化 Tavily 搜索工具

        Args:
            max_results: 最大搜索结果数
            include_domains: 包含的域名列表
            exclude_domains: 排除的域名列表
            include_answer: 是否包含答案
            search_depth: 搜索深度 ("basic" 或 "advanced")
            include_raw_content: 是否包含原始内容
            include_images: 是否包含图片
            include_image_descriptions: 是否包含图片描述
            api_key: API 密钥，如果未提供则从环境变量获取
        """
        super().__init__()
        self.max_results = max_results
        self.include_domains = include_domains or []
        self.exclude_domains = exclude_domains or []
        self.include_answer = include_answer
        self.search_depth = search_depth
        self.include_raw_content = include_raw_content
        self.include_images = include_images
        self.include_image_descriptions = include_image_descriptions
        self.api_wrapper = EnhancedTavilySearchAPIWrapper(api_key=api_key)

    def _run(
        self,
        query: str,
    ) -> str:
        """执行搜索

        Args:
            query: 搜索查询

        Returns:
            JSON 格式的搜索结果
        """
        try:
            raw_results = self.api_wrapper.raw_results(
                query=query,
                max_results=self.max_results,
                search_depth=self.search_depth,
                include_domains=self.include_domains,
                exclude_domains=self.exclude_domains,
                include_answer=self.include_answer,
                include_raw_content=self.include_raw_content,
                include_images=self.include_images,
                include_image_descriptions=self.include_image_descriptions,
            )

            cleaned_results = self.api_wrapper.clean_results_with_images(raw_results)

            # 添加额外信息
            response = {
                "query": query,
                "results": cleaned_results,
                "response_time": raw_results.get("response_time"),
            }

            # 如果有答案，单独添加
            if raw_results.get("answer"):
                response["answer"] = raw_results["answer"]

            result_json = json.dumps(response, ensure_ascii=False)
            logger.debug(
                "Tavily search results: %s",
                json.dumps(cleaned_results, indent=2, ensure_ascii=False)
            )
            return result_json

        except Exception as e:
            logger.error("Tavily search error: %s", e, exc_info=True)
            error_result = json.dumps({"error": str(e)}, ensure_ascii=False)
            return error_result

    async def _arun(
        self,
        query: str,
    ) -> str:
        """异步执行搜索

        Args:
            query: 搜索查询

        Returns:
            JSON 格式的搜索结果
        """
        try:
            raw_results = await self.api_wrapper.raw_results_async(
                query=query,
                max_results=self.max_results,
                search_depth=self.search_depth,
                include_domains=self.include_domains,
                exclude_domains=self.exclude_domains,
                include_answer=self.include_answer,
                include_raw_content=self.include_raw_content,
                include_images=self.include_images,
                include_image_descriptions=self.include_image_descriptions,
            )

            cleaned_results = self.api_wrapper.clean_results_with_images(raw_results)

            response = {
                "query": query,
                "results": cleaned_results,
                "response_time": raw_results.get("response_time"),
            }

            if raw_results.get("answer"):
                response["answer"] = raw_results["answer"]

            result_json = json.dumps(response, ensure_ascii=False)
            logger.debug(
                "Tavily search async results: %s",
                json.dumps(cleaned_results, indent=2, ensure_ascii=False)
            )
            return result_json

        except Exception as e:
            logger.error("Tavily search async error: %s", e, exc_info=True)
            error_result = json.dumps({"error": str(e)}, ensure_ascii=False)
            return error_result
