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
    from pydantic_ai.models.openai import OpenAIModel
    from pydantic_ai.models.google import GoogleModel  
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
        "orchestrator": "claude-3-5-sonnet-latest",
        "memory": "claude-3-5-haiku-latest",
        "code": "claude-3-5-sonnet-latest",
    },
    "openai": {
        "orchestrator": "gpt-4o",
        "memory": "gpt-4o-mini",
        "code": "gpt-4o",
    },
    "google": {
        "orchestrator": "gemini-1.5-pro",
        "memory": "gemini-1.5-flash",
        "code": "gemini-1.5-pro",
    }
}

def get_model_instance(provider_name: str, model_name: str):
    """Creates a PydanticAI model instance with an explicit provider and key."""
    key = get_api_key(provider_name)
    
    if not key or not key.strip():
        logger.warning(f"Key for {provider_name} is ABSENT or empty.")
        return None

    try:
        if provider_name == "anthropic":
            # PydanticAI 1.x handles API keys via environment variables by default.
            # Explicit key passing is done via client configuration if needed.
            return AnthropicModel(model_name)
            
        elif provider_name == "openai":
            return OpenAIModel(model_name)
            
        elif provider_name == "google":
            return GoogleModel(model_name)
            
    except Exception as e:
        logger.error(f"Provider {provider_name} rejected the key or failed to init: {e}")
        return None
    
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
            logger.warning(f"Failed to load models.yaml ({e}), using defaults.")

    instances = []
    # Hardcoded priority: Anthropic > OpenAI > Google
    for provider_name in ["anthropic", "openai", "google"]:
        provider_config = config.get(provider_name, {})
        model_name = provider_config.get(task, {}).get("model") if isinstance(provider_config.get(task), dict) else provider_config.get(task)
        
        if not model_name:
            task_defaults = DEFAULT_MODELS.get(provider_name, {})
            model_name = task_defaults.get(task) or task_defaults.get("orchestrator", "unknown")

        if model_name != "unknown":
            model_inst = get_model_instance(provider_name, model_name)
            if model_inst:
                instances.append(model_inst)

    return instances
