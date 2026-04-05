from anthropic import Anthropic
from openai import OpenAI
from src.utils.api_keys import get_api_key

# Selecting the llm whose api key is given, but prioritizing Claude over ChatGPT if both are given
def client_info():
    anthropic_key = get_api_key("anthropic")
    openai_key = get_api_key("openai")

    if anthropic_key and anthropic_key.strip():
        return {
            "client": Anthropic(api_key=anthropic_key),
            "name": "anthropic",
            "model": "claude-sonnet-4-5"
        }

    elif openai_key and openai_key.strip():
        return {
            "client": OpenAI(api_key=openai_key),
            "name": "openai",
            "model": "gpt-4o-mini"
        }

    else:
        raise Exception("No valid API keys found")