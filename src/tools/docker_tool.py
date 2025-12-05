import docker
from typing import Dict, Any, Optional
import tempfile
import os


class DockerTool:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            self.client = None
            print(f"Docker客户端初始化失败: {str(e)}")

    def is_available(self) -> bool:
        """检查Docker是否可用"""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False

    def run_code(self, code: str, language: str, timeout: int = 30) -> Dict[str, Any]:
        """在Docker容器中运行代码"""
        if not self.is_available():
            return {
                "status": "error",
                "output": "Docker不可用，请确保Docker已安装并运行",
                "exit_code": -1
            }

        # 映射语言到Docker镜像和命令
        language_configs = {
            "python": {
                "image": "python:3.10-slim",
                "extension": ".py",
                "command": ["python", "/app/code.py"]
            },
            "javascript": {
                "image": "node:18-slim",
                "extension": ".js",
                "command": ["node", "/app/code.js"]
            },
            "java": {
                "image": "openjdk:17-slim",
                "extension": ".java",
                "command": ["bash", "-c", "javac /app/code.java && java -cp /app Code"]
            },
            "cpp": {
                "image": "gcc:12-slim",
                "extension": ".cpp",
                "command": ["bash", "-c", "g++ /app/code.cpp -o /app/code && /app/code"]
            },
            "go": {
                "image": "golang:1.20-slim",
                "extension": ".go",
                "command": ["go", "run", "/app/code.go"]
            }
        }

        config = language_configs.get(language.lower())
        if not config:
            return {
                "status": "error",
                "output": f"不支持的语言: {language}",
                "exit_code": -1
            }

        try:
            # 创建临时目录存放代码
            with tempfile.TemporaryDirectory() as temp_dir:
                code_file = os.path.join(temp_dir, f"code{config['extension']}")
                with open(code_file, "w") as f:
                    f.write(code)

                # 运行Docker容器
                container = self.client.containers.run(
                    config["image"],
                    config["command"],
                    volumes={temp_dir: {"bind": "/app", "mode": "ro"}},
                    detach=True,
                    mem_limit="512m",
                    network_mode="none"  # 禁用网络，提高安全性
                )

                # 等待容器完成或超时
                container.wait(timeout=timeout)

                # 获取输出
                logs = container.logs().decode("utf-8")
                exit_code = container.attrs["State"]["ExitCode"]

                # 清理容器
                container.remove()

                return {
                    "status": "success" if exit_code == 0 else "error",
                    "output": logs,
                    "exit_code": exit_code
                }
        except Exception as e:
            return {
                "status": "error",
                "output": f"运行代码失败: {str(e)}",
                "exit_code": -1
            }

    def run_test(self, code: str, test_code: str, language: str, timeout: int = 30) -> Dict[str, Any]:
        """在Docker容器中运行测试代码"""
        if not self.is_available():
            return {
                "status": "error",
                "output": "Docker不可用，请确保Docker已安装并运行",
                "exit_code": -1
            }

        # 对于Python，使用pytest
        if language.lower() == "python":
            combined_code = f"{code}\n\n{test_code}"
            return self.run_code(combined_code, language, timeout)

        # 其他语言的测试逻辑可以在这里扩展
        return {
            "status": "error",
            "output": f"暂不支持{language}的测试功能",
            "exit_code": -1
        }

if __name__ == '__main__':
        docker_tool = DockerTool()
        print(docker_tool.is_available())
