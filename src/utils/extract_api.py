def get_api_key(file_path=".env.local") -> str:
    import os
    from dotenv import load_dotenv, dotenv_values

    load_dotenv(file_path)

    API_KEY = os.getenv("ANTHROPIC_API_KEY")

    return API_KEY