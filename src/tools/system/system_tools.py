"""
System tools for agents
"""

import os
import sys
import subprocess
import platform
from typing import Any, Dict, Optional
import asyncio


class BashTool:
    """Tool for executing bash commands"""

    name = "bash"
    description = "Execute bash commands"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": BashTool.name,
                "description": BashTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Bash command to execute"
                        },
                        "cwd": {
                            "type": "string",
                            "description": "Working directory (default: current directory)",
                            "default": None
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds (default: 30)",
                            "default": 30
                        }
                    },
                    "required": ["command"]
                }
            }
        }

    @staticmethod
    async def execute(command: str, cwd: Optional[str] = None, timeout: int = 30) -> Dict[str, Any]:
        """Execute the tool"""
        try:
            # Run command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )

            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

            # Decode output
            stdout_text = stdout.decode('utf-8', errors='ignore')
            stderr_text = stderr.decode('utf-8', errors='ignore')

            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "command": command
            }
        except asyncio.TimeoutError:
            # Kill the process if it times out
            try:
                process.kill()
            except:
                pass

            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }


class PythonExecuteTool:
    """Tool for executing Python code"""

    name = "python_execute"
    description = "Execute Python code"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": PythonExecuteTool.name,
                "description": PythonExecuteTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Optional file path for context (not executed)"
                        }
                    },
                    "required": ["code"]
                }
            }
        }

    @staticmethod
    async def execute(code: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Execute the tool"""
        try:
            # Prepare namespace for execution
            namespace = {
                '__name__': '__main__',
                '__file__': file_path or '<string>'
            }

            # Capture output
            import io
            import contextlib

            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            # Execute code with output capture
            with contextlib.redirect_stdout(stdout_capture), \
                 contextlib.redirect_stderr(stderr_capture):
                try:
                    exec(code, namespace)
                    success = True
                    error = None
                except Exception as e:
                    success = False
                    error = str(e)

            # Get captured output
            stdout_text = stdout_capture.getvalue()
            stderr_text = stderr_capture.getvalue()

            return {
                "success": success,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "error": error,
                "code_length": len(code)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "code_length": len(code)
            }


class SystemInfoTool:
    """Tool for getting system information"""

    name = "system_info"
    description = "Get system information"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": SystemInfoTool.name,
                "description": SystemInfoTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "info_type": {
                            "type": "string",
                            "description": "Type of information: 'os', 'python', 'env', 'disk', 'memory'",
                            "enum": ["os", "python", "env", "disk", "memory", "all"]
                        }
                    },
                    "required": []
                }
            }
        }

    @staticmethod
    async def execute(info_type: str = "all", **kwargs) -> Dict[str, Any]:
        """Execute the tool"""
        try:
            result = {}

            if info_type in ["os", "all"]:
                result["os"] = {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor()
                }

            if info_type in ["python", "all"]:
                result["python"] = {
                    "version": sys.version,
                    "executable": sys.executable,
                    "path": sys.path
                }

            if info_type in ["env", "all"]:
                # Get relevant environment variables
                env_vars = {}
                for key in ["PATH", "PYTHONPATH", "HOME", "USER", "USERNAME"]:
                    if key in os.environ:
                        env_vars[key] = os.environ[key]
                result["environment"] = env_vars

            if info_type in ["disk", "all"]:
                import shutil
                disk_usage = shutil.disk_usage(".")
                result["disk"] = {
                    "total": disk_usage.total,
                    "used": disk_usage.used,
                    "free": disk_usage.free
                }

            if info_type in ["memory", "all"]:
                try:
                    import psutil
                    memory = psutil.virtual_memory()
                    result["memory"] = {
                        "total": memory.total,
                        "available": memory.available,
                        "percent": memory.percent
                    }
                except ImportError:
                    result["memory"] = "psutil not installed"

            return {
                "success": True,
                "info": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }