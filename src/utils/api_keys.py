import os
from dotenv import load_dotenv
from pathlib import Path


PROVIDER_ALIASES = {
    "anthropic": "anthropic",
    "claude": "anthropic",
    "openai": "openai",
    "chatgpt": "openai",
    "gpt": "openai",
    "google": "google",
    "gemini": "google",
    "xai": "xai",
    "x": "xai",
    "grok": "xai",
    "twitter": "xai",
    "openrouter": "openrouter",
    "open_router": "openrouter",
    "mistral": "mistral",
    "bedrock": "bedrock",
    "aws_bedrock": "bedrock",
    "cerebras": "cerebras",
    "cohere": "cohere",
    "groq": "groq",
    "ollama": "ollama",
    "huggingface": "huggingface",
    "hugging_face": "huggingface",
    "hf": "huggingface",
    "github": "github",
    "gh": "github",
}


def normalize_provider_name(provider: str) -> str:
    """Return the canonical provider key used internally by Vraksha."""
    normalized = provider.lower().strip().replace("-", "_").replace(" ", "_")
    return PROVIDER_ALIASES.get(normalized, normalized)


PROVIDER_KEY_SCHEMA = {
    "anthropic": ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY", "ANTHROPIC_TOKEN", "CLAUDE_TOKEN"],
    "openai": ["OPENAI_API_KEY", "CHATGPT_API_KEY", "GPT_API_KEY", "OPENAI_TOKEN", "CHATGPT_TOKEN"],

    "google": ["GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_TOKEN", "GOOGLE_TOKEN"],

    "xai": ["XAI_API_KEY", "GROK_API_KEY", "X_API_KEY", "XAI_TOKEN", "GROK_TOKEN"],
    "openrouter": ["OPENROUTER_API_KEY", "OPEN_ROUTER_API_KEY", "OPENROUTER_TOKEN"],
    "mistral": ["MISTRAL_API_KEY", "MISTRAL_TOKEN"],

    "bedrock": ["AWS_BEARER_TOKEN_BEDROCK", "BEDROCK_API_KEY", "BEDROCK_TOKEN"],

    "cerebras": ["CEREBRAS_API_KEY", "CEREBRAS_TOKEN"],
    "cohere": ["CO_API_KEY", "COHERE_API_KEY", "COHERE_TOKEN"],
    "groq": ["GROQ_API_KEY", "GROQ_TOKEN"],

    "ollama": ["OLLAMA_BASE_URL", "OLLAMA_HOST"],
    "huggingface": ["HF_TOKEN", "HUGGINGFACE_API_KEY", "HUGGINGFACE_TOKEN", "HF_API_KEY"],
    "github": ["GITHUB_TOKEN", "GH_TOKEN"],
}



def init_env():
    """
    Load .env files once at startup.
    Walks up until project root and loads first matched .env* files.
    """
    current = Path(__file__).resolve().parent

    while current != current.parent:
        env_files = list(current.glob(".env*"))

        if env_files:
            for env_file in env_files:
                load_dotenv(env_file, override=True)
            break

        current = current.parent


class ApiKeyStore:
    def __init__(self, schema: dict):
        self.schema = schema
        self._keys = {}
        self._sources = {}

    def load_keys(self):
        keys = {}
        sources = {}

        for provider, env_vars in self.schema.items():
            provider = normalize_provider_name(provider)
            value = None
            source = None

            for env_var in env_vars:
                value = os.getenv(env_var)
                if value:
                    source = env_var
                    break

            keys[provider] = value
            sources[provider] = source

        self._keys = keys
        self._sources = sources

    def get_key(self, provider: str):
        return self._keys.get(normalize_provider_name(provider))

    def get_source(self, provider: str):
        return self._sources.get(normalize_provider_name(provider))



init_env()

key_store = ApiKeyStore(PROVIDER_KEY_SCHEMA)
key_store.load_keys()


def get_api_key(provider: str) -> str:
    return key_store.get_key(provider)


def get_api_key_source(provider: str) -> str:
    return key_store.get_source(provider)
