"""
钩子核心实现

定义钩子事件、上下文和钩子基类
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Union


class HookEvent(Enum):
    """钩子事件类型枚举

    对应Agent执行的不同阶段
    """
    # Agent执行阶段
    BEFORE_AGENT = "before_agent"       # Agent执行前
    AFTER_AGENT = "after_agent"         # Agent执行后

    # 模型调用阶段
    BEFORE_MODEL = "before_model"       # 模型调用前
    AFTER_MODEL = "after_model"         # 模型调用后
    WRAP_MODEL_CALL = "wrap_model_call" # 模型调用包装

    # 工具调用阶段
    BEFORE_TOOL_CALL = "before_tool_call" # 工具调用前
    AFTER_TOOL_CALL = "after_tool_call"   # 工具调用后
    WRAP_TOOL_CALL = "wrap_tool_call"     # 工具调用包装

    # 澄清阶段
    BEFORE_CLARIFICATION = "before_clarification"  # 澄清前
    AFTER_CLARIFICATION = "after_clarification"    # 澄清后
    WAIT_FOR_CLARIFICATION = "wait_for_clarification"  # 等待澄清输入




@dataclass
class HookContext:
    """钩子上下文
    
    传递钩子函数执行时的上下文信息
    """
    data: Any                       # 主要数据
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    event_type: Optional[HookEvent] = None  # 事件类型
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据
        
        Args:
            key: 元数据键
            value: 元数据值
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据
        
        Args:
            key: 元数据键
            default: 默认值
            
        Returns:
            元数据值或默认值
        """
        return self.metadata.get(key, default)
    
    def update(self, **kwargs) -> None:
        """更新上下文数据
        
        Args:
            **kwargs: 要更新的数据
        """
        if isinstance(self.data, dict):
            self.data.update(kwargs)
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            上下文的字符串表示
        """
        return f"HookContext(event={self.event_type}, data={self.data}, metadata={self.metadata})"


class Hook(ABC):
    """钩子基类
    
    定义钩子的基本接口
    """
    
    @abstractmethod
    async def __call__(self, context: HookContext, **kwargs) -> HookContext:
        """调用钩子

        Args:
            context: 钩子上下文
            **kwargs: 额外参数

        Returns:
            处理后的上下文
        """
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """钩子优先级
        
        Returns:
            钩子优先级
        """
        pass
    
    @property
    @abstractmethod
    def event_type(self) -> HookEvent:
        """钩子事件类型
        
        Returns:
            钩子事件类型
        """
        pass