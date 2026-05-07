from src.utils.client import client_info
import json


class NormalizedResponse:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason


class ContentBlock:
    def __init__(self, block_type, text=None, id=None, name=None, input=None):
        self.type = block_type
        self.text = text
        self.id = id
        self.name = name
        self.input = input

def call_llm(
    model_part: str,
    system: str,
    messages: list[dict],
    max_tokens: int = 1500,
    tools=None,
    raw: bool = False
) -> str | NormalizedResponse:
    """
    All shared info for all sub agents
    """
    llm = client_info(model_part)

    client = llm["client"]
    client_name = llm["name"]
    model = llm["model"]

    if client_name == "anthropic":
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=tools or [],
            messages=messages,
        )

        if raw:
            return response

        return response.content[0].text

    elif client_name == "openai":
        # Converting Anthropic-style messages to OpenAI-style ones
        openai_messages = [{
            "role": "system",
            "content": system
        }]

        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if isinstance(content, list):
                # Handle tool_use or tool_result blocks
                for block in content:
                    if block["type"] == "text":
                        openai_messages.append({"role": role, "content": block["text"]})

                    elif block["type"] == "tool_use":
                        # Assistant calling a tool
                        openai_messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": block["id"],
                                "type": "function",
                                "function": {
                                    "name": block["name"],
                                    "arguments": json.dumps(block["input"])
                                }
                            }]
                        })

                    elif block["type"] == "tool_result":
                        # User providing tool result
                        openai_messages.append({
                            "role": "tool",
                            "tool_call_id": block["tool_use_id"],
                            "content": block["content"]
                        })
            else:
                openai_messages.append({"role": role, "content": content})

        # Convert Anthropic-style tools to OpenAI-style
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

        response = client.chat.completions.create(
            model=model,
            messages=openai_messages,
            tools=openai_tools or None,
            max_tokens=max_tokens,
        )

        choice = response.choices[0]
        message = choice.message
        
        if raw:
            # Normalize to Anthropic-style
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

    raise Exception("Oops!\nCouldn't get response from client")

