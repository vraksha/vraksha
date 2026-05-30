from __future__ import annotations

import logging
from typing import Any

from src.providers.config import load_model_config
from src.providers.defaults import DEFAULT_MODELS
from src.utils.api_keys import get_api_key

logger = logging.getLogger(__name__)


def client_info(model_part: str) -> list[dict[str, Any]]:
    """Deprecated client list for src.utils.call_llm compatibility."""
    clients: list[dict[str, Any]] = []
    config = load_model_config()

    anthropic_key = get_api_key("anthropic")
    if anthropic_key:
        anthropic_client = _make_anthropic_client(anthropic_key)
        if anthropic_client:
            clients.append({
                "name": "anthropic",
                "client": anthropic_client,
                "model": _model_for(config, "anthropic", model_part),
            })

    openai_key = get_api_key("openai")
    if openai_key:
        openai_client = _make_openai_client(openai_key)
        if openai_client:
            clients.append({
                "name": "openai",
                "client": openai_client,
                "model": _model_for(config, "openai", model_part),
            })

    return clients


def _model_for(config: dict, provider: str, model_part: str) -> str:
    provider_config = config.get(provider, {})
    task_entry = provider_config.get(model_part) if isinstance(provider_config, dict) else None
    model_name = task_entry.get("model") if isinstance(task_entry, dict) else task_entry

    if model_name:
        return model_name

    defaults = DEFAULT_MODELS.get(provider, {})
    return defaults.get(model_part) or defaults.get("orchestrator", "unknown")


def _make_anthropic_client(api_key: str):
    try:
        from anthropic import Anthropic
    except ImportError:
        logger.debug("anthropic package not installed; skipping deprecated client_info entry.")
        return None

    return Anthropic(api_key=api_key)


def _make_openai_client(api_key: str):
    try:
        from openai import OpenAI
    except ImportError:
        logger.debug("openai package not installed; skipping deprecated client_info entry.")
        return None

    return OpenAI(api_key=api_key)
