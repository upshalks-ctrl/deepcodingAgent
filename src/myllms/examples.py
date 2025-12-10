"""
myllms 使用示例 - 使用新的简化 API
展示如何使用 get_llm_by_type() 和 create_model() 函数
"""

import asyncio
from typing import Dict, Any

from . import (
    get_llm_by_type,
    create_model,
    get_supported_providers,
    get_provider_info,
)


# ==============================================================================
# 示例 1: 基本用法 - 从配置文件自动加载
# ==============================================================================
async def example_1_basic_usage():
    """示例 1: 基本用法 - 从配置文件自动加载"""
    print("\n" + "=" * 60)
    print("示例 1: 基本用法 - 从配置文件自动加载")
    print("=" * 60)

    try:
        # 加载基础模型
        print("\n1.1 加载基础模型 (basic)")
        model = get_llm_by_type("basic")
        print(f"   创建了: {model}")

        # 加载代码模型
        print("\n1.2 加载代码模型 (coder)")
        model = get_llm_by_type("coder")
        print(f"   创建了: {model}")

        # 加载视觉模型
        print("\n1.3 加载视觉模型 (vision)")
        model = get_llm_by_type("vision")
        print(f"   创建了: {model}")

        # 加载推理模型
        print("\n1.4 加载推理模型 (reasoning)")
        model = get_llm_by_type("reasoning")
        print(f"   创建了: {model}")

    except FileNotFoundError as e:
        print(f"   [错误] 配置文件不存在: {e}")
    except Exception as e:
        print(f"   [错误] {e}")


# ==============================================================================
# 示例 2: 使用 create_model 直接创建
# ==============================================================================
async def example_2_create_model_directly():
    """示例 2: 使用 create_model 直接创建"""
    print("\n" + "=" * 60)
    print("示例 2: 使用 create_model 直接创建")
    print("=" * 60)

    # 创建 OpenAI 模型
    print("\n2.1 创建 OpenAI 模型")
    model = create_model(
        url="https://api.openai.com/v1",
        api_key="your-openai-key",
        model="gpt-4o-mini"
    )
    print(f"   创建了: {model}")

    # 创建 Anthropic 模型
    print("\n2.2 创建 Anthropic 模型")
    model = create_model(
        url="https://api.anthropic.com/v1",
        api_key="your-anthropic-key",
        model="claude-3-5-sonnet-20241022"
    )
    print(f"   创建了: {model}")

    # 创建 DeepSeek 模型
    print("\n2.3 创建 DeepSeek 模型")
    model = create_model(
        url="https://api.deepseek.com",
        api_key="your-deepseek-key",
        model="deepseek-chat"
    )
    print(f"   创建了: {model}")

    # 创建带额外参数的模型
    print("\n2.4 创建带额外参数的模型")
    model = create_model(
        url="https://api.openai.com/v1",
        api_key="your-openai-key",
        model="gpt-4o-mini",
        max_tokens=4096,
        temperature=0.7
    )
    print(f"   创建了: {model}")


# ==============================================================================
# 示例 3: 异步聊天测试
# ==============================================================================
async def example_3_async_chat():
    """示例 3: 异步聊天测试"""
    print("\n" + "=" * 60)
    print("示例 3: 异步聊天测试")
    print("=" * 60)

    try:
        # 创建模型
        model = get_llm_by_type("basic")
        print(f"\n3.1 创建了模型: {model}")

        # 准备消息
        messages = [
            {"role": "user", "content": "你好，请用一句话介绍一下你自己"}
        ]
        print(f"\n3.2 发送消息: {messages[0]['content']}")

        # 发送异步聊天请求
        response = await model.chat(messages)
        print(f"\n3.3 收到响应:")
        print(f"   内容: {response.content}")
        print(f"   完成原因: {response.finish_reason}")
        print(f"   使用量: {response.usage}")
        print(f"   模型: {response.model}")

    except Exception as e:
        print(f"   [错误] {e}")


# ==============================================================================
# 示例 4: 同步聊天测试
# ==============================================================================
async def example_4_sync_chat():
    """示例 4: 同步聊天测试"""
    print("\n" + "=" * 60)
    print("示例 4: 同步聊天测试")
    print("=" * 60)

    try:
        # 创建模型
        model = get_llm_by_type("basic")
        print(f"\n4.1 创建了模型: {model}")

        # 准备消息
        messages = [
            {"role": "user", "content": "请用 Python 写一个 Hello World 程序"}
        ]
        print(f"\n4.2 发送同步消息")

        # 发送同步聊天请求
        response = model.chat_sync(messages)
        print(f"\n4.3 收到同步响应:")
        print(f"   内容: {response.content}")

    except Exception as e:
        print(f"   [错误] {e}")


