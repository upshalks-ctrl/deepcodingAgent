# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import json
import os
from typing import Dict, List, Optional

import aiohttp
import requests

from src.config import load_yaml_config
from src.tools.search_postprocessor import SearchResultPostProcessor

# Tavily API URL
TAVILY_API_URL = "https://api.tavily.com"


def get_search_config():
    """获取搜索配置"""
    config = load_yaml_config("conf.yaml")
    search_config = config.get("SEARCH_ENGINE", {})
    return search_config


class EnhancedTavilySearchAPIWrapper:
    """Tavily 搜索 API 包装器"""

    def __init__(self, api_key: Optional[str] = None):
        """初始化 API 包装器

        Args:
            api_key: Tavily API 密钥，如果未提供则从环境变量获取
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")

    def raw_results(
        self,
        query: str,
        max_results: Optional[int] = 5,
        search_depth: Optional[str] = "advanced",
        include_domains: Optional[List[str]] = [],
        exclude_domains: Optional[List[str]] = [],
        include_answer: Optional[bool] = False,
        include_raw_content: Optional[bool] = False,
        include_images: Optional[bool] = False,
        include_image_descriptions: Optional[bool] = False,
    ) -> Dict:
        """获取原始搜索结果

        Args:
            query: 搜索查询
            max_results: 最大结果数
            search_depth: 搜索深度 ("basic" 或 "advanced")
            include_domains: 包含的域名列表
            exclude_domains: 排除的域名列表
            include_answer: 是否包含答案
            include_raw_content: 是否包含原始内容
            include_images: 是否包含图片
            include_image_descriptions: 是否包含图片描述

        Returns:
            原始搜索结果字典
        """
        params = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_domains": include_domains,
            "exclude_domains": exclude_domains,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "include_images": include_images,
            "include_image_descriptions": include_image_descriptions,
        }

        response = requests.post(
            f"{TAVILY_API_URL}/search",
            json=params,
        )
        response.raise_for_status()
        return response.json()

    async def raw_results_async(
        self,
        query: str,
        max_results: Optional[int] = 5,
        search_depth: Optional[str] = "advanced",
        include_domains: Optional[List[str]] = [],
        exclude_domains: Optional[List[str]] = [],
        include_answer: Optional[bool] = False,
        include_raw_content: Optional[bool] = False,
        include_images: Optional[bool] = False,
        include_image_descriptions: Optional[bool] = False,
    ) -> Dict:
        """异步获取原始搜索结果

        Args:
            query: 搜索查询
            max_results: 最大结果数
            search_depth: 搜索深度 ("basic" 或 "advanced")
            include_domains: 包含的域名列表
            exclude_domains: 排除的域名列表
            include_answer: 是否包含答案
            include_raw_content: 是否包含原始内容
            include_images: 是否包含图片
            include_image_descriptions: 是否包含图片描述

        Returns:
            原始搜索结果字典
        """
        params = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_domains": include_domains,
            "exclude_domains": exclude_domains,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "include_images": include_images,
            "include_image_descriptions": include_image_descriptions,
        }

        async def fetch() -> str:
            async with aiohttp.ClientSession(trust_env=True) as session:
                async with session.post(f"{TAVILY_API_URL}/search", json=params) as res:
                    if res.status == 200:
                        data = await res.text()
                        return data
                    else:
                        raise Exception(f"Error {res.status}: {res.reason}")

        results_json_str = await fetch()
        return json.loads(results_json_str)

    def clean_results_with_images(
        self, raw_results: Dict[str, List[Dict]]
    ) -> List[Dict]:
        """清理和格式化搜索结果

        Args:
            raw_results: 原始搜索结果

        Returns:
            清理后的结果列表
        """
        results = raw_results.get("results", [])
        clean_results = []

        # 处理网页结果
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

        # 处理图片结果
        images = raw_results.get("images", [])
        for image in images:
            clean_result = {
                "type": "image_url",
                "image_url": {"url": image.get("url", "")},
                "image_description": image.get("description", ""),
            }
            clean_results.append(clean_result)

        # 应用后处理器
        search_config = get_search_config()
        clean_results = SearchResultPostProcessor(
            min_score_threshold=search_config.get("min_score_threshold"),
            max_content_length_per_page=search_config.get(
                "max_content_length_per_page"
            ),
        ).process_results(clean_results)

        return clean_results
