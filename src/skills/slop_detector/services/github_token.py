import os
from pathlib import Path
from dotenv import load_dotenv


def get_token() -> str:
    # Walk up from this file's directory to find the project root containing .env files
    current = Path(__file__).resolve().parent

    while current != current.parent:
        env_files = list(current.glob(".env*"))

        if env_files:
            for env_file in env_files:
                load_dotenv(env_file)

            break
            
        current = current.parent

    return os.getenv("GITHUB_TOKEN")

