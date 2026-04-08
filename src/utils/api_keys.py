import os
from dotenv import load_dotenv
from pathlib import Path


def get_api_key(provider: str) -> str:
    # Walk up from this file's directory to find the project root containing .env files
    current = Path(__file__).resolve().parent

    while current != current.parent:
        env_files = list(current.glob(".env*"))

        if env_files:
            for env_file in env_files:
                load_dotenv(env_file)

            break
            
        current = current.parent


    if provider.lower() == "anthropic":
        return  os.getenv("ANTHROPIC_API_KEY")

    elif provider.lower() == "openai":
        return os.getenv("OPENAI_API_KEY")
        
    else:
        raise ValueError("Invalid provider")

