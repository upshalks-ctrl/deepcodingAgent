"""
Sandbox工具
提供安全的代码执行环境
"""

import asyncio
import subprocess
import tempfile
import os
import shutil
import sys
import json
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .decorators import tool

@dataclass
class ExecutionResult:
    """代码执行结果"""
    stdout: str = ""
    stderr: str = ""
    return_code: int = -1
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SandboxConfig:
    """沙箱配置"""
    timeout: int = 30  # 执行超时时间（秒）
    memory_limit: str = "512M"  # 内存限制
    working_dir: Optional[str] = None  # 工作目录
    python_path: Optional[str] = None  # Python路径
    env_vars: Dict[str, str] = None  # 环境变量

    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}


class PythonSandbox:
    """Python代码执行沙箱"""

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self.temp_dir = None
        self._setup()

    def _setup(self):
        """设置沙箱环境"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix="deepcode_sandbox_")

        # 设置工作目录
        if not self.config.working_dir:
            self.config.working_dir = self.temp_dir

        # 准备环境变量
        env = os.environ.copy()
        env.update(self.config.env_vars)
        env["PYTHONPATH"] = self.temp_dir
        if self.config.python_path:
            env["PATH"] = f"{self.config.python_path}:{env.get('PATH', '')}"

        self.env = env

    async def execute_code(
        self,
        code: str,
        files: Optional[Dict[str, str]] = None,
        command: Optional[str] = None
    ) -> ExecutionResult:
        """
        执行代码

        Args:
            code: 要执行的代码
            files: 额外的文件 {filename: content}
            command: 自定义执行命令

        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()

        try:
            # 写入文件
            if files:
                for filename, content in files.items():
                    filepath = os.path.join(self.temp_dir, filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)

            # 写入主代码文件
            main_file = os.path.join(self.temp_dir, "main.py")
            with open(main_file, 'w', encoding='utf-8') as f:
                f.write(code)

            # 构建执行命令
            if not command:
                command = f"{sys.executable} main.py"

            # 执行代码
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=self.config.working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.env
            )

            # 等待执行完成
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                stdout, stderr = b"", b"Execution timeout"
                return_code = -1
            else:
                return_code = process.returncode

            # 处理输出
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')

            execution_time = time.time() - start_time

            return ExecutionResult(
                stdout=stdout_str,
                stderr=stderr_str,
                return_code=return_code,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                stdout="",
                stderr=f"Sandbox error: {str(e)}",
                return_code=-1,
                execution_time=execution_time
            )

    async def execute_test(self, code: str, test_code: str) -> ExecutionResult:
        """
        执行测试代码

        Args:
            code: 主要代码
            test_code: 测试代码

        Returns:
            ExecutionResult: 测试结果
        """
        combined_code = f"""
# Main code
{code}

# Test code
{test_code}

# Run tests
if __name__ == "__main__":
    import unittest

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
"""
        return await self.execute_code(combined_code)

    def cleanup(self):
        """清理沙箱环境"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def __del__(self):
        """析构时自动清理"""
        self.cleanup()


# 全局沙箱实例
_sandbox_instance = None


def get_sandbox(config: Optional[SandboxConfig] = None) -> PythonSandbox:
    """获取沙箱实例（单例模式）"""
    global _sandbox_instance
    if _sandbox_instance is None:
        _sandbox_instance = PythonSandbox(config)
    return _sandbox_instance


@tool
async def execute_python_code(
    code: str,
    files: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    执行Python代码

    Args:
        code: Python代码
        files: 额外的文件字典 {filename: content}
        timeout: 超时时间（秒）

    Returns:
        Dict: 包含执行结果的字典
    """
    config = SandboxConfig()
    if timeout:
        config.timeout = timeout

    sandbox = get_sandbox(config)
    result = await sandbox.execute_code(code, files)

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "return_code": result.return_code,
        "execution_time": result.execution_time,
        "success": result.return_code == 0
    }


@tool
async def run_code_with_tests(
    code: str,
    test_code: str,
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    运行代码和测试

    Args:
        code: 主要代码
        test_code: 测试代码
        timeout: 超时时间（秒）

    Returns:
        Dict: 包含测试结果的字典
    """
    config = SandboxConfig()
    if timeout:
        config.timeout = timeout

    sandbox = get_sandbox(config)
    result = await sandbox.execute_test(code, test_code)

    return {
        "test_output": result.stdout,
        "test_errors": result.stderr,
        "return_code": result.return_code,
        "execution_time": result.execution_time,
        "tests_passed": result.return_code == 0
    }


@tool
async def install_package(package_name: str, version: Optional[str] = None) -> Dict[str, Any]:
    """
    在沙箱环境中安装Python包

    Args:
        package_name: 包名
        version: 版本号（可选）

    Returns:
        Dict: 安装结果
    """
    package_spec = f"{package_name}=={version}" if version else package_name

    config = SandboxConfig()
    sandbox = get_sandbox(config)

    result = await sandbox.execute_code(
        code=f"",
        command=f"pip install {package_spec}"
    )

    return {
        "package": package_spec,
        "installed": result.return_code == 0,
        "output": result.stdout,
        "errors": result.stderr
    }


@tool
def cleanup_sandbox():
    """
    清理沙箱环境
    """
    global _sandbox_instance
    if _sandbox_instance:
        _sandbox_instance.cleanup()
        _sandbox_instance = None
    return {"status": "cleaned"}