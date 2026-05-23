import os
import yaml
import logging
import sys
from get_root import root
from src.utils.api_keys import get_api_key

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# GRACEFUL ENGINE CHECK: Prevents messy crashes if PydanticAI is missing/misconfigured
# ------------------------------------------------------------------------------
try:
    from pydantic_ai.models.anthropic import AnthropicModel
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.models.google import GoogleModel
    from pydantic_ai.models.xai import XaiModel
    from pydantic_ai.models.bedrock import BedrockConverseModel
    from pydantic_ai.models.mistral import MistralModel
    from pydantic_ai.models.cerebras import CerebrasModel
    from pydantic_ai.models.cohere import CohereModel
    from pydantic_ai.models.groq import GroqModel
    from pydantic_ai.models.huggingface import HuggingFaceModel
    from pydantic_ai.models.ollama import OllamaModel
    from pydantic_ai.models.openrouter import OpenRouterModel

except ImportError as e:
    logger.warning("VRAKSHA ENGINE ERROR: PydanticAI components missing.")
    print("\n\033[38;5;203m[!] VRAKSHA ENGINE ERROR: PydanticAI components missing.\033[0m")
    print(f"Details: {e}")
    print("If you are in Docker, please run: \033[38;5;111mvraksha build\033[0m")
    print("If you are in venv, please run: \033[38;5;111mpip install -r requirements.txt\033[0m")
    sys.exit(1)


_CONFIG_PATH = root.project / "models.yaml"

# Baseline defaults if models.yaml is missing or corrupted
DEFAULT_MODELS = {
    "anthropic": {
        "orchestrator": "claude-4-5-sonnet-latest",
        "memory": "claude-4-5-haiku-latest",
        "code": "claude-4-5-sonnet-latest",
    },
    "openai": {
        "orchestrator": "gpt-4o",
        "memory": "gpt-4o-mini",
        "code": "gpt-4o",
    },
    "google": {
        "orchestrator": "gemini-3.1-pro",
        "memory": "gemini-3-flash",
        "code": "gemini-3.1-pro",
    },
    "xai": {
        "orchestrator": "grok-4-1-fast-non-reasoning",
        "memory": "grok-3-mini",
        "code": "grok-4-1-fast-non-reasoning",
    },
    "mistral": {
        "orchestrator": "mistral-large-latest",
        "memory": "mistral-small-latest",
        "code": "codestral-latest",
    },
    "cerebras": {
        "orchestrator": "llama3.3-70b",
        "memory": "llama3.1-8b",
        "code": "llama3.3-70b",
    },
    "cohere": {
        "orchestrator": "command-r-plus-08-2024",
        "memory": "command-r-08-2024",
        "code": "command-r-plus-08-2024",
    },
    "groq": {
        "orchestrator": "llama-3.3-70b-versatile",
        "memory": "llama-3.1-8b-instant",
        "code": "qwen-2.5-coder-32b",
    },
    "bedrock": {
        "orchestrator": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "memory": "amazon.nova-micro-v1:0",
        "code": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    },
    "huggingface": {
        "orchestrator": "meta-llama/Llama-3.3-70B-Instruct",
        "memory": "meta-llama/Llama-3.1-8B-Instruct",
        "code": "Qwen/Qwen2.5-Coder-32B-Instruct",
    },
    "ollama": {
        "orchestrator": "llama3.3",
        "memory": "llama3.1:8b",
        "code": "qwen2.5-coder:32b",
    },
    "openrouter": {
        "orchestrator": "anthropic/claude-sonnet-4-5",
        "memory": "google/gemini-3-flash",
        "code": "anthropic/claude-sonnet-4-5",
    }
}

PROVIDERS_PRIORITY_ORDER = {
    "google": GoogleModel,
    "openrouter": OpenRouterModel,
    "ollama": OllamaModel,
    "anthropic": AnthropicModel,
    "openai": OpenAIChatModel,
    "xai": XaiModel,
    "mistral": MistralModel,
    "cohere": CohereModel,
    "groq": GroqModel,
    "huggingface": HuggingFaceModel,
    "cerebras": CerebrasModel,
    "bedrock": BedrockConverseModel,
}

# Target environment variables mapping that PydanticAI / basic SDK wrappers strictly check
PYDANTIC_AI_ENV_MAPPING = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GEMINI_API_KEY",  # PydanticAI maps google: string short-hands directly here
    "xai": "XAI_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "cohere": "CO_API_KEY",  
    "groq": "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
    "huggingface": "HF_TOKEN",
    "ollama": "OLLAMA_BASE_URL",
}

def _normalize_provider(provider_name: str) -> str:
    """Normalizes informal provider aliases into strict registry keys."""
    name = provider_name.lower().strip()
    aliases = {
        "claude": "anthropic",
        "chatgpt": "openai",
        "gemini": "google",
        "x": "xai",
        "twitter": "xai"
    }
    return aliases.get(name, name)
    
    
def get_model_instance(provider_name: str, model_name: str):
    """Creates an initialized PydanticAI model instance synced with ApiKeyStore."""
    provider_name = _normalize_provider(provider_name)
    
    # Check key requirements (ollama utilizes custom URLs; bedrock utilizes AWS system profiles)
    if provider_name not in ["ollama", "bedrock"]:
        key = get_api_key(provider_name)
        if not key or not key.strip():
            logger.warning(f"Key/Token for {provider_name} is ABSENT in ApiKeyStore.")
            return None
        
        # Bridge the gap between your custom schema and what PydanticAI expects natively
        target_env = PYDANTIC_AI_ENV_MAPPING.get(provider_name)
        if target_env:
            os.environ[target_env] = key.strip()
            
    elif provider_name == "ollama":
        # Ensure OLLAMA_BASE_URL is explicitly back-populated if set in your schema
        base_url = get_api_key("ollama")
        if base_url:
            os.environ["OLLAMA_BASE_URL"] = base_url.strip()

    try:
        model_class = PROVIDERS_PRIORITY_ORDER.get(provider_name)
        if not model_class:
            logger.error(f"Provider '{provider_name}' is not supported or missing from registry.")
            return None
            
        return model_class(model_name)
            
    except Exception as e:
        logger.error(f"Provider {provider_name} failed to init model '{model_name}': {e}")
        return None

def get_model_priorities(task: str):
    """
    Returns a list of initialized PydanticAI Model instances, 
    prioritized by available keys and models.yaml config.
    """
    config = DEFAULT_MODELS
    if _CONFIG_PATH.exists():
        try:
            with open(_CONFIG_PATH, "r") as f:
                config = yaml.safe_load(f) or DEFAULT_MODELS
        except Exception as e:
            logger.warning(f"Failed to load models.yaml ({e}), using defaults...")

    instances = []
    
    for provider_name in PROVIDERS_PRIORITY_ORDER.keys():
        provider_config = config.get(provider_name, {})
        
        if isinstance(provider_config, dict):
            task_entry = provider_config.get(task)
            model_name = task_entry.get("model") if isinstance(task_entry, dict) else task_entry
        else:
            model_name = None
        
        if not model_name:
            task_defaults = DEFAULT_MODELS.get(provider_name, {})
            model_name = task_defaults.get(task) or task_defaults.get("orchestrator", "unknown")

        if model_name and model_name != "unknown":
            model_inst = get_model_instance(provider_name, model_name)
            if model_inst:
                instances.append(model_inst)

    return instances

