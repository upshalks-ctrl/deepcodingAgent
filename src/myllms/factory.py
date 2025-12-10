"""
模型工厂
根据提供商类型创建对应的模型实例
支持从配置文件加载模型配置
"""

from typing import Optional, Union, Dict, Any, List
import logging
import os
import yaml

from .base import BaseModel, ModelConfig
from .openai import OpenAIModel, create_openai_model
from .anthropic import AnthropicModel, create_anthropic_model
from .google import GoogleModel, create_google_model
from .dashscope import DashScopeModel, create_dashscope_model

logger = logging.getLogger(__name__)


def create_model(
    url: str,
    api_key: str,
    model: str,
    **kwargs
) -> BaseModel:
    """直接创建模型实例的工厂函数

    Args:
        url: API 基础 URL
        api_key: API 密钥
        model: 模型名称
        **kwargs: 其他配置参数（max_tokens, temperature, timeout 等）

    Returns:
        BaseModel: 模型实例

    Raises:
        ValueError: 不支持的提供商或配置错误

    Examples:
        ```python
        # OpenAI 模型
        model = create_model(
            url="https://api.openai.com/v1",
            api_key="your-key",
            model="gpt-4o-mini"
        )

        # Anthropic 模型
        model = create_model(
            url="https://api.anthropic.com/v1",
            api_key="your-key",
            model="claude-3-5-sonnet-20241022"
        )

        # DeepSeek 模型
        model = create_model(
            url="https://api.deepseek.com",
            api_key="your-key",
            model="deepseek-chat"
        )

        # 带额外参数
        model = create_model(
            url="https://api.openai.com/v1",
            api_key="your-key",
            model="gpt-4o-mini",
            max_tokens=4096,
            temperature=0.7
        )
        ```
    """
    # 根据 base_url 推断提供商
    provider = _infer_provider_from_url(url)

    if not provider:
        # 如果无法从 URL 推断，再根据模型名称推断
        provider = _infer_provider_from_model(model)

    if not provider:
        raise ValueError(
            f"Cannot infer provider for model: {model}, url: {url}"
        )

    # 提取配置参数（从 kwargs 中移除以避免重复传递）
    max_tokens = kwargs.pop("max_tokens", 4096)
    temperature = kwargs.pop("temperature", 0.7)
    timeout = kwargs.pop("timeout", 120.0)

    logger.info(
        f"Creating {provider} model: {model} "
        f"(max_tokens={max_tokens}, temperature={temperature})"
    )

    # 根据提供商创建模型
    if provider == "openai":
        return create_openai_model(
            api_key=api_key,
            model=model,
            base_url=url,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
            **kwargs
        )

    elif provider == "anthropic":
        return create_anthropic_model(
            api_key=api_key,
            model=model,
            base_url=url,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
            **kwargs
        )

    elif provider == "google":
        return create_google_model(
            api_key=api_key,
            model=model,
            base_url=url,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
            **kwargs
        )

    elif provider == "dashscope":
        return create_dashscope_model(
            api_key=api_key,
            model=model,
            base_url=url,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
            **kwargs
        )

    elif provider == "deepseek":
        # DeepSeek API 兼容 OpenAI，使用 OpenAI 模型创建函数
        return create_openai_model(
            api_key=api_key,
            model=model,
            base_url=url,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
            **kwargs
        )

    else:
        raise ValueError(f"Unsupported provider: {provider}")


