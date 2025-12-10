"""
DeepCodeAgent工具函数

提供常用的状态操作和消息处理工具函数
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import re


def get_last_user_message(messages: List[Dict[str, Any]]) -> Optional[str]:
    """
    获取最后一条用户消息

    Args:
        messages: 消息列表

    Returns:
        Optional[str]: 最后一条用户消息内容，如果没有则返回None
    """
    user_messages = [msg for msg in messages if msg.get("role") == "user"]
    return user_messages[-1]["content"] if user_messages else None


def get_last_message(messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    获取最后一条消息

    Args:
        messages: 消息列表

    Returns:
        Optional[Dict]: 最后一条消息，如果没有则返回None
    """
    return messages[-1] if messages else None


def get_all_user_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    获取所有用户消息

    Args:
        messages: 消息列表

    Returns:
        List[Dict]: 所有用户消息
    """
    return [msg for msg in messages if msg.get("role") == "user"]


def get_all_assistant_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    获取所有助手消息

    Args:
        messages: 消息列表

    Returns:
        List[Dict]: 所有助手消息
    """
    return [msg for msg in messages if msg.get("role") == "assistant"]


def get_messages_by_role(messages: List[Dict[str, Any]], role: str) -> List[Dict[str, Any]]:
    """
    根据角色获取消息

    Args:
        messages: 消息列表
        role: 消息角色

    Returns:
        List[Dict]: 指定角色的所有消息
    """
    return [msg for msg in messages if msg.get("role") == role]


def get_message_count(messages: List[Dict[str, Any]], role: Optional[str] = None) -> int:
    """
    获取消息数量

    Args:
        messages: 消息列表
        role: 可选的角色过滤

    Returns:
        int: 消息数量
    """
    if role:
        return len([msg for msg in messages if msg.get("role") == role])
    return len(messages)


def extract_requirement_from_messages(messages: List[Dict[str, Any]]) -> str:
    """
    从消息中提取用户需求（第一条用户消息）

    Args:
        messages: 消息列表

    Returns:
        str: 用户需求
    """
    last_user_msg = get_last_user_message(messages)
    return last_user_msg or ""


def filter_messages_by_keyword(messages: List[Dict[str, Any]], keyword: str) -> List[Dict[str, Any]]:
    """
    根据关键词过滤消息

    Args:
        messages: 消息列表
        keyword: 关键词

    Returns:
        List[Dict]: 包含关键词的消息
    """
    return [
        msg for msg in messages
        if keyword.lower() in msg.get("content", "").lower()
    ]


def get_messages_after_timestamp(messages: List[Dict[str, Any]], timestamp: str) -> List[Dict[str, Any]]:
    """
    获取指定时间戳之后的消息

    Args:
        messages: 消息列表
        timestamp: 时间戳（ISO格式）

    Returns:
        List[Dict]: 过滤后的消息
    """
    try:
        target_time = datetime.fromisoformat(timestamp)
        return [
            msg for msg in messages
            if datetime.fromisoformat(msg.get("timestamp", "")) > target_time
        ]
    except (ValueError, TypeError):
        return messages


def format_message_for_display(message: Dict[str, Any]) -> str:
    """
    格式化消息用于显示

    Args:
        message: 消息字典

    Returns:
        str: 格式化的消息字符串
    """
    role = message.get("role", "unknown")
    content = message.get("content", "")
    timestamp = message.get("timestamp", "")

    # 提取时间部分
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%H:%M:%S")
        except:
            time_str = timestamp
    else:
        time_str = ""

    return f"[{time_str}] {role}: {content}"


def format_conversation_history(messages: List[Dict[str, Any]], max_length: int = 2000) -> str:
    """
    格式化对话历史

    Args:
        messages: 消息列表
        max_length: 最大长度

    Returns:
        str: 格式化的对话历史
    """
    formatted = []
    for msg in messages:
        formatted.append(format_message_for_display(msg))

    conversation = "\n".join(formatted)

    # 如果超过最大长度，截取最后部分
    if len(conversation) > max_length:
        conversation = "...\n" + conversation[-max_length:]

    return conversation


def create_message(role: str, content: str, **kwargs) -> Dict[str, Any]:
    """
    创建消息字典

    Args:
        role: 消息角色
        content: 消息内容
        **kwargs: 其他消息属性

    Returns:
        Dict: 消息字典
    """
    return {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        **kwargs
    }


def create_user_message(content: str, **kwargs) -> Dict[str, Any]:
    """
    创建用户消息

    Args:
        content: 消息内容
        **kwargs: 其他消息属性

    Returns:
        Dict: 用户消息字典
    """
    return create_message("user", content, **kwargs)


