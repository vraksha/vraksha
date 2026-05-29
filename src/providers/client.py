import os
import yaml
import logging
import sys
from dataclasses import dataclass
from get_root import root
from src.utils.api_keys import get_api_key, get_api_key_source, normalize_provider_name

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


@dataclass(frozen=True)
class ModelCandidate:
    provider_name: str
    model_name: str

    def instantiate(self):
        return get_model_instance(self.provider_name, self.model_name)

    def __str__(self):
        model_class = PROVIDERS_PRIORITY_ORDER.get(self.provider_name)
        class_name = model_class.__name__ if model_class else self.provider_name
        return f"{class_name}({self.model_name})"

# Target environment variables mapping that PydanticAI / basic SDK wrappers strictly check.
# Each normalized key is copied into every SDK env var for that provider so aliases
# cannot accidentally route a request through a different configured account.
PYDANTIC_AI_ENV_MAPPING = {
    "openai": ("OPENAI_API_KEY",),
    "anthropic": ("ANTHROPIC_API_KEY",),
    "google": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "xai": ("XAI_API_KEY",),
    "mistral": ("MISTRAL_API_KEY",),
    "cohere": ("CO_API_KEY",),
    "groq": ("GROQ_API_KEY",),
    "openrouter": ("OPENROUTER_API_KEY",),
    "cerebras": ("CEREBRAS_API_KEY",),
    "huggingface": ("HF_TOKEN",),
    "ollama": ("OLLAMA_BASE_URL",),
}

def _normalize_provider(provider_name: str) -> str:
    """Normalizes informal provider aliases into strict registry keys."""
    return normalize_provider_name(provider_name)


def _set_provider_env(provider_name: str, value: str):
    for target_env in PYDANTIC_AI_ENV_MAPPING.get(provider_name, ()):
        os.environ[target_env] = value.strip()


def _normalize_model_config(config: dict) -> dict:
    """Merge alias provider sections in models.yaml into canonical provider keys."""
    normalized = {}

    for provider_name, provider_config in config.items():
        canonical_name = _normalize_provider(provider_name)

        if canonical_name in normalized:
            logger.warning(
                "Duplicate model config for provider alias '%s'; keeping earlier '%s' config.",
                provider_name,
                canonical_name,
            )
            continue

        normalized[canonical_name] = provider_config

    return normalized


def _load_model_config() -> dict:
    if not _CONFIG_PATH.exists():
        return _normalize_model_config(DEFAULT_MODELS)

    try:
        with open(_CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f) or DEFAULT_MODELS

        if not isinstance(config, dict):
            logger.warning("models.yaml did not contain a provider map; using defaults...")
            return _normalize_model_config(DEFAULT_MODELS)

        return _normalize_model_config(config)

    except Exception as e:
        logger.warning(f"Failed to load models.yaml ({e}), using defaults...")
        return _normalize_model_config(DEFAULT_MODELS)


def _provider_has_runtime_config(provider_name: str) -> bool:
    if provider_name == "bedrock":
        return bool(
            get_api_key("bedrock")
            or os.getenv("AWS_REGION")
            or os.getenv("AWS_DEFAULT_REGION")
            or os.getenv("AWS_PROFILE")
        )

    return bool(get_api_key(provider_name))

    
def get_model_instance(provider_name: str, model_name: str):
    """Creates an initialized PydanticAI model instance synced with ApiKeyStore."""
    provider_name = _normalize_provider(provider_name)
    
    # Check key requirements (ollama utilizes custom URLs; bedrock utilizes AWS system profiles)
    if provider_name not in ["ollama", "bedrock"]:
        key = get_api_key(provider_name)
        if not key or not key.strip():
            logger.warning(f"Key/Token for {provider_name} is ABSENT in ApiKeyStore.")
            return None
        
        _set_provider_env(provider_name, key)
            
    elif provider_name == "ollama":
        # Ensure OLLAMA_BASE_URL is explicitly back-populated if set in your schema
        base_url = get_api_key("ollama")
        if base_url:
            _set_provider_env("ollama", base_url)

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
    Returns lazy model candidates, prioritized by available provider config.
    Candidates are instantiated only when the engine actually attempts them.
    """
    config = _load_model_config()
    candidates = []
    
    for provider_name in PROVIDERS_PRIORITY_ORDER.keys():
        if not _provider_has_runtime_config(provider_name):
            logger.debug("Provider %s is not configured; skipping.", provider_name)
            continue

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
            key_source = get_api_key_source(provider_name)
            if key_source:
                logger.debug("Provider %s configured from %s.", provider_name, key_source)
            candidates.append(ModelCandidate(provider_name, model_name))

    return candidates
