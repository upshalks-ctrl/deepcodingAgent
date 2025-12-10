"""
钩子系统模块

提供基于事件的钩子机制，用于扩展Agent功能
"""

from .hooks import HookEvent, HookContext, Hook
from .registry import HookRegistry
from .context_manager import ContextCompressionHook, create_context_compression_hook

__all__ = [
    "HookEvent",
    "HookContext",
    "Hook",
    "HookRegistry",
    "hook",
    "ContextCompressionHook",
    "create_context_compression_hook",
]

# 全局钩子注册表
global_registry = HookRegistry()

# 钩子装饰器
def hook(event_type, priority=0):
    """钩子装饰器，用于注册钩子函数
    
    Args:
        event_type: 钩子事件类型
        priority: 钩子优先级，值越高执行顺序越靠前
    
    Returns:
        装饰后的函数
    """
    def decorator(func):
        global_registry.register(event_type, func, priority)
        return func
    return decorator