def create_assistant_message(content: str, **kwargs) -> Dict[str, Any]:
    """
    创建助手消息

    Args:
        content: 消息内容
        **kwargs: 其他消息属性

    Returns:
        Dict: 助手消息字典
    """
    return create_message("assistant", content, **kwargs)


def create_system_message(content: str, **kwargs) -> Dict[str, Any]:
    """
    创建系统消息

    Args:
        content: 消息内容
        **kwargs: 其他消息属性

    Returns:
        Dict: 系统消息字典
    """
    return create_message("system", content, **kwargs)


def is_empty_message(message: Dict[str, Any]) -> bool:
    """
    检查消息是否为空

    Args:
        message: 消息字典

    Returns:
        bool: 如果消息为空或只有空白字符则返回True
    """
    content = message.get("content", "").strip()
    return len(content) == 0


def clean_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    清理消息列表，移除空消息

    Args:
        messages: 消息列表

    Returns:
        List[Dict]: 清理后的消息列表
    """
    return [msg for msg in messages if not is_empty_message(msg)]


def get_conversation_turns(messages: List[Dict[str, Any]]) -> int:
    """
    获取对话轮数（用户-助手交互次数）

    Args:
        messages: 消息列表

    Returns:
        int: 对话轮数
    """
    user_messages = get_all_user_messages(messages)
    return len(user_messages)


def extract_keywords_from_messages(messages: List[Dict[str, Any]], max_keywords: int = 10) -> List[str]:
    """
    从消息中提取关键词

    Args:
        messages: 消息列表
        max_keywords: 最大关键词数量

    Returns:
        List[str]: 提取的关键词列表
    """
    # 合并所有用户消息内容
    all_content = " ".join([
        msg.get("content", "")
        for msg in get_all_user_messages(messages)
    ])

    # 简单的关键词提取（可以后续改进）
    # 提取技术相关词汇
    tech_keywords = re.findall(r'\b(?:Python|Java|Go|Rust|TypeScript|React|Node|Docker|Kubernetes|AWS|Azure|GCP|MongoDB|PostgreSQL|Redis|GraphQL|REST|API|Microservice|Architecture|Design|Pattern)\b', all_content, re.IGNORECASE)

    # 去重并限制数量
    unique_keywords = list(dict.fromkeys(tech_keywords))
    return unique_keywords[:max_keywords]


def summarize_messages(messages: List[Dict[str, Any]], max_length: int = 500) -> str:
    """
    总结消息列表

    Args:
        messages: 消息列表
        max_length: 最大长度

    Returns:
        str: 消息总结
    """
    if not messages:
        return "没有消息"

    user_msg_count = get_message_count(messages, "user")
    assistant_msg_count = get_message_count(messages, "assistant")
    turns = get_conversation_turns(messages)

    summary = f"对话统计:\n"
    summary += f"- 总消息数: {len(messages)}\n"
    summary += f"- 用户消息: {user_msg_count}\n"
    summary += f"- 助手消息: {assistant_msg_count}\n"
    summary += f"- 对话轮数: {turns}\n"

    # 添加最后一条用户消息的摘要
    last_user_msg = get_last_user_message(messages)
    if last_user_msg:
        summary += f"\n最后用户消息: {last_user_msg[:max_length]}"

    return summary


def validate_message_structure(message: Dict[str, Any]) -> bool:
    """
    验证消息结构是否正确

    Args:
        message: 消息字典

    Returns:
        bool: 如果消息结构正确则返回True
    """
    required_fields = ["role", "content"]
    return all(field in message for field in required_fields)


def merge_messages(*message_lists: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    合并多个消息列表

    Args:
        *message_lists: 多个消息列表

    Returns:
        List[Dict]: 合并后的消息列表
    """
    merged = []
    for msg_list in message_lists:
        merged.extend(msg_list)

    # 按时间戳排序
    merged.sort(key=lambda msg: msg.get("timestamp", ""))
    return merged


def get_recent_messages(messages: List[Dict[str, Any]], count: int = 10) -> List[Dict[str, Any]]:
    """
    获取最近的N条消息

    Args:
        messages: 消息列表
        count: 要获取的消息数量

    Returns:
        List[Dict]: 最近的消息列表
    """
    return messages[-count:] if len(messages) > count else messages


def has_user_requirement_been_updated(messages: List[Dict[str, Any]], original_requirement: str) -> bool:
    """
    检查用户需求是否被更新

    Args:
        messages: 消息列表
        original_requirement: 原始需求

    Returns:
        bool: 如果需求被更新则返回True
    """
    user_messages = get_all_user_messages(messages)
    if len(user_messages) <= 1:
        return False

    # 检查是否有新的用户消息与原始需求不同
    latest_user_msg = user_messages[-1]["content"]
    return latest_user_msg.strip() != original_requirement.strip()
