"""
钩子注册表

管理和触发钩子函数
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from collections import defaultdict

from .hooks import HookEvent, HookContext, Hook


class HookRegistry:
    """钩子注册表
    
    管理钩子函数的注册、注销和触发
    """
    
    def __init__(self):
        """初始化钩子注册表"""
        # 存储钩子函数：{event_type: List[(priority, hook_func)]}
        self._hooks: Dict[HookEvent, List[Tuple[int, Callable]]] = defaultdict(list)
    
    def register(
        self, 
        event_type: Union[HookEvent, str], 
        hook_func: Callable, 
        priority: int = 0
    ) -> None:
        """注册钩子函数
        
        Args:
            event_type: 钩子事件类型
            hook_func: 钩子函数，可以是同步或异步函数
            priority: 钩子优先级，值越高执行顺序越靠前
        """
        # 转换为HookEvent枚举
        if isinstance(event_type, str):
            event_type = HookEvent(event_type)
        
        # 添加到钩子列表
        self._hooks[event_type].append((priority, hook_func))
        
        # 按优先级排序，值越高越靠前
        self._hooks[event_type].sort(key=lambda x: x[0], reverse=True)
    
    def unregister(
        self, 
        event_type: Union[HookEvent, str], 
        hook_func: Callable
    ) -> bool:
        """注销钩子函数
        
        Args:
            event_type: 钩子事件类型
            hook_func: 要注销的钩子函数
            
        Returns:
            是否成功注销
        """
        # 转换为HookEvent枚举
        if isinstance(event_type, str):
            event_type = HookEvent(event_type)
        
        if event_type not in self._hooks:
            return False
        
        # 查找并删除钩子函数
        original_length = len(self._hooks[event_type])
        self._hooks[event_type] = [
            (p, f) for p, f in self._hooks[event_type] if f != hook_func
        ]
        
        return len(self._hooks[event_type]) < original_length
    
    def register_hooks(
        self, 
        hooks: List[Tuple[Union[HookEvent, str], Callable, int]]
    ) -> None:
        """批量注册钩子函数
        
        Args:
            hooks: 钩子列表，每个元素为(event_type, hook_func, priority)
        """
        for event_type, hook_func, priority in hooks:
            self.register(event_type, hook_func, priority)
    
    def clear(self, event_type: Optional[Union[HookEvent, str]] = None) -> None:
        """清空钩子函数
        
        Args:
            event_type: 可选，指定要清空的事件类型
                       如果为None，则清空所有钩子
        """
        if event_type is None:
            # 清空所有钩子
            self._hooks.clear()
        else:
            # 转换为HookEvent枚举
            if isinstance(event_type, str):
                event_type = HookEvent(event_type)
            
            # 清空指定事件类型的钩子
            if event_type in self._hooks:
                del self._hooks[event_type]
    
    async def trigger(
        self, 
        event_type: Union[HookEvent, str], 
        context: Union[HookContext, Any],
        **kwargs
    ) -> HookContext:
        """触发指定事件类型的所有钩子
        
        Args:
            event_type: 钩子事件类型
            context: 钩子上下文或数据
            **kwargs: 额外参数
            
        Returns:
            处理后的上下文
        """
        # 转换为HookEvent枚举
        if isinstance(event_type, str):
            event_type = HookEvent(event_type)
        
        # 转换为HookContext对象
        if not isinstance(context, HookContext):
            context = HookContext(data=context)
        
        # 设置事件类型
        context.event_type = event_type
        
        # 检查是否有钩子
        if event_type not in self._hooks:
            return context
        
        # 触发所有钩子
        result_context = context
        for priority, hook_func in self._hooks[event_type]:
            try:
                # 检查是否是 Hook 实例
                if isinstance(hook_func, Hook):
                    result_context = await hook_func(result_context, **kwargs)
                # 检查是否是异步函数
                elif asyncio.iscoroutinefunction(hook_func):
                    result_context = await hook_func(result_context, **kwargs)
                else:
                    result_context = hook_func(result_context, **kwargs)
            except Exception as e:
                # 捕获钩子执行异常，不影响后续钩子执行
                print(f"Hook execution failed: {e}")
        
        return result_context
    
    def get_hooks(self, event_type: Union[HookEvent, str]) -> List[Tuple[int, Callable]]:
        """获取指定事件类型的所有钩子
        
        Args:
            event_type: 钩子事件类型
            
        Returns:
            钩子列表，每个元素为(priority, hook_func)
        """
        # 转换为HookEvent枚举
        if isinstance(event_type, str):
            event_type = HookEvent(event_type)
        
        return self._hooks.get(event_type, [])
    
    def get_event_types(self) -> List[HookEvent]:
        """获取所有注册的事件类型
        
        Returns:
            事件类型列表
        """
        return list(self._hooks.keys())
    
    def get_hook_count(self, event_type: Optional[Union[HookEvent, str]] = None) -> int:
        """获取钩子数量
        
        Args:
            event_type: 可选，指定事件类型
                       如果为None，则返回所有钩子数量
            
        Returns:
            钩子数量
        """
        if event_type is None:
            # 返回所有钩子数量
            return sum(len(hooks) for hooks in self._hooks.values())
        else:
            # 转换为HookEvent枚举
            if isinstance(event_type, str):
                event_type = HookEvent(event_type)
            
            # 返回指定事件类型的钩子数量
            return len(self._hooks.get(event_type, []))
    
    def __len__(self) -> int:
        """获取钩子总数
        
        Returns:
            钩子总数
        """
        return self.get_hook_count()