def get_llm_by_type(model_type: str) -> BaseModel:
    """从配置文件自动加载模型实例

    Args:
        model_type: 模型类型 ("basic", "coder", "vision", "reasoning")

    Returns:
        BaseModel: 配置好的模型实例

    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: 模型类型未找到或配置无效

    Examples:
        ```python
        # 自动从 conf.yaml 加载
        model = get_llm_by_type("basic")

        model = get_llm_by_type("coder")

        model = get_llm_by_type("vision")

        model = get_llm_by_type("reasoning")
        ```
    """
    model_type = model_type.lower().strip()

    # 模型类型到配置键的映射
    type_config_keys = {
        "basic": "BASIC_MODEL",
        "coder": "CODE_MODEL",
        "code": "CODE_MODEL",  # 支持别名
        "vision": "VISION_MODEL",
        "reasoning": "REASONING_MODEL"
    }

    # 验证模型类型
    if model_type not in type_config_keys:
        raise ValueError(
            f"Unsupported model type: {model_type}. "
            f"Supported types: {list(type_config_keys.keys())}"
        )

    config_key = type_config_keys[model_type]

    # 默认配置文件路径
    default_paths = [
        "conf.yaml",
        "conf.yml",
        "config.yaml",
        "config.yml",
        ".conf.yaml",
        ".conf.yml"
    ]

    config = None
    for path in default_paths:
        if os.path.exists(path):
            logger.info(f"Using configuration file: {path}")
            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            break

    if not config:
        raise FileNotFoundError(
            "No configuration file found. Please create conf.yaml."
        )

    # 查找模型配置
    if config_key not in config:
        raise ValueError(
            f"Model type '{model_type}' not found in configuration. "
            f"Expected config key: {config_key}. "
            f"Available keys: {list(config.keys())}"
        )

    model_config = config[config_key]

    # 验证必需字段
    required_fields = ["model", "api_key"]
    for field in required_fields:
        if field not in model_config:
            raise ValueError(f"Missing required field '{field}' in model configuration")

    # 提取配置参数
    model_name = model_config["model"]
    api_key = model_config["api_key"]
    base_url = model_config.get("base_url")

    if not base_url:
        raise ValueError(f"Missing 'base_url' in {config_key} configuration")

    # 提取可选参数
    max_tokens = model_config.get("max_tokens", 4096)
    temperature = model_config.get("temperature", 0.7)
    timeout = model_config.get("timeout", 120.0)

    # 根据 base_url 推断提供商
    provider = _infer_provider_from_url(base_url)

    # 如果无法从 URL 推断，再根据模型名称推断
    if not provider:
        provider = _infer_provider_from_model(model_name)

    logger.info(
        f"Creating {provider} model: {model_name} "
        f"(max_tokens={max_tokens}, temperature={temperature})"
    )

    # 创建模型 - 直接根据提供商创建
    if provider == "openai":
        return create_openai_model(
            api_key=api_key,
            model=model_name,
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )
    elif provider == "anthropic":
        return create_anthropic_model(
            api_key=api_key,
            model=model_name,
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )
    elif provider == "google":
        return create_google_model(
            api_key=api_key,
            model=model_name,
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )
    elif provider == "dashscope":
        return create_dashscope_model(
            api_key=api_key,
            model=model_name,
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )
    elif provider == "deepseek":
        # DeepSeek API 兼容 OpenAI，使用 OpenAI 模型创建函数
        return create_openai_model(
            api_key=api_key,
            model=model_name,
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def _infer_provider_from_url(base_url: Optional[str]) -> Optional[str]:
    """根据 base_url 推断提供商

    Args:
        base_url: API 基础 URL

    Returns:
        Optional[str]: 提供商名称，如果无法推断则返回 None
    """
    if not base_url:
        return None

    base_url = base_url.lower()

    if "openai.com" in base_url:
        return "openai"
    elif "anthropic.com" in base_url:
        return "anthropic"
    elif "googleapis.com" in base_url or "generativelanguage.googleapis.com" in base_url:
        return "google"
    elif "dashscope.aliyuncs.com" in base_url:
        return "dashscope"
    elif "deepseek.com" in base_url:
        return "deepseek"

    return None


def _infer_provider_from_model(model_name: str) -> str:
    """根据模型名称推断提供商

    Args:
        model_name: 模型名称

    Returns:
        str: 提供商名称

    Raises:
        ValueError: 无法推断提供商
    """
    model_name = model_name.lower()

    # OpenAI 模型
    if any(prefix in model_name for prefix in ["gpt", "text-embedding", "dall-e"]):
        return "openai"

    # Anthropic 模型
    if "claude" in model_name:
        return "anthropic"

    # Google 模型
    if any(prefix in model_name for prefix in ["gemini", "palm", "bard"]):
        return "google"

    # DashScope 模型
    if any(prefix in model_name for prefix in ["qwen", "qwen-turbo", "qwen-plus", "qwen-max"]):
        return "dashscope"

    # DeepSeek 模型
    if "deepseek" in model_name:
        return "deepseek"

    # 默认返回 openai
    logger.warning(
        f"Could not infer provider from model name '{model_name}', "
        f"defaulting to 'openai'"
    )
    return "openai"


def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """从文件加载配置

    Args:
        config_path: 配置文件路径

    Returns:
        Dict[str, Any]: 配置字典

    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: 不支持的文件格式
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    if config_path.endswith(('.yaml', '.yml')):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    elif config_path.endswith('.json'):
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        raise ValueError(f"Unsupported configuration file format: {config_path}")


def get_supported_providers() -> List[str]:
    """获取支持的模型提供商列表

    Returns:
        List[str]: 支持的提供商名称列表
    """
    return ["openai", "anthropic", "google", "dashscope"]


def get_provider_info(provider: str) -> Dict[str, Any]:
    """获取提供商信息

    Args:
        provider: 提供商名称

    Returns:
        Dict[str, Any]: 提供商信息，包括默认模型和 URL

    Raises:
        ValueError: 不支持的提供商
    """
    provider = provider.lower().strip()

    info = {
        "openai": {
            "name": "OpenAI",
            "default_model": "gpt-4o-mini",
            "default_url": "https://api.openai.com/v1",
            "description": "OpenAI 的 GPT 模型",
            "env_key": "OPENAI_API_KEY"
        },
        "anthropic": {
            "name": "Anthropic",
            "default_model": "claude-3-5-sonnet-20241022",
            "default_url": "https://api.anthropic.com/v1",
            "description": "Anthropic 的 Claude 模型",
            "env_key": "ANTHROPIC_API_KEY"
        },
        "google": {
            "name": "Google",
            "default_model": "gemini-pro",
            "default_url": "https://generativelanguage.googleapis.com/v1beta",
            "description": "Google 的 Gemini 模型",
            "env_key": "GOOGLE_API_KEY"
        },
        "dashscope": {
            "name": "DashScope",
            "default_model": "qwen-turbo",
            "default_url": "https://dashscope.aliyuncs.com/api/v1",
            "description": "阿里云的 DashScope 模型",
            "env_key": "DASHSCOPE_API_KEY"
        }
    }

    if provider not in info:
        raise ValueError(f"Unsupported provider: {provider}")

    return info[provider]
