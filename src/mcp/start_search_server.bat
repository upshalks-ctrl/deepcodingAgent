@echo off
REM MCP 搜索服务器启动脚本 (Windows)

echo =============================================
echo MCP 搜索服务器
echo =============================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.11 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查项目路径
if not exist "src\mcp\run_search_server.py" (
    echo 错误: 未找到 run_search_server.py
    echo 请确保在项目根目录下运行此脚本
    pause
    exit /b 1
)

echo 启动 MCP 搜索服务器...
echo.

REM 启动服务器
python src\mcp\run_search_server.py %*

pause
