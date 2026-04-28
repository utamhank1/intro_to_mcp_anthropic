# MCP Chat

MCP Chat is a command-line interface application that enables interactive chat capabilities with AI models through the MCP (Model Context Protocol) architecture. The application supports document retrieval, command-based prompts, and extensible tool integrations.

## Prerequisites

- Python 3.10+
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

## Refactoring from Anthropic SDK to Gemini (OpenAI SDK)

The original tutorial uses the Anthropic SDK to call Claude models. If you don't have access to the Anthropic API or Vertex AI, follow these steps to refactor the code to use Google's free Gemini API via its OpenAI-compatible endpoint.

### Step 1: Get a free Gemini API key

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **Create API key**
3. Select **"Create API key in new project"** (important: do not use an existing GCP project, as it may not have free tier quotas)
4. Copy the generated key

### Step 2: Swap the dependency in `pyproject.toml`

Replace the `anthropic` package with `openai`:

```diff
 dependencies = [
-    "anthropic>=0.51.0",
+    "openai>=1.30.0",
     "mcp[cli]>=1.8.0",
     "prompt-toolkit>=3.0.51",
     "python-dotenv>=1.1.0",
 ]
```

### Step 3: Update `.env`

Replace the Anthropic environment variables with Gemini config:

```
GEMINI_MODEL="gemini-2.5-flash"
GEMINI_API_KEY="your-gemini-api-key-here"

# Set to 1 if you're using uv to run the project.
USE_UV=1
```

### Step 4: Refactor `main.py`

Replace the Anthropic config loading with Gemini config:

```python
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
```

Update the `Claude` constructor call to pass `api_key` and `base_url`:

```python
claude_service = Claude(
    model=gemini_model,
    api_key=gemini_api_key,
    base_url=gemini_base_url,
)
```

### Step 5: Refactor `core/claude.py`

This is the main LLM client. The key changes are:

1. **Import**: Replace `from anthropic import Anthropic` with `from openai import OpenAI`
2. **Constructor**: Accept `api_key` and `base_url`, create `OpenAI(api_key=..., base_url=...)`
3. **`chat()` method**: Use `client.chat.completions.create()` instead of `client.messages.create()`
   - Prepend `system` as a `{"role": "system"}` message instead of a separate parameter
   - Rename `stop_sequences` to `stop`
   - Remove `thinking` support (Anthropic-specific)
4. **`text_from_message()`**: Access `message.choices[0].message.content` instead of iterating content blocks
5. **`add_assistant_message()`**: Serialize `tool_calls` into the history dict when the assistant makes tool calls (OpenAI requires this for multi-turn tool use)

### Step 6: Refactor `core/tools.py`

Update the tool format and tool call handling:

1. **Remove Anthropic imports**: Remove `from anthropic.types import Message, ToolResultBlockParam`
2. **Tool definitions** (`get_all_tools`): Wrap each tool in OpenAI format:
   ```python
   # Anthropic format:
   {"name": "...", "description": "...", "input_schema": {...}}

   # OpenAI format:
   {"type": "function", "function": {"name": "...", "description": "...", "parameters": {...}}}
   ```
3. **Tool call extraction** (`execute_tool_requests`): Read from `message.choices[0].message.tool_calls` instead of filtering `message.content` blocks. Parse `tool_call.function.arguments` with `json.loads()` (OpenAI returns arguments as a JSON string, not a dict).
4. **Tool results**: Return `{"role": "tool", "tool_call_id": "...", "content": "..."}` messages instead of Anthropic's `{"type": "tool_result", "tool_use_id": "...", "content": "...", "is_error": ...}`

### Step 7: Refactor `core/chat.py`

1. **Remove** `from anthropic.types import MessageParam` — use `list[dict]` instead
2. **Tool call detection**: Check `response.choices[0].message.tool_calls` presence instead of `response.stop_reason == "tool_use"` (more robust for Gemini)
3. **Tool result insertion**: Use `self.messages.extend(tool_result_messages)` instead of wrapping results in a single user message. In OpenAI format, each tool result is a separate message with `role: "tool"`.

### Step 8: Update `core/cli_chat.py`

1. Remove `from anthropic.types import MessageParam`
2. Change return type annotations from `MessageParam` to `dict`

### Step 9: Install dependencies and run

```bash
uv sync
uv run main.py
```

## Key format differences (Anthropic vs. OpenAI/Gemini)

| Concept | Anthropic | OpenAI/Gemini |
|---------|-----------|---------------|
| Tool definition | `{"name", "description", "input_schema"}` | `{"type": "function", "function": {"name", "description", "parameters"}}` |
| Tool call in response | `block.type == "tool_use"` with `.id`, `.name`, `.input` | `message.tool_calls[i]` with `.id`, `.function.name`, `.function.arguments` (JSON string) |
| Tool result | User msg with `[{"type": "tool_result", "tool_use_id", ...}]` | Separate `{"role": "tool", "tool_call_id", "content"}` messages |
| Stop reason | `response.stop_reason == "tool_use"` | Check `message.tool_calls` presence |
| Response text | Iterate `message.content` blocks | `message.choices[0].message.content` |
| System prompt | Separate `system` parameter | `{"role": "system"}` message |

## Files that do NOT change

The MCP layer is provider-agnostic. These files remain untouched:

- `mcp_client.py` — MCP protocol client
- `mcp_server.py` — MCP server with tools and resources
- `core/cli.py` — CLI interface with completions and key bindings

## Usage

### Basic Interaction

Simply type your message and press Enter to chat with the model.

### Document Retrieval

Use the @ symbol followed by a document ID to include document content in your query:

```
> Tell me about @deposition.md
```

### Commands

Use the / prefix to execute commands defined in the MCP server:

```
> /summarize deposition.md
```

Commands will auto-complete when you press Tab.

## Development

### Adding New Documents

Edit the `mcp_server.py` file to add new documents to the `docs` dictionary.

### Implementing MCP Features

To fully implement the MCP features:

1. Complete the TODOs in `mcp_server.py`
2. Implement the missing functionality in `mcp_client.py`
