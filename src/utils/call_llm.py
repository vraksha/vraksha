from src.providers.client import client_info
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
    clients = client_info(model_part)
    
    last_error = None

    for llm in clients:
        client = llm["client"]
        client_name = llm["name"]
        model = llm["model"]

        try:
            if client_name == "anthropic":
                # Convert messages to plain dicts to avoid serialization errors with mock blocks
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

                        anthropic_messages.append({
                                "role": msg["role"],
                                "content": new_content
                            })
                    
                    else:
                        anthropic_messages.append(msg)

                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system,
                    tools=tools or [],
                    messages=anthropic_messages,
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
                        # Group all blocks for this message
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
                                    # User or other roles
                                    openai_messages.append({"role": role, "content": text})

                            elif b_type == "tool_use":
                                b_id = getattr(block, "id", block.get("id") if isinstance(block, dict) else "")
                                b_name = getattr(block, "name", block.get("name") if isinstance(block, dict) else "")
                                b_input = getattr(block, "input", block.get("input") if isinstance(block, dict) else {})
                                
                                assistant_tool_calls.append({
                                    "id": b_id,
                                    "type": "function",
                                    "function": {
                                        "name": b_name,
                                        "arguments": json.dumps(b_input)
                                    }
                                })

                            elif b_type == "tool_result":
                                b_id = getattr(block, "tool_use_id", block.get("tool_use_id") if isinstance(block, dict) else "")
                                b_content = getattr(block, "content", block.get("content") if isinstance(block, dict) else "")
                                
                                tool_results.append({
                                    "role": "tool",
                                    "tool_call_id": b_id,
                                    "content": b_content
                                })
                        
                        # After processing all blocks in this list-content message:
                        if role == "assistant":
                            msg_obj = {"role": "assistant", "content": assistant_text or None}

                            if assistant_tool_calls:
                                msg_obj["tool_calls"] = assistant_tool_calls
                                
                            openai_messages.append(msg_obj)
                        
                        # Add any tool results found in this block list
                        for tr in tool_results:
                            openai_messages.append(tr)

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
        
        except Exception as e:
            last_error = e
            error_msg = str(e).lower()

            # Check for common API errors: Auth, Quota, Rate Limit, Credits, Server Errors
            fallback_keywords = [
                "401", "402", "403", "429", "500", "502", "503", 
                "authentication", "api key", "quota", "credit", 
                "rate limit", "balance", "insufficient", "payment", "billing"
            ]
            
            if any(kw in error_msg for kw in fallback_keywords) and len(clients) > 1:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"API Provider '{client_name}' failed with an error. Falling back to the next available provider... (Error: {e})")
                continue

            raise e

    if last_error:
        raise last_error
    
    raise Exception("Oops!\nCouldn't get response from client")

