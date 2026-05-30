"""Compatibility facade for API key lookup helpers."""

from src.utils.api_key_utils.aliases import PROVIDER_ALIASES, normalize_provider_name
from src.utils.api_key_utils.env_loader import init_env
from src.utils.api_key_utils.schema import PROVIDER_KEY_SCHEMA
from src.utils.api_key_utils.store import ApiKeyStore

init_env()

key_store = ApiKeyStore(PROVIDER_KEY_SCHEMA)
key_store.load_keys()


def get_api_key(provider: str) -> str:
    return key_store.get_key(provider)


def get_api_key_source(provider: str) -> str:
    return key_store.get_source(provider)


__all__ = [
    "ApiKeyStore",
    "PROVIDER_ALIASES",
    "PROVIDER_KEY_SCHEMA",
    "get_api_key",
    "get_api_key_source",
    "init_env",
    "key_store",
    "normalize_provider_name",
]
