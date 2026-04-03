from anthropic import Anthropic
from openai import OpenAI
from src.utils.extract_api import get_api_key

# It selects the llm whose api key is given, but prioritizes claude over chatgpt if both are given
def client_info():
    anthropic_key = get_api_key("anthropic", ".env.local")
    openai_key = get_api_key("openai", ".env.local")

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