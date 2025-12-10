"""
澄清等待Hook实现

当coordinator需要澄清时，此hook会自动等待用户输入
支持测试模式下的输入回调
"""

from typing import Optional, Callable
import logging

from .hooks import HookEvent, HookContext

logger = logging.getLogger(__name__)


async def clarification_wait_handler(context: HookContext, **kwargs) -> HookContext:
    """
    澄清等待处理函数（async函数，可以直接注册到hook registry）

    Args:
        context: 钩子上下文，包含state数据
        **kwargs: 额外参数，可能包含coordinator实例

    Returns:
        处理后的上下文
    """
    state = context.data
    max_clarification_rounds = 5
    clarification_round = 0

    # 获取coordinator实例（如果提供）
    coordinator = kwargs.get('coordinator')

    # 循环处理澄清，直到不需要澄清或达到最大轮数
    while state.get("assigned_team") == "clarify_requirement":
        clarification_round += 1

        if clarification_round > max_clarification_rounds:
            logger.warning(f"澄清轮数超过限制({max_clarification_rounds})，强制完成")
            # 强制设置不需要澄清
            state["assigned_team"] = "basic_llm"
            state["enable_clarify_requirement"] = False
            break

        # 获取澄清问题
        messages = state.get("messages", [])
        if not messages:
            logger.warning("需要澄清但没有找到澄清问题")
            break

        # 获取最新的澄清问题
        latest_question = None
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and msg.get("content"):
                latest_question = msg.get("content")
                break

        if not latest_question:
            logger.warning("需要澄清但找不到问题内容")
            break

        # 显示澄清问题
        print(f"\n{'='*60}")
        print(" 需要澄清 ")
        print(f"{'='*60}")
        print(f"{latest_question}")
        print(f"{'='*60}")

        # 显示选项提示
        print("\n选项:")
        print("  1. 输入回答继续澄清")
        print("  2. 输入 'skip' 跳过澄清（将分配到基础对话）")
        print("  3. 输入 'quit' 退出澄清流程")

        # 获取用户输入
        try:
            # 检查是否有输入回调
            input_callback = kwargs.get('input_callback')
            if input_callback:
                # 测试模式：使用回调函数
                user_input = input_callback(latest_question)
                logger.info(f"测试输入: {user_input[:50]}...")
            else:
                # 正常模式：等待用户输入
                print("\n请输入您的回答: ", end="", flush=True)
                user_input = input().strip()

            # 检查退出命令
            if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                logger.info("用户选择退出澄清")
                break

            # 检查跳过命令
            if user_input.lower() in ['skip', '跳过', 's']:
                logger.info("用户选择跳过澄清")
                state["assigned_team"] = "basic_llm"
                state["enable_clarify_requirement"] = False
                break

            # 处理用户输入
            if user_input:
                # 添加用户回答到消息列表
                if "messages" not in state:
                    state["messages"] = []

                state["messages"].append({
                    "role": "user",
                    "content": user_input,
                    "timestamp": __import__("datetime").datetime.now().isoformat()
                })

                # 更新澄清后的需求
                current_clarified = state.get("clarified_requirement", "")
                if current_clarified:
                    state["clarified_requirement"] = f"{current_clarified} {user_input}".strip()
                else:
                    state["clarified_requirement"] = user_input

                logger.info(f"澄清轮次: {clarification_round}/{max_clarification_rounds}")

                # 如果有coordinator实例，重新判断是否还需要澄清
                if coordinator:
                    print("\n[协调器] 正在分析您的回答...")
                    try:
                        # 调用coordinator的ainvoke方法重新判断
                        state = await coordinator.ainvoke(state)
                    except Exception as e:
                        logger.error(f"重新调用coordinator失败: {e}")
                        break

                    # 如果不再需要澄清，退出循环
                    if state.get("assigned_team") != "clarify_requirement":
                        print(f"\n[协调器] 澄清完成！")
                        print(f"[协调器] 分配到团队: {state.get('assigned_team')}")
                        if state.get("coordinator_action"):
                            print(f"[协调器] 原因: {state.get('coordinator_action', '')}")
                        break
                else:
                    # 没有coordinator实例，只处理一次输入
                    logger.warning("未提供coordinator实例，只能处理一次澄清输入")
                    break

        except (EOFError, KeyboardInterrupt):
            logger.info("用户中断输入，退出澄清")
            break
        except Exception as e:
            logger.error(f"获取用户输入时出错: {e}")
            break

    return context


# 保持向后兼容的类实现
class ClarificationWaitHook:
    """
    澄清等待Hook（兼容性类）

    注意：推荐使用 clarification_wait_handler 函数而不是这个类
    """

    def __init__(self, input_callback: Optional[Callable[[str], str]] = None):
        """
        初始化澄清等待Hook

        Args:
            input_callback: 输入回调函数，用于测试
        """
        self.input_callback = input_callback
        self.max_clarification_rounds = 5

    @property
    def priority(self) -> int:
        """Hook优先级"""
        return 100

    @property
    def event_type(self) -> HookEvent:
        """Hook事件类型"""
        return HookEvent.WAIT_FOR_CLARIFICATION

    async def __call__(self, context: HookContext, **kwargs) -> HookContext:
        """
        调用澄清等待Hook
        """
        # 如果有input_callback，传递给handler
        if self.input_callback and 'input_callback' not in kwargs:
            kwargs['input_callback'] = self.input_callback

        # 调用实际的处理函数
        return await clarification_wait_handler(context, **kwargs)


def create_clarification_hook_with_callback(callback: Callable[[str], str]) -> Callable:
    """
    创建带回调的澄清等待Hook函数

    Args:
        callback: 输入回调函数

    Returns:
        配置好的澄清等待Hook函数
    """
    async def wrapper(context: HookContext, **kwargs):
        kwargs['input_callback'] = callback
        return await clarification_wait_handler(context, **kwargs)

    return wrapper


def create_default_clarification_hook() -> Callable:
    """
    创建默认的澄清等待Hook函数

    Returns:
        澄清等待Hook函数（使用标准输入）
    """
    return clarification_wait_handler
