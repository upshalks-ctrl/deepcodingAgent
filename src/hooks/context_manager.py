"""
上下文管理器

用于管理对话历史，自动压缩消息以控制 tokens 使用量
"""

import copy
import json
import logging
import re
from typing import Any, Dict, List, Optional
from .hooks import Hook, HookEvent, HookContext
from ..myllms import get_llm_by_type

logger = logging.getLogger(__name__)


class ContextCompressionHook(Hook):
    """上下文压缩钩子"""

    def __init__(self, max_tokens: int = 100000, compression_model: str = "basic"):
        """
        初始化上下文压缩钩子

        Args:
            max_tokens: 最大允许的 tokens 数量
            compression_model: 用于压缩的模型类型
        """
        self.max_tokens = max_tokens
        self.compression_model = compression_model
        self.compression_llm = get_llm_by_type(compression_model)
        self._event_type = HookEvent.BEFORE_MODEL
        self._priority = 10
        self.preserve_prefix_message_count=6

    @property
    def event_type(self) -> HookEvent:
        """钩子事件类型"""
        return self._event_type

    @property
    def priority(self) -> int:
        """钩子优先级"""
        return self._priority

    async def __call__(self, context: HookContext, **kwargs) -> HookContext:
        """调用钩子"""
        return await self.execute(context)

    async def execute(self, context: HookContext) -> HookContext:
        """
        执行上下文压缩

        Args:
            context: 钩子上下文，包含 messages 数据

        Returns:
            更新后的钩子上下文
        """
        if context.event_type != HookEvent.BEFORE_MODEL:
            return context

        # 获取消息列表
        messages = context.data.get("messages", [])
        if not messages:
            return context

        # 转换消息为字典格式
        message_dicts = []
        for msg in messages:
            if isinstance(msg, dict):
                # 已经是字典格式
                message_dicts.append(msg)
            elif hasattr(msg, 'to_dict'):
                # 有to_dict方法的对象
                message_dicts.append(msg.to_dict())
            elif hasattr(msg, '__dict__'):
                # 普通对象，提取属性
                message_dict = {}
                for attr in ['role', 'content', 'tool_calls', 'tool_call_id']:
                    if hasattr(msg, attr):
                        message_dict[attr] = getattr(msg, attr)
                message_dicts.append(message_dict)
            else:
                # 其他格式，跳过
                continue

        if not message_dicts:
            return context


        # 如果未超过限制，直接返回
        if not self.is_over_limit(message_dicts):
            return context

        # 执行压缩
        compressed_messages = self._compress_messages(message_dicts)

        # 更新上下文数据
        # 保持原始格式，如果原先是 Message 对象列表，需要转换回来
        if all(hasattr(msg, 'to_dict') for msg in messages):
            # 原来都是 Message 对象，保持原格式
            from src.my_agent.models import Message
            context.data["messages"] = [
                Message(
                    role=msg_dict.get("role", "user"),
                    content=msg_dict.get("content", ""),
                    tool_calls=msg_dict.get("tool_calls"),
                    tool_call_id=msg_dict.get("tool_call_id")
                )
                for msg_dict in compressed_messages
            ]
        else:
            # 原来是字典格式，保持字典格式
            context.data["messages"] = compressed_messages

        # 添加压缩记录到元数据
        context.metadata["compressed"] = True


        return context

    def count_tokens(self, messages: List[dict[str,str]]) -> int:
        """
        Count tokens in message list

        Args:
            messages: List of messages

        Returns:
            Number of tokens
        """
        total_tokens = 0
        for message in messages:
            total_tokens += self._count_message_tokens(message)
        return total_tokens
    
    def _count_message_tokens(self, message: dict[str,str]) -> int:
        """
        Count tokens in a single message

        Args:
            message: Message object

        Returns:
            Number of tokens
        """
        # Estimate token 计数 based 在 characterlength (different calculation regarding English 和 non-English)
        token_count = 0
        role = message.get("role", "")
        content = message.get("content", "")

        if role:
            token_count += self._count_text_tokens(role) * 1.1
        if content:
            token_count += self._count_text_tokens(content) * 1.3

        # Ensure 在 least 1 token
        return max(1, int(token_count))

    def _count_text_tokens(self, text: str) -> int:
        """
        Count tokens in text with different calculations for English and non-English characters.
        English characters: 4 characters ≈ 1 token
        Non-English characters (e.g., Chinese): 1 character ≈ 1 token

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        if not text:
            return 0

        english_chars = 0
        non_english_chars = 0

        for char in text:
            #check if character is ASCII (English letters, digits, punctuation)
            if ord(char) < 128:
                english_chars += 1
            else:
                non_english_chars += 1

        # Calculate tokens: English 在 4 chars/token, others 在 1 char/token
        english_tokens = english_chars // 4
        non_english_tokens = non_english_chars

        return english_tokens + non_english_tokens

    def is_over_limit(self, messages: List[Dict[str, Any]]) -> bool:
        """
        Check if messages exceed token limit

        Args:
            messages: List of messages

        Returns:
            Whether limit is exceeded
        """
        return self.count_tokens(messages) > self.max_tokens
    
    def _compress_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compress compressible messages

        Args:
            messages: List of messages to compress

        Returns:
            Compressed message list
        """
        # 初始化 preserve_suffix_message_count
        if not hasattr(self, 'preserve_suffix_message_count'):
            self.preserve_suffix_message_count = 4

        available_token = self.max_tokens
        prefix_messages = []

        # 1. Preserve head messages 的 specifiedlength 到 retain system prompts 和 user input
        for i in range(min(self.preserve_prefix_message_count, len(messages))):
            cur_token_cnt = self._count_message_tokens(messages[i])
            if available_token > 0 and available_token >= cur_token_cnt:
                prefix_messages.append(messages[i])
                available_token -= cur_token_cnt
            elif available_token > 0:
                # Truncatecontent 到 fit available tokens
                truncated_message = self._truncate_message_content(
                    messages[i], available_token
                )
                prefix_messages.append(truncated_message)
                return prefix_messages
            else:
                break

        # 2. Compress subsequent messages 从  tail, some messages possible be discarded
        messages = messages[len(prefix_messages) :]
        suffix_messages = []
        for i in range(len(messages) - 1, max(len(messages)-self.preserve_suffix_message_count-1,-1), -1):
            cur_token_cnt = self._count_message_tokens(messages[i])

            if cur_token_cnt > 0 and available_token >= cur_token_cnt:
                suffix_messages = [messages[i]] + suffix_messages
                available_token -= cur_token_cnt
            elif available_token > 0:
                # Truncatecontent 到 fit available tokens
                truncated_message = self._truncate_message_content(
                    messages[i], available_token
                )
                suffix_messages = [truncated_message] + suffix_messages
                return prefix_messages + suffix_messages
            else:
                break

        # 如果中间还有消息被舍弃，创建摘要
        middle_messages = messages[len(prefix_messages):len(messages) - len(suffix_messages)]
        if middle_messages and available_token > 0:
            summary_content = self._create_summary_message(middle_messages)
            if summary_content:
                summary_tokens = self._count_text_tokens(summary_content)
                if available_token >= summary_tokens:
                    prefix_messages.append({
                        "role": "system",
                        "content": summary_content
                    })
                    available_token -= summary_tokens

        return prefix_messages + suffix_messages

    def _truncate_message_content(
        self, message: Dict[str, Any], max_tokens: int
    ) -> Dict[str, Any]:
        """
        Truncate message content while preserving all other attributes

        Args:
            message: The message to truncate
            max_tokens: Maximum number of tokens to keep

        Returns:
            New message instance with truncated content
        """
        #create  deep copy 的  original消息 到 preserve all attributes
        truncated_message = copy.deepcopy(message)

        # Truncate only content attribute
        # 估算字符数：英文字符4个=1token，中文字符1个=1token
        content = str(message.get("content", ""))

        # 计算可以保留的字符数
        english_chars = 0
        non_english_chars = 0
        for char in content:
            if ord(char) < 128:
                english_chars += 1
            else:
                non_english_chars += 1

        # 根据token限制计算需要截断的字符数
        total_tokens = english_chars // 4 + non_english_chars
        if total_tokens <= max_tokens:
            return truncated_message

        # 需要截断，按比例减少字符
        needed_reduction = (total_tokens - max_tokens) / total_tokens
        keep_chars = int(len(content) * (1 - needed_reduction))

        truncated_message["content"] = content[:keep_chars] + "..."

        return truncated_message

    def _create_summary_message(self, messages: List[Dict[str, Any]]) -> str | None:
        """
        使用LLM创建摘要
        """
        if not messages:
            return None

        # 1. 将中间消息convert为stringformat，供 LLM 阅读
        conversation_text = ""
        for msg in messages:
            role = msg.get("role", "unknown")
            role_name = "Human" if role == "user" else ("System" if role == "system" else "AI")
            content = msg.get("content", "")
            conversation_text += f"{role_name}: {content}\n"

        # 2. 创建提示
        prompt = (
            "阅读以下对话历史，简明扼要地总结关键信息、用户的核心需求以及做出的关键技术决策。"
            "忽略闲聊，保留上下文中的变量、参数和代码逻辑依赖。"
            "摘要应当简短。"
            f"\n\n对话历史:\n{conversation_text}"
        )

        # 3. 调用大模型generate摘要
        try:
            llm = get_llm_by_type("basic")
            summary_response = llm.invoke([{"role":"system","content":"prompt"}])
            summary_content = summary_response.content
        except Exception as e:
            # 降级处理：如果LLM调用失败，返回一个简单的占位符
            summary_content = f"（由于网络错误，中间 {len(messages)} 条消息已被折叠）"

        # 4. 返回摘要内容
        return f"【系统摘要：之前的对话中，{summary_content}】"

# 创建上下文压缩钩子实例
def create_context_compression_hook(max_tokens: int = 100000, model: str = "basic") -> ContextCompressionHook:
    """
    创建上下文压缩钩子

    Args:
        max_tokens: 最大 tokens 限制
        model: 压缩使用的模型

    Returns:
        上下文压缩钩子实例
    """
    return ContextCompressionHook(max_tokens=max_tokens, compression_model=model)