#!/usr/bin/env python3
"""
启动 MCP 搜索服务器
"""

import asyncio
import argparse
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.mcp.search_mcp_server import MCPSearchServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='MCP 搜索服务器')
    parser.add_argument(
        '--tool',
        type=str,
        default='tavily_search',
        choices=['tavily_search', 'duckduckgo_search', 'arxiv_search', 'wikipedia_search'],
        help='默认搜索工具 (默认: tavily_search)'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=5,
        help='默认最大结果数 (默认: 5)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试日志'
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("调试模式已启用")

    # 设置环境变量
    os.environ['DEFAULT_SEARCH_TOOL'] = args.tool
    os.environ['DEFAULT_MAX_RESULTS'] = str(args.max_results)

    logger.info("=" * 60)
    logger.info("MCP 搜索服务器")
    logger.info("=" * 60)
    logger.info(f"默认搜索工具: {args.tool}")
    logger.info(f"默认最大结果数: {args.max_results}")
    logger.info("=" * 60)
    logger.info("\n启动服务器...")
    logger.info("按 Ctrl+C 停止服务器\n")

    try:
        # 启动服务器
        asyncio.run(MCPSearchServer().run())
    except KeyboardInterrupt:
        logger.info("\n服务器已停止")
    except Exception as e:
        logger.error(f"服务器错误: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
