from src.utils.client import client_info

def call_llm(role: str, system: str, messages: list[dict], max_tokens: int = 1500) -> str:
    # All shared info for all sub agents
    llm = client_info(role)

    client = llm["client"]
    client_name = llm["name"]
    model = llm["model"]

    if client_name == "anthropic":
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )

        return response.content[0].text

    elif client_name == "openai":
        response = client.responses.create(
            model=model,
            max_output_tokens=max_tokens,
            input=[
                {
                    "role": "system",
                    "content": system
                },
                *messages
            ]
        )

        return response.output_text

    raise Exception("Oops!\nCouldn't get response from client")

