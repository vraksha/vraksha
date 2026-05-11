from abc import ABC, abstractmethod
import json

class ContentBlock:
    def __init__(self, block_type, text=None, id=None, name=None, input=None, tool_use_id=None, content=None):
        self.type = block_type
        self.text = text
        self.id = id
        self.name = name
        self.input = input
        self.tool_use_id = tool_use_id
        self.content = content

class NormalizedResponse:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason

class BaseLLMProvider(ABC):
    def __init__(self, client, model):
        self.client = client
        self.model = model

    @abstractmethod
    def call(self, system: str, messages: list[dict], max_tokens: int, tools: list[dict] = None, raw: bool = False) -> str | NormalizedResponse:
        pass

class AnthropicProvider(BaseLLMProvider):
    def call(self, system: str, messages: list[dict], max_tokens: int, tools: list[dict] = None, raw: bool = False) -> str | NormalizedResponse:
        # Convert messages to plain dicts to avoid serialization errors
        anthropic_messages = []
        for msg in messages:
            content = msg["content"]
            if isinstance(content, list):
                new_content = []
                for block in content:
                    if hasattr(block, "type"):
                        b = {"type": block.type}
                        if block.type == "text":
                            b["text"] = block.text
                        elif block.type == "tool_use":
                            b["id"] = block.id
                            b["name"] = block.name
                            b["input"] = block.input
                        elif block.type == "tool_result":
                            b["tool_use_id"] = block.tool_use_id
                            b["content"] = block.content
                        new_content.append(b)
                    else:
                        new_content.append(block)
                anthropic_messages.append({"role": msg["role"], "content": new_content})
            else:
                anthropic_messages.append(msg)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            tools=tools or [],
            messages=anthropic_messages,
        )

        if raw:
            content_blocks = []
            for block in response.content:
                if block.type == "text":
                    content_blocks.append(ContentBlock("text", text=block.text))
                elif block.type == "tool_use":
                    content_blocks.append(ContentBlock("tool_use", id=block.id, name=block.name, input=block.input))
            
            stop_reason = response.stop_reason
            return NormalizedResponse(content_blocks, stop_reason)

        return response.content[0].text

class OpenAIProvider(BaseLLMProvider):
    def call(self, system: str, messages: list[dict], max_tokens: int, tools: list[dict] = None, raw: bool = False) -> str | NormalizedResponse:
        openai_messages = [{"role": "system", "content": system}]
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if isinstance(content, list):
                assistant_text = ""
                assistant_tool_calls = []
                tool_results = []
                for block in content:
                    b_type = getattr(block, "type", block.get("type") if isinstance(block, dict) else None)
                    if b_type == "text":
                        text = getattr(block, "text", block.get("text") if isinstance(block, dict) else "")
                        if role == "assistant":
                            assistant_text += text
                        else:
                            openai_messages.append({"role": role, "content": text})
                    elif b_type == "tool_use":
                        b_id = getattr(block, "id", block.get("id") if isinstance(block, dict) else "")
                        b_name = getattr(block, "name", block.get("name") if isinstance(block, dict) else "")
                        b_input = getattr(block, "input", block.get("input") if isinstance(block, dict) else {})
                        assistant_tool_calls.append({
                            "id": b_id,
                            "type": "function",
                            "function": {"name": b_name, "arguments": json.dumps(b_input)}
                        })
                    elif b_type == "tool_result":
                        b_id = getattr(block, "tool_use_id", block.get("tool_use_id") if isinstance(block, dict) else "")
                        b_content = getattr(block, "content", block.get("content") if isinstance(block, dict) else "")
                        tool_results.append({"role": "tool", "tool_call_id": b_id, "content": b_content})
                
                if role == "assistant":
                    msg_obj = {"role": "assistant", "content": assistant_text or None}
                    if assistant_tool_calls:
                        msg_obj["tool_calls"] = assistant_tool_calls
                    openai_messages.append(msg_obj)
                for tr in tool_results:
                    openai_messages.append(tr)
            else:
                openai_messages.append({"role": role, "content": content})

        openai_tools = []
        if tools:
            for tool in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["input_schema"]
                    }
                })

        response = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            tools=openai_tools or None,
            max_tokens=max_tokens,
        )

        choice = response.choices[0]
        message = choice.message
        if raw:
            content_blocks = []
            if message.content:
                content_blocks.append(ContentBlock("text", text=message.content))
            if message.tool_calls:
                for tc in message.tool_calls:
                    content_blocks.append(ContentBlock(
                        "tool_use",
                        id=tc.id,
                        name=tc.function.name,
                        input=json.loads(tc.function.arguments)
                    ))
            stop_reason = "end_turn"
            if choice.finish_reason == "tool_calls":
                stop_reason = "tool_use"
            elif choice.finish_reason == "stop":
                stop_reason = "end_turn"
            return NormalizedResponse(content_blocks, stop_reason)

        return message.content or ""
