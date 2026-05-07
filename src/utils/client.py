from anthropic import Anthropic
from openai import OpenAI
from src.utils.api_keys import get_api_key

import yaml
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent.parent / "models.yaml"

_model_cache = None

def get_model(part: str, provider: str) ->  str:
    global _model_cache
    if _model_cache is None:
        with open(_CONFIG_PATH) as f:
            _model_cache = yaml.safe_load(f)
            
    return _model_cache[provider][part]["model"]


# Selecting the llms whose api keys are given, prioritizing Claude over ChatGPT
def client_info(part: str) -> list[dict]:
    anthropic_key = get_api_key("anthropic")
    openai_key = get_api_key("openai")
    
    clients = []

    if anthropic_key and anthropic_key.strip():
        clients.append({
            "client": Anthropic(api_key=anthropic_key),
            "name": "anthropic",
            "model": get_model(part, "anthropic")
        })

    if openai_key and openai_key.strip():
        clients.append({
            "client": OpenAI(api_key=openai_key),
            "name": "openai",
            "model": get_model(part, "openai")
        })

    if not clients:
        raise Exception("No valid API keys found")
        
    return clients

