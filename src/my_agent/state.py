"""
基础状态管理模块

定义messageState作为基础状态，只包含消息列表
"""

from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


class MessageState(TypedDict):
    """
    基础消息状态

    只包含消息列表，其他状态可以继承此类并添加更多字段
    """
    messages: List[Dict[str, Any]]


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    progress: int = 0
    stage: str = "initialized"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Metadata:
    """元数据信息"""
    task_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)

