import asyncio
import functools
import inspect
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")


def log_io(func: Callable) -> Callable:
    """
    A decorator that logs the input parameters and output of a tool function.

    Args:
        func: The tool function to be decorated

    Returns:
        The wrapped function with input/output logging
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Log input parameters
        func_name = func.__name__
        params = ", ".join(
            [*(str(arg) for arg in args), *(f"{k}={v}" for k, v in kwargs.items())]
        )
        logger.info(f"Tool {func_name} called with parameters: {params}")

        # Execute the function
        result = func(*args, **kwargs)

        # Log the output
        logger.info(f"Tool {func_name} returned: {result}")

        return result

    return wrapper


class LoggedToolMixin:
    """A mixin class that adds logging functionality to any tool."""

    def _log_operation(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        """Helper method to log tool operations."""
        tool_name = self.__class__.__name__.replace("Logged", "")
        params = ", ".join(
            [*(str(arg) for arg in args), *(f"{k}={v}" for k, v in kwargs.items())]
        )
        logger.debug(f"Tool {tool_name}.{method_name} called with parameters: {params}")

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """Override _run method to add logging."""
        self._log_operation("_run", *args, **kwargs)
        result = super()._run(*args, **kwargs)
        logger.debug(
            f"Tool {self.__class__.__name__.replace('Logged', '')} returned: {result}"
        )
        return result


def create_logged_tool(base_tool_class: Type[T]) -> Type[T]:
    """
    Factory function to create a logged version of any tool class.

    Args:
        base_tool_class: The original tool class to be enhanced with logging

    Returns:
        A new class that inherits from both LoggedToolMixin and the base tool class
    """

    class LoggedTool(LoggedToolMixin, base_tool_class):
        pass

    # Set a more descriptive name for the class
    LoggedTool.__name__ = f"Logged{base_tool_class.__name__}"
    return LoggedTool


class BaseTool(ABC):
    """
    工具抽象基类，简化工具定义和调用。

    继承此类并实现 execute 方法即可创建工具。
    _arun 方法使用 run_in_executor 自动实现异步调用。

    使用示例:
        class WeatherTool(BaseTool):
            name = "get_weather"
            description = "获取指定城市的天气信息"

            def execute(self, city: str) -> str:
                return f"{city}的天气：晴朗，22°C"

        tool = WeatherTool()
    """

    name: str = ""
    description: str = ""

    def __init__(self):
        """初始化工具实例"""
        if not self.name:
            self.name = self.__class__.__name__
        if not self.description:
            self.description = self.__doc__ or f"{self.name} tool"

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """同步执行方法，默认调用 execute"""
        return self.execute(*args, **kwargs)

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """同步执行方法，子类必须实现"""
        pass

    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        """
        异步执行方法，自动使用 run_in_executor 调用 _run。

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            执行结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, *args, **kwargs)

    def get_tool_definition(self) -> Dict[str, Any]:
        """
        获取工具定义（JSON Schema 格式）

        Returns:
            工具定义字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._generate_schema()
        }

    def _generate_schema(self) -> Dict[str, Any]:
        """
        从 execute 方法签名自动生成 JSON Schema

        Returns:
            参数 Schema
        """
        sig = inspect.signature(self.execute)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            param_type = self._infer_type(param.annotation)
            properties[param_name] = {
                "type": param_type
            }

            if param.default == inspect.Parameter.empty:
                required.append(param_name)

            if param.default != inspect.Parameter.empty:
                properties[param_name]["default"] = param.default

        schema = {
            "type": "object",
            "properties": properties
        }

        if required:
            schema["required"] = required

        return schema

    def _infer_type(self, annotation: Any) -> str:
        """
        从类型注解推断 JSON Schema 类型

        Args:
            annotation: Python 类型

        Returns:
            JSON Schema 类型字符串
        """
        return _infer_parameter_type(annotation)


def tool(name: Optional[str] = None,
         description: Optional[str] = None,
         parameters: Optional[Dict[str, Any]] = None):
    """
    工具装饰器，将函数转换为工具定义。

    自动从函数签名生成 JSON Schema，并提供异步执行支持。

    Args:
        name: 工具名称（默认使用函数名）
        description: 工具描述（默认使用函数文档）
        parameters: 参数字典（如果提供，将覆盖自动生成的 Schema）

    使用示例:

        @tool()
        def get_weather(city: str) -> str:
            '''获取指定城市的天气信息'''
            return f"{city}的天气：晴朗，22°C"

        agent.register_tool_from_tool(get_weather)
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"{tool_name} tool"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        if not parameters:
            sig = inspect.signature(func)
            properties = {}
            required = []

            for param_name, param in sig.parameters.items():
                param_type = _infer_parameter_type(param.annotation)
                properties[param_name] = {"type": param_type}

                if param.default == inspect.Parameter.empty:
                    required.append(param_name)

                if param.default != inspect.Parameter.empty:
                    properties[param_name]["default"] = param.default

            schema = {
                "type": "object",
                "properties": properties
            }

            if required:
                schema["required"] = required
        else:
            schema = parameters

        wrapper._tool_config = {
            "name": tool_name,
            "description": tool_description,
            "parameters": schema,
            "handler": func,
            "is_async": inspect.iscoroutinefunction(func)
        }

        return wrapper

    return decorator


def _infer_parameter_type(annotation: Any) -> str:
    """
    从类型注解推断参数字符串类型

    Args:
        annotation: Python 类型

    Returns:
        JSON Schema 类型字符串
    """
    if annotation == inspect.Parameter.empty:
        return "string"

    if hasattr(annotation, '__origin__'):
        origin = annotation.__origin__
        if origin == Union:
            return "string"

    type_str = str(annotation).lower()

    if 'int' in type_str:
        return "integer"
    if 'float' in type_str or 'double' in type_str:
        return "number"
    if 'bool' in type_str:
        return "boolean"
    if 'str' in type_str or 'string' in type_str:
        return "string"
    if 'list' in type_str or 'list' in type_str:
        return "array"
    if 'dict' in type_str or 'dict' in type_str or 'mapping' in type_str:
        return "object"

    return "string"