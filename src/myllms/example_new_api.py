"""
新 API 使用示例
展示如何使用 create_model() 根据模型类型创建模型
"""

import asyncio
from typing import Dict, Any
from src.myllms import create_model

# 配置字典示例
config_dict: Dict[str, Any] = {
    "BASIC_MODEL": {
        "model": "gpt-4o-mini",
        "api_key": "your-openai-key",
        "base_url": "https://api.openai.com/v1",
        "max_tokens": 4096,
        "temperature": 0.7
    },
    "CODE_MODEL": {
        "model": "gpt-4o",
        "api_key": "your-openai-key",
        "base_url": "https://api.openai.com/v1",
        "max_tokens": 8192,
        "temperature": 0.2
    },
    "VISION_MODEL": {
        "model": "gpt-4o",
        "api_key": "your-openai-key",
        "base_url": "https://api.openai.com/v1",
        "max_tokens": 8192,
        "temperature": 0.5
    },
    "REASONING_MODEL": {
        "model": "deepseek-chat",
        "api_key": "your-deepseek-key",
        "base_url": "https://api.deepseek.com",
        "max_tokens": 8192,
        "temperature": 0.3
    }
}


async def example_basic_model():
    """示例 1: 创建基础模型"""
    print("\n" + "=" * 60)
    print("示例 1: 创建基础模型")
    print("=" * 60)

    model = create_model("basic", config_dict=config_dict)
    print(f"创建了: {model}")

    messages = [{"role": "user", "content": "你好，请介绍一下你自己"}]

    # 异步调用
    response = await model.chat(messages)
    print(f"\n响应: {response.content}")


async def example_coder_model():
    """示例 2: 创建代码模型"""
    print("\n" + "=" * 60)
    print("示例 2: 创建代码模型")
    print("=" * 60)

    model = create_model("coder", config_dict=config_dict)
    print(f"创建了: {model}")

    messages = [
        {
            "role": "user",
            "content": "请写一个 Python 函数来计算斐波那契数列"
        }
    ]

    response = await model.chat(messages)
    print(f"\n响应:\n{response.content}")


async def example_vision_model():
    """示例 3: 创建视觉模型"""
    print("\n" + "=" * 60)
    print("示例 3: 创建视觉模型")
    print("=" * 60)

    model = create_model("vision", config_dict=config_dict)
    print(f"创建了: {model}")

    # 注意：这里只是示例，实际使用时需要提供图像
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请描述这张图片"},
                {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
            ]
        }
    ]

    print("\n注意: 视觉模型需要图像输入")


async def example_reasoning_model():
    """示例 4: 创建推理模型"""
    print("\n" + "=" * 60)
    print("示例 4: 创建推理模型")
    print("=" * 60)

    model = create_model("reasoning", config_dict=config_dict)
    print(f"创建了: {model}")

    messages = [
        {
            "role": "user",
            "content": "请解决这个逻辑题: 如果所有的猫都喜欢鱼，小明有一只猫，那么这只猫喜欢鱼吗？"
        }
    ]

    response = await model.chat(messages)
    print(f"\n响应:\n{response.content}")


def example_with_config_file():
    """示例 5: 使用配置文件"""
    print("\n" + "=" * 60)
    print("示例 5: 使用配置文件")
    print("=" * 60)

    # 使用 conf.yaml 配置文件
    model = create_model(
        model_type="basic",
        config_path="conf.yaml"
    )
    print(f"从配置文件创建了: {model}")


def example_override_params():
    """示例 6: 覆盖配置参数"""
    print("\n" + "=" * 60)
    print("示例 6: 覆盖配置参数")
    print("=" * 60)

    # 覆盖配置文件中的参数
    model = create_model(
        model_type="basic",
        config_dict=config_dict,
        max_tokens=2048,  # 覆盖默认值
        temperature=0.5   # 覆盖默认值
    )
    print(f"创建了: {model}")
    print(f"Max tokens: {model.config.max_tokens}")
    print(f"Temperature: {model.config.temperature}")


async def main():
    """运行所有示例"""
    print("\n" + "=" * 70)
    print("myllms 新 API 使用示例")
    print("=" * 70)

    # 运行异步示例
    await example_basic_model()
    await example_coder_model()
    await example_vision_model()
    await example_reasoning_model()

    # 运行同步示例
    example_with_config_file()
    example_override_params()

    print("\n" + "=" * 70)
    print("所有示例运行完成！")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
