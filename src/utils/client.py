from anthropic import Anthropic
from openai import OpenAI
from src.utils.api_keys import get_api_key

import yaml
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent.parent / "models.yaml"

_model_cache = None

def get_model(role: str, provider: str) ->  str:
    global _model_cache
    if _model_cache is None:
        with open(_CONFIG_PATH) as f:
            _model_cache = yaml.safe_load(f)
            
    return _model_cache[provider][role]["model"]


# Selecting the llm whose api key is given, but prioritizing Claude over ChatGPT if both are given
def client_info(role: str) -> dict:
    anthropic_key = get_api_key("anthropic")
    openai_key = get_api_key("openai")

    if anthropic_key and anthropic_key.strip():
        return {
            "client": Anthropic(api_key=anthropic_key),
            "name": "anthropic",
            "model": get_model(role, "anthropic")
        }

    elif openai_key and openai_key.strip():
        return {
            "client": OpenAI(api_key=openai_key),
            "name": "openai",
            "model": get_model(role, "openai")
        }

    else:
        raise Exception("No valid API keys found")

