"""
人工审核hooks系统
对关键操作进行人工审核
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta

from .hooks import Hook, HookEvent, HookContext
from .registry import HookRegistry


class ApprovalStatus:
    """审核状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


@dataclass
class ApprovalRequest:
    """审核请求"""
    id: str
    operation_type: str
    description: str
    context: Dict[str, Any]
    requested_at: datetime
    timeout_minutes: int = 5
    status: str = ApprovalStatus.PENDING
    response: Optional[str] = None
    responded_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """检查是否超时"""
        return datetime.now() > self.requested_at + timedelta(minutes=self.timeout_minutes)

    def approve(self, response: str = ""):
        """批准"""
        self.status = ApprovalStatus.APPROVED
        self.response = response
        self.responded_at = datetime.now()

    def reject(self, response: str):
        """拒绝"""
        self.status = ApprovalStatus.REJECTED
        self.response = response
        self.responded_at = datetime.now()


class ApprovalManager:
    """审核管理器"""

    def __init__(self):
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.approval_history: List[ApprovalRequest] = []

    def create_request(
        self,
        operation_type: str,
        description: str,
        context: Dict[str, Any],
        timeout_minutes: int = 5
    ) -> ApprovalRequest:
        """创建审核请求"""
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.pending_requests)}"

        request = ApprovalRequest(
            id=request_id,
            operation_type=operation_type,
            description=description,
            context=context,
            requested_at=datetime.now(),
            timeout_minutes=timeout_minutes
        )

        self.pending_requests[request_id] = request
        return request

    async def wait_for_approval(self, request_id: str) -> ApprovalRequest:
        """等待审核结果"""
        request = self.pending_requests.get(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")

        # 显示审核请求
        self._display_approval_request(request)

        # 等待审核
        while request.status == ApprovalStatus.PENDING:
            if request.is_expired():
                request.status = ApprovalStatus.TIMEOUT
                break

            await asyncio.sleep(1)

        # 移动到历史记录
        self.approval_history.append(request)
        self.pending_requests.pop(request_id, None)

        return request

    def _display_approval_request(self, request: ApprovalRequest):
        """显示审核请求"""
        print("\n" + "="*80)
        print("⚠️  需要人工审核")
        print("="*80)
        print(f"请求ID: {request.id}")
        print(f"操作类型: {request.operation_type}")
        print(f"描述: {request.description}")
        print(f"超时时间: {request.timeout_minutes}分钟")
        print("\n上下文信息:")
        for key, value in request.context.items():
            print(f"  {key}: {value}")
        print("\n请在终端中输入决定:")
        print("  - 输入 'y' 或 'yes' 批准")
        print("  - 输入 'n' 或 'no' 拒绝（可附加原因）")
        print("="*80)

    async def handle_user_input(self, request_id: str, user_input: str):
        """处理用户输入"""
        request = self.pending_requests.get(request_id)
        if not request or request.status != ApprovalStatus.PENDING:
            return

        user_input = user_input.strip().lower()

        if user_input in ['y', 'yes', '是', '批准', 'approve']:
            request.approve("用户批准")
        elif user_input in ['n', 'no', '否', '拒绝', 'reject']:
            # 提取原因
            if len(user_input.split()) > 1:
                reason = " ".join(user_input.split()[1:])
            else:
                reason = "用户拒绝"
            request.reject(reason)


# 全局审核管理器
_approval_manager = ApprovalManager()


class CodeExecutionApprovalHook(Hook):
    """代码执行审核钩子"""

    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve

    @property
    def priority(self) -> int:
        return 100

    @property
    def event_type(self) -> HookEvent:
        return HookEvent.BEFORE_TOOL_CALL

    async def __call__(self, context: HookContext, **kwargs) -> HookContext:
        """审核代码执行"""
        tool_name = context.get_metadata("tool_name", "")

        # 只审核执行类工具
        if tool_name not in ["execute_python_code", "run_code_with_tests"]:
            return context

        if self.auto_approve:
            # 自动批准模式
            context.set_metadata("execution_approved", True)
            return context

        # 创建审核请求
        code = context.get_metadata("code", "")
        approval_manager = get_approval_manager()

        request = approval_manager.create_request(
            operation_type="code_execution",
            description=f"执行Python代码 ({len(code)}字符)",
            context={
                "code_preview": code[:200] + "..." if len(code) > 200 else code,
                "tool_name": tool_name
            }
        )

        # 等待审核
        result = await approval_manager.wait_for_approval(request.id)

        if result.status == ApprovalStatus.APPROVED:
            context.set_metadata("execution_approved", True)
        else:
            context.set_metadata("execution_approved", False)
            context.set_metadata("rejection_reason", result.response or "审核未通过")

        return context


class PlanApprovalHook(Hook):
    """计划审核钩子"""

    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve

    @property
    def priority(self) -> int:
        return 90

    @property
    def event_type(self) -> HookEvent:
        return HookEvent.BEFORE_AGENT

    async def __call__(self, context: HookContext, **kwargs) -> HookContext:
        """审核执行计划"""
        phase = context.get_metadata("phase", "")

        # 只审核规划阶段的结果
        if phase != "PlanningPhase":
            return context

        if self.auto_approve:
            context.set_metadata("plan_approved", True)
            return context

        # 从数据中提取计划
        state = context.data
        if hasattr(state, 'plan') and state.plan:
            plan = state.plan

            approval_manager = get_approval_manager()

            request = approval_manager.create_request(
                operation_type="plan_approval",
                description="审核执行计划",
                context={
                    "plan_preview": plan[:500] + "..." if len(plan) > 500 else plan,
                    "phase": phase
                }
            )

            # 等待审核
            result = await approval_manager.wait_for_approval(request.id)

            if result.status == ApprovalStatus.APPROVED:
                context.set_metadata("plan_approved", True)
            else:
                context.set_metadata("plan_approved", False)
                context.set_metadata("rejection_reason", result.response or "计划未通过审核")

        return context


class SystemOperationApprovalHook(Hook):
    """系统操作审核钩子"""

    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve

    @property
    def priority(self) -> int:
        return 110

    @property
    def event_type(self) -> HookEvent:
        return HookEvent.BEFORE_TOOL_CALL

    async def __call__(self, context: HookContext, **kwargs) -> HookContext:
        """审核系统级操作"""
        tool_name = context.get_metadata("tool_name", "")

        # 需要审核的系统操作
        dangerous_operations = [
            "install_package",
            "file_delete",
            "file_move",
            "shell_execute",
            "network_request"
        ]

        if tool_name not in dangerous_operations:
            return context

        if self.auto_approve:
            context.set_metadata("operation_approved", True)
            return context

        # 创建审核请求
        approval_manager = get_approval_manager()

        request = approval_manager.create_request(
            operation_type="system_operation",
            description=f"执行系统操作: {tool_name}",
            context={
                "tool_name": tool_name,
                "parameters": context.get_metadata("parameters", {})
            }
        )

        # 等待审核
        result = await approval_manager.wait_for_approval(request.id)

        if result.status == ApprovalStatus.APPROVED:
            context.set_metadata("operation_approved", True)
        else:
            context.set_metadata("operation_approved", False)
            context.set_metadata("rejection_reason", result.response or "操作未通过审核")

        return context


def get_approval_manager() -> ApprovalManager:
    """获取审核管理器"""
    return _approval_manager


def register_approval_hooks(
    registry: HookRegistry,
    auto_approve_code: bool = False,
    auto_approve_plan: bool = False,
    auto_approve_system: bool = False
):
    """注册所有审核钩子"""
    registry.register(
        CodeExecutionApprovalHook(auto_approve=auto_approve_code),
        priority=100
    )

    registry.register(
        PlanApprovalHook(auto_approve=auto_approve_plan),
        priority=90
    )

    registry.register(
        SystemOperationApprovalHook(auto_approve=auto_approve_system),
        priority=110
    )