import json
from openai import OpenAI


class Claude:
    def __init__(self, model: str, api_key: str, base_url: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self.model = model

    def add_user_message(self, messages: list, message):
        if hasattr(message, "choices"):
            content = message.choices[0].message.content or ""
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": message})

    def add_assistant_message(self, messages: list, message):
        if hasattr(message, "choices"):
            assistant_msg = message.choices[0].message
            entry = {
                "role": "assistant",
                "content": assistant_msg.content or "",
            }
            if assistant_msg.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in assistant_msg.tool_calls
                ]
            messages.append(entry)
        else:
            messages.append({"role": "assistant", "content": message})

    def text_from_message(self, message) -> str:
        content = message.choices[0].message.content
        return content if content else ""

    def chat(
        self,
        messages,
        system=None,
        temperature=1.0,
        stop_sequences=None,
        tools=None,
        thinking=False,
        thinking_budget=1024,
    ):
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        params = {
            "model": self.model,
            "max_tokens": 8000,
            "messages": full_messages,
            "temperature": temperature,
        }

        if stop_sequences:
            params["stop"] = stop_sequences

        if tools:
            params["tools"] = tools

        response = self.client.chat.completions.create(**params)
        return response
