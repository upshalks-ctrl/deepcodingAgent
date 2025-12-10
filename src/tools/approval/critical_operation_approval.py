"""
关键操作审批工具

用于在执行危险或重要操作前进行人工审批
"""

import json
from typing import Dict, Any, List, Optional
from src.tools.approval.approval_tools import ApprovalConfig


class CriticalOperationApproval:
    """关键操作审批管理器"""

    def __init__(self):
        self.approval_config = ApprovalConfig()

        # 定义需要审批的操作类型
        self.critical_operations = {
            "file_operations": {
                "delete": True,  # 删除文件需要审批
                "write_system": True,  # 写入系统文件需要审批
                "modify_config": True,  # 修改配置文件需要审批
            },
            "code_operations": {
                "install_dependencies": True,  # 安装依赖需要审批
                "run_untrusted_code": True,  # 运行不受信任的代码需要审批
                "access_network": True,  # 网络访问需要审批
            },
            "system_operations": {
                "execute_bash": True,  # 执行shell命令需要审批
                "modify_env": True,  # 修改环境变量需要审批
                "access_database": True,  # 访问数据库需要审批
            }
        }

    def is_approval_required(self, operation_type: str, operation: str) -> bool:
        """检查操作是否需要审批"""
        if operation_type in self.critical_operations:
            return self.critical_operations[operation_type].get(operation, False)
        return False

    async def request_approval(
        self,
        operation_type: str,
        operation: str,
        details: Dict[str, Any]
    ) -> bool:
        """
        请求人工审批

        Args:
            operation_type: 操作类型（file_operations, code_operations, system_operations）
            operation: 具体操作（delete, write_system, execute_bash等）
            details: 操作详情

        Returns:
            是否批准
        """
        # 检查是否启用了自动批准
        if self.approval_config.config.get("auto_approve", False):
            return True

        # 检查特定类型的自动批准
        approval_key = f"auto_approve_{operation_type}"
        if self.approval_config.config.get(approval_key, False):
            return True

        # 检查已批准的操作列表
        operation_id = f"{operation_type}:{operation}"
        if operation_id in self.approval_config.config.get("approved_operations", []):
            return True

        # 检查被拒绝的操作列表
        if operation_id in self.approval_config.config.get("denied_operations", []):
            return False

        # 显示审批请求
        print("\n" + "=" * 60)
        print("[关键操作审批请求]")
        print("=" * 60)
        print(f"操作类型: {operation_type}")
        print(f"具体操作: {operation}")
        print("\n操作详情:")
        for key, value in details.items():
            print(f"  {key}: {value}")
        print("\n风险等级:", self._get_risk_level(operation_type, operation))
        print("=" * 60)

        # 请求用户输入
        while True:
            print("\n请选择:")
            print("  y/yes/是 - 批准此操作")
            print("  n/no/否 - 拒绝此操作")
            print("  a/always - 总是批准此类操作")
            print("  d/deny - 总是拒绝此类操作")
            print("  s/skip - 跳过此操作")

            choice = input("\n您的选择: ").lower().strip()

            if choice in ['y', 'yes', '是']:
                return True
            elif choice in ['n', 'no', '否']:
                return False
            elif choice in ['a', 'always']:
                self.approval_config.config["approved_operations"].append(operation_id)
                self.approval_config.save_config()
                print(f"\n已记住: 将总是批准 {operation_id}")
                return True
            elif choice in ['d', 'deny']:
                self.approval_config.config["denied_operations"].append(operation_id)
                self.approval_config.save_config()
                print(f"\n已记住: 将总是拒绝 {operation_id}")
                return False
            elif choice in ['s', 'skip']:
                print("\n操作已跳过")
                return False
            else:
                print("\n无效的选择，请重试")

    def _get_risk_level(self, operation_type: str, operation: str) -> str:
        """获取操作风险等级"""
        high_risk = {
            "file_operations": ["delete", "write_system"],
            "system_operations": ["execute_bash", "modify_env"],
            "code_operations": ["run_untrusted_code"]
        }

        if operation_type in high_risk and operation in high_risk[operation_type]:
            return "🔴 高风险"
        else:
            return "🟡 中风险"

    def get_approval_status(self) -> Dict[str, Any]:
        """获取当前审批配置状态"""
        return {
            "auto_approve": self.approval_config.config.get("auto_approve", False),
            "approved_operations": self.approval_config.config.get("approved_operations", []),
            "denied_operations": self.approval_config.config.get("denied_operations", []),
            "auto_approve_types": {
                k: v for k, v in self.approval_config.config.items()
                if k.startswith("auto_approve_") and k != "auto_approve"
            }
        }


# 创建全局实例
approval_manager = CriticalOperationApproval()


# 装饰器：为工具添加审批
def require_approval(operation_type: str, operation: str):
    """装饰器：为工具函数添加审批要求"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 检查是否需要审批
            if approval_manager.is_approval_required(operation_type, operation):
                # 收集操作详情
                details = {
                    "function": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }

                # 请求审批
                if not await approval_manager.request_approval(
                    operation_type,
                    operation,
                    details
                ):
                    # 如果拒绝，返回错误结果
                    return {
                        "success": False,
                        "error": "操作被人工审批拒绝",
                        "operation": f"{operation_type}:{operation}"
                    }

            # 执行原函数
            return await func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator


# 示例：创建需要审批的工具函数
@require_approval("system_operations", "execute_bash")
async def safe_bash_execute(command: str) -> Dict[str, Any]:
    """安全的bash命令执行（需要审批）"""
    import subprocess
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@require_approval("file_operations", "delete")
async def safe_file_delete(file_path: str) -> Dict[str, Any]:
    """安全的文件删除（需要审批）"""
    import os
    try:
        os.remove(file_path)
        return {
            "success": True,
            "message": f"文件已删除: {file_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # 测试审批系统
    async def test_approval():
        print("测试审批系统")
        print("=" * 60)

        # 显示当前状态
        status = approval_manager.get_approval_status()
        print("\n当前审批配置:")
        print(json.dumps(status, indent=2, ensure_ascii=False))

        # 测试需要审批的操作
        print("\n测试执行bash命令:")
        result = await safe_bash_execute("echo 'Hello World'")
        print(f"结果: {result}")

    import asyncio
    asyncio.run(test_approval())