# ==============================================================================
# 示例 5: 流式输出测试
# ==============================================================================
async def example_5_streaming():
    """示例 5: 流式输出测试"""
    print("\n" + "=" * 60)
    print("示例 5: 流式输出测试")
    print("=" * 60)

    try:
        # 创建模型
        model = get_llm_by_type("basic")
        print(f"\n5.1 创建了模型: {model}")

        # 准备消息
        messages = [
            {"role": "user", "content": "请列出 5 个 Python 的优点"}
        ]
        print(f"\n5.2 请求流式响应")

        # 异步流式响应
        print("\n5.3 异步流式响应:")
        print("   ", end="", flush=True)
        async for chunk in model.stream_chat(messages):
            print(chunk, end="", flush=True)
        print("\n")

        # 同步流式响应
        print("\n5.4 同步流式响应:")
        result = model.stream_chat_sync(messages)
        print(f"   结果: {result}")

    except Exception as e:
        print(f"   [错误] {e}")


# ==============================================================================
# 示例 6: 工具调用测试
# ==============================================================================
async def example_6_tool_calling():
    """示例 6: 工具调用测试"""
    print("\n" + "=" * 60)
    print("示例 6: 工具调用测试")
    print("=" * 60)

    try:
        # 创建模型
        model = get_llm_by_type("basic")
        print(f"\n6.1 创建了模型: {model}")

        # 定义工具
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "获取天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "城市名称"
                            }
                        },
                        "required": ["city"]
                    }
                }
            }
        ]
        print(f"\n6.2 定义了工具: get_weather")

        # 准备消息
        messages = [
            {"role": "user", "content": "北京的天气怎么样？"}
        ]
        print(f"\n6.3 发送带工具调用的消息")

        # 发送带工具调用的请求
        response = await model.chat(messages, tools=tools)
        print(f"\n6.4 收到响应:")
        print(f"   内容: {response.content}")
        print(f"   工具调用: {response.tool_calls}")

    except Exception as e:
        print(f"   [错误] {e}")


# ==============================================================================
# 示例 7: 错误处理测试
# ==============================================================================
async def example_7_error_handling():
    """示例 7: 错误处理测试"""
    print("\n" + "=" * 60)
    print("示例 7: 错误处理测试")
    print("=" * 60)

    print("\n7.1 测试无效的模型类型")
    try:
        _ = get_llm_by_type("invalid_type")
    except ValueError as e:
        print(f"   [预期错误] {e}")

    print("\n7.2 测试缺少配置文件的模型类型")
    try:
        _ = get_llm_by_type("basic")
    except FileNotFoundError as e:
        print(f"   [预期错误] {e}")

    print("\n7.3 测试 create_model 与无效 URL")
    try:
        _ = create_model(
            url="https://invalid-url.com",
            api_key="test-key",
            model="test-model"
        )
    except Exception as e:
        print(f"   [预期错误] {e}")


# ==============================================================================
# 示例 8: 测试所有模型类型
# ==============================================================================
async def example_8_all_model_types():
    """示例 8: 测试所有模型类型"""
    print("\n" + "=" * 60)
    print("示例 8: 测试所有模型类型")
    print("=" * 60)

    model_types = [
        ("basic", "基础模型"),
        ("coder", "代码模型"),
        ("vision", "视觉模型"),
        ("reasoning", "推理模型")
    ]

    for config_key, description in model_types:
        print(f"\n8.{model_types.index((config_key, description)) + 1} 创建 {description} ({config_key})")
        try:
            model = get_llm_by_type(config_key)
            print(f"   [成功] {model}")
            print(f"   模型: {model.config.model}")
            print(f"   Base URL: {model.config.base_url}")
            print(f"   最大令牌数: {model.config.max_tokens}")
            print(f"   温度: {model.config.temperature}")
        except Exception as e:
            print(f"   [失败] {e}")


# ==============================================================================
# 示例 9: 测试不同提供商
# ==============================================================================
async def example_9_different_providers():
    """示例 9: 测试不同提供商"""
    print("\n" + "=" * 60)
    print("示例 9: 测试不同提供商")
    print("=" * 60)

    # 测试 OpenAI 提供商
    print("\n9.1 测试 OpenAI 提供商")
    try:
        model = create_model(
            url="https://api.openai.com/v1",
            api_key="test-key",
            model="gpt-4o-mini"
        )
        print(f"   [成功] {model}")
        print(f"   提供商: OpenAI")
    except Exception as e:
        print(f"   [失败] {e}")

    # 测试 Anthropic 提供商
    print("\n9.2 测试 Anthropic 提供商")
    try:
        model = create_model(
            url="https://api.anthropic.com/v1",
            api_key="test-key",
            model="claude-3-5-sonnet-20241022"
        )
        print(f"   [成功] {model}")
        print(f"   提供商: Anthropic")
    except Exception as e:
        print(f"   [失败] {e}")

    # 测试 Google 提供商
    print("\n9.3 测试 Google 提供商")
    try:
        model = create_model(
            url="https://generativelanguage.googleapis.com/v1beta",
            api_key="test-key",
            model="gemini-pro"
        )
        print(f"   [成功] {model}")
        print(f"   提供商: Google")
    except Exception as e:
        print(f"   [失败] {e}")

    # 测试 DashScope 提供商
    print("\n9.4 测试 DashScope 提供商")
    try:
        model = create_model(
            url="https://dashscope.aliyuncs.com/api/v1",
            api_key="test-key",
            model="qwen-turbo"
        )
        print(f"   [成功] {model}")
        print(f"   提供商: DashScope")
    except Exception as e:
        print(f"   [失败] {e}")

    # 测试 DeepSeek 提供商
    print("\n9.5 测试 DeepSeek 提供商")
    try:
        model = create_model(
            url="https://api.deepseek.com",
            api_key="test-key",
            model="deepseek-chat"
        )
        print(f"   [成功] {model}")
        print(f"   提供商: DeepSeek")
    except Exception as e:
        print(f"   [失败] {e}")


