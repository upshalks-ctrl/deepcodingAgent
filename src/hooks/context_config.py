"""
上下文管理配置

定义不同场景下的上下文压缩配置
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ContextCompressionConfig:
    """上下文压缩配置"""
    max_tokens: int
    model: str
    strategies: list
    enabled: bool = True


# 预定义的配置
CONTEXT_CONFIGS: Dict[str, ContextCompressionConfig] = {
    # 基础配置 - 适中的 tokens 限制
    "basic": ContextCompressionConfig(
        max_tokens=50000,
        model="basic",
        strategies=["system_messages", "tool_messages", "old_messages"]
    ),

    # 高容量配置 - 更高的 tokens 限制
    "high_capacity": ContextCompressionConfig(
        max_tokens=100000,
        model="basic",
        strategies=["system_messages", "tool_messages", "old_messages"]
    ),

    # 紧凑配置 - 严格的 tokens 限制
    "compact": ContextCompressionConfig(
        max_tokens=30000,
        model="basic",
        strategies=["system_messages", "tool_messages", "old_messages", "aggressive"]
    ),

    # 开发配置 - 调试用，不压缩
    "development": ContextCompressionConfig(
        max_tokens=200000,
        model="basic",
        strategies=[],
        enabled=False
    ),

    # 生产配置 - 激进的压缩策略
    "production": ContextCompressionConfig(
        max_tokens=80000,
        model="basic",
        strategies=["system_messages", "tool_messages", "old_messages"]
    ),
}


def get_context_config(config_name: str) -> ContextCompressionConfig:
    """
    获取上下文压缩配置

    Args:
        config_name: 配置名称

    Returns:
        上下文压缩配置
    """
    if config_name not in CONTEXT_CONFIGS:
        raise ValueError(f"Unknown context config: {config_name}. Available: {list(CONTEXT_CONFIGS.keys())}")

    return CONTEXT_CONFIGS[config_name]


def register_context_config(name: str, config: ContextCompressionConfig):
    """
    注册新的上下文压缩配置

    Args:
        name: 配置名称
        config: 配置对象
    """
    CONTEXT_CONFIGS[name] = config


# 环境变量映射
ENV_CONFIG_MAPPING = {
    "development": "development",
    "dev": "development",
    "testing": "basic",
    "test": "basic",
    "production": "production",
    "prod": "production",
}


def get_config_from_env() -> str:
    """
    从环境变量获取配置名称

    Returns:
        配置名称
    """
    import os

    env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
    return ENV_CONFIG_MAPPING.get(env, "basic")