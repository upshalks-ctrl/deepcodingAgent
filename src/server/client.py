import json
import asyncio
import os
import sys

from langchain_core.messages import AIMessage

# --- 添加以下代码 ---
# 获取当前文件的绝对路径
current_path = os.path.abspath(__file__)
# 获取当前文件所在的目录 (src/server/)
server_dir = os.path.dirname(current_path)
# 获取 src 目录
src_dir = os.path.dirname(server_dir)
# 获取项目根目录 (deepcodeagent1/)
project_root = os.path.dirname(src_dir)

# 将项目根目录添加到 sys.path
if project_root not in sys.path:
    sys.path.append(project_root)
# --- 代码添加结束 ---


from src.llms.llm import get_llm_by_type
from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client




class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.llm = get_llm_by_type("basic")


    async def connect_to_server(self):
        server_params = StdioServerParameters(
            # 服务器执行的命令，这里我们使用 uv 来运行 web_search.py
            command='uv',
            # 运行的参数
            args=['run', 'D:\\code\\PythonWorkPath\\deepcodeagent1\\src\\server\\web_search.py'],
            # 环境变量，默认为 None，表示使用当前环境变量
            # env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params))
        stdio, write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(stdio, write))

        await self.session.initialize()

    async def process_query(self, query: str) -> str:
        # 这里需要通过 system prompt 来约束一下大语言模型，
        # 否则会出现不调用工具，自己乱回答的情况
        system_prompt = (
            "You are a helpful assistant."
            "You have the function of online search. "
            "Please MUST call web_search tool to search the Internet content before answering."
            "Please do not lose the user's question information when searching,"
            "and try to maintain the completeness of the question content as much as possible."
            "When there is a date related question in the user's question,"
            "please use the search function directly to search and PROHIBIT inserting specific time."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        # 获取所有 mcp 服务器 工具列表信息
        response = await self.session.list_tools()
        # 生成 function call 的描述信息
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
        } for tool in response.tools]

        # 请求 deepseek，function call 的描述信息通过 tools 参数传入
        self.llm.bind_tools(available_tools)
        response = await self.llm.ainvoke(messages)
        print(response)
        # 处理返回的内容
        content = response.choices[0]
        if content.finish_reason == "tool_calls":
            # 如何是需要使用工具，就解析工具
            tool_call = content.message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            # 执行工具
            result = await self.session.call_tool(tool_name, tool_args)
            print(f"\n\n[Calling tool {tool_name} with args {tool_args}]\n\n")

            # 将 deepseek 返回的调用哪个工具数据和工具执行完成后的数据都存入messages中
            messages.append(content.message.model_dump())
            messages.append({
                "role": "tool",
                "content": result.content[0].text,
                "tool_call_id": tool_call.id,
            })

            # 将上面的结果再返回给 deepseek 用于生产最终的结果
            response =await self.llm.ainvoke(messages)
            return response.choices[0].message.content

        return content.message.content

    async def chat_loop(self):
        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                import traceback
                traceback.print_exc()

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    client = MCPClient()
    try:
        await client.connect_to_server()
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys

    asyncio.run(main())