# ==============================================================================
# 示例 10: 上下文管理器测试
# ==============================================================================
async def example_10_context_managers():
    """示例 10: 上下文管理器测试"""
    print("\n" + "=" * 60)
    print("示例 10: 上下文管理器测试")
    print("=" * 60)

    # 异步上下文管理器
    print("\n10.1 异步上下文管理器")
    try:
        async with get_llm_by_type("basic") as model:
            print(f"   创建了模型: {model}")
            messages = [{"role": "user", "content": "你好"}]
            response = await model.chat(messages)
            print(f"   响应: {response.content}")
    except Exception as e:
        print(f"   [错误] {e}")

    # 同步上下文管理器
    print("\n10.2 同步上下文管理器")
    try:
        with get_llm_by_type("basic") as model:
            print(f"   创建了模型: {model}")
            messages = [{"role": "user", "content": "你好"}]
            response = model.chat_sync(messages)
            print(f"   响应: {response.content}")
    except Exception as e:
        print(f"   [错误] {e}")


# ==============================================================================
# 示例 11: 获取提供商信息
# ==============================================================================
async def example_11_provider_info():
    """示例 11: 获取提供商信息"""
    print("\n" + "=" * 60)
    print("示例 11: 获取提供商信息")
    print("=" * 60)

    # 获取支持的提供商
    providers = get_supported_providers()
    print(f"\n11.1 支持的提供商: {providers}")

    # 获取每个提供商的信息
    for provider in providers:
        print(f"\n11.{providers.index(provider) + 2} {provider.upper()} 提供商信息:")
        try:
            info = get_provider_info(provider)
            for key, value in info.items():
                print(f"   {key}: {value}")
        except ValueError as e:
            print(f"   [错误] {e}")


# ==============================================================================
# 示例 12: 复杂对话测试
# ==============================================================================
async def example_12_complex_conversation():
    """示例 12: 复杂对话测试"""
    print("\n" + "=" * 60)
    print("示例 12: 复杂对话测试")
    print("=" * 60)

    try:
        # 创建模型
        model = get_llm_by_type("basic")
        print(f"\n12.1 创建了模型: {model}")

        # 多轮对话
        conversation = [
            {"role": "user", "content": "我想学习 Python，请推荐几本书"},
            {"role": "assistant", "content": "我推荐《Python编程：从入门到实践》、《流畅的Python》和《Python Cookbook》。"},
            {"role": "user", "content": "这些书有什么区别？"}
        ]

        print("\n12.2 进行多轮对话")
        for i, message in enumerate(conversation, 1):
            print(f"\n   消息 {i}: [{message['role']}] {message['content']}")

        # 发送对话
        response = await model.chat(conversation)
        print(f"\n12.3 收到响应:")
        print(f"   {response.content}")

    except Exception as e:
        print(f"   [错误] {e}")


# ==============================================================================
# 主函数 - 运行所有示例
# ==============================================================================
async def main():
    """运行所有示例"""
    print("=" * 70)
    print("myllms 使用示例 - 简化 API")
    print("=" * 70)

    examples = [
        ("基本用法", example_1_basic_usage),
        ("直接创建", example_2_create_model_directly),
        ("异步聊天", example_3_async_chat),
        ("同步聊天", example_4_sync_chat),
        ("流式输出", example_5_streaming),
        ("工具调用", example_6_tool_calling),
        ("错误处理", example_7_error_handling),
        ("所有模型类型", example_8_all_model_types),
        ("不同提供商", example_9_different_providers),
        ("上下文管理器", example_10_context_managers),
        ("提供商信息", example_11_provider_info),
        ("复杂对话", example_12_complex_conversation),
    ]

    print(f"\n可用的示例 ({len(examples)} 个):")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    while True:
        try:
            choice = input("\n请选择要运行的示例 (输入数字，0 退出): ").strip()

            if choice == "0":
                print("\n再见!")
                break

            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                name, func = examples[idx]
                print(f"\n运行示例 {idx + 1}: {name}")
                print("-" * 60)
                await func()
            else:
                print("无效的选择，请重新输入")

        except ValueError:
            print("请输入有效数字")
        except KeyboardInterrupt:
            print("\n\n再见!")
            break


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
