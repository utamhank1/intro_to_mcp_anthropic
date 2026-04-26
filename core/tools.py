import json
from typing import Optional, Literal, List
from mcp.types import CallToolResult, Tool, TextContent
from mcp_client import MCPClient


class ToolManager:
    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPClient]) -> list[dict]:
        tools = []
        for client in clients.values():
            tool_models = await client.list_tools()
            tools += [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema,
                    },
                }
                for t in tool_models
            ]
        return tools

    @classmethod
    async def _find_client_with_tool(
        cls, clients: list[MCPClient], tool_name: str
    ) -> Optional[MCPClient]:
        for client in clients:
            tools = await client.list_tools()
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                return client
        return None

    @classmethod
    def _build_tool_result_message(
        cls,
        tool_call_id: str,
        text: str,
        status: Literal["success", "error"],
    ) -> dict:
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": text,
        }

    @classmethod
    async def execute_tool_requests(
        cls, clients: dict[str, MCPClient], message
    ) -> List[dict]:
        tool_calls = message.choices[0].message.tool_calls or []
        tool_result_messages: list[dict] = []

        for tool_call in tool_calls:
            tool_call_id = tool_call.id
            tool_name = tool_call.function.name
            try:
                tool_input = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_input = {}

            client = await cls._find_client_with_tool(
                list(clients.values()), tool_name
            )

            tool_output = None
            if not client:
                tool_result_msg = cls._build_tool_result_message(
                    tool_call_id, "Could not find that tool", "error"
                )
                tool_result_messages.append(tool_result_msg)
                continue

            try:
                tool_output: CallToolResult | None = await client.call_tool(
                    tool_name, tool_input
                )
                items = []
                if tool_output:
                    items = tool_output.content
                content_list = [
                    item.text for item in items if isinstance(item, TextContent)
                ]
                content_json = json.dumps(content_list)
                tool_result_msg = cls._build_tool_result_message(
                    tool_call_id,
                    content_json,
                    "error"
                    if tool_output and tool_output.isError
                    else "success",
                )
            except Exception as e:
                error_message = f"Error executing tool '{tool_name}': {e}"
                print(error_message)
                tool_result_msg = cls._build_tool_result_message(
                    tool_call_id,
                    json.dumps({"error": error_message}),
                    "error",
                )

            tool_result_messages.append(tool_result_msg)
        return tool_result_messages
