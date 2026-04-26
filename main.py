import asyncio
import sys
import os
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from mcp_client import MCPClient
from core.claude import Claude

from core.cli_chat import CliChat
from core.cli import CliApp

load_dotenv(override=True)

gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
gemini_api_key = os.getenv("GEMINI_API_KEY", "")
gemini_base_url = os.getenv(
    "GEMINI_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/",
)

assert gemini_api_key and gemini_api_key != "your-gemini-api-key-here", (
    "Error: GEMINI_API_KEY cannot be empty. "
    "Get a free key at https://aistudio.google.com/apikey and add it to .env"
)


async def main():
    claude_service = Claude(
        model=gemini_model,
        api_key=gemini_api_key,
        base_url=gemini_base_url,
    )

    server_scripts = sys.argv[1:]
    clients = {}

    command, args = (
        ("uv", ["run", "mcp_server.py"])
        if os.getenv("USE_UV", "0") == "1"
        else ("python", ["mcp_server.py"])
    )

    async with AsyncExitStack() as stack:
        doc_client = await stack.enter_async_context(
            MCPClient(command=command, args=args)
        )
        clients["doc_client"] = doc_client

        for i, server_script in enumerate(server_scripts):
            client_id = f"client_{i}_{server_script}"
            client = await stack.enter_async_context(
                MCPClient(command="uv", args=["run", server_script])
            )
            clients[client_id] = client

        chat = CliChat(
            doc_client=doc_client,
            clients=clients,
            claude_service=claude_service,
        )

        cli = CliApp(chat)
        await cli.initialize()
        await cli.run()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
