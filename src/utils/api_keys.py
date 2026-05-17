import os
from dotenv import load_dotenv
from pathlib import Path


PROVIDER_KEY_SCHEMA = {
    "anthropic": ["ANTHROPIC_API_KEY"],
    "openai": ["OPENAI_API_KEY"],

    "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],

    "xai": ["XAI_API_KEY"],
    "openrouter": ["OPENROUTER_API_KEY"],
    "mistral": ["MISTRAL_API_KEY"],

    "bedrock": ["AWS_BEARER_TOKEN_BEDROCK"],

    "cerebras": ["CEREBRAS_API_KEY"],
    "cohere": ["CO_API_KEY"],
    "groq": ["GROQ_API_KEY"],

    "ollama": ["OLLAMA_BASE_URL"],
    "huggingface": ["HF_TOKEN"],
    "github": ["GITHUB_TOKEN"],
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

    def load_keys(self):
        keys = {}

        for provider, env_vars in self.schema.items():
            value = None

            for env_var in env_vars:
                value = os.getenv(env_var)
                if value:
                    break

            keys[provider] = value

        self._keys = keys

    def get_key(self, provider: str):
        return self._keys.get(provider.lower())



init_env()

key_store = ApiKeyStore(PROVIDER_KEY_SCHEMA)
key_store.load_keys()


def get_api_key(provider: str) -> str:
    return key_store.get_key(provider)
    