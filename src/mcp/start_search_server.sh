#!/bin/bash
# MCP 搜索服务器启动脚本 (Linux/macOS)

set -e

echo "============================================="
echo "MCP 搜索服务器"
echo "============================================="
echo

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python 3，请先安装 Python 3.11 或更高版本"
    echo "macOS: brew install python3"
    echo "Ubuntu/Debian: sudo apt-get install python3"
    exit 1
fi

# 检查项目路径
if [ ! -f "src/mcp/run_search_server.py" ]; then
    echo "错误: 未找到 run_search_server.py"
    echo "请确保在项目根目录下运行此脚本"
    exit 1
fi

# 给脚本添加执行权限
chmod +x src/mcp/run_search_server.py

echo "启动 MCP 搜索服务器..."
echo

# 启动服务器
exec python3 src/mcp/run_search_server.py "$@"
