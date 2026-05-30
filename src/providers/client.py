"""Compatibility facade for provider model selection."""

from src.providers.candidate import ModelCandidate
from src.providers.config import (
    CONFIG_PATH as _CONFIG_PATH,
    load_model_config as _load_model_config,
    normalize_model_config as _normalize_model_config,
    normalize_provider as _normalize_provider,
)
from src.providers.defaults import DEFAULT_MODELS
from src.providers.env import (
    PYDANTIC_AI_ENV_MAPPING,
    provider_has_runtime_config as _provider_has_runtime_config,
    set_provider_env as _set_provider_env,
)
from src.providers.factory import get_model_instance
from src.providers.imports import PROVIDERS_PRIORITY_ORDER
from src.providers.legacy_client_info import client_info
from src.providers.priorities import get_model_priorities

__all__ = [
    "DEFAULT_MODELS",
    "ModelCandidate",
    "PROVIDERS_PRIORITY_ORDER",
    "PYDANTIC_AI_ENV_MAPPING",
    "_CONFIG_PATH",
    "_load_model_config",
    "_normalize_model_config",
    "_normalize_provider",
    "_provider_has_runtime_config",
    "_set_provider_env",
    "client_info",
    "get_model_instance",
    "get_model_priorities",
]
